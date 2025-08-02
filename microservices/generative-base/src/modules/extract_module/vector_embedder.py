"""
Enhanced vector embedding with content-type specific models
"""
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Optional

class VectorEmbedder:
    """
    A utility class to compute context-aware vector embeddings
    """
    
    def __init__(self):
        """Initialize different models for different content types"""
        self.models: Dict[str, SentenceTransformer] = {
            "product": SentenceTransformer('all-MiniLM-L6-v2'),
            "social": SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2'),
            "trends": SentenceTransformer('all-mpnet-base-v2')
        }
        
    def embed_text(self, text: str, content_type: str = "product") -> List[float]:
        """
        Compute embeddings based on content type
        
        Args:
            text: Input text to embed
            content_type: Type of content (product, social, trends)
        """
        if not text:
            return []
            
        model = self.models.get(content_type, self.models["product"])
        try:
            embedding = model.encode(text)
            return embedding.tolist()
        except Exception as e:
            raise RuntimeError(f"Error computing {content_type} embedding: {str(e)}")

    def embed_many(
        self,
        texts: List[str],
        content_type: str = "product",
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Batch compute embeddings with type-specific models
        """
        if not texts:
            return []
            
        model = self.models.get(content_type, self.models["product"])
        try:
            embeddings = model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            raise RuntimeError(f"Error in batch embedding: {str(e)}") 