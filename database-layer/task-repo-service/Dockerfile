FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY src/ ./src/

# Create non-root user
RUN addgroup --system app && adduser --system --group app
USER app

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8503
ENV HOST=0.0.0.0

# Run the application
CMD ["python", "-m", "src.main"] 