#!/bin/bash
# Initialize the marketing-base microservice directory structure

set -e

# Create directory structure
mkdir -p src/api
mkdir -p src/config
mkdir -p src/processing
mkdir -p src/repository
mkdir -p src/service
mkdir -p src/utils
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p docs
mkdir -p deploy

# Ensure __init__.py files exist
touch src/__init__.py
touch src/api/__init__.py
touch src/config/__init__.py
touch src/processing/__init__.py
touch src/repository/__init__.py
touch src/service/__init__.py
touch src/utils/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py

# Create a .env file template
cat > .env.example << EOL
# Server settings
MARKETING_HOST=0.0.0.0
MARKETING_PORT=8000
MARKETING_LOG_LEVEL=INFO

# MongoDB settings
MARKETING_MONGODB_URI=mongodb://localhost:27017
MARKETING_MONGODB_DATABASE=marketing

# Redis settings
MARKETING_REDIS_URI=redis://localhost:6379/0
MARKETING_REDIS_PASSWORD=

# Worker settings
MARKETING_WORKER_ENABLED=true
MARKETING_WORKER_POLL_INTERVAL=60
MARKETING_WORKER_THREADS=2

# Email settings
MARKETING_SMTP_HOST=smtp.example.com
MARKETING_SMTP_PORT=587
MARKETING_SMTP_USERNAME=user@example.com
MARKETING_SMTP_PASSWORD=password
MARKETING_DEFAULT_SENDER_EMAIL=marketing@example.com
MARKETING_DEFAULT_SENDER_NAME=Marketing Team

# Security settings
MARKETING_API_KEY=your-api-key-here
MARKETING_CORS_ORIGINS=*
EOL

# Create a basic .gitignore file
cat > .gitignore << EOL
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/

# Environment variables
.env

# IDE files
.idea/
.vscode/
*.swp
*.swo

# Logs
logs/
*.log

# Coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*,cover
EOL

echo "Directory structure created successfully!"
echo "Copy .env.example to .env and customize it for your environment." 