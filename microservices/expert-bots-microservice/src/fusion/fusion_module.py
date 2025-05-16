"""
FusionModule: Provides methods to fuse the original query with the retrieved context documents.
"""

class FusionModule:
    @staticmethod
    def fuse_context(query: str, retrieved_docs: list, fusion_config: dict) -> str:
        """
        Fuse the original query with retrieved context.

        Args:
            query (str): The original user query.
            retrieved_docs (list): Context documents retrieved by the knowledge base.
            fusion_config (dict): Configuration for the fusion strategy (e.g., strategy: 'RAG-Sequence').

        Returns:
            str: The fused prompt ready for the generation layer.
        """
        # For now, implement a simple fusion by concatenating the query and context.
        # Later, this method can be extended to support RAG-Token, FiD, etc.
        fused_context = "\n".join(retrieved_docs) if retrieved_docs else ""
        fused_prompt = f"{query}\n\nContext:\n{fused_context}"
        return fused_prompt 