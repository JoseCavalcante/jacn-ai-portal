# Build stage for shared dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies (e.g., for build or specific libraries)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY . .

# Expose ports (Backend: 8000, Frontend: 8501)
EXPOSE 8000
EXPOSE 8501

# Scripts/Command will be handled by Docker Compose or specific overrides