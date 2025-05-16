# Prismicx Microservices

This repository contains the microservices architecture for the Prismicx platform. The platform consists of several microservices working together to provide analysis, generative, marketing, and communication capabilities.

## Architecture

The platform follows the MACH (Microservices, API-first, Cloud-native, Headless) architecture pattern:

- **Microservices**: Each service is independently deployable with its own database
- **API-first**: All services expose well-defined REST APIs
- **Cloud-native**: Designed to run in containerized environments
- **Headless**: Backend and frontend are decoupled

### Microservices

The platform consists of the following microservices:

- **Analysis Base**: Provides analytical capabilities for data processing
- **Generative Base**: Provides generative AI capabilities
- **Communication Base**: Manages conversational interactions and operational communications
- **Marketing Base**: Specialized for marketing campaigns, segmentation, and analytics

## Service Responsibilities

### Communication Base
- Conversational interactions with users
- Session management for maintaining conversation context
- Conversation stage tracking and analysis
- LLM integration for generating responses
- Operational communications (order confirmations, status updates, etc.)

### Marketing Base
- Marketing campaign management
- Customer segmentation
- A/B testing capabilities
- Marketing analytics and reporting
- Campaign performance tracking

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for local development)
- MongoDB
- Redis

### Installation

1. Clone the repository:

```bash
git clone https://github.com/your-org/prismicx.git
cd prismicx
```

2. Start the microservices using Docker Compose:

```bash
docker-compose up -d
```

This will start all services including MongoDB and Redis.

### Service Endpoints

- **Analysis Base**: http://localhost:8100
  - Health check: http://localhost:8100/health
  - Metrics: http://localhost:8100/metrics
  - API docs: http://localhost:8100/docs

- **Generative Base**: http://localhost:8000
  - Health check: http://localhost:8000/health
  - Metrics: http://localhost:8000/metrics
  - API docs: http://localhost:8000/docs

## Development

### Local Development Setup

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
# For Analysis Base
cd microservices/analysis-base
pip install -r requirements.txt

# For Generative Base
cd microservices/generative-base
pip install -r requirements.txt
```

3. Create a `.env` file in each microservice directory with appropriate configuration.

4. Run the services:

```bash
# Analysis Base
cd microservices/analysis-base
python analysis_main.py

# Generative Base
cd microservices/generative-base
python src/main.py
```

### Project Structure

```
prismicx/
├── microservices/
│   ├── analysis-base/
│   │   ├── src/
│   │   │   ├── api/
│   │   │   ├── common/
│   │   │   ├── config/
│   │   │   ├── processing/
│   │   │   │   ├── components/
│   │   │   ├── repository/
│   │   │   └── service/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── generative-base/
│   │   ├── src/
│   │   │   ├── api/
│   │   │   ├── common/
│   │   │   ├── processing/
│   │   │   │   ├── components/
│   │   │   ├── repository/
│   │   │   └── service/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── docker-compose.yml
│
└── README.md
```

## API Usage

### Analysis Base

Request to process an analysis template:

```bash
curl -X POST http://localhost:8100/api/v1/templates/process \
  -H "Content-Type: application/json" \
  -d '{
    "template": {
      "type": "descriptive",
      "config": {
        "fields": ["revenue", "users", "engagement"]
      }
    },
    "input_data": {
      "dataset": "monthly_metrics"
    }
  }'
```

### Generative Base

Request to process a generative template:

```bash
curl -X POST http://localhost:8000/api/v1/templates/process \
  -H "Content-Type: application/json" \
  -d '{
    "template": {
      "type": "text_generation",
      "config": {
        "prompt": "Write a product description for a premium coffee maker",
        "max_tokens": 250
      }
    }
  }'
```

## License

[MIT License](LICENSE) 