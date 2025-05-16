# Vector Store Service Reference

*Documentation Version: 1.1 - Last Updated: 2024*

## Overview

The Vector Store Service provides a centralized solution for managing vector embeddings and semantic search across all microservices in the PrismicX platform. It enables storing text with vector embeddings, performing semantic similarity searches, and managing multi-tenant vector databases.

The service now includes specialized support for niche-specific vector stores to efficiently organize and retrieve information for different domains (clothing, jewelry, accessories, etc.).

## Technical Details
- **Service Port**: 8510 (external and internal)
- **Database Technology**: MongoDB (metadata) + Vector Databases (FAISS, Chroma, Qdrant)
- **Database Names**: 
  - MongoDB: vector_store_system (system database)
  - Per-tenant databases: tenant_{tenant_id}
- **Docker Container**: vector-store-service

## Data Architecture

The Vector Store Service uses a hybrid approach for storing vector data:

1. **MongoDB Databases**:
   - Stores metadata about vector stores and documents
   - Maintains collection information and document references
   - Implements tenant isolation with per-tenant databases

2. **Vector Database Storage**:
   - **General Vector Stores**: FAISS/Chroma for general-purpose stores
   - **Niche Vector Stores**: Qdrant for efficient niche-based filtering
   - Organized by tenant ID and collection name
   - Persists vector embeddings and indices for efficient retrieval

3. **Multi-Tenancy**:
   - Tenant isolation at the database level (separate MongoDB databases)
   - Tenant isolation at the filesystem level (separate directories)
   - Tenant context provided via the `X-Tenant-ID` header

## Collections and Data Model

### MongoDB Collections

#### vector_stores Collection
Stores metadata about general vector stores (collections of documents).

```json
{
  "name": "clothing-niche",
  "metadata": {
    "name": "clothing-niche",
    "description": "Vector store for clothing domain knowledge",
    "bot_type": "sales",
    "domain": "fashion",
    "tags": ["clothing", "fashion", "sales"],
    "created_at": "2023-01-01T00:00:00.000Z",
    "updated_at": "2023-01-01T00:00:00.000Z",
    "vector_count": 100,
    "embedding_dim": 384,
    "store_type": "chroma",
    "embedding_model": "sentence_transformers",
    "model_name": "all-MiniLM-L6-v2"
  },
  "tenant_id": "tenant_id_123"
}
```

#### vector_documents Collection
Stores metadata about individual documents in general vector stores.

```json
{
  "id": "doc_123",
  "collection_name": "clothing-niche",
  "text": "Document text content",
  "metadata": {
    "source": "clothing-catalog",
    "author": "Fashion Inc.",
    "created_at": "2023-01-01T00:00:00.000Z",
    "content_type": "product",
    "domain": "fashion",
    "category": "dresses",
    "tags": ["summer", "casual"],
    "tenant_id": "tenant_id_123",
    "additional_metadata": {
      "price_range": "medium",
      "season": "summer"
    }
  }
}
```

#### niches Collection
Stores metadata about niche categories for niche-specific vector stores.

```json
{
  "_id": "ObjectId(...)",
  "store_name": "fashion-niches",
  "name": "summer-dresses",
  "description": "Summer dresses collection",
  "parent_niche": "dresses",
  "keywords": ["summer", "lightweight", "breathable"],
  "tags": ["seasonal", "women"],
  "bot_types": ["sales", "consultancy"],
  "created_at": "2024-01-01T00:00:00.000Z",
  "tenant_id": "tenant_id_123"
}
```

#### niche_documents Collection
Stores metadata about documents in niche-specific vector stores.

```json
{
  "id": "doc_456",
  "store_name": "fashion-niches",
  "niche": "summer-dresses",
  "sub_niche": "casual",
  "text": "Document text content",
  "metadata": {
    "source": "summer-catalog",
    "author": "Fashion Inc.",
    "created_at": "2024-01-01T00:00:00.000Z",
    "content_type": "product",
    "domain": "fashion",
    "category": "dresses",
    "tags": ["summer", "casual"],
    "tenant_id": "tenant_id_123"
  },
  "created_at": "2024-01-01T00:00:00.000Z",
  "tenant_id": "tenant_id_123"
}
```

### Filesystem Structure

The vector stores are stored on the filesystem using the following directory structure:

```
/app/data/
  ├── vector_stores/           # General-purpose vector stores 
  │   ├── system/              # System-level vector stores
  │   │   └── common-knowledge/  # Example system collection
  │   ├── tenant_123/          # Tenant-specific vector stores
  │   │   ├── clothing-niche/  # Collection: clothing-niche
  │   │   └── jewelry-niche/   # Collection: jewelry-niche
  │   └── tenant_456/          # Another tenant
  │       └── support-knowledge/ # Collection: support-knowledge
  │
  └── niche_vector_stores/     # Niche-specific vector stores (Qdrant)
      ├── system/              # System-level niche stores
      │   └── common-niches/     # Example system niche collection
      ├── tenant_123/          # Tenant-specific niche stores
      │   └── fashion-niches/    # Collection organized by niches
      └── tenant_456/          # Another tenant
          └── electronics-niches/ # Collection organized by niches
```

## API Endpoints

### General Vector Store Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/vectors/stores` | POST | Create a new vector store |
| `/api/v1/vectors/stores` | GET | List all vector stores |
| `/api/v1/vectors/stores/{collection_name}` | GET | Get vector store information |
| `/api/v1/vectors/stores/{collection_name}/documents` | POST | Add documents to a vector store |
| `/api/v1/vectors/stores/{collection_name}/documents` | DELETE | Delete documents from a vector store |
| `/api/v1/vectors/search` | POST | Search for similar documents |

### Niche Vector Store Management (New)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/niches/stores` | POST | Create a new niche-specific vector store |
| `/api/v1/niches/niches` | GET | List all available niches |
| `/api/v1/niches/stores/{store_name}/documents` | POST | Add documents to a niche store |
| `/api/v1/niches/search/{store_name}` | POST | Search within a niche store |
| `/api/v1/niches/stores/{store_name}/documents` | DELETE | Delete documents from a niche store |

### Administration

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/admin/stats` | GET | Get service statistics |
| `/api/v1/admin/rebuild-indexes` | POST | Rebuild database indexes |
| `/api/v1/admin/clear-tenant-data/{tenant_id}` | POST | Clear all data for a tenant |

### Health Checks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Check service health |
| `/ping` | GET | Simple liveness check |

## Client Usage Examples

### Create a Vector Store

```python
import httpx

async def create_vector_store(name, description, bot_type, domain, tenant_id=None):
    """Create a new vector store in the Vector Store Service."""
    url = "http://vector-store-service:8510/api/v1/vectors/stores"
    headers = {"Content-Type": "application/json"}
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id
        
    data = {
        "name": name,
        "description": description,
        "bot_type": bot_type,
        "domain": domain,
        "store_type": "chroma",
        "embedding_model": "sentence_transformers",
        "model_name": "all-MiniLM-L6-v2",
        "tags": [bot_type, domain]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        return response.json() if response.status_code == 201 else None
```

### Add Documents to a Vector Store

```python
async def add_documents(collection_name, documents, tenant_id=None):
    """Add documents to a vector store."""
    url = f"http://vector-store-service:8510/api/v1/vectors/stores/{collection_name}/documents"
    headers = {"Content-Type": "application/json"}
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id
        
    data = {
        "documents": [
            {
                "text": doc_text,
                "metadata": doc_metadata
            } for doc_text, doc_metadata in documents
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        return response.json() if response.status_code == 200 else None
```

### Search for Similar Documents

```python
async def search_vector_store(query, collection_name, tenant_id=None):
    """Search for similar documents in a vector store."""
    url = "http://vector-store-service:8510/api/v1/vectors/search"
    headers = {"Content-Type": "application/json"}
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id
        
    data = {
        "text": query,
        "collection_name": collection_name,
        "top_k": 5,
        "similarity_threshold": 0.7
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        return response.json() if response.status_code == 200 else None
```

### Create a Niche Vector Store (New)

```python
async def create_niche_store(name, niches, tenant_id=None):
    """Create a new niche-specific vector store."""
    url = "http://vector-store-service:8510/api/v1/niches/stores"
    headers = {"Content-Type": "application/json"}
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id
        
    data = {
        "name": name,
        "description": "Niche-specific vector store",
        "niches": [
            {
                "name": niche_name,
                "description": niche_description,
                "parent_niche": parent,
                "keywords": keywords,
                "tags": tags,
                "bot_types": bot_types
            } for niche_name, niche_description, parent, keywords, tags, bot_types in niches
        ],
        "store_type": "qdrant"  # Using Qdrant for niche stores
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        return response.json() if response.status_code == 201 else None
```

### Add Documents to a Niche Store (New)

```python
async def add_niche_documents(store_name, documents, tenant_id=None):
    """Add documents to a niche store."""
    url = f"http://vector-store-service:8510/api/v1/niches/stores/{store_name}/documents"
    headers = {"Content-Type": "application/json"}
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id
        
    data = {
        "documents": [
            {
                "text": doc_text,
                "niche": niche,
                "sub_niche": sub_niche,
                "metadata": doc_metadata
            } for doc_text, niche, sub_niche, doc_metadata in documents
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        return response.json() if response.status_code == 200 else None
```

### Search Within a Niche (New)

```python
async def search_niche(query, store_name, niche=None, tenant_id=None):
    """Search for documents within a specific niche."""
    url = f"http://vector-store-service:8510/api/v1/niches/search/{store_name}"
    headers = {"Content-Type": "application/json"}
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id
        
    data = {
        "text": query,
        "collection_name": store_name,
        "top_k": 5,
        "similarity_threshold": 0.7,
        "hybrid_search": True,  # Enable hybrid search
        "keyword_weight": 0.3   # Weight for keyword search component
    }
    
    params = {}
    if niche:
        params["niche"] = niche
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, params=params, headers=headers)
        return response.json() if response.status_code == 200 else None
```

## Integration with Other Microservices

The Vector Store Service is designed to be used by these microservices:

1. **Communication Base**: For storing and retrieving bot-specific knowledge
   ```python
   # In communication-base microservice
   async def get_bot_knowledge(query, bot_type, tenant_id):
       collection_name = f"{bot_type}-knowledge"
       return await search_vector_store(query, collection_name, tenant_id)
   ```

2. **Expert Base**: For domain-specific knowledge retrieval
   ```python
   # In expert-base microservice
   async def get_domain_knowledge(query, domain, tenant_id):
       collection_name = f"{domain}-expertise"
       return await search_vector_store(query, collection_name, tenant_id)
   ```

3. **Sales Bot**: For niche-specific product information (New)
   ```python
   # In sales-bot microservice
   async def get_niche_products(query, niche, tenant_id):
       store_name = "product-niches"
       return await search_niche(query, store_name, niche, tenant_id)
   ```

4. **Consultancy Bot**: For niche-specific domain knowledge (New)
   ```python
   # In consultancy-bot microservice
   async def get_niche_expertise(query, domain, niche, tenant_id):
       store_name = f"{domain}-niches"
       return await search_niche(query, store_name, niche, tenant_id)
   ```

## Environment Variables

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

## Docker Configuration

```yaml
# From docker-compose.yml
vector-store-service:
  build: ./vector-store-service
  container_name: vector-store-service
  ports:
    - "8510:8510"
  environment:
    - MONGODB_URL=mongodb://mongodb-system:27017
    - TENANT_MGMT_URL=http://tenant-mgmt-service:8501
    - VECTOR_STORE_DIR=/app/data/vector_stores
    - NICHE_VECTOR_STORE_DIR=/app/data/niche_vector_stores
    - LOG_LEVEL=INFO
  volumes:
    - ./data/vector_stores:/app/data/vector_stores
    - ./data/niche_vector_stores:/app/data/niche_vector_stores
  networks:
    - tenant-db-net
    - service-network
  depends_on:
    - mongodb-system
  restart: unless-stopped
```

## Niche-Based Vector Databases: Design & Strategy

### Overview

The vector store service implements specialized niche-based vector databases to efficiently organize and retrieve domain-specific knowledge. These vector databases provide contextualized information retrieval capabilities tailored to specific industry domains and use cases.

### Niche Vector Database Design

#### What vector databases do we need?

Our system uses **Qdrant** as the primary vector database for niche-specific information due to its efficient filtering capabilities and performance advantages for categorized data. Each niche vector database contains:

1. **Domain-specific content**: Information, terminology, and concepts specific to a particular industry or domain
2. **Use case specific data**: Content tailored for sales, consultancy, generation, and expert system needs
3. **Specialized vocabulary**: Industry-specific terminology and jargon with contextual meanings
4. **Domain-relevant frameworks**: Methodologies, best practices, and frameworks relevant to specific domains
5. **Strategic planning templates**: Templates and structures for strategic plans in different industries
6. **Pain points database**: Common challenges and pain points specific to each niche/industry

#### Content Organization by Niche

Each niche vector database is organized into these key categories:

| Niche Example | Content Types | Use Cases | Special Considerations |
|---------------|---------------|-----------|------------------------|
| Fashion/Clothing | Product descriptions, trends, materials, sizing | Sales, visual descriptions, seasonal trends | Visual elements, seasonal context |
| Jewelry | Product details, gemstones, metals, craftsmanship | Sales, appraisal, authentication | Value assessment, authentication |
| Electronics | Specifications, compatibility, troubleshooting | Technical support, comparisons, recommendations | Rapid obsolescence, technical depth |
| Financial Services | Regulations, products, risk assessments | Compliance guidance, product recommendations | Regulatory requirements, risk factors |
| Healthcare | Medical terms, procedures, compliance | Consultancy, documentation, compliance | Privacy regulations, accuracy requirements |

### Usage by Different Services

The niche vector databases serve different purposes depending on the service:

#### Sales Service Usage
- Product recommendations based on customer preferences
- Feature comparisons within specific product categories
- Pricing and positioning strategies for different market segments
- Contextual product information during customer interactions
- Sales scripts and templates tailored to specific industries

#### Consultancy Service Usage
- Industry-specific best practices and methodologies
- Domain frameworks for strategic planning
- Reference cases and implementation examples
- Regulatory and compliance information
- Industry benchmarks and performance metrics

#### Generation Service Usage
- Content templates for industry-specific documentation
- Tone and style guidelines for different domains
- Technical specifications and requirements by industry
- Visual design references and guidelines
- Formatting conventions for industry documents

#### Expert System Usage
- Specialized knowledge bases for complex problem-solving
- Root-cause analysis frameworks by domain
- Decision trees for industry-specific troubleshooting
- Implementation guidelines for technical solutions
- Quality assurance procedures and compliance checks

### System Vector Database Management

The vector database system will:

1. **Automatically populate and update** niche-specific information from authoritative sources
2. **Maintain knowledge freshness** with automated update mechanisms
3. **Track usage patterns** to optimize retrieval performance
4. **Identify knowledge gaps** based on failed retrieval attempts
5. **Suggest new content categories** based on emerging trends in each niche

### Additional Vector Database Requirements

Beyond niche-specific databases, the system requires:

1. **Cross-domain knowledge base**: For interdisciplinary queries and broader contextual understanding
2. **User interaction history**: To capture and learn from past interactions and outcomes
3. **Compliance and regulatory database**: For handling compliance requirements across domains
4. **Common objections and responses**: For consistent handling of common queries
5. **Multilingual terminology**: For international contexts and cross-language support

### Implementation Roadmap

1. **Initial phase**: Implement core niche databases for primary domains
2. **Expansion phase**: Add specialized sub-niches and more granular categorization
3. **Integration phase**: Connect vector DBs with recommendation systems and personalization
4. **Optimization phase**: Fine-tune embedding models for domain-specific semantic understanding
5. **Automation phase**: Implement self-updating mechanisms for knowledge freshness

This architecture ensures that our vector database strategy can scale with the platform's growth while maintaining specialization and contextual relevance across diverse domains and use cases. 