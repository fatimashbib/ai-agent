FROM python:3.9-slim-bullseye

WORKDIR /app

# Create directories with proper permissions
RUN mkdir -p /app/db && \
    mkdir -p /app/scoring_models && \
    chmod -R 777 /app/db && \
    chmod -R 777 /app/scoring_models

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install DeepSeek SDK (if available) or prepare for API usage
RUN pip install --no-cache-dir requests numpy scikit-learn joblib

# Copy application code
COPY . .

# Environment variables
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:////app/db/ai-agent.db
ENV DEEPSEEK_API_KEY=sk-c2f1f20e654441eb8ba47f51ce683c40

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]