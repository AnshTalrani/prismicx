FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port
EXPOSE 8501

# Set environment variables
ENV TENANT_SERVICE_HOST=0.0.0.0
ENV TENANT_SERVICE_PORT=8501
ENV TENANT_SERVICE_LOG_LEVEL=INFO
ENV TENANT_MONGODB_URI=mongodb://admin:password@mongodb:27017
ENV TENANT_REGISTRY_DB=tenant_registry

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8501"] 