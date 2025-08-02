"""
API dependencies for the Expert Base microservice.

This module defines FastAPI dependencies for the Expert Base microservice.
"""

from fastapi import Depends, Request, HTTPException, Header
from typing import Optional

from src.common.config import settings
from src.common.exceptions import AuthenticationException
from src.modules.expert_orchestrator import ExpertOrchestrator


async def verify_api_key(
    authorization: Optional[str] = Header(None)
) -> None:
    """
    Verify the API key in the Authorization header.
    
    Args:
        authorization: The Authorization header value.
        
    Raises:
        AuthenticationException: If the API key is invalid.
    """
    if not authorization:
        raise AuthenticationException("Missing API key")
    
    # Expected format: "Bearer <api_key>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationException("Invalid authorization format")
    
    api_key = parts[1]
    if api_key != settings.API_KEY:
        raise AuthenticationException("Invalid API key")


def get_expert_orchestrator(request: Request) -> ExpertOrchestrator:
    """
    Get the expert orchestrator from the FastAPI app state.
    
    Args:
        request: The FastAPI request.
        
    Returns:
        The expert orchestrator instance.
    """
    return request.app.state.expert_orchestrator 