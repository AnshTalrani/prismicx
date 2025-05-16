"""
Simple Conversation Example

This script demonstrates a simple usage of the conversation flow management system.
It simulates a conversation with each type of bot.
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.conversation.manager import ConversationManager
from src.config.config_integration import ConfigIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# Example conversations for different bot types
EXAMPLE_CONVERSATIONS = {
    "sales": [
        "Hi there, I'm interested in your products",
        "I'm looking for software solutions for my business",
        "We're a medium-sized tech company with about 100 employees",
        "Our budget is around $50,000 and we need it implemented in 3 months",
        "Tell me more about your premium package",
        "That sounds expensive. Do you have any discounts?",
        "I think I'd like to move forward with the standard package",
        "My email is test@example.com",
        "Thanks for your help!"
    ],
    "consultancy": [
        "Hello, I need some business advice",
        "I run a retail business and we're struggling with inventory management",
        "We're a small company with 3 physical stores",
        "Our main challenge is predicting demand and optimizing stock levels",
        "That's helpful advice. How would we implement these changes?",
        "What timeline would you recommend for rolling out these changes?",
        "I'd like to discuss this further with a consultant",
        "My email is retailmanager@example.com and I'm available next Tuesday",
        "Thank you for the guidance"
    ],
    "support": [
        "Hi, I'm having an issue with your product",
        "The software keeps crashing when I try to export reports",
        "I'm using Windows 10 with the latest version of your app",
        "The error code is ERR-5432",
        "I tried rebooting but it didn't help",
        "Let me try that solution... It worked! Thank you",
        "Is there anything else I should know to prevent this issue?",
        "That's very helpful, I appreciate your assistance",
        "Yes, I'd rate my experience as 9 out of 10"
    ]
}

async def simulate_conversation(bot_type: str, messages: List[str]) -> None:
    """
    Simulate a conversation with a specific bot type.
    
    Args:
        bot_type: Type of bot (sales, consultancy, support)
        messages: List of user messages
    """
    logger.info(f"Starting {bot_type} bot conversation simulation")
    
    # Initialize components
    config_integration = ConfigIntegration()
    conversation_manager = ConversationManager(config_integration=config_integration)
    
    # Create a unique session ID
    session_id = f"{bot_type}-{int(datetime.utcnow().timestamp())}"
    user_id = "example-user-123"
    
    # Process each message
    for i, message in enumerate(messages):
        logger.info(f"User: {message}")
        
        response_data = await conversation_manager.process_message(
            message=message,
            session_id=session_id,
            user_id=user_id,
            bot_type=bot_type,
            platform="example",
            metadata={"simulation": True, "message_number": i + 1}
        )
        
        # Handle typing simulation
        typing_delay = response_data.get("metadata", {}).get("typing_delay", 1.0)
        logger.info(f"Bot is typing... ({typing_delay:.1f}s)")
        await asyncio.sleep(min(typing_delay, 2.0))  # Cap at 2 seconds for simulation
        
        # Display response
        logger.info(f"Bot ({bot_type}): {response_data.get('text', '')}")
        
        # Pause between turns
        await asyncio.sleep(1.0)
    
    logger.info(f"Completed {bot_type} bot conversation simulation")

async def main() -> None:
    """
    Run the conversation simulations.
    """
    logger.info("Starting conversation simulations")
    
    for bot_type, messages in EXAMPLE_CONVERSATIONS.items():
        await simulate_conversation(bot_type, messages)
        logger.info("-" * 50)
    
    logger.info("All simulations completed")

if __name__ == "__main__":
    asyncio.run(main()) 