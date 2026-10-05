import json
import uuid
import datetime as dt
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from pydantic import BaseModel

from app.core.database import get_session
from app.models.entities import (
    Merchant, Customer, Transaction, CashLog, Expense, 
    UdhaarRecord, Campaign, Approval, AuditLogEntry, ScoreSnapshot
)
from app.services.metrics import MetricsService
from app.services.item_inference import ItemInferenceService
from app.services.footfall import FootfallService
from app.services.opportunities import OpportunityService
from app.services.udhaar import UdhaarService
from app.services.munim_score import MunimScoreService
from app.services.morning_brief import MorningBriefService
from app.services.voice import HinglishVoiceParser, VoiceSynthesizer
from app.services.scheduler import is_eod_ritual_active, set_eod_ritual_active
from app.agent.executor import MunimAgent
from app.agent.guardrails import GuardrailService
from app.adapters.mock_adapters import MockSoundboxAdapter, MockUPICollectAdapter, MockMessagingAdapter
from app.sim.uplift_simulator import CampaignUpliftSimulator
from app.eval.qa_benchmark import EvalRunner
from app.core.config import DATA_DIR

api_router = APIRouter()

# --- Merchants ---
@api_router.get("/merchants")
def list_merchants(session: Session = Depends(get_session)):
    merchants = session.exec(select(Merchant)).all()
    return merchants

@api_router.get("/merchants/{merchant_id}")
def get_merchant(merchant_id: str, session: Session = Depends(get_session)):
    m = session.exec(select(Merchant).where(Merchant.id == merchant_id)).first()
    if not m:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return m

# --- Financial Metrics ---
@api_router.get("/merchants/{merchant_id}/summary")
def get_summary(merchant_id: str, target_date: Optional[str] = None, session: Session = Depends(get_session)):
    d = dt.date.fromisoformat(target_date) if target_date else None
    return MetricsService.get_daily_summary(session, merchant_id, d)

@api_router.get("/merchants/{merchant_id}/trend")
def get_trend(merchant_id: str, days: int = 14, session: Session = Depends(get_session)):
    return MetricsService.get_revenue_trend(session, merchant_id, days)

@api_router.get("/merchants/{merchant_id}/heatmap")
def get_heatmap(merchant_id: str, session: Session = Depends(get_session)):
    return MetricsService.get_hourly_heatmap(session, merchant_id)

# --- Product Mix & Bayesian Item Inference ---
@api_router.get("/merchants/{merchant_id}/product-mix")
def get_product_mix(merchant_id: str, session: Session = Depends(get_session)):
    return ItemInferenceService.infer_product_mix(session, merchant_id)

class ConfirmItemRequest(BaseModel):
    amount: float
    confirmed_item: str

@api_router.post("/merchants/{merchant_id}/confirm-item")
def confirm_item(merchant_id: str, req: ConfirmItemRequest, session: Session = Depends(get_session)):
    return ItemInferenceService.confirm_price_point(
        session, merchant_id, req.amount, req.confirmed_item
    )

# --- Footfall Sensor & Live Burst Injection ---
@api_router.get("/merchants/{merchant_id}/footfall")
def get_footfall(merchant_id: str, session: Session = Depends(get_session)):
    return FootfallService.analyze_live_rate(session, merchant_id)

class BurstRequest(BaseModel):
    count: int = 16
    amount: float = 20.0

@api_router.post("/merchants/{merchant_id}/inject-burst")
def inject_burst(merchant_id: str, req: BurstRequest, session: Session = Depends(get_session)):
    result = FootfallService.inject_simulated_burst(
        session, merchant_id, req.count, req.amount
    )
    # Broadcast soundbox announcement if rush
    if result["analysis"]["status"] == "RUSH":
        GuardrailService.announce_to_soundbox(
            merchant_id, 
            result["analysis"]["announcement"]
        )
    return result

# --- Bahi-Khata Ritual & Hinglish Voice Parser ---
class VoiceParseRequest(BaseModel):
    transcript: str

@api_router.post("/bahi-khata/parse-voice")
def parse_voice(req: VoiceParseRequest):
    return HinglishVoiceParser.extract_bahi_khata_fields(req.transcript)

class BahiKhataLogRequest(BaseModel):
    cash_in: float = 0.0
    expense_category: Optional[str] = None
    expense_amount: float = 0.0
    expense_desc: Optional[str] = None
    date: Optional[str] = None

@api_router.post("/merchants/{merchant_id}/bahi-khata/log")
def log_bahi_khata(merchant_id: str, req: BahiKhataLogRequest, session: Session = Depends(get_session)):
    d = dt.date.fromisoformat(req.date) if req.date else dt.date.today()
    if req.cash_in > 0:
        c = session.exec(select(CashLog).where(CashLog.merchant_id == merchant_id, CashLog.date == d)).first()
        if not c:
            session.add(CashLog(merchant_id=merchant_id, date=d, cash_in=req.cash_in, source_text="App logged"))
        else:
            c.cash_in = req.cash_in
            session.add(c)

    if req.expense_amount > 0 and req.expense_category:
        exp = Expense(
            merchant_id=merchant_id,
            date=d,
            category=req.expense_category,
            amount=req.expense_amount,
            source_text=req.expense_desc or f"{req.expense_category} expense"
        )
        session.add(exp)

    session.commit()
    set_eod_ritual_active(False)
    return MetricsService.get_daily_summary(session, merchant_id, d)

@api_router.get("/merchants/{merchant_id}/bahi-khata/ritual-status")
def ritual_status(merchant_id: str):
    return {"end_of_day_active": is_eod_ritual_active()}

# --- Udhaar Module ---
@api_router.get("/merchants/{merchant_id}/udhaar")
def list_udhaar(merchant_id: str, session: Session = Depends(get_session)):
    return UdhaarService.get_ledger(session, merchant_id)

class AddUdhaarRequest(BaseModel):
    customer_name: str
    amount: float
    due_days: int = 7

@api_router.post("/merchants/{merchant_id}/udhaar")
def add_udhaar(merchant_id: str, req: AddUdhaarRequest, session: Session = Depends(get_session)):
    return UdhaarService.add_entry(session, merchant_id, req.customer_name, req.amount, req.due_days)

class SendReminderRequest(BaseModel):
    tone: str = "soft"  # soft | firm | funny

@api_router.post("/merchants/{merchant_id}/udhaar/{udhaar_id}/remind")
def remind_debtor(merchant_id: str, udhaar_id: int, req: SendReminderRequest, session: Session = Depends(get_session)):
    return UdhaarService.create_reminder_action(session, merchant_id, udhaar_id, req.tone)

# --- Opportunities & Recommendations ---
@api_router.get("/merchants/{merchant_id}/opportunities")
def get_opportunities(merchant_id: str, session: Session = Depends(get_session)):
    return OpportunityService.detect_all_opportunities(session, merchant_id)

@api_router.get("/merchants/{merchant_id}/explain-dip")
def explain_dip(merchant_id: str, target_date: Optional[str] = None, session: Session = Depends(get_session)):
    d = dt.date.fromisoformat(target_date) if target_date else dt.date(2026, 7, 12)
    return OpportunityService.explain_dip(session, merchant_id, d)

# --- Campaigns, Approvals & Guardrail Execution ---
@api_router.get("/merchants/{merchant_id}/campaigns")
def list_campaigns(merchant_id: str, session: Session = Depends(get_session)):
    return session.exec(select(Campaign).where(Campaign.merchant_id == merchant_id)).all()

class CreateCampaignRequest(BaseModel):
    offer_text: str
    discount_pct: float
    audience_count: int = 25
    budget: float = 500.0
    opportunity_id: Optional[int] = None

@api_router.post("/merchants/{merchant_id}/campaigns")
def create_campaign(merchant_id: str, req: CreateCampaignRequest, session: Session = Depends(get_session)):
    camp = Campaign(
        merchant_id=merchant_id,
        opportunity_id=req.opportunity_id,
        name=f"Campaign: {req.offer_text[:25]}",
        offer_text=req.offer_text,
        discount_pct=req.discount_pct,
        audience_count=req.audience_count,
        budget=req.budget,
        status="PENDING_APPROVAL"
    )
    session.add(camp)
    session.commit()

    idempotency_key = f"camp_{camp.id}_{int(req.budget)}"
    payload = {
        "campaign_id": camp.id,
        "campaign_name": camp.name,
        "offer_text": req.offer_text,
        "discount_pct": req.discount_pct,
        "audience_count": req.audience_count,
        "budget": req.budget,
        "notify_soundbox": True,
        "notice_text": f"{camp.name} taiyar hai."
    }
    return GuardrailService.process_action(
        session=session,
        merchant_id=merchant_id,
        action_name="START_CAMPAIGN",
        risk_tier=2,
        payload=payload,
        idempotency_key=idempotency_key
    )

@api_router.get("/merchants/{merchant_id}/approvals")
def list_approvals(merchant_id: str, session: Session = Depends(get_session)):
    approvals = session.exec(
        select(Approval).where(
            Approval.merchant_id == merchant_id,
            Approval.status == "PENDING_APPROVAL"
        )
    ).all()
    res = []
    for a in approvals:
        res.append({
            "id": a.id,
            "merchant_id": a.merchant_id,
            "action": a.action,
            "risk_tier": a.risk_tier,
            "payload": json.loads(a.payload),
            "status": a.status,
            "created_at": a.created_at.isoformat()
        })
    return res

class ResolveApprovalRequest(BaseModel):
    decision: str  # "APPROVED" | "REJECTED"

@api_router.post("/merchants/{merchant_id}/approvals/{approval_id}/resolve")
def resolve_approval(merchant_id: str, approval_id: int, req: ResolveApprovalRequest, session: Session = Depends(get_session)):
    return GuardrailService.resolve_approval(session, merchant_id, approval_id, req.decision)

@api_router.post("/campaigns/{campaign_id}/simulate-uplift")
def simulate_uplift(campaign_id: int, session: Session = Depends(get_session)):
    return CampaignUpliftSimulator.run_simulation(session, campaign_id)

# --- Audit Log ---
@api_router.get("/merchants/{merchant_id}/audit-log")
def get_audit_log(merchant_id: str, session: Session = Depends(get_session)):
    entries = session.exec(
        select(AuditLogEntry).where(AuditLogEntry.merchant_id == merchant_id).order_by(AuditLogEntry.ts.desc()).limit(50)
    ).all()
    return [{
        "id": e.id,
        "actor": e.actor,
        "action": e.action,
        "risk_tier": e.risk_tier,
        "payload": json.loads(e.payload),
        "idempotency_key": e.idempotency_key,
        "timestamp": e.ts.isoformat()
    } for e in entries]

# --- Munim Score ---
@api_router.get("/merchants/{merchant_id}/score")
def get_score(merchant_id: str, session: Session = Depends(get_session)):
    return MunimScoreService.evaluate_merchant_score(session, merchant_id)

# --- Morning Brief ---
@api_router.get("/merchants/{merchant_id}/morning-brief")
def get_morning_brief(merchant_id: str):
    return MorningBriefService.generate_brief(merchant_id)

# --- Chat & Soundbox Output ---
class ChatRequest(BaseModel):
    merchant_id: str
    message: str

@api_router.post("/chat")
def chat(req: ChatRequest):
    return MunimAgent.run(req.merchant_id, req.message)

@api_router.get("/merchants/{merchant_id}/soundbox/history")
def soundbox_history(merchant_id: str):
    return MockSoundboxAdapter.get_history(merchant_id)

# --- Evaluation Dashboard Endpoints ---
@api_router.get("/eval/results")
def get_eval_results():
    eval_file = DATA_DIR / "eval_results.json"
    if eval_file.exists():
        return json.loads(eval_file.read_text(encoding="utf-8"))
    return EvalRunner.run_all_evaluations()

@api_router.post("/eval/run")
def trigger_eval():
    return EvalRunner.run_all_evaluations()

# --- Voice & TTS Synthesizer ---
class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None

@api_router.post("/voice/tts")
async def generate_tts(req: TTSRequest):
    """
    Synthesize natural neural voice audio for Soundbox announcements.
    Returns the public audio URL (/api/audio/tts_xxx.mp3) and caching status.
    """
    return await VoiceSynthesizer.synthesize_speech(req.text, req.voice)
