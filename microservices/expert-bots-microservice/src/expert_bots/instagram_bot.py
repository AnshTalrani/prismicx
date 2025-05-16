"""
InstagramBot for generating Instagram-specific content.
"""

from typing import Dict, Any
from src.expert_bots.expert_bot import ExpertBot
from src.utils.logger import Logger
from transformers import AutoModelForCausalLM
from peft import PeftModel
from src.agent.src.error_handling.error_types import IntentNotSupportedError

class InstagramBot(ExpertBot):
    PROMPT_STRATEGIES = {
        'pre': "Generate creative strategy for Instagram post...",
        'pro': "Refactor this content for better engagement...",
        'post': "Post-publishing checklist:\n1. Hashtag optimization..."
    }

    def __init__(self, lora_adapter: str, knowledge_base: Any, logger: Logger, config: Dict = None):
        """
        Initializes the InstagramBot with its LoRA adapter, KnowledgeBase, and configuration.

        Args:
            lora_adapter (str): Path to the Instagram LoRA adapter.
            knowledge_base (Any): Instance of KnowledgeBaseComponent.
            logger (Logger): Logger instance for logging activities.
            config (Dict, optional): Configuration for generation parameters.
        """
        super().__init__(lora_adapter, knowledge_base)
        self.logger = logger
        self.config = config or {}

    def load_model(self, lora_adapter: str):
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

    def get_prompt_strategy(self, intent: str) -> str:
        if intent not in self.PROMPT_STRATEGIES:
            raise IntentNotSupportedError(f"InstagramBot doesn't support {intent} intent")
        return self.PROMPT_STRATEGIES[intent]

    def process(self, request: Dict) -> Dict:
        """
        Generates Instagram-specific content using the fused prompt and generation parameters.

        Args:
            request (Dict): Request dictionary with a 'formatted_prompt' and generation config.

        Returns:
            Dict: Output containing generated Instagram content or error details.
        """
        try:
            # Use pre-formatted prompt from orchestrator.
            llm_params = request.get("llm_config", {})
            generated_content = self.llm.generate(
                prompt=request['formatted_prompt'],
                **llm_params
            )
            return {
                "expert": "instagram",
                "intent": request['intent'],
                "generated_content": generated_content
            }
        except Exception as e:
            self.logger.log_error(f"InstagramBot error: {e}")
            return {"error": "Content generation failed"} 