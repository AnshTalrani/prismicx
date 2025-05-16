"""
Base class for domain-specific ExpertBots.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from src.knowledge_base.knowledge_base_component import KnowledgeBaseComponent

class ExpertBot(ABC):
    def __init__(self, lora_adapter: str, knowledge_base: KnowledgeBaseComponent):
        """
        Initializes the ExpertBot with a LoRA adapter and KnowledgeBase.

        Args:
            lora_adapter (str): Path to the LoRA adapter.
            knowledge_base (KnowledgeBaseComponent): Instance of KnowledgeBaseComponent for guidelines retrieval.
        """
        self.llm = self.load_model(lora_adapter)
        self.knowledge_base = knowledge_base

    @abstractmethod
    def load_model(self, lora_adapter: str):
        """
        Loads the fine-tuned LLM with the specified LoRA adapter.

        Args:
            lora_adapter (str): Path to the LoRA adapter.

        Returns:
            Any: Loaded LLM model.
        """
        pass

    @abstractmethod
    def get_prompt_strategy(self, intent: str) -> str:
        """Get appropriate prompt strategy based on intent"""
        pass

    @abstractmethod
    def process(self, request: Dict) -> Dict:
        """Process request with intent-specific strategy"""
        pass 