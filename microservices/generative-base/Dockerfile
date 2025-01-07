# Dockerfile for the generative-base microservice

FROM python:3.11-slim

# Set a working directory
WORKDIR /app

# Copy source code
COPY src/ ./src
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy tests
COPY tests/ ./tests

# Run tests during build phase (basic example)
RUN python -m unittest discover -s tests

# Set the entrypoint
ENTRYPOINT ["python", "src/generative_main.py"] 