"""
FusionStrategy defines an interface for fusing a user query with retrieved context.
"""

from abc import ABC, abstractmethod
from typing import List

class FusionStrategy(ABC):
    @abstractmethod
    def fuse(self, query: str, retrieved_docs: List[str]) -> str:
        """
        Fuse the original query with retrieved documents.

        Args:
            query (str): The original user query.
            retrieved_docs (List[str]): A list of retrieved document strings.

        Returns:
            str: The fused prompt.
        """
        pass

class RAGSequenceFusionStrategy(FusionStrategy):
    def fuse(self, query: str, retrieved_docs: List[str]) -> str:
        fused_context = "\n".join(retrieved_docs)
        return f"{query}\n\nContext:\n{fused_context}"

class RAGTokenFusionStrategy(FusionStrategy):
    def fuse(self, query: str, retrieved_docs: List[str]) -> str:
        # Alternative simple fusion strategy (for demonstration).
        fused_context = " ".join(retrieved_docs)
        return f"{query} {fused_context}" 