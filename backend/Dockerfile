# Stage 1: Builder
FROM python:3.9-slim as builder

WORKDIR /app

# Install build deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Configure pip for better reliability
RUN python -m pip install --upgrade pip && \
    pip config set global.retries 10 && \
    pip config set global.timeout 60

# Create and use virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.9-slim

WORKDIR /app

# Install runtime deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgomp1 \
    libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copy virtualenv
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create directory structure
RUN mkdir -p /app/db /app/scoring_models && \
    chmod -R 777 /app

# Copy app code
COPY --chown=1000:1000 . .

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ML_MODEL_PATH=/app/scoring_models/strength_model.joblib \
    DATABASE_URL=sqlite:////app/db/ai-agent.db

USER 1000

HEALTHCHECK --interval=30s --timeout=10s \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]