"""
Topic mapper for mapping queries to relevant User Details topics.
Provides functionality to connect user messages with appropriate topic data.
"""

import logging
from typing import Dict, List, Any, Optional
import aiohttp

from src.config.config_inheritance import ConfigInheritance
from src.models.llm.model_registry import ModelRegistry
from src.clients.user_details_client import user_details_client

class TopicMapper:
    """
    Maps queries to relevant User Details topics.
    Uses a combination of keyword matching and semantic matching.
    """
    
    def __init__(self):
        """Initialize the topic mapper."""
        self.config_inheritance = ConfigInheritance()
        self.model_registry = ModelRegistry()
        self.logger = logging.getLogger(__name__)
        self._topic_keywords = {}
        self._topic_descriptions = {}
    
    async def map_query_to_topics(
        self, query: str, bot_type: str, limit: int = 3
    ) -> List[str]:
        """
        Map a query to relevant topic IDs.
        
        Args:
            query: The query to map
            bot_type: The type of bot
            limit: Maximum number of topics to return
            
        Returns:
            List of relevant topic IDs
        """
        # Get bot configuration
        config = self.config_inheritance.get_config(bot_type)
        
        # Decide mapping strategy based on configuration
        mapping_strategy = config.get("user_details.topic_mapping_strategy", "hybrid")
        
        if mapping_strategy == "keyword":
            return await self._map_by_keywords(query, bot_type, limit)
        elif mapping_strategy == "semantic":
            return await self._map_by_semantic_similarity(query, bot_type, limit)
        elif mapping_strategy == "llm":
            return await self._map_by_llm(query, bot_type, limit)
        else:  # Default to hybrid
            return await self._map_hybrid(query, bot_type, limit)
    
    async def _map_by_keywords(self, query: str, bot_type: str, limit: int) -> List[str]:
        """Map query to topics using keyword matching."""
        # Get topic keywords if not already loaded
        if not self._topic_keywords:
            await self._load_topic_metadata()
        
        # Get bot-specific topic filtering
        config = self.config_inheritance.get_config(bot_type)
        filtered_topics = config.get("user_details.relevant_topics", [])
        
        # Check each topic's keywords against the query
        scores = {}
        for topic_id, keywords in self._topic_keywords.items():
            # Skip if not in filtered topics (when filtered_topics is not empty)
            if filtered_topics and topic_id not in filtered_topics:
                continue
                
            score = 0
            for keyword in keywords:
                if keyword.lower() in query.lower():
                    score += 1
            
            if score > 0:
                scores[topic_id] = score
        
        # Sort topics by score and return top 'limit' topic IDs
        sorted_topics = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [topic_id for topic_id, _ in sorted_topics[:limit]]
    
    async def _map_by_semantic_similarity(self, query: str, bot_type: str, limit: int) -> List[str]:
        """Map query to topics using semantic similarity."""
        # Get topic descriptions if not already loaded
        if not self._topic_descriptions:
            await self._load_topic_metadata()
        
        # Get bot-specific topic filtering
        config = self.config_inheritance.get_config(bot_type)
        filtered_topics = config.get("user_details.relevant_topics", [])
        
        # Get embedding model from config
        model_name = config.get("user_details.embedding_model", "default_embedding_model")
        embedding_model = self.model_registry.get_embedding_model(model_name, bot_type)
        
        if not embedding_model:
            self.logger.error(f"No embedding model found for {bot_type}, falling back to keyword matching")
            return await self._map_by_keywords(query, bot_type, limit)
        
        try:
            # Get query embedding
            query_embedding = await embedding_model.embed_query(query)
            
            # Get embeddings for topic descriptions
            topic_embeddings = {}
            for topic_id, description in self._topic_descriptions.items():
                # Skip if not in filtered topics (when filtered_topics is not empty)
                if filtered_topics and topic_id not in filtered_topics:
                    continue
                    
                # Get embedding for this topic description
                topic_embedding = await embedding_model.embed_documents([description])
                topic_embeddings[topic_id] = topic_embedding[0]
            
            # Calculate similarity scores
            scores = {}
            for topic_id, topic_embedding in topic_embeddings.items():
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, topic_embedding)
                scores[topic_id] = similarity
            
            # Sort topics by score and return top 'limit' topic IDs
            sorted_topics = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            return [topic_id for topic_id, _ in sorted_topics[:limit]]
            
        except Exception as e:
            self.logger.error(f"Error in semantic mapping: {e}")
            return await self._map_by_keywords(query, bot_type, limit)
    
    async def _map_by_llm(self, query: str, bot_type: str, limit: int) -> List[str]:
        """Map query to topics using LLM classification."""
        # Get available topics
        topics = await user_details_client.get_available_topics()
        if not topics:
            self.logger.error("No topics available, falling back to keyword matching")
            return await self._map_by_keywords(query, bot_type, limit)
        
        # Get bot-specific topic filtering
        config = self.config_inheritance.get_config(bot_type)
        filtered_topics = config.get("user_details.relevant_topics", [])
        
        # Filter topics if needed
        if filtered_topics:
            topics = [topic for topic in topics if topic.get("id") in filtered_topics]
        
        # Get LLM model from config
        model_name = config.get("user_details.mapping_model", "default_nlp_model")
        llm = self.model_registry.get_model(model_name, bot_type)
        
        if not llm:
            self.logger.error(f"No LLM found for {bot_type}, falling back to keyword matching")
            return await self._map_by_keywords(query, bot_type, limit)
        
        try:
            # Create prompt for topic classification
            topic_descriptions = "\n".join([
                f"- {topic.get('id')}: {topic.get('description', 'No description')}"
                for topic in topics
            ])
            
            prompt = f"""
            I need to map the following query to the most relevant topics from this list:
            
            {topic_descriptions}
            
            Query: "{query}"
            
            Please return the IDs of the {limit} most relevant topics, comma-separated.
            Only include the topic IDs, nothing else.
            """
            
            # Get response from LLM
            response = await llm.ainvoke(prompt)
            
            # Parse response to get topic IDs
            topic_ids = [
                topic_id.strip() 
                for topic_id in response.content.strip().split(",")
            ]
            
            # Validate topic IDs
            valid_topic_ids = []
            all_topic_ids = [topic.get("id") for topic in topics]
            
            for topic_id in topic_ids:
                if topic_id in all_topic_ids:
                    valid_topic_ids.append(topic_id)
                else:
                    self.logger.warning(f"Invalid topic ID in LLM response: {topic_id}")
            
            return valid_topic_ids[:limit]
            
        except Exception as e:
            self.logger.error(f"Error in LLM mapping: {e}")
            return await self._map_by_keywords(query, bot_type, limit)
    
    async def _map_hybrid(self, query: str, bot_type: str, limit: int) -> List[str]:
        """Map query to topics using a hybrid approach."""
        # Get bot configuration
        config = self.config_inheritance.get_config(bot_type)
        
        # Try LLM mapping first
        if config.get("user_details.use_llm_mapping", True):
            llm_topics = await self._map_by_llm(query, bot_type, limit)
            if llm_topics:
                return llm_topics
        
        # Try semantic mapping next
        if config.get("user_details.use_semantic_mapping", True):
            semantic_topics = await self._map_by_semantic_similarity(query, bot_type, limit)
            if semantic_topics:
                return semantic_topics
        
        # Fall back to keyword mapping
        return await self._map_by_keywords(query, bot_type, limit)
    
    async def _load_topic_metadata(self):
        """Load topic keywords and descriptions."""
        topics = await user_details_client.get_available_topics()
        
        for topic in topics:
            topic_id = topic.get("id")
            if not topic_id:
                continue
                
            # Extract keywords
            keywords = topic.get("keywords", [])
            self._topic_keywords[topic_id] = keywords
            
            # Extract description
            description = topic.get("description", "")
            self._topic_descriptions[topic_id] = description
    
    def _cosine_similarity(self, vec1, vec2) -> float:
        """Calculate cosine similarity between two vectors."""
        # Simple dot product for normalized vectors
        return sum(a * b for a, b in zip(vec1, vec2))

# Global instance
topic_mapper = TopicMapper() 