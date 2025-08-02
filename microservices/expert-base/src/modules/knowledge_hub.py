"""
Knowledge Hub for the Expert Base microservice.

This module provides functionality for retrieving and managing domain-specific
knowledge for expert frameworks.
"""

from typing import Dict, Any, List, Optional
from loguru import logger

from src.infrastructure.vector_store import VectorStoreClient


class KnowledgeHub:
    """
    Knowledge Hub for retrieving domain-specific knowledge.
    
    This class provides methods for retrieving and managing knowledge that
    is relevant to specific expert frameworks and intents.
    """
    
    def __init__(self, vector_store_client: VectorStoreClient):
        """
        Initialize the Knowledge Hub.
        
        Args:
            vector_store_client: The vector store client to use for knowledge retrieval.
        """
        self.vector_store = vector_store_client
        logger.info("Initialized Knowledge Hub")
    
    async def retrieve_knowledge(
        self,
        expert_id: str,
        intent: str,
        content: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve knowledge relevant to the expert, intent, and content.
        
        Args:
            expert_id: The ID of the expert.
            intent: The processing intent.
            content: The content being processed.
            filters: Optional additional filters for knowledge retrieval.
            
        Returns:
            A dictionary containing retrieved knowledge and context.
        """
        try:
            # Apply the expert and intent to the filters
            combined_filters = {
                "expert_id": expert_id,
                "intent": intent
            }
            
            # Add custom filters if provided
            if filters:
                combined_filters.update(filters)
            
            logger.info(f"Retrieving knowledge for expert='{expert_id}', intent='{intent}'")
            
            # Query the vector store
            collection_name = f"{expert_id}_knowledge"
            results = await self.vector_store.query(
                collection_name=collection_name,
                text=content,
                filters=combined_filters,
                limit=10
            )
            
            # Extract and format the knowledge items
            knowledge_items = []
            for result in results:
                knowledge_items.append({
                    "text": result["text"],
                    "metadata": result["metadata"],
                    "relevance": result.get("score", 1.0)
                })
            
            # Format the knowledge context
            knowledge_context = {
                "items": [item["text"] for item in knowledge_items],
                "metadata": [item["metadata"] for item in knowledge_items],
                "relevance_scores": [item["relevance"] for item in knowledge_items],
                "count": len(knowledge_items)
            }
            
            logger.info(f"Retrieved {len(knowledge_items)} knowledge items")
            
            return knowledge_context
        except Exception as e:
            logger.error(f"Error retrieving knowledge: {e}")
            # Return empty knowledge context on error
            return {"items": [], "metadata": [], "relevance_scores": [], "count": 0}
    
    async def store_knowledge(
        self,
        expert_id: str,
        intent: str,
        texts: List[str],
        metadata_list: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Store knowledge for an expert and intent.
        
        Args:
            expert_id: The ID of the expert.
            intent: The processing intent.
            texts: The knowledge texts to store.
            metadata_list: The metadata for each knowledge text.
            ids: Optional IDs for the knowledge items.
        """
        try:
            # Ensure the metadata includes expert_id and intent
            for metadata in metadata_list:
                metadata["expert_id"] = expert_id
                metadata["intent"] = intent
            
            # Store in the vector store
            collection_name = f"{expert_id}_knowledge"
            await self.vector_store.store(
                collection_name=collection_name,
                texts=texts,
                metadata=metadata_list,
                ids=ids
            )
            
            logger.info(f"Stored {len(texts)} knowledge items for expert='{expert_id}', intent='{intent}'")
        except Exception as e:
            logger.error(f"Error storing knowledge: {e}")
            raise
    
    async def delete_knowledge(
        self,
        expert_id: str,
        filters: Optional[Dict[str, Any]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Delete knowledge for an expert.
        
        Args:
            expert_id: The ID of the expert.
            filters: Optional filters to apply.
            ids: Optional IDs of knowledge items to delete.
        """
        try:
            # Apply the expert to the filters
            combined_filters = {"expert_id": expert_id}
            
            # Add custom filters if provided
            if filters:
                combined_filters.update(filters)
            
            # Delete from the vector store
            collection_name = f"{expert_id}_knowledge"
            await self.vector_store.delete(
                collection_name=collection_name,
                filters=combined_filters,
                ids=ids
            )
            
            logger.info(f"Deleted knowledge for expert='{expert_id}'")
        except Exception as e:
            logger.error(f"Error deleting knowledge: {e}")
            raise
    
    async def seed_example_knowledge(self) -> None:
        """
        Seed example knowledge for testing purposes.
        
        This method adds some example knowledge items to the vector store
        for testing and demonstration purposes.
        """
        try:
            # Instagram knowledge
            instagram_texts = [
                "Instagram posts with carousel images typically get higher engagement rates than single-image posts.",
                "The optimal Instagram caption length is between 125-150 characters for maximum engagement.",
                "Including a call-to-action in your Instagram caption can increase comment rates by up to 40%.",
                "Instagram's algorithm favors content that generates meaningful interactions, such as comments and shares.",
                "Using 5-10 relevant hashtags provides optimal reach for Instagram posts.",
                "Posts with user-generated content receive 4.5% higher conversion rates on Instagram.",
                "The best times to post on Instagram are typically Tuesday through Friday from 10am-3pm.",
                "Instagram Reels currently receive higher organic reach than regular posts or IGTV.",
                "Including a face in your Instagram image can increase engagement by 38%.",
                "Instagram stories with interactive elements like polls or questions get more replies and engagement."
            ]
            
            instagram_metadata = [
                {"domain": "instagram", "content_type": "generation", "category": "best_practices"},
                {"domain": "instagram", "content_type": "generation", "category": "captions"},
                {"domain": "instagram", "content_type": "generation", "category": "engagement"},
                {"domain": "instagram", "content_type": "analysis", "category": "algorithm"},
                {"domain": "instagram", "content_type": "generation", "category": "hashtags"},
                {"domain": "instagram", "content_type": "analysis", "category": "conversion"},
                {"domain": "instagram", "content_type": "generation", "category": "timing"},
                {"domain": "instagram", "content_type": "analysis", "category": "content_types"},
                {"domain": "instagram", "content_type": "generation", "category": "visuals"},
                {"domain": "instagram", "content_type": "review", "category": "stories"}
            ]
            
            await self.store_knowledge(
                expert_id="instagram",
                intent="generate",
                texts=instagram_texts[:5],
                metadata_list=instagram_metadata[:5]
            )
            
            await self.store_knowledge(
                expert_id="instagram",
                intent="analyze",
                texts=instagram_texts[5:8],
                metadata_list=instagram_metadata[5:8]
            )
            
            await self.store_knowledge(
                expert_id="instagram",
                intent="review",
                texts=instagram_texts[8:],
                metadata_list=instagram_metadata[8:]
            )
            
            logger.info("Seeded example knowledge for Instagram expert")
        except Exception as e:
            logger.error(f"Error seeding example knowledge: {e}")
            raise 