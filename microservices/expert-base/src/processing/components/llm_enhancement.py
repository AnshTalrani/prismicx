"""
LLM enhancement component for content generation.

This module provides a component that uses LLMs to enhance content
based on the expert framework and intent.
"""

from typing import Dict, Any
from loguru import logger

from src.processing.components.base import ContentEnhancementComponent


class LLMContentEnhancement(ContentEnhancementComponent):
    """
    Component that uses LLMs to enhance content.
    
    This component uses an LLM to enhance content based on the expert
    framework and intent. It uses the knowledge context to provide
    domain-specific enhancements.
    """
    
    def __init__(self, model_provider):
        """
        Initialize the component.
        
        Args:
            model_provider: The model provider for LLM inference.
        """
        self.model_provider = model_provider
    
    async def process(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance the content with the given context.
        
        Args:
            content: The content to enhance.
            context: The processing context.
            
        Returns:
            A dictionary containing the enhanced content.
        """
        try:
            # Extract configuration
            config = context.get("config", {})
            knowledge = context.get("knowledge", {})
            expert_type = config.get("expert_type", "general")
            
            # Extract knowledge items
            knowledge_items = knowledge.get("items", [])
            knowledge_text = "\n".join([f"- {item}" for item in knowledge_items])
            
            # Get a model from the provider
            model = self.model_provider.get_model(config.get("model_id", "default"))
            
            # Construct the prompt based on expert type and knowledge
            prompt = self._construct_prompt(content, expert_type, knowledge_text, config)
            
            # Generate enhanced content
            enhanced = await model.generate(prompt, config)
            
            logger.debug(f"Enhanced content generated for expert type: {expert_type}")
            
            return {"content": enhanced}
            
        except Exception as e:
            logger.error(f"Error in LLM content enhancement: {e}")
            # Return the original content on error
            return {"content": content}
    
    def _construct_prompt(
        self, 
        content: str, 
        expert_type: str, 
        knowledge_text: str, 
        config: Dict[str, Any]
    ) -> str:
        """
        Construct a prompt for the LLM based on expert type and knowledge.
        
        Args:
            content: The content to enhance.
            expert_type: The type of expert.
            knowledge_text: The knowledge context.
            config: The configuration.
            
        Returns:
            A prompt for the LLM.
        """
        # Customize prompt based on expert type
        if expert_type == "instagram":
            base_prompt = f"""
You are an Instagram content expert. Enhance the following content to make it more engaging 
and effective for Instagram. Consider best practices for Instagram content.

If the content is appropriate as is, return it unchanged.

Knowledge context:
{knowledge_text}

Content parameters:
- Tone: {config.get('tone', 'friendly and engaging')}
- Target audience: {config.get('target_audience', 'general')}
- Length: {config.get('length', 'appropriate for Instagram')}

Content to enhance:
{content}

Enhanced content:
"""
        elif expert_type == "etsy":
            base_prompt = f"""
You are an Etsy product description expert. Enhance the following content to make it more 
appealing and effective for Etsy listings. Consider best practices for Etsy product descriptions.

If the content is appropriate as is, return it unchanged.

Knowledge context:
{knowledge_text}

Content parameters:
- Tone: {config.get('tone', 'warm and descriptive')}
- Target audience: {config.get('target_audience', 'Etsy shoppers')}
- Length: {config.get('length', 'appropriate for Etsy')}

Content to enhance:
{content}

Enhanced content:
"""
        elif expert_type == "marketing":
            base_prompt = f"""
You are a marketing content expert. Enhance the following content to make it more persuasive 
and effective for marketing purposes. Consider best practices for marketing content.

If the content is appropriate as is, return it unchanged.

Knowledge context:
{knowledge_text}

Content parameters:
- Tone: {config.get('tone', 'persuasive and professional')}
- Target audience: {config.get('target_audience', 'potential customers')}
- Length: {config.get('length', 'appropriate for marketing')}

Content to enhance:
{content}

Enhanced content:
"""
        elif expert_type == "branding":
            base_prompt = f"""
You are a branding expert. Enhance the following content to align with brand guidelines 
and strengthen brand identity. Consider best practices for brand consistency.

If the content is appropriate as is, return it unchanged.

Knowledge context:
{knowledge_text}

Content parameters:
- Tone: {config.get('tone', 'on-brand and consistent')}
- Target audience: {config.get('target_audience', 'brand audience')}
- Length: {config.get('length', 'appropriate for the brand')}

Content to enhance:
{content}

Enhanced content:
"""
        else:
            # Generic prompt for unspecified expert types
            base_prompt = f"""
Enhance the following content to make it more effective and engaging.
If the content is appropriate as is, return it unchanged.

Knowledge context:
{knowledge_text}

Content parameters:
- Tone: {config.get('tone', 'professional')}
- Target audience: {config.get('target_audience', 'general')}
- Length: {config.get('length', 'appropriate')}

Content to enhance:
{content}

Enhanced content:
"""
        
        return base_prompt
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """
        Validate the configuration for this component.
        
        Args:
            config: The configuration to validate.
            
        Returns:
            True if the configuration is valid, False otherwise.
        """
        # Check for minimum required configuration
        if not config.get("model_id"):
            logger.warning("No model_id specified in configuration")
            return False
            
        return True 