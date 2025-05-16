"""
Main application entry point for the Agent microservice with PostgreSQL multi-tenant support.
"""
import os
import logging
import asyncio
import sys
from typing import Dict, Any
import signal

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# Import repositories
from src.infrastructure.repositories.template_repository import FileTemplateRepository
from src.infrastructure.repositories.request_repository import InMemoryRequestRepository
from src.infrastructure.repositories.file_purpose_repository import FilePurposeRepository
from src.infrastructure.clients.category_repository_client import CategoryRepositoryClient

# Import PostgreSQL repositories and utilities
from src.postgres_migration.infrastructure.repositories.postgres_context_repository import PostgresContextRepository
from src.postgres_migration.infrastructure.middleware.tenant_middleware import TenantMiddleware
from src.postgres_migration.utils.database_initializer import initialize_database
from src.postgres_migration.infrastructure.repositories.postgres_connection_manager import close_pools

# Import services
from src.application.services.default_nlp_service import DefaultNLPService
from src.application.services.template_service import TemplateService
from src.application.services.context_manager import ContextManager
from src.application.services.output_manager import OutputManager
from src.application.services.default_orchestration_service import DefaultOrchestrationService
from src.application.services.logging_communication_service import LoggingCommunicationService
from src.application.services.request_service import RequestService
from src.application.services.batch_processor import BatchProcessor
from microservices.agent.src.infrastructure.services.batch_scheduler import BatchScheduler

# Import interfaces
from src.application.interfaces.template_service import ITemplateService
from src.application.interfaces.nlp_service import INLPService
from src.application.interfaces.orchestration_service import IOrchestrationService
from src.application.interfaces.communication_service import ICommunicationService
from src.application.interfaces.request_service import IRequestService
from src.application.interfaces.repository.category_repository import ICategoryRepository

# Import API routers
from src.api.consultancy_bot_api import router as bot_router
from src.infrastructure.services.consultancy_bot_handler import ConsultancyBotHandler

# Import ID utilities
from src.utils.id_utils import generate_request_id, generate_batch_id, validate_request_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Agent Microservice (PostgreSQL)")

# Add tenant middleware
app.add_middleware(TenantMiddleware, header_name="X-Tenant-ID")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create shared services
template_repository = FileTemplateRepository()
request_repository = InMemoryRequestRepository()
purpose_repository = FilePurposeRepository(template_repository=template_repository)
nlp_service = DefaultNLPService(purpose_repository)
template_service = TemplateService(
    template_repository=template_repository,
    purpose_repository=purpose_repository
)

# Create context repository, manager and output manager
# Use the PostgresContextRepository
conditions_path = os.getenv("CONTEXT_CONDITIONS_PATH", "data/context/context_conditions.json")

# Create the PostgresContextRepository
postgres_repository = PostgresContextRepository()
logger.info("Using PostgresContextRepository for multi-tenant contexts")

# Create output manager with the repository
output_manager = OutputManager(repository=postgres_repository)

# Get cleanup interval from environment
cleanup_interval_hours = int(os.getenv("CONTEXT_CLEANUP_INTERVAL_HOURS", "24"))

# Create context manager with cleanup functionality
context_manager = ContextManager(
    repository=postgres_repository,
    output_manager=output_manager,
    conditions_path=conditions_path,
    cleanup_interval_hours=cleanup_interval_hours
)

logger.info("Using PostgreSQL for context management")

# Create other services
orchestration_service = DefaultOrchestrationService(context_manager=context_manager)
communication_service = LoggingCommunicationService()
request_service = RequestService(
    request_repository=request_repository,
    template_service=template_service,
    context_manager=context_manager,
    orchestration_service=orchestration_service,
    communication_service=communication_service,
    nlp_service=nlp_service
)

# Initialize the category repository client
category_repository_url = os.getenv("CATEGORY_REPOSITORY_URL", "http://category-service:8080/api")
category_repository_api_key = os.getenv("CATEGORY_REPOSITORY_API_KEY", "")
category_repository = CategoryRepositoryClient(
    base_url=category_repository_url,
    api_key=category_repository_api_key
)

# Get batch processing configuration from environment variables
max_concurrent_items = int(os.getenv("BATCH_MAX_CONCURRENT_ITEMS", "5"))
retry_limit = int(os.getenv("BATCH_RETRY_LIMIT", "3"))

# Initialize batch processor with all required dependencies
batch_processor = BatchProcessor(
    context_manager=context_manager,
    request_service=request_service,
    category_repository=category_repository,
    max_concurrent_items=max_concurrent_items,
    retry_limit=retry_limit
)
batch_scheduler = BatchScheduler(batch_processor)

# Create API dependencies
def get_template_service():
    return template_service

def get_request_service():
    return request_service

def get_batch_processor():
    return batch_processor

def get_category_repository():
    return category_repository

def get_consultancy_bot_handler():
    return ConsultancyBotHandler(request_service)

def get_context_manager():
    return context_manager

def get_output_manager():
    return output_manager

# Add API routers
app.include_router(bot_router, dependencies=[Depends(get_consultancy_bot_handler)])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok", 
        "service": "agent",
        "context_storage": "postgresql-multi-tenant",
        "tenant_aware": True
    }

# Admin endpoint to manually run context cleanup
@app.post("/admin/context/cleanup")
async def run_context_cleanup(days: int = 30):
    """Run manual context cleanup."""
    deleted_count = await context_manager.run_manual_cleanup(days)
    return {
        "status": "completed",
        "deleted_count": deleted_count
    }

# Background task to periodically process pending contexts
async def process_pending_contexts():
    """Periodically process pending contexts."""
    while True:
        try:
            count = await context_manager.process_pending_contexts()
            if count > 0:
                logger.info(f"Processed {count} pending contexts")
        except Exception as e:
            logger.error(f"Error processing pending contexts: {str(e)}")
        
        # Sleep for a while before checking again
        await asyncio.sleep(30)  # Check every 30 seconds

# Background task to periodically promote waiting contexts
async def promote_waiting_contexts():
    """Periodically promote waiting contexts to prevent starvation."""
    while True:
        try:
            # Wait first to allow system to initialize
            await asyncio.sleep(300)  # Wait 5 minutes after startup
            
            # Promote contexts that have been waiting too long
            promoted = await context_manager.promote_waiting_contexts()
            if promoted > 0:
                logger.info(f"Promoted {promoted} waiting contexts")
                
            # Sleep for a while before checking again
            await asyncio.sleep(300)  # Check every 5 minutes
                
        except Exception as e:
            logger.error(f"Error promoting waiting contexts: {str(e)}")
            await asyncio.sleep(60)  # Wait a minute before trying again

# Startup handler
@app.on_event("startup")
async def startup_event():
    """Initialize database, background tasks and services on startup."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, handle_exit_signal)
    signal.signal(signal.SIGTERM, handle_exit_signal)

    try:
        # Initialize the database first
        success = await initialize_database()
        if not success:
            logger.error("Failed to initialize database, some features may not work correctly")
        
        # Start the context cleanup task
        await context_manager.start_cleanup_task()
        logger.info("Started context cleanup task")
        
        # Start the context promotion task
        await context_manager.start_promotion_task()
        logger.info("Started context promotion task")
        
        # Start batch scheduler
        await batch_scheduler.start()
        logger.info("Started batch scheduler")
        
        # Start background processing tasks
        asyncio.create_task(process_pending_contexts())
        asyncio.create_task(promote_waiting_contexts())
        logger.info("Started background processing tasks")
        
        logger.info("Agent microservice startup complete (PostgreSQL multi-tenant mode)")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")

# Shutdown handler
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    try:
        # Stop batch scheduler
        await batch_scheduler.stop()
        logger.info("Stopped batch scheduler")
        
        # Stop context promotion task
        await context_manager.stop_promotion_task()
        logger.info("Stopped context promotion task")
        
        # Stop context cleanup task
        await context_manager.stop_cleanup_task()
        logger.info("Stopped context cleanup task")
        
        # Close database connection pools
        await close_pools()
        logger.info("Closed database connection pools")
        
        logger.info("Completed shutdown cleanup")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# Signal handler for graceful shutdown
def handle_exit_signal(sig, frame):
    """Handle termination signals to allow graceful shutdown."""
    logger.info(f"Received termination signal {sig}, initiating shutdown...")
    sys.exit(0)

# Main entry point for running directly
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    uvicorn.run("postgres_migration.main_pg:app", host=host, port=port, reload=reload) 