# Dockerfile for the expert-bots microservice

FROM python:3.11-slim

WORKDIR /app

COPY src/ ./src
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY tests/ ./tests

RUN python -m unittest discover -s tests

ENTRYPOINT ["python", "src/expert_bots_main.py"] 