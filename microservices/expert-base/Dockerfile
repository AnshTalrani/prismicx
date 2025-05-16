FROM python:3.10-slim

WORKDIR /app

# Copy requirements file
COPY microservices/expert-base/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY microservices/expert-base/src/ ./src/

# Set Python path
ENV PYTHONPATH=/app

# Command to run the service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"] 