"""
Entity tracking memory that maintains information about entities mentioned in conversations.

This module provides a specialized memory implementation that keeps track of entities
mentioned throughout conversations, along with their associated attributes and context.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Set, Tuple

from langchain.memory import ConversationEntityMemory
from langchain.schema import BaseMessage

class EnhancedEntityMemory(ConversationEntityMemory):
    """
    Enhanced entity memory that tracks entity mentions with additional context.
    
    This class extends the ConversationEntityMemory to provide more sophisticated
    entity tracking, including sentiment, importance, and context retrieval based
    on conversation flow.
    """
    
    def __init__(
        self,
        llm: Any,
        session_manager: Any,
        session_id: str,
        entity_extraction_service: Any,
        max_entities: int = 100,
        memory_key: str = "entities",
        **kwargs
    ):
        """
        Initialize enhanced entity memory.
        
        Args:
            llm: LLM for entity extraction and summarization
            session_manager: Session management service
            session_id: Session identifier
            entity_extraction_service: Service for entity extraction from Phase 2.1
            max_entities: Maximum number of entities to track
            memory_key: Key to use for memory in chain inputs/outputs
        """
        super().__init__(
            llm=llm,
            return_messages=True,
            k=max_entities,
            **kwargs
        )
        self.session_manager = session_manager
        self.session_id = session_id
        self.entity_extraction_service = entity_extraction_service
        self.max_entities = max_entities
        self.memory_key = memory_key
        self.logger = logging.getLogger(__name__)
        
        # Store sentiment and importance with entities
        self.entity_attributes = {}
        
        # Load existing entities if available
        self._load_from_session()
    
    def _load_from_session(self) -> None:
        """
        Load entities from session if available.
        """
        try:
            session_entities = self.session_manager.get_session_entities(self.session_id)
            if session_entities:
                self.entity_store = session_entities.get("entities", {})
                self.entity_attributes = session_entities.get("attributes", {})
                self.logger.info(f"Loaded {len(self.entity_store)} entities from session {self.session_id}")
        except Exception as e:
            self.logger.warning(f"Failed to load entities from session: {e}")
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """
        Save context and extract entities with enhanced attributes.
        
        Args:
            inputs: Input values
            outputs: Output values
        """
        # Extract input/output text for entity extraction
        input_text = inputs.get("question", "")
        output_text = outputs.get("answer", "")
        
        # Use the entity extraction service from Phase 2.1
        extracted_entities = self.entity_extraction_service.extract_entities(
            input_text, output_text, self.session_id
        )
        
        # Update entities with extracted information
        for entity in extracted_entities:
            entity_name = entity["name"]
            entity_type = entity["type"]
            entity_sentiment = entity.get("sentiment", 0.0)
            entity_importance = entity.get("importance", 0.5)
            
            # Update entity summary
            summary = self.entity_store.get(entity_name, "")
            new_info = entity.get("context", "")
            updated_summary = self._update_entity_summary(entity_name, summary, new_info)
            
            # Store updated entity information
            self.entity_store[entity_name] = updated_summary
            
            # Store attributes
            if entity_name not in self.entity_attributes:
                self.entity_attributes[entity_name] = {
                    "type": entity_type,
                    "sentiment": entity_sentiment,
                    "importance": entity_importance,
                    "first_seen": time.time(),
                    "mentions": 1
                }
            else:
                # Update attributes
                attrs = self.entity_attributes[entity_name]
                attrs["sentiment"] = (attrs["sentiment"] * attrs["mentions"] + entity_sentiment) / (attrs["mentions"] + 1)
                attrs["importance"] = max(attrs["importance"], entity_importance)
                attrs["mentions"] += 1
                attrs["last_seen"] = time.time()
        
        # Save to session
        try:
            self.session_manager.store_session_entities(
                self.session_id, 
                {
                    "entities": self.entity_store,
                    "attributes": self.entity_attributes
                }
            )
            self.logger.debug(f"Saved entities to session {self.session_id}")
        except Exception as e:
            self.logger.warning(f"Failed to save entities to session: {e}")
    
    def _update_entity_summary(self, entity_name: str, existing_summary: str, new_info: str) -> str:
        """
        Update entity summary with new information.
        
        Args:
            entity_name: Name of the entity
            existing_summary: Existing entity summary
            new_info: New information about the entity
            
        Returns:
            Updated entity summary
        """
        if not existing_summary:
            return new_info
        
        if not new_info:
            return existing_summary
        
        # Use LLM to combine information
        try:
            prompt = f"""
            Entity: {entity_name}
            
            Existing information:
            {existing_summary}
            
            New information:
            {new_info}
            
            Create a concise, updated summary about this entity that combines both pieces of information,
            avoids redundancy, and includes the most important details.
            """
            
            updated_summary = self.llm.predict(prompt)
            return updated_summary.strip()
        except Exception as e:
            self.logger.warning(f"Failed to update entity summary: {e}")
            # Fallback to simple concatenation
            return f"{existing_summary}\n\nAdditional information: {new_info}"
    
    def get_entities_by_importance(self, min_importance: float = 0.0) -> List[Dict]:
        """
        Get entities sorted by importance score.
        
        Args:
            min_importance: Minimum importance score (0.0 to 1.0)
            
        Returns:
            List of entity dictionaries
        """
        entities = []
        
        for name, attrs in self.entity_attributes.items():
            if attrs.get("importance", 0.0) >= min_importance:
                entities.append({
                    "name": name,
                    "summary": self.entity_store.get(name, ""),
                    **attrs
                })
        
        # Sort by importance (descending)
        return sorted(entities, key=lambda e: e.get("importance", 0.0), reverse=True)
    
    def get_entities_by_type(self, entity_type: str) -> List[Dict]:
        """
        Get entities of a specific type.
        
        Args:
            entity_type: Entity type to filter by
            
        Returns:
            List of entity dictionaries
        """
        entities = []
        
        for name, attrs in self.entity_attributes.items():
            if attrs.get("type") == entity_type:
                entities.append({
                    "name": name,
                    "summary": self.entity_store.get(name, ""),
                    **attrs
                })
        
        return entities
    
    def get_recently_mentioned_entities(self, limit: int = 5) -> List[Dict]:
        """
        Get recently mentioned entities.
        
        Args:
            limit: Maximum number of entities to return
            
        Returns:
            List of entity dictionaries
        """
        entities = []
        
        for name, attrs in self.entity_attributes.items():
            if "last_seen" in attrs:
                entities.append({
                    "name": name,
                    "summary": self.entity_store.get(name, ""),
                    **attrs
                })
        
        # Sort by last_seen (descending)
        sorted_entities = sorted(entities, key=lambda e: e.get("last_seen", 0), reverse=True)
        return sorted_entities[:limit]
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load entity memory variables for use in chains.
        
        Args:
            inputs: Input values
            
        Returns:
            Memory variables including relevant entities
        """
        # Get context-relevant entities
        relevant_entities = self._get_relevant_entities(inputs)
        
        # Format entities for memory
        formatted_entities = {}
        for entity in relevant_entities:
            name = entity["name"]
            summary = entity["summary"]
            formatted_entities[name] = summary
        
        return {self.memory_key: formatted_entities}
    
    def _get_relevant_entities(self, inputs: Dict[str, Any]) -> List[Dict]:
        """
        Get entities relevant to the current context.
        
        Args:
            inputs: Input values
            
        Returns:
            List of relevant entity dictionaries
        """
        # Start with high-importance entities
        important_entities = self.get_entities_by_importance(min_importance=0.7)
        
        # Add recently mentioned entities
        recent_entities = self.get_recently_mentioned_entities(limit=3)
        
        # Extract query text
        query = inputs.get("question", "")
        
        # If query exists, use entity extraction to find mentioned entities
        mentioned_entities = []
        if query:
            extracted = self.entity_extraction_service.extract_entities(query, "", self.session_id)
            for entity in extracted:
                name = entity["name"]
                if name in self.entity_store:
                    mentioned_entities.append({
                        "name": name,
                        "summary": self.entity_store[name],
                        **(self.entity_attributes.get(name, {}))
                    })
        
        # Combine entities (removing duplicates)
        seen = set()
        all_entities = []
        
        for entity_list in [mentioned_entities, important_entities, recent_entities]:
            for entity in entity_list:
                name = entity["name"]
                if name not in seen:
                    seen.add(name)
                    all_entities.append(entity)
        
        return all_entities 