"""
KnowledgeBaseComponent for managing domain-specific guidelines.
"""

from typing import List, Dict, Any
from abc import ABC, abstractmethod
from src.knowledge_base.retrieval_strategy import RetrievalStrategy, DenseRetrievalStrategy


# Placeholder for vector DB client
class VectorDBClient:
    def upsert(self, vectors: List[Any], metadata: Dict[str, Any]) -> None:
        pass

    def query(self, filters: Dict[str, Any]) -> List[Any]:
        pass

class KnowledgeBaseComponent:
    def __init__(
        self,
        vector_db: str,
        # retrieval strategy, chunking strategy, and embedding strategy will be specified in the config file for each request
        retrieval_strategy: RetrievalStrategy = None,
        chunking_strategy: ChunkingStrategy = None,
        embedding_strategy: EmbeddingStrategy = None
    ):
        """
        Initializes the KnowledgeBaseComponent with a vector database instance, retrieval strategy,
        chunking strategy, and embedding strategy.

        Args:
            vector_db (str): Identifier for the vector database to use.
            retrieval_strategy (RetrievalStrategy, optional): A strategy instance for context retrieval.
            chunking_strategy (ChunkingStrategy, optional): A strategy for chunking documents.
            embedding_strategy (EmbeddingStrategy, optional): A strategy for embedding document chunks.
        """
        self.vector_db = VectorDBClient()  # Initialize with an actual client if available
        # If no retrieval strategy is provided, use a default (e.g., DenseRetrievalStrategy)
        self.retrieval_strategy = retrieval_strategy or DenseRetrievalStrategy()
        # Use default strategies if not provided
        self.chunking_strategy = chunking_strategy or DefaultChunkingStrategy()
        self.embedding_strategy = embedding_strategy or DefaultEmbeddingStrategy()

    def ingest(self, documents: List[str], intent_tag: str) -> None:
        """
        Ingests new documents into the KnowledgeBase.

        Args:
            documents (List[str]): List of documents to ingest.
            intent_tag (str): The intent tag associated with the documents.
        """
        # Use the injected chunking and embedding strategies:
        chunks = self.chunking_strategy.chunk(documents)
        embeddings = self.embedding_strategy.embed(chunks)
        self.vector_db.upsert(vectors=embeddings, metadata={"intent_tag": intent_tag})

    def retrieve(self, intent_tag: str, filters: Dict[str, Any]) -> str:
        """
        Retrieves guidelines based on intent_tag and filters using the retrieval strategy.

        Args:
            intent_tag (str): The intent tag for which to retrieve guidelines.
            filters (Dict[str, Any]): Additional filters for retrieval.

        Returns:
            str: Retrieved guidelines as a single concatenated string.
        """
        results = self.retrieval_strategy.retrieve(intent_tag, filters)
        guidelines = " ".join([result["content"] for result in results])
        return guidelines 


# --- New Strategy Interfaces for Chunking and Embedding ---
#chunking and embedding strategies should be aligned with the retrieval strategy
class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, documents: List[str]) -> List[str]:
        """
        Splits documents into chunks.

        Args:
            documents (List[str]): List of documents to chunk.

        Returns:
            List[str]: List of document chunks.
        """
        pass

class DefaultChunkingStrategy(ChunkingStrategy):
    def chunk(self, documents: List[str]) -> List[str]:
        # Default implementation: Return the documents as-is.
        return documents

class EmbeddingStrategy(ABC):
    @abstractmethod
    def embed(self, chunks: List[str]) -> List[Any]:
        """
        Generates embeddings for the given document chunks.

        Args:
            chunks (List[str]): List of document chunks.

        Returns:
            List[Any]: List of embeddings.
        """
        pass

class DefaultEmbeddingStrategy(EmbeddingStrategy):
    def embed(self, chunks: List[str]) -> List[Any]:
        # Default implementation: Simply return the chunks for now.
        return chunks

# --- End of New Strategy Interfaces ---

