# Production container pinned to Python 3.11
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (curl, ffmpeg for audio processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy source code and documentation
COPY backend/ /app/backend/
COPY data/ /app/data/
COPY docs/ /app/docs/

# Seed initial database if not present
RUN python -m backend.app.sim.seed

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
