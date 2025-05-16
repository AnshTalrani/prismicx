# Vector Store Service

A centralized service for managing vector embeddings and semantic search across all microservices in the PrismicX platform.

## Overview

The Vector Store Service provides a unified API for storing, managing, and retrieving vector embeddings. It supports multi-tenancy, different embedding models, and multiple vector database backends.

Key features:
- Create and manage vector stores for different bot types and domains
- Store and retrieve documents with metadata
- Perform semantic search with filters
- **NEW**: Niche-specific vector stores for efficient categorized storage and retrieval
- **NEW**: Hybrid search combining vector similarity with keyword matching
- Support for multiple embedding models (Sentence Transformers, OpenAI, HuggingFace)
- Support for multiple vector store backends (FAISS, Chroma, **NEW**: Qdrant)
- Multi-tenancy support with data isolation

## Getting Started

### Prerequisites

- Python 3.10+
- MongoDB
- Docker and Docker Compose

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB connection URL | `mongodb://localhost:27017` |
| `TENANT_MGMT_URL` | Tenant Management Service URL | `http://tenant-mgmt-service:8501` |
| `VECTOR_STORE_DIR` | Directory for storing vector data | `./data/vector_stores` |
| `NICHE_VECTOR_STORE_DIR` | Directory for niche vector stores | `./data/niche_vector_stores` |
| `OPENAI_API_KEY` | API key for OpenAI embeddings | (None) |
| `HOST` | Host to bind the service | `0.0.0.0` |
| `PORT` | Port to bind the service | `8510` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Running with Docker

```bash
# Build the Docker image
docker build -t vector-store-service .

# Run the service
docker run -p 8510:8510 \
  -e MONGODB_URL=mongodb://mongodb:27017 \
  -e TENANT_MGMT_URL=http://tenant-mgmt-service:8501 \
  -v ./data:/app/data \
  vector-store-service
```

### Running with Docker Compose

Add the following to your `docker-compose.yml`:

```yaml
services:
  vector-store-service:
    build: ./vector-store-service
    ports:
      - "8510:8510"
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - TENANT_MGMT_URL=http://tenant-mgmt-service:8501
      - VECTOR_STORE_DIR=/app/data/vector_stores
      - NICHE_VECTOR_STORE_DIR=/app/data/niche_vector_stores
    volumes:
      - ./data:/app/data
    networks:
      - service-network
      - database-network
    depends_on:
      - mongodb
```

## API Reference

### General Vector Store Management

#### Create a new vector store

```
POST /api/v1/vectors/stores
```

Request body:
```json
{
  "name": "clothing-niche",
  "description": "Vector store for clothing domain knowledge",
  "bot_type": "sales",
  "domain": "fashion",
  "store_type": "chroma",
  "embedding_model": "sentence_transformers",
  "model_name": "all-MiniLM-L6-v2",
  "tags": ["clothing", "fashion", "sales"]
}
```

#### List all vector stores

```
GET /api/v1/vectors/stores
```

#### Get vector store information

```
GET /api/v1/vectors/stores/{collection_name}
```

#### Add documents to a vector store

```
POST /api/v1/vectors/stores/{collection_name}/documents
```

Request body:
```json
{
  "documents": [
    {
      "text": "Document text content",
      "metadata": {
        "source": "clothing-catalog",
        "category": "dresses",
        "tags": ["summer", "casual"]
      }
    }
  ]
}
```

#### Search for documents

```
POST /api/v1/vectors/search
```

Request body:
```json
{
  "text": "summer dresses with floral patterns",
  "collection_name": "clothing-niche",
  "filter_metadata": {
    "category": "dresses"
  },
  "top_k": 5,
  "similarity_threshold": 0.7
}
```

#### Delete documents

```
DELETE /api/v1/vectors/stores/{collection_name}/documents
```

Request body:
```json
{
  "document_ids": ["doc1", "doc2"],
  "filter_metadata": {
    "category": "discontinued"
  }
}
```

### Niche Vector Store Management (New)

#### Create a new niche-specific vector store

```
POST /api/v1/niches/stores
```

Request body:
```json
{
  "name": "fashion-niches",
  "description": "Niche-specific vector store for fashion",
  "niches": [
    {
      "name": "summer-dresses",
      "description": "Summer dresses collection",
      "parent_niche": "dresses",
      "keywords": ["summer", "lightweight", "breathable"],
      "tags": ["seasonal", "women"],
      "bot_types": ["sales", "consultancy"]
    },
    {
      "name": "winter-jackets",
      "description": "Winter jackets collection",
      "parent_niche": "outerwear",
      "keywords": ["winter", "warm", "insulated"],
      "tags": ["seasonal", "outerwear"],
      "bot_types": ["sales"]
    }
  ],
  "store_type": "qdrant"
}
```

#### List all niches

```
GET /api/v1/niches/niches
```

Query parameters:
- `store_name` (optional): Filter by store name

#### Add documents to a niche store

```
POST /api/v1/niches/stores/{store_name}/documents
```

Request body:
```json
{
  "documents": [
    {
      "text": "Beautiful floral summer dress with adjustable straps and flowing skirt.",
      "niche": "summer-dresses",
      "sub_niche": "casual",
      "metadata": {
        "source": "summer-catalog",
        "author": "Fashion Inc.",
        "content_type": "product",
        "tags": ["summer", "casual", "floral"]
      }
    }
  ]
}
```

#### Search within a niche

```
POST /api/v1/niches/search/{store_name}
```

Request body:
```json
{
  "text": "floral pattern summer dress",
  "collection_name": "fashion-niches",
  "top_k": 5,
  "hybrid_search": true,
  "keyword_weight": 0.3
}
```

Query parameters:
- `niche` (optional): Specific niche to search within
- `sub_niche` (optional): Specific sub-niche to search within

#### Delete niche documents

```
DELETE /api/v1/niches/stores/{store_name}/documents
```

Query parameters:
- `niche` (optional): Niche to delete from
- `document_ids` (optional): IDs of documents to delete

### Admin APIs

#### Get service statistics

```
GET /api/v1/admin/stats
```

#### Rebuild database indexes

```
POST /api/v1/admin/rebuild-indexes
```

#### Clear tenant data

```
POST /api/v1/admin/clear-tenant-data/{tenant_id}
```

### Health Checks

#### Health check

```
GET /health
```

#### Ping

```
GET /ping
```

## Development

### Project Structure

```
vector-store-service/
├── app/
│   ├── models/         # Pydantic models
│   │   └── vector_store.py  # Data models for vector operations
│   │   └── niche_vector_service.py  # Niche-specific vector store service
│   ├── routers/        # API route definitions
│   │   ├── vector_store.py  # General vector store endpoints
│   │   ├── niche_store.py   # Niche-specific vector store endpoints
│   │   ├── health.py        # Health check endpoints
│   │   └── admin.py         # Admin endpoints
│   ├── services/       # Business logic
│   │   ├── vector_store_service.py  # General vector store service
│   │   └── niche_vector_service.py  # Niche-specific vector store service
│   ├── main.py         # Application entry point
│   ├── dependencies.py # Dependency injection
│   └── middleware.py   # Custom middleware
├── Dockerfile
└── requirements.txt
```

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
cd app
uvicorn main:app --host 0.0.0.0 --port 8510 --reload
```

## Integration with Other Microservices

The Vector Store Service is designed to be used by other microservices for:

1. **Communication Base**: Storing and retrieving bot-specific knowledge
2. **Expert Base**: Managing domain knowledge for expert systems
3. **Sales Bot**: Accessing niche-specific product information
4. **Consultancy Bot**: Retrieving niche expertise and domain knowledge

Example client usage:

### General Vector Search
```python
import httpx

async def search_vector_store(query, collection_name, tenant_id=None):
    async with httpx.AsyncClient() as client:
        headers = {"Content-Type": "application/json"}
        if tenant_id:
            headers["X-Tenant-ID"] = tenant_id
            
        response = await client.post(
            "http://vector-store-service:8510/api/v1/vectors/search",
            json={
                "text": query,
                "collection_name": collection_name,
                "top_k": 5
            },
            headers=headers
        )
        
        return response.json()
```

### Niche-Specific Search (New)
```python
async def search_niche(query, store_name, niche=None, tenant_id=None):
    async with httpx.AsyncClient() as client:
        headers = {"Content-Type": "application/json"}
        if tenant_id:
            headers["X-Tenant-ID"] = tenant_id
            
        params = {}
        if niche:
            params["niche"] = niche
            
        response = await client.post(
            f"http://vector-store-service:8510/api/v1/niches/search/{store_name}",
            json={
                "text": query,
                "collection_name": store_name,
                "top_k": 5,
                "hybrid_search": True
            },
            params=params,
            headers=headers
        )
        
        return response.json()
```

## Contributing

Please follow these guidelines when contributing to this service:

1. Follow the existing code style and conventions
2. Add docstrings to all functions and classes
3. Write tests for new functionality
4. Update this README with any new features or API changes

## License

This service is part of the PrismicX platform and is subject to the same license terms. 