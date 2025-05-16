"""
Priority-based processor for extracted entities.
Processes entities according to their priorities defined in configuration.
"""

import logging
from typing import Dict, List, Any, Optional

from src.config.config_inheritance import ConfigInheritance

class PriorityProcessor:
    """
    Priority-based processor for extracted entities.
    Handles entity prioritization and action triggering based on rules.
    """
    
    def __init__(self):
        """Initialize the priority processor."""
        self.config_inheritance = ConfigInheritance()
        self.logger = logging.getLogger(__name__)
    
    def process_entities(self, bot_type: str, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process entities according to their priorities.
        
        Args:
            bot_type: The type of bot (consultancy, sales, support)
            entities: Dictionary of extracted entities
            
        Returns:
            List of prioritized entities with metadata
        """
        config = self.config_inheritance.get_config(bot_type)
        priority_configs = config.get("nlp.priorities", {})
        
        # Store priority levels
        priority_levels = {}
        
        # Assign priorities to entities
        for category, items in entities.items():
            if not items:
                continue
                
            # Get priority for this category
            category_priority = priority_configs.get(category, {}).get("level", 0)
            
            # Process items in the category
            for item in items:
                # Check if this is already a dictionary
                if isinstance(item, dict):
                    # Copy the item to avoid modifying the original
                    processed_item = item.copy()
                else:
                    # Create a dictionary for the item
                    processed_item = {"value": item}
                
                # Add metadata
                processed_item["category"] = category
                processed_item["priority"] = category_priority
                
                # Store by priority level
                if category_priority not in priority_levels:
                    priority_levels[category_priority] = []
                
                priority_levels[category_priority].append(processed_item)
        
        # Sort by priority (higher values first)
        sorted_priorities = sorted(priority_levels.keys(), reverse=True)
        
        # Flatten into a single list maintaining priority order
        prioritized_entities = []
        for priority in sorted_priorities:
            prioritized_entities.extend(priority_levels[priority])
        
        return prioritized_entities
    
    def get_action_triggers(self, bot_type: str, prioritized_entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get actions that should be triggered based on prioritized entities.
        
        Args:
            bot_type: The type of bot (consultancy, sales, support)
            prioritized_entities: List of prioritized entities
            
        Returns:
            List of action triggers with related entities
        """
        config = self.config_inheritance.get_config(bot_type)
        trigger_configs = config.get("nlp.triggers", {})
        
        triggers = []
        
        # Check each entity against trigger conditions
        for entity in prioritized_entities:
            category = entity.get("category")
            
            # Get triggers for this category
            category_triggers = trigger_configs.get(category, [])
            
            for trigger_config in category_triggers:
                # Check trigger conditions
                trigger_type = trigger_config.get("type")
                condition = trigger_config.get("condition", {})
                
                if self._check_trigger_condition(entity, condition):
                    # Create trigger with entity that caused it
                    trigger = {
                        "type": trigger_type,
                        "entity": entity,
                        "action": trigger_config.get("action"),
                        "priority": entity.get("priority", 0)
                    }
                    
                    triggers.append(trigger)
        
        # Sort triggers by priority
        return sorted(triggers, key=lambda t: t.get("priority", 0), reverse=True)
    
    def _check_trigger_condition(self, entity: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """
        Check if an entity meets a trigger condition.
        
        Args:
            entity: The entity to check
            condition: The condition to evaluate
            
        Returns:
            True if the condition is met, False otherwise
        """
        condition_type = condition.get("type")
        
        if not condition_type:
            # No condition means always trigger
            return True
        
        if condition_type == "value_equals":
            # Check if the entity value equals the target value
            value = entity.get("value")
            target = condition.get("target")
            return value == target
            
        elif condition_type == "value_contains":
            # Check if the entity value contains the target string
            value = entity.get("value", "")
            target = condition.get("target", "")
            
            # Handle different value types
            if isinstance(value, str) and isinstance(target, str):
                return target.lower() in value.lower()
            return False
            
        elif condition_type == "priority_above":
            # Check if the entity priority is above a threshold
            priority = entity.get("priority", 0)
            threshold = condition.get("threshold", 0)
            return priority > threshold
            
        # Unknown condition type
        return False

# Global instance
priority_processor = PriorityProcessor() 