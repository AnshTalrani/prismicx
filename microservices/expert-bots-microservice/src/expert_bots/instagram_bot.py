"""
InstagramBot for generating Instagram-specific content.
"""

from typing import Dict, Any
from src.expert_bots.expert_bot import ExpertBot
from src.utils.logger import Logger
from transformers import AutoModelForCausalLM
from peft import PeftModel

class InstagramBot(ExpertBot):
    def __init__(self, lora_adapter: str, knowledge_base: Any, logger: Logger):
        """
        Initializes the InstagramBot with its LoRA adapter and KnowledgeBase.

        Args:
            lora_adapter (str): Path to the Instagram LoRA adapter.
            knowledge_base (Any): Instance of KnowledgeBaseComponent.
            logger (Logger): Logger instance for logging activities.
        """
        super().__init__(lora_adapter, knowledge_base)
        self.logger = logger

    def load_model(self, lora_adapter: str) -> AutoModelForCausalLM:
        """
        Loads the fine-tuned Instagram LLM using the specified LoRA adapter.

        Args:
            lora_adapter (str): Path to the Instagram LoRA adapter.

        Returns:
            AutoModelForCausalLM: Loaded LLM model.
        """
        base_model = AutoModelForCausalLM.from_pretrained("mistral-7b")
        instagram_adapter = PeftModel.from_pretrained(base_model, lora_adapter)
        return instagram_adapter

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates an Instagram post based on the request parameters.

        Args:
            request (Dict[str, Any]): Request containing parameters like theme and details.

        Returns:
            Dict[str, Any]: Generated Instagram post.
        """
        try:
            # Retrieve Instagram-specific guidelines
            guidelines = self.knowledge_base.retrieve(
                intent_tag="instagram_post", 
                filters={"theme": request.get("theme")}
            )
            # Generate post using fine-tuned LLM
            prompt = f"Generate Instagram post with: {request.get('details')}. Guidelines: {guidelines}"
            generated_content = self.llm.generate(prompt)
            self.logger.log_activity("Instagram post generated successfully.")
            return {"content": generated_content}
        except Exception as e:
            self.logger.log_error(f"Error in InstagramBot.process: {e}")
            return {"error": "Failed to generate Instagram post"} 