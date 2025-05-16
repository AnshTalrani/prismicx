# Use official Python image as base
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 5000

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . .

# Create necessary directories if they don't exist
RUN mkdir -p config

# Create a default empty templates.json if it doesn't exist
RUN if [ ! -f config/templates.json ]; then echo "{}" > config/templates.json; fi

# Expose port
EXPOSE $PORT

# Set the entrypoint to run the API
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:5000", "api.user_insight_api:app"] 