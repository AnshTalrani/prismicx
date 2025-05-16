"""
User Details RAG component for retrieving personalized user information.
Connects to the User Details microservice for topic-based retrieval.
"""

import logging
from typing import Dict, List, Any, Optional
from langchain.schema import Document

from src.config.config_inheritance import ConfigInheritance
from src.clients.user_details_client import user_details_client
from src.langchain_components.rag.topic_mapper import topic_mapper

class UserDetailsRAG:
    """
    User Details RAG component for retrieving personalized user information.
    Provides a retriever interface compatible with LangChain.
    """
    
    def __init__(self):
        """Initialize the User Details RAG component."""
        self.config_inheritance = ConfigInheritance()
        self.logger = logging.getLogger(__name__)
    
    async def get_relevant_documents(
        self, query: str, user_id: str, bot_type: str, limit: int = 5
    ) -> List[Document]:
        """
        Get relevant user details documents for a query.
        
        Args:
            query: The query to match against topics
            user_id: The user ID
            bot_type: The type of bot
            limit: Maximum number of documents to return
            
        Returns:
            List of LangChain Document objects
        """
        # Get bot configuration
        config = self.config_inheritance.get_config(bot_type)
        
        # Map query to relevant topics
        relevant_topic_ids = await topic_mapper.map_query_to_topics(query, bot_type)
        
        # If no topics mapped, use configured default topics
        if not relevant_topic_ids:
            relevant_topic_ids = config.get("user_details.default_topics", [])
        
        # Retrieve insights for relevant topics
        documents = []
        for topic_id in relevant_topic_ids:
            topic_insights = await user_details_client.get_topic_insights(user_id, topic_id)
            if not topic_insights:
                continue
                
            # Convert insights to a document
            topic_name = topic_insights.get("topic_name", topic_id)
            content = self._format_insights_as_text(topic_insights)
            
            if content:
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": "user_details",
                        "topic_id": topic_id,
                        "topic_name": topic_name,
                        "user_id": user_id
                    }
                )
                documents.append(doc)
        
        # Sort documents by relevance (if we implement a scoring mechanism)
        # For now, just take the top 'limit' documents
        return documents[:limit]
    
    def _format_insights_as_text(self, insights: Dict[str, Any]) -> str:
        """
        Format insights as text for inclusion in LangChain documents.
        
        Args:
            insights: Topic insights dictionary
            
        Returns:
            Formatted text representation of insights
        """
        if not insights or "data" not in insights:
            return ""
        
        topic_name = insights.get("topic_name", "Unknown Topic")
        result = f"# User insights on {topic_name}\n\n"
        
        data = insights.get("data", {})
        for key, value in data.items():
            if isinstance(value, dict):
                result += f"## {key}\n"
                for subkey, subvalue in value.items():
                    result += f"- {subkey}: {subvalue}\n"
                result += "\n"
            elif isinstance(value, list):
                result += f"## {key}\n"
                for item in value:
                    if isinstance(item, dict):
                        for subkey, subvalue in item.items():
                            result += f"- {subkey}: {subvalue}\n"
                    else:
                        result += f"- {item}\n"
                result += "\n"
            else:
                result += f"## {key}\n"
                result += f"{value}\n\n"
        
        return result
    
    def get_retriever_for_bot(self, bot_type: str):
        """
        Get a specialized retriever for a specific bot type.
        
        Args:
            bot_type: The type of bot
            
        Returns:
            Bot-specific retriever function
        """
        # Get bot configuration
        config = self.config_inheritance.get_config(bot_type)
        
        if bot_type == "consultancy":
            # Consultancy bot focuses on business context and pain points
            return self._get_consultancy_retriever(config)
        elif bot_type == "sales":
            # Sales bot focuses on preferences and purchase history
            return self._get_sales_retriever(config)
        elif bot_type == "support":
            # Support bot focuses on user history and preferences
            return self._get_support_retriever(config)
        else:
            # Default retriever
            return self.get_relevant_documents
    
    def _get_consultancy_retriever(self, config: Dict[str, Any]):
        """Get consultancy-specific retriever."""
        # Prioritize business context, pain points, and previous consultations
        async def consultancy_retriever(query: str, user_id: str, bot_type: str, limit: int = 5):
            # Override topic mapping with consultancy-specific mapping
            business_topic_ids = config.get("user_details.business_topics", [])
            
            # Get documents from business topics first
            business_docs = []
            for topic_id in business_topic_ids:
                topic_insights = await user_details_client.get_topic_insights(user_id, topic_id)
                if not topic_insights:
                    continue
                    
                content = self._format_insights_as_text(topic_insights)
                if content:
                    doc = Document(
                        page_content=content,
                        metadata={"source": "user_details", "topic_id": topic_id}
                    )
                    business_docs.append(doc)
            
            # Then get regular documents
            regular_docs = await self.get_relevant_documents(query, user_id, bot_type, limit)
            
            # Combine and limit
            combined_docs = business_docs + [doc for doc in regular_docs if doc not in business_docs]
            return combined_docs[:limit]
            
        return consultancy_retriever
    
    def _get_sales_retriever(self, config: Dict[str, Any]):
        """Get sales-specific retriever."""
        # Prioritize user preferences, purchase history, and campaign interaction
        async def sales_retriever(query: str, user_id: str, bot_type: str, limit: int = 5):
            # Override topic mapping with sales-specific mapping
            preference_topic_ids = config.get("user_details.preference_topics", [])
            purchase_topic_ids = config.get("user_details.purchase_topics", [])
            
            # Get documents from preference topics first
            preference_docs = []
            for topic_id in preference_topic_ids:
                topic_insights = await user_details_client.get_topic_insights(user_id, topic_id)
                if not topic_insights:
                    continue
                    
                content = self._format_insights_as_text(topic_insights)
                if content:
                    doc = Document(
                        page_content=content,
                        metadata={"source": "user_details", "topic_id": topic_id}
                    )
                    preference_docs.append(doc)
            
            # Then get purchase history
            purchase_docs = []
            for topic_id in purchase_topic_ids:
                topic_insights = await user_details_client.get_topic_insights(user_id, topic_id)
                if not topic_insights:
                    continue
                    
                content = self._format_insights_as_text(topic_insights)
                if content:
                    doc = Document(
                        page_content=content,
                        metadata={"source": "user_details", "topic_id": topic_id}
                    )
                    purchase_docs.append(doc)
            
            # Combine preferences and purchases, then add regular documents
            combined_docs = preference_docs + purchase_docs
            regular_docs = await self.get_relevant_documents(query, user_id, bot_type, limit)
            
            combined_docs += [doc for doc in regular_docs if doc not in combined_docs]
            return combined_docs[:limit]
            
        return sales_retriever
    
    def _get_support_retriever(self, config: Dict[str, Any]):
        """Get support-specific retriever."""
        # Prioritize user history and personalization
        async def support_retriever(query: str, user_id: str, bot_type: str, limit: int = 5):
            # Override topic mapping with support-specific mapping
            history_topic_ids = config.get("user_details.history_topics", [])
            
            # Get documents from history topics first
            history_docs = []
            for topic_id in history_topic_ids:
                topic_insights = await user_details_client.get_topic_insights(user_id, topic_id)
                if not topic_insights:
                    continue
                    
                content = self._format_insights_as_text(topic_insights)
                if content:
                    doc = Document(
                        page_content=content,
                        metadata={"source": "user_details", "topic_id": topic_id}
                    )
                    history_docs.append(doc)
            
            # Then get regular documents
            regular_docs = await self.get_relevant_documents(query, user_id, bot_type, limit)
            
            # Combine and limit
            combined_docs = history_docs + [doc for doc in regular_docs if doc not in history_docs]
            return combined_docs[:limit]
            
        return support_retriever

# Global instance
user_details_rag = UserDetailsRAG() 