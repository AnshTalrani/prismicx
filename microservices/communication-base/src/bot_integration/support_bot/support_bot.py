"""
Module for handling customer support queries.
Utilizes dedicated LLM and LoRA adapter for empathetic troubleshooting.
"""

from src.bot_integration.adapter_manager import get_adapter
from src.langchain_components.llm_chain import generate_response
from src.bot_integration.support_bot.config import SUPPORT_BOT_CONFIG

def handle_request(prompt: str):
    adapter = get_adapter("support", SUPPORT_BOT_CONFIG.get("adapters", []))
    instructions = SUPPORT_BOT_CONFIG.get("system_message", "")
    # Generate a response using the custom instructions for support.
    response = generate_response(prompt, adapter=adapter, bot_type="support", instructions=instructions)
    return response 