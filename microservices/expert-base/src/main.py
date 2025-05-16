"""
Expert Base Microservice Main Entry Point

This module initializes the expert-base microservice and its components.
"""

import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import json

from src.api.models import ExpertRequest, ExpertResponse
from src.api.routes import router as api_router
from src.common.config import settings
from src.common.exception_handlers import register_exception_handlers
from src.common.logging import setup_logging
from src.infrastructure.vector_store import get_vector_db_client
from src.infrastructure.model_provider import get_model_provider
from src.processing.factory import ProcessorFactory
from src.modules.expert_registry import ExpertRegistry
from src.modules.knowledge_hub import KnowledgeHub
from src.modules.expert_orchestrator import ExpertOrchestrator

# Initialize FastAPI app
app = FastAPI(
    title="Expert Base API",
    description="Expert Base microservice for specialized AI-powered content expertise",
    version="1.0.0"
)

# Setup logging
setup_logging()

# Setup CORS
if settings.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register exception handlers
register_exception_handlers(app)

# Register API routes
app.include_router(api_router, prefix="/api/v1")

# Initialize service components on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Expert Base microservice")
    
    try:
        # Initialize vector database client
        vector_db_client = get_vector_db_client()
        
        # Initialize model provider
        model_provider = get_model_provider()
        
        # Initialize knowledge hub
        knowledge_hub = KnowledgeHub(vector_db_client)
        
        # Initialize processor factory
        processor_factory = ProcessorFactory(model_provider)
        
        # Initialize expert registry
        expert_registry = ExpertRegistry()
        await expert_registry.load_configurations()
        
        # Initialize expert orchestrator
        expert_orchestrator = ExpertOrchestrator(
            expert_registry=expert_registry,
            processor_factory=processor_factory,
            knowledge_hub=knowledge_hub
        )
        
        # Store initialized components as app state
        app.state.expert_orchestrator = expert_orchestrator
        app.state.knowledge_hub = knowledge_hub
        
        # Seed example knowledge if in development mode
        if os.environ.get("ENVIRONMENT", "development") == "development":
            logger.info("Seeding example knowledge")
            await knowledge_hub.seed_example_knowledge()
        
        logger.info("Expert Base microservice initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Expert Base microservice: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Expert Base microservice")

@app.get("/health")
async def health_check():
    """Health check endpoint for the Expert Base microservice."""
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint for the Expert Base microservice."""
    # Check if all components are initialized
    if not hasattr(app.state, "expert_orchestrator"):
        raise HTTPException(status_code=503, detail="Expert Base not fully initialized")
    
    return {"status": "ready"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ENVIRONMENT", "development") == "development"
    ) 