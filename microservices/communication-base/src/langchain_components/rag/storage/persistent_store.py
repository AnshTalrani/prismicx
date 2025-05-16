"""Persistent storage manager for vector stores and documents."""

from langchain_community.vectorstores import Chroma
from typing import Dict, List, Optional
import os

class PersistentStoreManager:
    def __init__(self, base_path: str = "data/vector_stores"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        
    def get_store_path(self, bot_type: str, category: str) -> str:
        """Get the persistent storage path for a specific store."""
        return os.path.join(self.base_path, bot_type, category)
    
    def create_store(self, documents: List, bot_type: str, category: str) -> Chroma:
        """Create a persistent vector store."""
        store_path = self.get_store_path(bot_type, category)
        os.makedirs(store_path, exist_ok=True)
        
        return Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=store_path
        )
    
    def load_store(self, bot_type: str, category: str) -> Optional[Chroma]:
        """Load an existing vector store."""
        store_path = self.get_store_path(bot_type, category)
        if os.path.exists(store_path):
            return Chroma(
                persist_directory=store_path,
                embedding_function=self.embeddings
            )
        return None 