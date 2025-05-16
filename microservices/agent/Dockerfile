# Purpose: Defines the Docker configuration for building and running the agent microservice.

# Dockerfile for the agent microservice

FROM python:3.9-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create directory for shared modules
RUN mkdir -p /app/database-layer/common

# Copy common library for task repository
COPY database-layer/common/ /app/database-layer/common/

# Copy requirements file
COPY microservices/agent/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e /app/database-layer/common/ \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY microservices/agent/ .

# Expose API port
EXPOSE 8000

# Set task repository environment variables
ENV TASK_REPO_URL=http://task-repo-service:8503 \
    TASK_REPO_API_KEY=dev_api_key \
    SERVICE_ID=agent-service \
    CONTEXT_CLEANUP_INTERVAL_HOURS=24 \
    COMPLETED_CONTEXT_TTL=86400 \
    FAILED_CONTEXT_TTL=604800

# Run the application with uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"] 