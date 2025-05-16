"""FastAPI application setup for the agent microservice."""
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os

from src.interfaces.api.controllers.request_controller import RequestController
from src.application.services.request_service import RequestService
from src.infrastructure.repositories.in_memory_request_repository import InMemoryRequestRepository
from src.infrastructure.repositories.template_repository import FileTemplateRepository
from src.application.services.default_context_service import DefaultContextService
from src.application.services.logging_communication_service import LoggingCommunicationService
from src.application.services.default_nlp_service import DefaultNLPService
from src.infrastructure.config.feature_flags import FeatureFlagManager
from src.infrastructure.config.config_manager import ConfigManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title="Agent Microservice API",
        description="API for processing agent requests",
        version="0.1.0",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Set up configuration
    config_manager = ConfigManager.create_default()
    
    # Set up feature flags
    feature_flags = FeatureFlagManager.from_env()
    feature_flags.register_flag("async_processing", 
                               os.environ.get("ENABLE_ASYNC_PROCESSING", "false").lower() == "true")
    
    # Register dependencies
    register_dependencies(app, config_manager, feature_flags)
    
    # Register routes
    register_routes(app)
    
    @app.on_event("startup")
    async def startup_event():
        """Run startup tasks."""
        logger.info("Starting agent microservice API")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Run shutdown tasks."""
        logger.info("Shutting down agent microservice API")
    
    return app


def register_dependencies(app: FastAPI, 
                         config_manager: ConfigManager, 
                         feature_flags: FeatureFlagManager) -> None:
    """
    Register application dependencies.
    
    Args:
        app: FastAPI application
        config_manager: Configuration manager
        feature_flags: Feature flag manager
    """
    # Repositories
    app.dependency_overrides[InMemoryRequestRepository] = lambda: InMemoryRequestRepository()
    app.dependency_overrides[InMemoryTemplateRepository] = lambda: InMemoryTemplateRepository()
    
    # Service dependencies
    app.dependency_overrides[ConfigManager] = lambda: config_manager
    app.dependency_overrides[FeatureFlagManager] = lambda: feature_flags
    
    # Application services
    app.dependency_overrides[DefaultContextService] = lambda: DefaultContextService()
    app.dependency_overrides[LoggingCommunicationService] = lambda: LoggingCommunicationService()
    app.dependency_overrides[DefaultNLPService] = lambda: DefaultNLPService()
    
    # Register the request service
    def get_request_service(
        request_repo: InMemoryRequestRepository = Depends(),
        template_repo: FileTemplateRepository = Depends(),
        context_service: DefaultContextService = Depends(),
        communication_service: LoggingCommunicationService = Depends(),
        nlp_service: DefaultNLPService = Depends(),
    ) -> RequestService:
        # Import TemplateService here to ensure proper initialization order
        from src.application.services.template_service import TemplateService
        
        # Create the template service
        template_service = TemplateService(
            template_repository=template_repo,
            # Create FilePurposeRepository or use other dependency injection here
            purpose_repository=None  # This should be properly injected
        )
        
        return RequestService(
            request_repository=request_repo,
            template_service=template_service,  # Use template_service instead of template_repository
            context_service=context_service,
            communication_service=communication_service,
            nlp_service=nlp_service,
        )
    
    app.dependency_overrides[RequestService] = get_request_service
    
    # Register the request controller
    def get_request_controller(
        request_service: RequestService = Depends(),
        feature_flags: FeatureFlagManager = Depends(),
    ) -> RequestController:
        return RequestController(
            request_service=request_service,
            feature_flags=feature_flags,
        )
    
    app.dependency_overrides[RequestController] = get_request_controller


def register_routes(app: FastAPI) -> None:
    """
    Register API routes.
    
    Args:
        app: FastAPI application
    """
    # Get controller instances
    request_controller = app.dependency_overrides[RequestController]()
    
    # Include routers
    app.include_router(request_controller.router)
    
    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok"}


app = create_app() 