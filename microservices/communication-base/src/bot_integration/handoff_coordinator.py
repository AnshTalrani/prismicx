"""
Handoff coordinator for managing transitions between different bot types.

This module provides functionality for coordinating handoffs between different bot
types, ensuring conversation continuity and smooth transitions for users.
"""

import logging
import time
from typing import Dict, Any, List, Optional

from langchain.schema.runnable import RunnableBranch

class HandoffCoordinator:
    """
    Handoff coordinator for managing transitions between different bot types.
    
    This class manages the handoff process between bots, prepares context for the
    receiving bot, and ensures conversation continuity during transitions.
    """
    
    def __init__(
        self,
        config_integration: Any,
        session_manager: Any,
        bot_manager: Any,
        rules_engine: Any = None
    ):
        """
        Initialize handoff coordinator.
        
        Args:
            config_integration: Integration with the config system
            session_manager: Session management service
            bot_manager: Bot management service
            rules_engine: Optional rules engine for handoff decisions
        """
        self.config_integration = config_integration
        self.session_manager = session_manager
        self.bot_manager = bot_manager
        self.rules_engine = rules_engine
        self.logger = logging.getLogger(__name__)
    
    async def initiate_handoff(
        self,
        from_bot_type: str,
        to_bot_type: str,
        session_id: str,
        user_id: str,
        reason: str,
        transition_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate a handoff from one bot type to another.
        
        Args:
            from_bot_type: Source bot type
            to_bot_type: Target bot type
            session_id: Session identifier
            user_id: User identifier
            reason: Reason for handoff
            transition_message: Optional message to display during transition
            
        Returns:
            Handoff result with status and information
        """
        try:
            # Check if target bot type is valid
            if not self._is_valid_bot_type(to_bot_type):
                return {
                    "success": False,
                    "error": f"Invalid target bot type: {to_bot_type}",
                    "reason": reason
                }
            
            # Get handoff config
            handoff_config = self._get_handoff_config(from_bot_type, to_bot_type)
            
            # Create handoff context
            handoff_context = await self._create_handoff_context(
                from_bot_type, to_bot_type, session_id, user_id, reason, handoff_config
            )
            
            # Store handoff context
            await self.session_manager.store_handoff_context(
                session_id, handoff_context
            )
            
            # Generate transition message if not provided
            if not transition_message:
                transition_message = self._generate_transition_message(
                    from_bot_type, to_bot_type, reason, handoff_config
                )
            
            # Update session with new bot type
            await self.session_manager.update_session_bot_type(
                session_id, to_bot_type
            )
            
            # Log handoff
            self.logger.info(
                f"Handoff initiated from {from_bot_type} to {to_bot_type}",
                extra={
                    "session_id": session_id,
                    "user_id": user_id,
                    "reason": reason
                }
            )
            
            return {
                "success": True,
                "from_bot_type": from_bot_type,
                "to_bot_type": to_bot_type,
                "reason": reason,
                "transition_message": transition_message,
                "context_size": len(handoff_context.get("shared_memory", [])),
                "handoff_id": handoff_context.get("handoff_id")
            }
            
        except Exception as e:
            self.logger.error(
                f"Handoff failed: {e}",
                extra={
                    "session_id": session_id,
                    "user_id": user_id,
                    "from_bot_type": from_bot_type,
                    "to_bot_type": to_bot_type
                },
                exc_info=True
            )
            
            return {
                "success": False,
                "error": str(e),
                "reason": reason
            }
    
    def check_handoff_needed(
        self,
        current_bot_type: str,
        query: str,
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Check if a handoff is needed based on query and context.
        
        Args:
            current_bot_type: Current bot type
            query: User query
            session_id: Session identifier
            user_id: User identifier
            
        Returns:
            Handoff recommendation with target bot and reason
        """
        # Skip if no rules engine
        if not self.rules_engine:
            return {"handoff_needed": False}
        
        try:
            # Check rules
            result = self.rules_engine.evaluate_handoff_rules(
                current_bot_type, query, session_id, user_id
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                f"Error checking handoff rules: {e}",
                extra={
                    "session_id": session_id,
                    "user_id": user_id,
                    "current_bot_type": current_bot_type
                },
                exc_info=True
            )
            
            return {"handoff_needed": False}
    
    async def receive_handoff(
        self,
        session_id: str,
        bot_type: str
    ) -> Dict[str, Any]:
        """
        Receive a handoff and prepare context for the bot.
        
        Args:
            session_id: Session identifier
            bot_type: Bot type receiving the handoff
            
        Returns:
            Handoff context with shared memory and metadata
        """
        try:
            # Get handoff context
            handoff_context = await self.session_manager.get_handoff_context(session_id)
            
            if not handoff_context:
                return {"success": False, "error": "No handoff context found"}
            
            # Check if this bot is the intended recipient
            to_bot_type = handoff_context.get("to_bot_type")
            if to_bot_type != bot_type:
                self.logger.warning(
                    f"Handoff intended for {to_bot_type}, but received by {bot_type}",
                    extra={"session_id": session_id}
                )
            
            # Format context for this bot type
            formatted_context = self._format_context_for_bot(handoff_context, bot_type)
            
            return {
                "success": True,
                "context": formatted_context,
                "metadata": handoff_context.get("metadata", {})
            }
            
        except Exception as e:
            self.logger.error(
                f"Error receiving handoff: {e}",
                extra={"session_id": session_id, "bot_type": bot_type},
                exc_info=True
            )
            
            return {"success": False, "error": str(e)}
    
    async def _create_handoff_context(
        self,
        from_bot_type: str,
        to_bot_type: str,
        session_id: str,
        user_id: str,
        reason: str,
        handoff_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a handoff context with relevant shared information.
        
        Args:
            from_bot_type: Source bot type
            to_bot_type: Target bot type
            session_id: Session identifier
            user_id: User identifier
            reason: Handoff reason
            handoff_config: Handoff configuration
            
        Returns:
            Handoff context dictionary
        """
        # Create unique handoff ID
        handoff_id = f"{from_bot_type}_{to_bot_type}_{int(time.time())}"
        
        # Get memory to share
        shared_memory = await self._get_shared_memory(
            from_bot_type, to_bot_type, session_id, handoff_config
        )
        
        # Get entities to share
        shared_entities = await self._get_shared_entities(
            from_bot_type, to_bot_type, session_id, handoff_config
        )
        
        # Get user profile information
        user_profile = await self.session_manager.get_user_profile(user_id)
        
        # Create context
        context = {
            "handoff_id": handoff_id,
            "from_bot_type": from_bot_type,
            "to_bot_type": to_bot_type,
            "timestamp": time.time(),
            "reason": reason,
            "shared_memory": shared_memory,
            "shared_entities": shared_entities,
            "user_profile": user_profile,
            "metadata": {
                "handoff_count": await self._get_handoff_count(session_id) + 1,
                "source_config": handoff_config
            }
        }
        
        return context
    
    async def _get_shared_memory(
        self,
        from_bot_type: str,
        to_bot_type: str,
        session_id: str,
        handoff_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get memory to share during handoff.
        
        Args:
            from_bot_type: Source bot type
            to_bot_type: Target bot type
            session_id: Session identifier
            handoff_config: Handoff configuration
            
        Returns:
            List of memory items to share
        """
        # Get memory sharing configuration
        memory_config = handoff_config.get("memory_sharing", {})
        share_all = memory_config.get("share_all", False)
        max_items = memory_config.get("max_items", 10)
        
        # Get session memory
        memory = await self.session_manager.get_session_memory(session_id)
        
        if not memory:
            return []
        
        # Convert to serializable format
        memory_items = []
        for item in memory:
            if hasattr(item, "to_dict"):
                memory_items.append(item.to_dict())
            elif isinstance(item, dict):
                memory_items.append(item)
        
        # Apply sharing rules
        if share_all:
            return memory_items[:max_items]
        else:
            # Filter by importance or relevance
            important_items = []
            for item in memory_items:
                # Simple heuristic - check for importance markers
                importance = item.get("metadata", {}).get("importance", 0.5)
                if importance >= memory_config.get("importance_threshold", 0.7):
                    important_items.append(item)
            
            return important_items[:max_items]
    
    async def _get_shared_entities(
        self,
        from_bot_type: str,
        to_bot_type: str,
        session_id: str,
        handoff_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get entities to share during handoff.
        
        Args:
            from_bot_type: Source bot type
            to_bot_type: Target bot type
            session_id: Session identifier
            handoff_config: Handoff configuration
            
        Returns:
            Dictionary of entities to share
        """
        # Get entity sharing configuration
        entity_config = handoff_config.get("entity_sharing", {})
        share_all = entity_config.get("share_all", False)
        
        # Get session entities
        entities = await self.session_manager.get_session_entities(session_id)
        
        if not entities:
            return {}
        
        if share_all:
            return entities
        else:
            # Filter by allowed entity types
            allowed_types = entity_config.get("allowed_types", [])
            filtered_entities = {}
            
            for entity_id, entity in entities.items():
                entity_type = entity.get("type")
                if entity_type in allowed_types:
                    filtered_entities[entity_id] = entity
            
            return filtered_entities
    
    def _format_context_for_bot(
        self,
        handoff_context: Dict[str, Any],
        bot_type: str
    ) -> Dict[str, Any]:
        """
        Format handoff context for a specific bot type.
        
        Args:
            handoff_context: Handoff context
            bot_type: Bot type
            
        Returns:
            Formatted context
        """
        # Get bot-specific preferences
        bot_config = self.config_integration.get_config(bot_type)
        handoff_prefs = bot_config.get("handoff_preferences", {})
        
        # Create formatted context
        formatted = {
            "memory": handoff_context.get("shared_memory", []),
            "entities": handoff_context.get("shared_entities", {}),
            "user_profile": handoff_context.get("user_profile", {})
        }
        
        # Apply bot-specific formatting preferences
        if "memory_format" in handoff_prefs:
            memory_format = handoff_prefs["memory_format"]
            if memory_format == "summary":
                # Summarize memory instead of full history
                formatted["memory"] = self._summarize_memory(formatted["memory"])
        
        if "entity_format" in handoff_prefs:
            entity_format = handoff_prefs["entity_format"]
            if entity_format == "simplified":
                # Simplify entity information
                formatted["entities"] = self._simplify_entities(formatted["entities"])
        
        return formatted
    
    def _summarize_memory(self, memory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Summarize memory items.
        
        Args:
            memory: Memory items
            
        Returns:
            Summarized memory
        """
        # Simple implementation - just take most recent items
        # In a real implementation, this would use LLM to summarize
        return memory[-3:]
    
    def _simplify_entities(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simplify entity information.
        
        Args:
            entities: Entity dictionary
            
        Returns:
            Simplified entities
        """
        # Simple implementation - keep only essential fields
        simplified = {}
        
        for entity_id, entity in entities.items():
            simplified[entity_id] = {
                "type": entity.get("type"),
                "name": entity.get("name"),
                "importance": entity.get("importance", 0.5)
            }
        
        return simplified
    
    def _generate_transition_message(
        self,
        from_bot_type: str,
        to_bot_type: str,
        reason: str,
        handoff_config: Dict[str, Any]
    ) -> str:
        """
        Generate a transition message for the handoff.
        
        Args:
            from_bot_type: Source bot type
            to_bot_type: Target bot type
            reason: Handoff reason
            handoff_config: Handoff configuration
            
        Returns:
            Transition message
        """
        # Check for preconfigured message
        if "transition_message" in handoff_config:
            return handoff_config["transition_message"]
        
        # Generate based on bot types
        bot_names = {
            "consultancy": "Consultancy Specialist",
            "sales": "Sales Representative",
            "support": "Support Agent"
        }
        
        from_name = bot_names.get(from_bot_type, from_bot_type.capitalize())
        to_name = bot_names.get(to_bot_type, to_bot_type.capitalize())
        
        return f"I'm transferring you to our {to_name} who can better assist with your request. Your conversation history will be shared to provide a seamless experience."
    
    def _get_handoff_config(
        self,
        from_bot_type: str,
        to_bot_type: str
    ) -> Dict[str, Any]:
        """
        Get handoff configuration for a specific transition.
        
        Args:
            from_bot_type: Source bot type
            to_bot_type: Target bot type
            
        Returns:
            Handoff configuration
        """
        # Get source bot config
        from_config = self.config_integration.get_config(from_bot_type)
        
        # Check for specific config for this transition
        handoff_configs = from_config.get("handoffs", {})
        specific_config = handoff_configs.get(to_bot_type, {})
        
        # Merge with default handoff config
        default_config = handoff_configs.get("default", {})
        
        # Create merged config
        config = {**default_config, **specific_config}
        
        return config
    
    def _is_valid_bot_type(self, bot_type: str) -> bool:
        """
        Check if a bot type is valid.
        
        Args:
            bot_type: Bot type to check
            
        Returns:
            True if valid, False otherwise
        """
        return bot_type in ["consultancy", "sales", "support"]
    
    async def _get_handoff_count(self, session_id: str) -> int:
        """
        Get the number of previous handoffs in this session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Handoff count
        """
        session_data = await self.session_manager.get_session(session_id)
        return session_data.get("handoff_count", 0)
    
    def create_handoff_runnable(
        self,
        session_id: str,
        user_id: str
    ):
        """
        Create a LangChain runnable for handling handoffs.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            
        Returns:
            RunnableBranch for handoff processing
        """
        async def should_handoff(inputs):
            current_bot_type = inputs.get("bot_type", "consultancy")
            query = inputs.get("query", "")
            
            result = self.check_handoff_needed(current_bot_type, query, session_id, user_id)
            return result.get("handoff_needed", False)
        
        async def process_handoff(inputs):
            current_bot_type = inputs.get("bot_type", "consultancy")
            handoff_result = self.check_handoff_needed(current_bot_type, inputs.get("query", ""), session_id, user_id)
            
            if handoff_result.get("handoff_needed", False):
                to_bot_type = handoff_result.get("target_bot")
                reason = handoff_result.get("reason", "Based on query content")
                
                # Initiate handoff
                result = await self.initiate_handoff(
                    current_bot_type, to_bot_type, session_id, user_id, reason
                )
                
                return {
                    "handoff_initiated": True,
                    "result": result,
                    "transition_message": result.get("transition_message", "")
                }
            
            return {"handoff_initiated": False}
        
        async def continue_normal(inputs):
            return {"handoff_initiated": False}
        
        # Create RunnableBranch
        return RunnableBranch(
            (should_handoff, process_handoff),
            (continue_normal)
        ) 