# Outreach System

A comprehensive AI-powered outreach and communication platform that combines speech recognition, natural language processing, emotion detection, and text-to-speech capabilities for intelligent customer outreach and engagement.

## 🚀 Features

- **Speech-to-Text (ASR)**: Real-time audio transcription using Whisper
- **Language Models**: Integration with OpenAI, Anthropic, and local LLMs
- **Text-to-Speech (TTS)**: High-quality voice synthesis with Kokoro
- **Emotion Detection**: Multimodal emotion analysis from audio and text
- **Campaign Management**: Comprehensive campaign orchestration and workflow management
- **Real-time Communication**: WebSocket-based real-time messaging
- **Analytics & Reporting**: Advanced analytics and insights
- **Health Monitoring**: Comprehensive system health monitoring
- **Multi-tenant Architecture**: Scalable multi-tenant support

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Architecture](#architecture)
- [Development](#development)
- [Deployment](#deployment)
- [Contributing](#contributing)

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+

### Quick Start with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd outreach
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the services:
```bash
docker-compose up -d
```

4. Access the application:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Grafana: http://localhost:3000 (admin/admin)

### Manual Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export DATABASE_URL="postgresql://user:password@localhost/outreach"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="your-secret-key"
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the application:
```bash
uvicorn src.main:app --reload
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `SECRET_KEY` | Application secret key | Required |
| `DEBUG` | Debug mode | `False` |
| `ENVIRONMENT` | Environment name | `development` |
| `OPENAI_API_KEY` | OpenAI API key | None |
| `ANTHROPIC_API_KEY` | Anthropic API key | None |
| `WHISPER_MODEL_SIZE` | Whisper model size | `base` |
| `LLM_PROVIDER` | LLM provider | `openai` |

### AI Model Configuration

The system supports multiple AI model configurations:

#### ASR (Speech-to-Text)
- **Provider**: Whisper
- **Model Sizes**: tiny, base, small, medium, large
- **Languages**: Multi-language support

#### LLM (Language Models)
- **Providers**: OpenAI, Anthropic, Local models
- **Models**: GPT-3.5, GPT-4, Claude, LLaMA, etc.

#### TTS (Text-to-Speech)
- **Provider**: Kokoro
- **Features**: Voice customization, emotion-aware synthesis

#### Emotion Detection
- **Type**: Multimodal (audio + text)
- **Categories**: happy, sad, angry, neutral, excited, calm, etc.

## 📖 Usage

### Creating a Campaign

```python
from outreach.src.models.schemas import CampaignCreate

campaign_data = CampaignCreate(
    name="Welcome Campaign",
    description="Welcome new customers",
    campaign_type="outbound",
    workflow_id=workflow_id
)

response = await client.post("/api/v1/campaigns/", json=campaign_data.dict())
```

### Starting a Conversation

```python
from outreach.src.models.schemas import ConversationCreate

conversation_data = ConversationCreate(
    campaign_id=campaign_id,
    contact_id=contact_id,
    initial_message=MessageCreate(
        content="Hello! How can I help you today?",
        content_type="text/plain"
    )
)

response = await client.post("/api/v1/conversations/", json=conversation_data.dict())
```

### Real-time Communication

```javascript
// WebSocket connection
const ws = new WebSocket(`ws://localhost:8000/api/v1/conversations/${conversationId}/ws`);

// Send message
ws.send(JSON.stringify({
    type: "message",
    data: {
        content: "Hello!",
        content_type: "text/plain"
    }
}));

// Receive messages
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Received:", data);
};
```

## 📚 API Documentation

### Core Endpoints

#### Campaigns
- `POST /api/v1/campaigns/` - Create campaign
- `GET /api/v1/campaigns/` - List campaigns
- `GET /api/v1/campaigns/{id}` - Get campaign
- `PUT /api/v1/campaigns/{id}` - Update campaign
- `DELETE /api/v1/campaigns/{id}` - Delete campaign
- `POST /api/v1/campaigns/{id}/start` - Start campaign
- `POST /api/v1/campaigns/{id}/pause` - Pause campaign
- `POST /api/v1/campaigns/{id}/resume` - Resume campaign

#### Conversations
- `POST /api/v1/conversations/` - Create conversation
- `GET /api/v1/conversations/` - List conversations
- `GET /api/v1/conversations/{id}` - Get conversation
- `POST /api/v1/conversations/{id}/messages` - Send message
- `GET /api/v1/conversations/{id}/messages` - Get messages
- `POST /api/v1/conversations/{id}/end` - End conversation
- `GET /api/v1/conversations/{id}/state` - Get conversation state
- `PUT /api/v1/conversations/{id}/state` - Update conversation state

#### Analytics
- `GET /api/v1/analytics/campaigns` - Campaign analytics
- `GET /api/v1/analytics/conversations` - Conversation analytics
- `GET /api/v1/analytics/performance` - Performance analytics
- `GET /api/v1/analytics/models` - Model analytics
- `GET /api/v1/analytics/emotions` - Emotion analytics

#### Health
- `GET /api/v1/health/` - Basic health check
- `GET /api/v1/health/detailed` - Detailed health check
- `GET /api/v1/health/models` - Model health
- `GET /api/v1/health/database` - Database health
- `GET /api/v1/health/redis` - Redis health

### WebSocket Endpoints

- `WS /api/v1/conversations/{id}/ws` - Real-time conversation

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   AI Models     │    │   Database      │
│                 │    │                 │    │                 │
│ - API Routes    │◄──►│ - ASR (Whisper) │    │ - PostgreSQL    │
│ - WebSocket     │    │ - LLM (OpenAI)  │    │ - Redis         │
│ - Middleware    │    │ - TTS (Kokoro)  │    │                 │
│ - Services      │    │ - Emotion       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Monitoring    │    │   Analytics     │    │   External      │
│                 │    │                 │    │   Services      │
│ - Prometheus    │    │ - Metrics       │    │ - Email         │
│ - Grafana       │    │ - Reports       │    │ - SMS           │
│ - Health Checks │    │ - Insights      │    │ - APIs          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow

1. **Campaign Creation**: User creates campaign with workflow definition
2. **Contact Processing**: System processes contacts and creates conversations
3. **AI Processing**: ASR, LLM, TTS, and emotion models process interactions
4. **Real-time Communication**: WebSocket handles real-time messaging
5. **Analytics**: System collects metrics and generates insights
6. **Reporting**: Comprehensive reports and dashboards

## 🧪 Development

### Setting up Development Environment

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Set up pre-commit hooks:
```bash
pre-commit install
```

3. Run tests:
```bash
pytest
```

4. Run linting:
```bash
black src/
isort src/
flake8 src/
mypy src/
```

### Project Structure

```
outreach/
├── src/
│   ├── api/                 # API endpoints
│   ├── config/              # Configuration
│   ├── core/                # Core business logic
│   ├── models/              # AI models and data models
│   ├── repositories/        # Data access layer
│   ├── services/            # Business services
│   └── utils/               # Utilities
├── tests/                   # Test suite
├── docs/                    # Documentation
├── monitoring/              # Monitoring configuration
├── nginx/                   # Nginx configuration
├── docker-compose.yml       # Docker services
├── Dockerfile              # Docker build
├── requirements.txt         # Dependencies
└── README.md               # This file
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test
pytest tests/test_campaigns.py

# Run integration tests
pytest tests/integration/
```

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**:
```bash
export ENVIRONMENT=production
export DEBUG=false
export SECRET_KEY=<secure-secret-key>
```

2. **Database Migration**:
```bash
alembic upgrade head
```

3. **Docker Deployment**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

4. **Kubernetes Deployment**:
```bash
kubectl apply -f k8s/
```

### Monitoring

- **Metrics**: Prometheus + Grafana
- **Logs**: Structured JSON logging
- **Health Checks**: `/health` endpoints
- **Alerts**: Configured in Prometheus

### Scaling

- **Horizontal Scaling**: Multiple application instances
- **Load Balancing**: Nginx reverse proxy
- **Database**: Read replicas and connection pooling
- **Caching**: Redis for session and model caching

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run tests and linting: `make test`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation
- Use conventional commit messages
- Add type hints to all functions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [API Docs](http://localhost:8000/docs)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

## 🔗 Links

- [Project Homepage](https://github.com/your-repo)
- [API Documentation](http://localhost:8000/docs)
- [Architecture Documentation](docs/architecture.md)
- [Deployment Guide](docs/deployment.md) 