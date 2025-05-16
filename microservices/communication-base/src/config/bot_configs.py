"""
Central configuration registry for all bot types.

This module imports individual bot configurations and creates a central registry
that can be accessed using the bot type as a key.
"""

from src.bot_integration.consultancy_bot.config import CONSULTANCY_BOT_CONFIG
from src.bot_integration.sales_bot.config import SALES_BOT_CONFIG
from src.bot_integration.support_bot.config import SUPPORT_BOT_CONFIG

# Central registry of bot configurations
BOT_CONFIGS = {
    "consultancy": CONSULTANCY_BOT_CONFIG,
    "sales": SALES_BOT_CONFIG,
    "support": SUPPORT_BOT_CONFIG
}

def get_bot_config(bot_type: str):
    """
    Get the configuration for a specific bot type.
    
    Args:
        bot_type: The type of bot (consultancy, sales, support)
        
    Returns:
        The configuration dictionary for the specified bot type
        
    Raises:
        KeyError: If the specified bot type is not found
    """
    if bot_type not in BOT_CONFIGS:
        raise KeyError(f"Bot type '{bot_type}' not found. Available types: {list(BOT_CONFIGS.keys())}")
    
    return BOT_CONFIGS[bot_type] 