# Purpose: Defines the Docker configuration for building and running the agent microservice.

# Dockerfile for the agent microservice

FROM python:3.11-slim

WORKDIR /app

# Copy only the requirements file to leverage Docker cache
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY src/ ./src

# Expose the port the app runs on
EXPOSE 80

# Use uvicorn as the entry point for FastAPI
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"] 