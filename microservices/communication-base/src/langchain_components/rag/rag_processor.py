"""Enhanced RAG processor using modern LangChain components."""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from .rag.document_loaders import DocumentLoader
from .rag.vectorstore_manager import VectorStoreManager
from .rag.chain_builder import RAGChainBuilder
import os

@dataclass
class RAGResponse:
    answer: str
    sources: List[str]
    metadata: Dict
    timestamp: datetime

class RAGProcessor:
    """Main RAG processing class integrating all components."""
    
    def __init__(self):
        self.document_loader = DocumentLoader()
        self.vectorstore_manager = VectorStoreManager()
        self.chain_builder = RAGChainBuilder()
        
    async def setup_knowledge_base(self, bot_type: str, doc_paths: Dict[str, str]):
        """Initialize knowledge base for a bot type."""
        for category, path in doc_paths.items():
            if not os.path.exists(path):
                continue
                
            documents = self.document_loader.load_directory(path)
            self.vectorstore_manager.create_store(documents, bot_type, category)
    
    async def get_response(
        self,
        query: str,
        bot_type: str,
        category: str,
        chat_history: List,
        memory
    ) -> RAGResponse:
        """Get a response using the RAG system."""
        # Get bot-specific retriever
        retriever = self.vectorstore_manager.get_retriever(bot_type, category)
        
        # Create bot-specific RAG chain
        rag_chain = self.chain_builder.create_rag_chain(retriever, memory)
        
        # Get response with context
        response = await rag_chain.ainvoke({
            "question": query,
            "chat_history": chat_history
        })
        
        return RAGResponse(
            answer=response.content,
            sources=retriever.get_relevant_documents(query),
            metadata={"bot_type": bot_type, "category": category},
            timestamp=datetime.utcnow()
        )

# Global instance
rag_processor = RAGProcessor() 