"""
Example Usage of Integrated RAG System

This script demonstrates how to use the RAG system with LangChain integration.
It shows a simple conversation flow that incorporates retrieved information.

To run this example:
1. Ensure all dependencies are installed
2. Make sure the user_details microservice is running
3. Run the script with: python -m src.langchain_components.rag.example_usage
"""

import asyncio
import logging
import os
from typing import Dict, Any, List, Optional

from src.config.config_integration import ConfigIntegration
from src.models.llm.base_llm_manager import BaseLLMManager
from src.langchain_components.rag.rag_coordinator import RAGCoordinator
from src.langchain_components.rag.user_details_rag import UserDetailsRAG
from src.langchain_components.rag.vector_store_rag import VectorStoreRAG
from src.langchain_components.rag.database_rag import DatabaseRAG
from src.langchain_components.rag.query_preprocessor import QueryPreprocessor
from src.langchain_components.rag.langchain_integration import LangChainRAGIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# This would normally be imported from a proper implementation
class MockLLMManager(BaseLLMManager):
    """Mock LLM Manager for demonstration purposes."""
    
    def __init__(self, bot_type: str):
        """Initialize the mock LLM manager."""
        self.bot_type = bot_type
        self.models = {}
        
    def _load_specific_model(self, model_path: str) -> Any:
        """Mock implementation of model loading."""
        # In a real implementation, this would load an actual model
        return {"name": "mock_model", "path": model_path}
        
    def prepare_inference_params(self, model_name: str, **kwargs) -> Dict[str, Any]:
        """Mock implementation of inference parameter preparation."""
        return {"temperature": 0.7, "max_tokens": 100}
        
    def get_model(self, model_name: str) -> Any:
        """Get a mock model."""
        # In a real implementation, this would return an actual model
        from langchain.llms.fake import FakeListLLM
        return FakeListLLM(responses=["This is a mock response based on the retrieved information."])
        
    def get_embeddings(self) -> Any:
        """Get mock embeddings."""
        # In a real implementation, this would return actual embeddings
        from langchain.embeddings.fake import FakeEmbeddings
        return FakeEmbeddings(size=1536)

async def setup_rag_system(bot_type: str) -> LangChainRAGIntegration:
    """
    Set up the RAG system components.
    
    Args:
        bot_type: Type of bot
        
    Returns:
        LangChain RAG integration instance
    """
    logger.info(f"Setting up RAG system for {bot_type} bot")
    
    # Initialize configuration
    config_integration = ConfigIntegration()
    
    # Initialize RAG components
    user_details_rag = UserDetailsRAG()
    vector_store_rag = VectorStoreRAG()
    database_rag = DatabaseRAG()
    query_preprocessor = QueryPreprocessor()
    
    # Initialize RAG coordinator
    rag_coordinator = RAGCoordinator(
        config_integration=config_integration,
        user_details_rag=user_details_rag,
        vector_store_rag=vector_store_rag,
        database_rag=database_rag,
        query_preprocessor=query_preprocessor
    )
    
    # Initialize mock LLM manager
    llm_manager = MockLLMManager(bot_type)
    
    # Initialize LangChain integration
    langchain_integration = LangChainRAGIntegration(
        rag_coordinator=rag_coordinator,
        llm_manager=llm_manager,
        config_integration=config_integration
    )
    
    return langchain_integration

async def simulate_conversation(
    langchain_integration: LangChainRAGIntegration,
    bot_type: str,
    user_id: str,
    session_id: str,
    questions: List[str]
) -> None:
    """
    Simulate a conversation with RAG-enhanced responses.
    
    Args:
        langchain_integration: LangChain RAG integration instance
        bot_type: Type of bot
        user_id: User ID
        session_id: Session ID
        questions: List of questions to ask
    """
    logger.info(f"Starting conversation simulation for {bot_type} bot")
    
    # Create memory for the conversation
    memory = langchain_integration.get_or_create_memory(session_id)
    
    # Process each question
    for i, question in enumerate(questions):
        logger.info(f"Question {i+1}: {question}")
        
        # Run the RAG chain with the question
        result = await langchain_integration.arun_rag_chain(
            query=question,
            bot_type=bot_type,
            session_id=session_id,
            user_id=user_id,
            chain_type="conversational",
            memory=memory
        )
        
        # Extract and display the answer
        answer = result.get("answer", "No answer found")
        logger.info(f"Answer: {answer}")
        
        # Display source documents
        source_docs = result.get("source_documents", [])
        if source_docs:
            logger.info(f"Sources used ({len(source_docs)} documents):")
            for i, doc in enumerate(source_docs[:2]):  # Show first 2 sources
                source = doc.metadata.get("source", "unknown")
                logger.info(f"  Source {i+1}: {source}")
        
        logger.info("-" * 50)

async def main():
    """Run the RAG example."""
    # Bot types
    bot_types = ["sales", "consultancy", "support"]
    
    # Example user and session IDs
    user_id = "user123"
    session_id = "session456"
    
    # Example questions for each bot type
    questions = {
        "sales": [
            "What products would you recommend for me?",
            "Do you have information about my previous purchases?",
            "Can you tell me about new offerings that match my interests?"
        ],
        "consultancy": [
            "What business challenges do I face?",
            "Can you analyze my company's growth potential?",
            "What strategies would you recommend for my situation?"
        ],
        "support": [
            "I'm having an issue with my account",
            "What was the status of my last ticket?",
            "How can I upgrade my subscription?"
        ]
    }
    
    # Run demonstration for each bot type
    for bot_type in bot_types:
        logger.info(f"\n{'='*80}\nDemonstrating RAG for {bot_type.upper()} bot\n{'='*80}")
        
        # Set up the RAG system
        langchain_integration = await setup_rag_system(bot_type)
        
        # Simulate a conversation
        await simulate_conversation(
            langchain_integration=langchain_integration,
            bot_type=bot_type,
            user_id=user_id,
            session_id=f"{session_id}_{bot_type}",
            questions=questions[bot_type]
        )
        
        logger.info(f"\nCompleted {bot_type} bot demonstration\n")

if __name__ == "__main__":
    # Run the example
    asyncio.run(main()) 