FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port
EXPOSE 8502

# Set environment variables
ENV USER_SERVICE_HOST=0.0.0.0
ENV USER_SERVICE_PORT=8502
ENV USER_SERVICE_LOG_LEVEL=INFO
ENV USER_DB_HOST=postgres-system
ENV USER_DB_PORT=5432
ENV USER_DB_USER=user_service
ENV USER_DB_PASSWORD=password
ENV USER_DB_NAME=system_users

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8502"] 