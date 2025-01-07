# Dockerfile for the marketing-base microservice

FROM python:3.11-slim

WORKDIR /app

# Copy source code
COPY src/ ./src
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# Copy tests
COPY tests/ ./tests

RUN python -m unittest discover -s tests

ENTRYPOINT ["python", "src/marketing_main.py"] 