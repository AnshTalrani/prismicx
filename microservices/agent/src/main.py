"""
Main application entry point for the Agent microservice.
"""
import os
import logging
import asyncio
import sys
from typing import Dict, Any
import signal
import httpx

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# Import repositories
from src.infrastructure.repositories.template_repository import FileTemplateRepository
from src.infrastructure.repositories.in_memory_request_repository import InMemoryRequestRepository
from src.infrastructure.repositories.file_purpose_repository import FilePurposeRepository
from src.infrastructure.clients.category_repository_client import CategoryRepositoryClient
# Import TaskRepositoryAdapter
from src.infrastructure.repositories.task_repository_adapter import TaskRepositoryAdapter
from src.config.task_repository_config import SERVICE_ID as DEFAULT_SERVICE_ID
# Import UserRepository
from src.infrastructure.repositories.user_repository import UserRepository

# Import services
from src.application.services.default_nlp_service import DefaultNLPService
from src.application.services.template_service import TemplateService
from src.application.services.context_manager import ContextManager
from src.application.services.output_manager import OutputManager
from src.application.services.default_orchestration_service import DefaultOrchestrationService
from src.application.services.logging_communication_service import LoggingCommunicationService
from src.application.services.request_service import RequestService
from src.application.services.batch_processor import BatchProcessor
from src.infrastructure.services.batch_scheduler import BatchScheduler

# Import interfaces
from src.application.interfaces.template_service import ITemplateService
from src.application.interfaces.nlp_service import INLPService
from src.application.interfaces.orchestration_service import IOrchestrationService
from src.application.interfaces.communication_service import ICommunicationService
from src.application.interfaces.request_service import IRequestService
from src.application.interfaces.repository.category_repository import ICategoryRepository

# Import API routers
from src.api.consultancy_bot_api import router as bot_router
from src.api.batch_api import router as batch_router
from src.infrastructure.services.consultancy_bot_handler import ConsultancyBotHandler
from src.api import dependencies

# Import ID utilities
from src.utils.id_utils import generate_request_id, generate_batch_id, validate_request_id

# Import ConfigDatabaseClient
from src.infrastructure.clients.config_database_client import ConfigDatabaseClient

# Get configuration values
service_id = os.getenv("SERVICE_ID", "agent-service")
conditions_path = os.getenv("CONTEXT_CONDITIONS_PATH", "data/context/context_conditions.json")

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
app = FastAPI(title="Agent Microservice")

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
purpose_repository = FilePurposeRepository()  # Load purposes from config
nlp_service = DefaultNLPService(purpose_repository)
template_service = TemplateService(
    template_repository=template_repository,
    purpose_repository=purpose_repository
)

# Initialize the user repository for system_users database access
user_repository = UserRepository()

# Create the TaskRepositoryAdapter to connect to the task-repo-service in database layer
task_repository = TaskRepositoryAdapter(service_id=service_id)
logger.info(f"Using TaskRepositoryAdapter with service_id: {service_id}")

# Create output manager with the task repository
output_manager = OutputManager(repository=task_repository, user_repository=user_repository)

# Get cleanup interval from environment
cleanup_interval_hours = int(os.getenv("CONTEXT_CLEANUP_INTERVAL_HOURS", "24"))

# Create context manager with cleanup functionality
context_manager = ContextManager(
    repository=task_repository,
    output_manager=output_manager,
    conditions_path=conditions_path,
    cleanup_interval_hours=cleanup_interval_hours,
    user_repository=user_repository
)

logger.info("Using Task Repository Service in database layer for context management")

# Create other services
orchestration_service = DefaultOrchestrationService(context_manager=context_manager)
communication_service = LoggingCommunicationService()
request_service = RequestService(
    request_repository=request_repository,
    template_service=template_service,
    context_manager=context_manager,
    orchestration_service=orchestration_service,
    communication_service=communication_service,
    nlp_service=nlp_service,
    user_repository=user_repository
)

# Initialize the category repository client
category_repository_url = os.getenv("CATEGORY_REPOSITORY_URL", "http://category-repository-service:8080/api/v1")
category_repository_api_key = os.getenv("CATEGORY_REPOSITORY_API_KEY", "")
category_repository = CategoryRepositoryClient(
    base_url=category_repository_url,
    api_key=category_repository_api_key
)

# Get batch processing configuration from environment variables
max_concurrent_items = int(os.getenv("BATCH_MAX_CONCURRENT_ITEMS", "5"))
retry_limit = int(os.getenv("BATCH_RETRY_LIMIT", "3"))
config_cache_ttl = int(os.getenv("CONFIG_CACHE_TTL", "3600"))
config_poll_interval = int(os.getenv("CONFIG_POLL_INTERVAL", "60"))

# Initialize HTTP client for config database
http_client = httpx.AsyncClient(
    timeout=30.0,
    base_url=os.getenv("CONFIG_SERVICE_URL", "http://config-service:8000"),
    headers={
        "Authorization": f"Bearer {os.getenv('CONFIG_SERVICE_API_KEY', '')}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
)

# Initialize config database client
config_db_client = ConfigDatabaseClient(
    base_url=os.getenv("CONFIG_SERVICE_URL", "http://config-service:8000"),
    timeout=30.0,
    api_key=os.getenv('CONFIG_SERVICE_API_KEY', '')
)

# Initialize batch processor with all required dependencies
batch_processor = BatchProcessor(
    context_manager=context_manager,
    request_service=request_service,
    category_repository=category_repository,
    config_db_client=config_db_client,
    user_repository=user_repository,
    max_concurrent_items=max_concurrent_items,
    retry_limit=retry_limit
)

# Initialize batch scheduler with config database client
batch_scheduler = BatchScheduler(
    batch_processor=batch_processor,
    config_db_client=config_db_client
)
batch_scheduler.change_poll_interval = config_poll_interval

logger.info("BatchProcessor and BatchScheduler initialized with Config Database integration")

# Set up dependency injection for API routes
dependencies.set_batch_processor(batch_processor)
dependencies.set_request_service(request_service)
dependencies.set_template_service(template_service)
dependencies.set_context_manager(context_manager)
dependencies.set_output_manager(output_manager)
dependencies.set_user_repository(user_repository)
dependencies.set_consultancy_bot_handler(ConsultancyBotHandler(request_service, user_repository=user_repository))
dependencies.set_category_repository(category_repository)

# Create API dependencies (kept for backward compatibility)
def get_template_service():
    return template_service

def get_request_service():
    return request_service

def get_batch_processor():
    return batch_processor

def get_category_repository():
    return category_repository

def get_consultancy_bot_handler():
    return ConsultancyBotHandler(request_service, user_repository=user_repository)

def get_context_manager():
    return context_manager

def get_output_manager():
    return output_manager

def get_user_repository():
    return user_repository

# Add API routers
app.include_router(bot_router, dependencies=[Depends(get_consultancy_bot_handler)])
app.include_router(batch_router, dependencies=[Depends(get_batch_processor)])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok", 
        "service": "agent",
        "context_storage": "database_layer_task_repository",
        "storage_service": "task-repo-service"
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
    """
    Execute startup tasks.
    """
    global batch_processor, batch_scheduler
    
    logger.info("Agent microservice starting up")
    
    # Initialize user repository
    try:
        await user_repository.initialize()
        logger.info("User repository initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize user repository: {str(e)}")
        # Continue startup - we don't want to prevent the service from starting
        # if user repository initialization fails
    
    # Start the context cleanup task
    asyncio.create_task(context_manager.cleanup_old_contexts())
    
    try:
        # Start the context cleanup task
        await context_manager.start_cleanup_task()
        logger.info("Started context cleanup task")
        
        # Start the context promotion task
        await context_manager.start_promotion_task()
        logger.info("Started context promotion task")
        
        # Initialize batch scheduler
        await batch_scheduler.initialize()
        logger.info("Initialized batch scheduler with static configurations")
        
        # Initialize dynamic schedules based on user preferences
        if hasattr(batch_scheduler, "initialize_dynamic_schedules"):
            await batch_scheduler.initialize_dynamic_schedules()
            logger.info("Initialized dynamic schedules from user preferences")
            
            # Start monitoring for configuration changes
            if hasattr(batch_scheduler, "start_config_change_monitor"):
                await batch_scheduler.start_config_change_monitor()
                logger.info("Started monitoring for user preference changes")
        
        # Start batch scheduler
        await batch_scheduler.start()
        logger.info("Started batch scheduler")
        
        # Start background processing tasks
        asyncio.create_task(process_pending_contexts())
        asyncio.create_task(promote_waiting_contexts())
        logger.info("Started background processing tasks")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")

# Shutdown handler
@app.on_event("shutdown")
async def shutdown_event():
    """
    Execute shutdown tasks.
    """
    logger.info("Agent microservice shutting down")
    
    # Close user repository connection
    try:
        await user_repository.close()
        logger.info("User repository closed successfully")
    except Exception as e:
        logger.error(f"Error closing user repository: {str(e)}")
    
    # Close other connections
    await http_client.aclose()
    
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
        
        # Additional cleanup would go here
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
    
    uvicorn.run("main:app", host=host, port=port, reload=reload) 