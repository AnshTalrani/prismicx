"""
Module defining prompt templates using Langchain's ChatPromptTemplate.
This stub formats incoming data into a prompt string.
"""

from .dynamic_template_engine import DynamicTemplateEngine, TemplateConfig, TemplateType

class PromptManager:
    def __init__(self):
        self.template_engine = DynamicTemplateEngine()
        
    async def get_prompt(
        self,
        message: str,
        session_data: Dict,
        bot_config: Dict,
        analysis_results: Dict
    ) -> ChatPromptTemplate:
        """Get appropriate prompt template based on context."""
        template_config = self._create_template_config(
            bot_config, analysis_results
        )
        
        return await self.template_engine.generate_template(
            analysis_results=analysis_results,
            user_profile=session_data["user_profile"],
            template_config=template_config,
            campaign_data=session_data.get("campaign_data")
        )

def format_prompt(data: dict) -> str:
    # Extract the user message from data and format it.
    user_message = data.get("message", "")
    # In production, use Langchain's ChatPromptTemplate to format multi-part messages.
    return f"User: {user_message}" 