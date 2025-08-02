"""
This module serves as the core communication microservice in a MACH architecture system.

Key Responsibilities:
1. API Gateway: Provides REST endpoints for chat interactions using FastAPI
2. Session Management: Maintains user chat sessions and handles cleanup
3. Bot Orchestration: Routes requests to appropriate specialized chat bots
   - Consultancy bot for business advice
   - Sales bot for product inquiries 
   - Support bot for customer service

Technical Implementation:
- FastAPI for high-performance async API endpoints
- Pydantic models for request/response validation
- Secure middleware for request verification
- Environment-based configuration
- Graceful startup/shutdown handling

MACH Architecture Alignment:
- Microservices: Self-contained communication service
- API-First: RESTful endpoints as primary interface
- Cloud-Native: Docker-ready with environment configuration
- Headless: Decoupled from presentation layer

This service acts as the central communication hub, managing chat sessions and routing
messages to specialized bot handlers while maintaining security and scalability.
"""

import os
import sys
from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any

from src.config import Config
from src.api_gateway import app as api_gateway_app
from src.middleware import verify_request
from src.session.session_manager import session_manager
from src.bot_integration import consultancy_bot, sales_bot, support_bot
from src.database import get_db_session, get_database_adapter

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: str
    bot_type: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    metadata: Optional[Dict[str, Any]] = None

BOT_HANDLERS = {
    "consultancy": consultancy_bot.handle_request,
    "sales": sales_bot.handle_request,
    "support": support_bot.handle_request
}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    verified: bool = Depends(verify_request)
):
    """Handle chat requests for all bot types."""
    if request.bot_type not in BOT_HANDLERS:
        raise HTTPException(status_code=400, detail="Invalid bot type")
    
    try:
        # Get handler for bot type
        handler = BOT_HANDLERS[request.bot_type]
        
        # Process request
        if request.bot_type == "sales":
            # Sales bot uses a different signature with direct LLM generation
            response = await handler(
                prompt=request.message,
                session_id=request.session_id,
                user_id=request.user_id,
                context=request.context
            )
        else:
            # Other bots use the standard signature
            response = await handler(
                prompt=request.message,
                session_id=request.session_id,
                user_id=request.user_id
            )
        
        return ChatResponse(
            response=response,
            session_id=request.session_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    # Start session cleanup task
    session_manager.start_cleanup_task()
    
    # Initialize database adapter
    db_adapter = get_database_adapter()

def main():
    """
    Main execution function of the communication-base microservice.
    Raises an EnvironmentError if required configuration is missing.
    """
    required_env_var = "COMM_BASE_API_KEY"
    api_key = os.getenv(required_env_var)
    if not api_key:
        raise EnvironmentError(f"The required environment variable '{required_env_var}' is not set.")
    
    print("Starting communication-base microservice...")
    print(f"Using API key: {api_key[:4]}****")  # Mask sensitive data
    print("communication-base microservice is running.")
    # To launch the FastAPI app from the command line locally, uncomment the following lines:
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main() 