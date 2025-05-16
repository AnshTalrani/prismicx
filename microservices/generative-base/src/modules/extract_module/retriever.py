"""
Data retrieval component for performing similarity search based on vector embeddings.
"""

import numpy as np
from typing import List, Tuple
from .vector_embedder import VectorEmbedder
from ..common.utils import Utils

class DataRetriever:
    """
    Handles retrieval of data based on vector embeddings stored within records.
    """

    def __init__(self, stored_records: List[dict] = None):
        """
        Initialize the DataRetriever.

        Args:
            stored_records (List[dict]): List of records where each record contains an 'embeddings' key.
                                         Defaults to an empty list.
        """
        self.embedder = VectorEmbedder()
        self.stored_records = stored_records if stored_records is not None else []

    @Utils.retry_operation
    def retrieve_similar(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = 0.0,
        content_type: str = "product"
    ) -> List[Tuple[dict, float]]:
        """
        Retrieve records that are most similar to the given query text.

        Args:
            query (str): The query text used for similarity search.
            top_k (int): Number of top similar records to return.
            threshold (float): Minimum similarity threshold for returned records.
            content_type (str): Content type used for computing query embeddings.

        Returns:
            List[Tuple[dict, float]]: A list of tuples (record, similarity) sorted by descending similarity.
        """
        query_embedding = np.array(self.embedder.embed_text(query, content_type=content_type))
        results = []
        for record in self.stored_records:
            record_embedding = record.get('embeddings')
            if record_embedding is None:
                continue
            record_embedding_array = np.array(record_embedding)
            similarity = self.cosine_similarity(query_embedding, record_embedding_array)
            if similarity >= threshold:
                results.append((record, similarity))
        # Sort records by similarity in descending order.
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    @staticmethod
    def cosine_similarity(vec1: np.array, vec2: np.array) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            vec1 (np.array): First vector.
            vec2 (np.array): Second vector.

        Returns:
            float: Cosine similarity value.
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2) 