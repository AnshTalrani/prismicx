"""
Exception handlers for the Expert Base microservice.

This module defines exception handlers for FastAPI to handle custom exceptions.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from src.common.exceptions import (
    ExpertBaseException, 
    ExpertNotFoundException,
    IntentNotSupportedException,
    ProcessingException,
    ConfigurationException,
    ValidationException,
    AuthenticationException,
    UnauthorizedException,
    VectorDBException,
    ModelProviderException
)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register exception handlers for the FastAPI application.
    
    Args:
        app: The FastAPI application instance.
    """
    
    @app.exception_handler(ExpertBaseException)
    async def expert_base_exception_handler(request: Request, exc: ExpertBaseException) -> JSONResponse:
        """
        Handle all ExpertBaseException instances.
        
        Args:
            request: The FastAPI request.
            exc: The exception instance.
            
        Returns:
            JSONResponse with error details.
        """
        logger.error(f"ExpertBaseException: {exc.message} - {exc.details}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle all other exceptions.
        
        Args:
            request: The FastAPI request.
            exc: The exception instance.
            
        Returns:
            JSONResponse with error details.
        """
        logger.exception(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "details": {"error": str(exc)}
            }
        ) 