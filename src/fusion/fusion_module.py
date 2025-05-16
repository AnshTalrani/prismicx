"""
FusionModule: Provides methods to fuse the original query with the retrieved context documents.
"""

from src.fusion.fusion_strategy import RAGSequenceFusionStrategy, RAGTokenFusionStrategy

class FusionModule:
    @staticmethod
    def fuse_context(query: str, retrieved_docs: list, fusion_config: dict) -> str:
        """
        Fuse the original query with retrieved context based on the specified fusion strategy in the config.

        Args:
            query (str): The original user query.
            retrieved_docs (list): Context documents retrieved by the knowledge base.
            fusion_config (dict): Configuration for the fusion strategy.
        
        Returns:
            str: The fused prompt ready for the generation layer.
        """
        # Select fusion strategy based on fusion_config
        strategy_name = fusion_config.get("strategy", "RAG-Sequence")
        if strategy_name == "RAG-Sequence":
            strategy = RAGSequenceFusionStrategy()
        elif strategy_name == "RAG-Token":
            strategy = RAGTokenFusionStrategy()
        else:
            # Can be extended to support other strategies (e.g., Fusion-in-Decoder)
            strategy = RAGSequenceFusionStrategy()
        
        return strategy.fuse(query, retrieved_docs) 