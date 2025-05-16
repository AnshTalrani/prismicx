# Use an official Python runtime as the base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PORT=8000 \
    CAMPAIGN_CHECK_INTERVAL=60 \
    TASK_CHECK_INTERVAL=30 \
    METRICS_PORT=8080 \
    MAX_BATCH_SIZE=100 \
    WORKER_ID="" \
    # Task Repository Service configuration
    TASK_REPO_URL=http://task-repo-service:8503 \
    TASK_REPO_API_KEY=dev_api_key \
    SERVICE_ID=marketing-service

# Create non-root user for running the container
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create app directories
RUN mkdir -p /app/logs && chown -R appuser:appuser /app/logs

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl \
       gcc \
       python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create directory structure for database layer
RUN mkdir -p /app/database-layer/common

# Copy requirements first for layer caching
COPY requirements.txt .

# Copy database layer common package
COPY --from=database-layer /app/common /app/database-layer/common

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

# Install database layer common package
RUN pip install --no-cache-dir -e /app/database-layer/common

# Install additional dependencies for batch processing
RUN pip install --no-cache-dir prometheus_client structlog

# Copy application code
COPY . .

# Create volume for persistent data
VOLUME ["/app/data"]

# Expose ports (API and metrics)
EXPOSE ${PORT} ${METRICS_PORT}

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:${METRICS_PORT}/metrics || exit 1

# Add configuration comment
# Note: This microservice uses the centralized task repository service (task-repo-service)
# for all task management operations. The old PostgreSQL task repository has been removed.
# The TaskRepositoryAdapter connects to the task-repo-service via its REST API.

# Switch to non-root user
USER appuser

# Define entrypoint and command
ENTRYPOINT ["python"]
CMD ["-m", "src.interfaces.workers.campaign_processor"] 