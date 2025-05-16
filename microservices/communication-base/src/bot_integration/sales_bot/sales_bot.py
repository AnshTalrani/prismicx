"""
Module for handling sales bot requests.
Processes batch and campaign inputs for dynamic customer engagement.
"""

from src.bot_integration.adapter_manager import get_adapter
from src.langchain_components.llm_chain import generate_response
from src.bot_integration.sales_bot.config import SALES_BOT_CONFIG
from typing import Dict

async def handle_request(
    prompt: str,
    session_id: str,
    user_id: str,
    context: Dict = None
) -> str:
    """
    Handle a sales bot request.
    
    Args:
        prompt: The user's message
        session_id: Current session ID
        user_id: ID of the user
        context: Additional context for the request
        
    Returns:
        Generated response
    """
    adapter = get_adapter("sales", SALES_BOT_CONFIG.get("adapters", []))
    instructions = SALES_BOT_CONFIG.get("system_message", "")
    
    # Generate a response using the custom instructions for sales
    response = await generate_response(
        prompt=prompt,
        adapter=adapter,
        bot_type="sales",
        instructions=instructions,
        context=context
    )
    return response

class SalesBot:
    def __init__(self):
        self.config = SALES_BOT_CONFIG
    
    async def process_campaign_message(
        self,
        user_data: Dict,
        campaign: Campaign,
        stage: str
    ) -> Dict:
        """Generate campaign-specific response"""
        # Get stage-specific template
        template = self._get_stage_template(
            stage,
            campaign.stage_notes[stage]
        )
        
        # Generate personalized content
        content = await self._generate_content(
            template=template,
            user_data=user_data,
            campaign_info=campaign.product_info,
            campaign_config=self.config.get("campaign_config", {})
        )
        
        return {
            "content": content,
            "next_actions": campaign.stages[stage]["next_actions"],
            "metrics": self._calculate_metrics(content, user_data)
        } 