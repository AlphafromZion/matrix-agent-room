FROM python:3.12-slim

# Install build dependencies for matrix-nio[e2e] (libolm)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libolm-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .

# Data directory for session/key storage
RUN mkdir -p /app/data

CMD ["python", "base_bot.py"]
