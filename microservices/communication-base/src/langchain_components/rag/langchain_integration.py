"""
LangChain RAG Integration

This module provides the integration layer between our custom RAG components
and LangChain chains, ensuring smooth interoperability and maximizing the
benefits of both systems.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Callable
import asyncio
from pydantic import BaseModel, Field

from langchain.schema import Document
from langchain.schema.runnable import Runnable
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.conversational_retrieval.base import create_conversational_retrieval_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain.memory import ConversationBufferMemory

from src.config.config_integration import ConfigIntegration
from src.models.llm.base_llm_manager import BaseLLMManager
from src.langchain_components.rag.rag_coordinator import RAGCoordinator


class LangChainRAGIntegration:
    """
    Integration layer between custom RAG components and LangChain.
    
    This class serves as a bridge between our custom RAG implementation
    and LangChain's chain capabilities, ensuring they work together seamlessly.
    """
    
    def __init__(
        self,
        rag_coordinator: Optional[RAGCoordinator] = None,
        llm_manager: Optional[BaseLLMManager] = None,
        config_integration: Optional[ConfigIntegration] = None
    ):
        """
        Initialize the LangChain RAG integration.
        
        Args:
            rag_coordinator: RAG coordinator instance
            llm_manager: LLM manager for accessing language models
            config_integration: Config integration instance
        """
        self.rag_coordinator = rag_coordinator
        self.llm_manager = llm_manager
        self.config_integration = config_integration or ConfigIntegration()
        self.logger = logging.getLogger(__name__)
        
        # Cache for chains
        self._chain_cache: Dict[str, Any] = {}
    
    def create_retrieval_chain(
        self,
        bot_type: str,
        session_id: str,
        user_id: Optional[str] = None,
        chain_type: str = "stuff",
        memory: Optional[Any] = None
    ) -> Any:
        """
        Create a LangChain retrieval chain using our custom RAG components.
        
        Args:
            bot_type: Type of bot (consultancy, sales, support)
            session_id: Session identifier
            user_id: User identifier (optional)
            chain_type: Type of chain to create (stuff, map_reduce, refine)
            memory: Optional memory component
            
        Returns:
            LangChain retrieval chain
        """
        # Create cache key
        cache_key = f"{bot_type}_{session_id}_{chain_type}"
        if cache_key in self._chain_cache:
            return self._chain_cache[cache_key]
        
        # Get configuration
        config = self.config_integration.get_config(bot_type)
        rag_config = config.get("rag", {})
        
        # Get LLM
        if not self.llm_manager:
            self.logger.error("Cannot create chain: LLM manager not provided")
            raise ValueError("LLM manager is required to create a chain")
            
        llm_id = rag_config.get("llm_id", "default")
        llm = self.llm_manager.get_model(llm_id)
        
        # Get retriever from RAG coordinator
        if not self.rag_coordinator:
            self.logger.error("Cannot create chain: RAG coordinator not provided")
            raise ValueError("RAG coordinator is required to create a chain")
            
        retriever = self.rag_coordinator.get_langchain_retriever(
            bot_type=bot_type,
            session_id=session_id,
            user_id=user_id
        )
        
        # Create document compression if configured
        if rag_config.get("use_document_compression", False):
            compression_ratio = rag_config.get("compression_ratio", 0.75)
            retriever = self._create_compressed_retriever(
                retriever, 
                llm, 
                compression_ratio
            )
        
        # Get prompt templates
        document_prompt_template = rag_config.get(
            "document_prompt_template",
            "Use the following pieces of context to answer the question at the end. "
            "If you don't know the answer, just say that you don't know, don't try to make up an answer.\n\n"
            "{context}\n\n"
            "Question: {question}\n"
            "Answer: "
        )
        
        document_prompt = PromptTemplate(
            template=document_prompt_template,
            input_variables=["context", "question"]
        )
        
        # Create the chain
        if chain_type == "conversational":
            if not memory:
                memory = ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True
                )
                
            chain = create_conversational_retrieval_chain(
                llm=llm,
                retriever=retriever,
                memory=memory,
                condense_question_prompt=self._get_condense_question_prompt(bot_type)
            )
        else:  # Default to "stuff"
            document_chain = create_stuff_documents_chain(
                llm=llm, 
                prompt=document_prompt
            )
            
            chain = create_retrieval_chain(
                retriever, 
                document_chain
            )
        
        # Cache and return
        self._chain_cache[cache_key] = chain
        return chain
    
    def _get_condense_question_prompt(self, bot_type: str) -> PromptTemplate:
        """Get the condensed question prompt for conversational chains."""
        config = self.config_integration.get_config(bot_type)
        rag_config = config.get("rag", {})
        
        template = rag_config.get(
            "condense_question_template",
            "Given the following conversation and a follow up question, rephrase the follow up "
            "question to be a standalone question that captures all relevant context from the chat history.\n\n"
            "Chat History:\n{chat_history}\n"
            "Follow Up Question: {question}\n"
            "Standalone Question:"
        )
        
        return PromptTemplate(
            template=template,
            input_variables=["chat_history", "question"]
        )
    
    def _create_compressed_retriever(
        self, 
        retriever: Any, 
        llm: Any, 
        compression_ratio: float = 0.75
    ) -> Any:
        """Create a compressed retriever using LangChain's document compressors."""
        from langchain.retrievers import ContextualCompressionRetriever
        
        # This is a simple compression using embedding similarity
        # Could be enhanced with more sophisticated methods
        embeddings = self.llm_manager.get_embeddings()
        compressor = EmbeddingsFilter(embeddings=embeddings, similarity_threshold=compression_ratio)
        
        return ContextualCompressionRetriever(
            base_retriever=retriever,
            base_compressor=compressor
        )
    
    def run_rag_chain(
        self,
        query: str,
        bot_type: str,
        session_id: str,
        user_id: Optional[str] = None,
        chain_type: str = "stuff",
        memory: Optional[Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run a RAG chain to answer a query.
        
        Args:
            query: User query
            bot_type: Type of bot
            session_id: Session identifier
            user_id: User identifier (optional)
            chain_type: Type of chain to use
            memory: Optional memory component
            **kwargs: Additional arguments for the chain
            
        Returns:
            Chain result
        """
        try:
            # Get or create chain
            chain = self.create_retrieval_chain(
                bot_type=bot_type,
                session_id=session_id,
                user_id=user_id,
                chain_type=chain_type,
                memory=memory
            )
            
            # Prepare inputs
            inputs = {"question": query}
            if chain_type == "conversational" and "chat_history" not in kwargs:
                # For conversational chains, chat history comes from memory
                inputs = {"question": query}
            else:
                # For other chains, we might need to pass additional arguments
                inputs.update(kwargs)
            
            # Run chain
            self.logger.info(f"Running {chain_type} RAG chain for query: {query}")
            result = chain.invoke(inputs)
            
            return result
        except Exception as e:
            self.logger.error(f"Error running RAG chain: {e}")
            # Return graceful error response
            return {
                "answer": f"I encountered an error while searching for information: {str(e)}",
                "source_documents": []
            }
    
    async def arun_rag_chain(
        self,
        query: str,
        bot_type: str,
        session_id: str,
        user_id: Optional[str] = None,
        chain_type: str = "stuff",
        memory: Optional[Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run a RAG chain asynchronously.
        
        This method wraps the synchronous run_rag_chain method in a thread
        to make it work with async code.
        
        Args:
            query: User query
            bot_type: Type of bot
            session_id: Session identifier
            user_id: User identifier (optional)
            chain_type: Type of chain to use
            memory: Optional memory component
            **kwargs: Additional arguments for the chain
            
        Returns:
            Chain result
        """
        # Run in thread to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.run_rag_chain(
                query=query,
                bot_type=bot_type,
                session_id=session_id,
                user_id=user_id,
                chain_type=chain_type,
                memory=memory,
                **kwargs
            )
        )
    
    def get_document_splitter(self, bot_type: str) -> RecursiveCharacterTextSplitter:
        """
        Get a document splitter configured for the bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            Document splitter instance
        """
        config = self.config_integration.get_config(bot_type)
        rag_config = config.get("rag", {})
        
        chunk_size = rag_config.get("chunk_size", 1000)
        chunk_overlap = rag_config.get("chunk_overlap", 200)
        
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
    
    def clear_chain_cache(self) -> None:
        """Clear the chain cache."""
        self._chain_cache.clear()
        self.logger.info("Chain cache cleared")
    
    def get_or_create_memory(
        self, 
        session_id: str, 
        memory_type: str = "buffer"
    ) -> Any:
        """
        Get or create a memory component for conversational chains.
        
        Args:
            session_id: Session identifier
            memory_type: Type of memory to create
            
        Returns:
            Memory component
        """
        # This could be expanded to support different memory types
        if memory_type == "buffer":
            return ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
        else:
            self.logger.warning(f"Unsupported memory type: {memory_type}, using buffer")
            return ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )

# Example usage:
"""
# Initialize components
config_integration = ConfigIntegration()
llm_manager = LLMManager("sales")  # Using hypothetical LLMManager
rag_coordinator = RAGCoordinator(config_integration=config_integration)

# Create integration
langchain_integration = LangChainRAGIntegration(
    rag_coordinator=rag_coordinator,
    llm_manager=llm_manager,
    config_integration=config_integration
)

# Use in conversation flow
async def handle_user_message(user_id, session_id, message):
    # Run RAG chain
    result = await langchain_integration.arun_rag_chain(
        query=message,
        bot_type="sales",
        session_id=session_id,
        user_id=user_id,
        chain_type="conversational"
    )
    
    # Extract and return response
    return result["answer"]
""" 