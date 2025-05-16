"""
RetrievalStrategy defines an interface for retrieving context from the KnowledgeBase.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class RetrievalStrategy(ABC):
    @abstractmethod
    def retrieve(self, intent_tag: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieve documents based on the intent_tag and filters.
        
        Args:
            intent_tag (str): The intent tag for which to fetch context.
            filters (Dict[str, Any]): Additional filters or parameters.
        
        Returns:
            List[Dict[str, Any]]: A list of result dictionaries.
        """
        pass

class DenseRetrievalStrategy(RetrievalStrategy):
    def retrieve(self, intent_tag: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Implementation for dense retrieval.
        # For demo purposes, return dummy result.
        return [{"content": f"Dense result for {intent_tag}"}]

class SparseRetrievalStrategy(RetrievalStrategy):
    def retrieve(self, intent_tag: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Implementation for sparse retrieval.
        return [{"content": f"Sparse result for {intent_tag}"}] 