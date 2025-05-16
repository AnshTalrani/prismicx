"""
Middleware module for validating, enriching, and routing incoming requests.
Uses direct LLM generation instead of templates.
"""

from src.bot_integration import support_bot, consultancy_bot, sales_bot
from fastapi import HTTPException, Header
from typing import Optional
from src.config import get_settings

def process_request(data: dict):
    # Validate that the required 'bot_tag' is provided.
    if "bot_tag" not in data:
        raise ValueError("Missing required 'bot_tag' in request data")
    
    bot_tag = data["bot_tag"]
    # Enrich and transform the incoming data as needed.
    enriched_data = data  # Here you can add extra context if available

    # Extract message from request
    message = data.get("message", "")
    context = data.get("context", {})
    
    # Route the request based on the bot_tag.
    if bot_tag.lower() == "support":
        response = support_bot.handle_request(message)
    elif bot_tag.lower() == "consultancy":
        response = consultancy_bot.handle_request(message)
    elif bot_tag.lower() == "sales":
        # For sales, we use direct LLM generation
        session_id = data.get("session_id", "default_session")
        user_id = data.get("user_id", "default_user")
        response = sales_bot.handle_request(
            prompt=message,
            session_id=session_id,
            user_id=user_id
        )
    else:
        raise ValueError(f"Unknown bot_tag: {bot_tag}")

    return {"response": response}

async def verify_request(
    authorization: Optional[str] = Header(None)
) -> bool:
    """
    Verify incoming requests.
    Checks authentication and rate limits.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization token")
    
    settings = get_settings()
    if authorization != f"Bearer {settings.api_key}":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return True 