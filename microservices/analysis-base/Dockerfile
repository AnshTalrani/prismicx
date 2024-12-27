FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src /app/src
ENV PYTHONPATH="${PYTHONPATH}:/app/src"
CMD ["uvicorn", "src.analysis_main:app", "--host", "0.0.0.0", "--port", "8100"] 
RUN ls -R /app
RUN python -c "import src.analysis_main" 