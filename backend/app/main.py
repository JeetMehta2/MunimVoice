import json
import logging
from contextlib import asynccontextmanager
from typing import Dict, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db
from app.core.ground_truth_db import init_ground_truth_db
from app.api.routes import api_router
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("munim")

# WebSocket Live Event Hub
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, merchant_id: str, websocket: WebSocket):
        await websocket.accept()
        if merchant_id not in self.active_connections:
            self.active_connections[merchant_id] = []
        self.active_connections[merchant_id].append(websocket)

    def disconnect(self, merchant_id: str, websocket: WebSocket):
        if merchant_id in self.active_connections:
            if websocket in self.active_connections[merchant_id]:
                self.active_connections[merchant_id].remove(websocket)

    async def broadcast_event(self, merchant_id: str, event_type: str, data: dict):
        if merchant_id in self.active_connections:
            payload = json.dumps({"type": event_type, "data": data})
            for connection in self.active_connections[merchant_id]:
                try:
                    await connection.send_text(payload)
                except Exception:
                    pass

ws_manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Munim backend databases...")
    init_db()
    init_ground_truth_db()
    logger.info("Precaching default Soundbox voice announcements...")
    from app.services.voice import VoiceSynthesizer
    VoiceSynthesizer.precache_defaults()
    logger.info("Starting background scheduler...")
    start_scheduler()
    yield
    # Shutdown
    logger.info("Stopping background scheduler...")
    stop_scheduler()

app = FastAPI(
    title="Munim - AI Business Partner for Paytm Merchants",
    description="Voice-first business copilot for Indian merchants. Simulated Soundbox, item inference, and credit scoring.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router, prefix="/api")

# Mount static audio files
settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/audio", StaticFiles(directory=str(settings.AUDIO_DIR)), name="audio")

@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "version": "1.0.0", "app": "Munim"}

@app.websocket("/ws/live/{merchant_id}")
async def websocket_endpoint(websocket: WebSocket, merchant_id: str):
    await ws_manager.connect(merchant_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("action") == "PING":
                    await websocket.send_text(json.dumps({"type": "PONG"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(merchant_id, websocket)

# Mount built frontend SPA fallback at root
FRONTEND_DIST = settings.AUDIO_DIR.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
