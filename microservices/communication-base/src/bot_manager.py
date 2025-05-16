"""Main bot management system."""

from typing import Dict, Optional
from config.config_manager import ConfigManager
from langchain_components.rag.chain_builder import RAGChainBuilder
from langchain_components.memory_manager.enhanced_memory import EnhancedMemoryManager

class BotManager:
    """Manages bot initialization and message handling."""
    
    def __init__(self, bot_type: str):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_bot_config(bot_type)
        self.chain_builder = self._init_chain_builder()
        self.memory_manager = self._init_memory_manager()
    
    def _init_chain_builder(self) -> RAGChainBuilder:
        """Initialize chain builder with config."""
        chain_config = self.config_manager.get_chain_config(self.config)
        return RAGChainBuilder(chain_config)
    
    def _init_memory_manager(self) -> EnhancedMemoryManager:
        """Initialize memory manager with config."""
        return EnhancedMemoryManager(self.config)
    
    async def handle_message(
        self,
        message: str,
        session_id: str,
        user_id: str
    ) -> Dict:
        """Handle incoming message using config-driven components."""
        
        # Get analysis and template
        template, analysis = await self.memory_manager.process_message(
            message=message,
            session_id=session_id,
            user_id=user_id,
            bot_config=self.config
        )
        
        # Build and run chain
        chain = self.chain_builder.create_rag_chain(
            retriever=self._get_retriever(),
            memory=self.memory_manager,
            session_id=session_id
        )
        
        response = await chain.ainvoke({
            "question": message,
            "user_id": user_id,
            "bot_config": self.config,
            "analysis": analysis
        })
        
        return {
            "response": response,
            "analysis": analysis,
            "template_used": template
        }
    
    def _get_retriever(self):
        """Get configured retriever."""
        retrieval_config = self.config["chain_config"]["retrieval"]
        # Initialize retriever based on config
        pass 