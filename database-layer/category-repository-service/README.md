# Category Repository Service

A centralized service for managing categories, factors, batch as objects, campaigns and their relationships.

## Overview

The Category Repository Service provides a unified interface for storing and retrieving category-related data used across multiple microservices. It follows a repository pattern with MongoDB as the underlying storage.

## Key Features

- Management of category hierarchies and taxonomies
- Factor storage with metadata and performance metrics
- Batch as objects (BAO) management with JSON data
- Campaign definitions with performance tracking
- User/entity assignment management
- Caching layer for performance optimization

## API Endpoints

### Categories

- `POST /api/v1/categories` - Create a new category
- `GET /api/v1/categories/{category_id}` - Get a category by ID
- `PUT /api/v1/categories/{category_id}` - Update a category
- `DELETE /api/v1/categories/{category_id}` - Delete a category
- `GET /api/v1/categories?type={type}` - Get categories by type

### Factors

- `POST /api/v1/factors` - Create a new factor
- `GET /api/v1/factors/{factor_id}` - Get a factor by ID
- `PUT /api/v1/factors/{factor_id}` - Update a factor
- `DELETE /api/v1/factors/{factor_id}` - Delete a factor
- `GET /api/v1/categories/{category_id}/factors` - Get factors by category
- `PUT /api/v1/factors/{factor_id}/metrics` - Update factor metrics

### Batch As Objects

- `POST /api/v1/batch-as-objects` - Create a new batch as object
- `GET /api/v1/batch-as-objects/{bao_id}` - Get a batch as object by ID
- `PUT /api/v1/batch-as-objects/{bao_id}` - Update a batch as object
- `DELETE /api/v1/batch-as-objects/{bao_id}` - Delete a batch as object
- `GET /api/v1/categories/{category_id}/batch-as-objects` - Get batch as objects by category
- `PUT /api/v1/batch-as-objects/{bao_id}/metrics` - Update batch as object metrics

### Campaigns

- `POST /api/v1/campaigns` - Create a new campaign
- `GET /api/v1/campaigns/{campaign_id}` - Get a campaign by ID
- `PUT /api/v1/campaigns/{campaign_id}` - Update a campaign
- `DELETE /api/v1/campaigns/{campaign_id}` - Delete a campaign
- `GET /api/v1/categories/{category_id}/campaigns` - Get campaigns by category
- `PUT /api/v1/campaigns/{campaign_id}/metrics` - Update campaign metrics

### Assignments

- `POST /api/v1/assignments` - Create a new entity assignment
- `DELETE /api/v1/assignments` - Delete an entity assignment
- `GET /api/v1/items/{category_type}/{item_id}/entities` - Get entities assigned to an item
- `GET /api/v1/entities/{entity_type}/{entity_id}/items` - Get items assigned to an entity
- `GET /api/v1/entities/{entity_type}/{entity_id}/details/{category_type}` - Get detailed item information
- `GET /api/v1/assignments/check` - Check if an entity is assigned to an item

## Configuration

The service is configured using environment variables:

```
MONGODB_URI=mongodb://username:password@mongodb:27017/
MONGODB_DATABASE=category_repository
API_KEY=your_secret_api_key
```

## Development

### Prerequisites

- Python 3.10 or higher
- MongoDB

### Local Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with required environment variables
6. Run the service: `uvicorn src.main:app --reload`

### Docker Setup

1. Build the Docker image: `docker build -t category-repository-service .`
2. Run the container: `docker run -p 8080:8080 --env-file .env category-repository-service`

## Integration

To integrate with this service from other microservices, use the provided endpoints with proper authentication. Include the `X-API-Key` header in all requests.

## Schema

See the [models/category.py](./src/models/category.py) file for the complete data schema. 