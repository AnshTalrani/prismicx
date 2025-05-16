"""
Conversation States

This package provides common state handlers and utilities for the conversation flow system.
All bot-specific state definitions are loaded from their respective configuration files.
"""

import logging
from typing import Dict, Any, Callable, Awaitable

logger = logging.getLogger(__name__)

# Common states used across all bot types
COMMON_STATES = {
    "error": {
        "name": "error",
        "description": "Error handling state",
        "required_entities": [],
        "transitions": [
            {"target": "greeting", "conditions": [
                {"type": "message_count", "threshold": 1}
            ]}
        ],
        "adapters": [],
        "default_response": "I'm sorry, but I encountered an error processing your request. Let's start over. How can I help you today?",
        "use_rag": False
    },
    
    "human_handoff": {
        "name": "human_handoff",
        "description": "Transitioning to human agent",
        "required_entities": ["email"],
        "transitions": [
            {"target": "farewell", "conditions": [
                {"type": "entity_present", "entity_name": "email"}
            ]}
        ],
        "adapters": [],
        "default_response": "I'll connect you with a human agent who can better assist with this. Could you provide your email address for them to contact you?",
        "use_rag": False
    },
    
    "inactive": {
        "name": "inactive",
        "description": "Conversation inactive state",
        "required_entities": [],
        "transitions": [
            {"target": "greeting", "conditions": [
                {"type": "message_count", "threshold": 1}
            ]}
        ],
        "adapters": [],
        "default_response": "I noticed our conversation has been inactive. Is there anything else I can help you with?",
        "use_rag": False
    }
}

# Common state handlers
async def handle_error_state(
    state_name: str,
    message: str,
    context: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """
    Handle the error state for all bot types.
    
    Args:
        state_name: Current state name
        message: User message
        context: Conversation context
        
    Returns:
        Dictionary with response and context updates
    """
    state_config = COMMON_STATES.get(state_name, {})
    
    # Log the error for analysis
    error_info = context.get("error_info", {})
    logging.error(f"Conversation error: {error_info.get('message', 'Unknown error')}")
    
    # Clear error info to prevent loop
    context_updates = {
        "error_info": None
    }
    
    return {
        "response": state_config.get("default_response"),
        "context_updates": context_updates,
        "adapters": [],
        "use_rag": False
    }

async def handle_human_handoff_state(
    state_name: str,
    message: str,
    context: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """
    Handle the human handoff state for all bot types.
    
    Args:
        state_name: Current state name
        message: User message
        context: Conversation context
        
    Returns:
        Dictionary with response and context updates
    """
    state_config = COMMON_STATES.get(state_name, {})
    
    # Extract email if present in message
    context_updates = {}
    entities = context.get("entities", {}).copy()
    
    # If email not provided, get it from the message or user info
    if "email" not in entities:
        # Check user info first
        user_email = context.get("user_info", {}).get("profile", {}).get("email")
        if user_email:
            entities["email"] = {
                "value": user_email,
                "confidence": 1.0,
                "source": "user_profile",
                "timestamp": context.get("last_accessed")
            }
            context_updates["entities"] = entities

    # Track handoff in analytics
    context_updates["handoff_info"] = {
        "requested_at": context.get("last_accessed"),
        "reason": context.get("current_state", "unknown"),
        "conversation_length": len(context.get("messages", [])),
        "bot_type": context.get("bot_type")
    }
    
    return {
        "response": state_config.get("default_response"),
        "context_updates": context_updates,
        "adapters": [],
        "use_rag": False
    }

async def handle_inactive_state(
    state_name: str,
    message: str,
    context: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """
    Handle the inactive state for all bot types.
    
    Args:
        state_name: Current state name
        message: User message
        context: Conversation context
        
    Returns:
        Dictionary with response and context updates
    """
    state_config = COMMON_STATES.get(state_name, {})
    
    # Reset inactivity tracking
    context_updates = {
        "inactivity": {
            "last_active": context.get("last_accessed"),
            "warned": True
        }
    }
    
    return {
        "response": state_config.get("default_response"),
        "context_updates": context_updates,
        "adapters": [],
        "use_rag": False
    }

# Common state handlers mapping
COMMON_STATE_HANDLERS = {
    "error": handle_error_state,
    "human_handoff": handle_human_handoff_state,
    "inactive": handle_inactive_state
}

# State machine handler type definition
StateHandlerType = Callable[[str, str, Dict[str, Any], Dict[str, Any]], Awaitable[Dict[str, Any]]]

def get_common_state_definition(state_name: str) -> Dict[str, Any]:
    """
    Get the definition of a common state.
    
    Args:
        state_name: The state name
        
    Returns:
        State definition dictionary or empty dict if not found
    """
    return COMMON_STATES.get(state_name, {})

def get_common_state_handler(state_name: str) -> StateHandlerType:
    """
    Get the handler function for a common state.
    
    Args:
        state_name: The state name
        
    Returns:
        State handler function or None if not found
    """
    return COMMON_STATE_HANDLERS.get(state_name) 