FROM python:3.10-slim

WORKDIR /app

# Install system dependencies including PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app

# Default port for the service
EXPOSE 8510

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8510", "--reload"] 