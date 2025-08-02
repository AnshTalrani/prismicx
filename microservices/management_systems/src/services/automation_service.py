"""
Service for managing automation rules and triggers.

This service provides the business logic for:
- Managing automation rules
- Processing triggers from management modules
- Executing actions based on rules
"""

import logging
import sys
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from bson.objectid import ObjectId

# Add database-layer to Python path
db_layer_path = Path(__file__).parent.parent.parent.parent.parent / "database-layer"
sys.path.append(str(db_layer_path))

from common.db_client import db_client
from ..plugins.registry import ModuleRegistry
from ..automation.automation_engine import AutomationEngine

logger = logging.getLogger(__name__)

class AutomationService:
    """Service for managing automation rules and triggers."""
    
    def __init__(self):
        """Initialize the automation service."""
        self.db_client = db_client
        
        # Create a user ID and API key for the automation engine
        # In a real system, these would come from configuration
        self.automation_engine = AutomationEngine(
            user_id="system",
            api_key="automation-service"
        )
        
    def get_available_triggers(self, module_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all available triggers from management modules.
        
        Args:
            module_type (Optional[str]): Filter by module type if provided
            
        Returns:
            List[Dict[str, Any]]: List of trigger information
        """
        triggers = []
        
        # Get modules from the registry
        modules = ModuleRegistry.get_modules()
        
        for module_name, module_instance in modules.items():
            # Skip if we're filtering by module type and this isn't a match
            if module_type and module_name != module_type:
                continue
                
            # Get triggers from this module
            if hasattr(module_instance, 'get_available_triggers'):
                module_triggers = module_instance.get_available_triggers()
                
                # Add module type to each trigger
                for trigger in module_triggers:
                    trigger['module_type'] = module_name
                    
                triggers.extend(module_triggers)
                
        return triggers
        
    def create_automation_rule(
        self,
        name: str,
        module_type: str,
        trigger_id: str,
        conditions: List[Dict[str, Any]],
        actions: List[Dict[str, Any]],
        description: Optional[str] = None,
        is_active: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new automation rule.
        
        Args:
            name (str): Name of the rule
            module_type (str): Type of management module
            trigger_id (str): ID of the trigger
            conditions (List[Dict[str, Any]]): List of conditions
            actions (List[Dict[str, Any]]): List of actions
            description (Optional[str]): Description of the rule
            is_active (bool): Whether the rule is active
            
        Returns:
            Dict[str, Any]: The created rule
        """
        # Validate that the module type and trigger exist
        modules = ModuleRegistry.get_modules()
        if module_type not in modules:
            raise ValueError(f"Invalid module type: {module_type}")
            
        module = modules[module_type]
        triggers = module.get_available_triggers()
        if not any(t["id"] == trigger_id for t in triggers):
            raise ValueError(f"Invalid trigger ID for module {module_type}: {trigger_id}")
            
        # Create the rule
        now = datetime.now().isoformat()
        rule_id = str(uuid.uuid4())
        
        rule = {
            "id": rule_id,
            "name": name,
            "description": description,
            "module_type": module_type,
            "trigger_id": trigger_id,
            "conditions": conditions,
            "actions": actions,
            "is_active": is_active,
            "created_at": now,
            "updated_at": now
        }
        
        # Save to database
        try:
            self.db_client.config.automation_rules.insert_one(rule)
            
            # Register the rule with the automation engine
            # In a real implementation, this would set up the appropriate event handlers
            logger.info(f"Created automation rule: {rule_id}")
            
            return rule
        except Exception as e:
            logger.error(f"Error creating automation rule: {str(e)}")
            raise
            
    def get_automation_rules(
        self,
        module_type: Optional[str] = None,
        trigger_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Get automation rules with optional filtering.
        
        Args:
            module_type (Optional[str]): Filter by module type
            trigger_id (Optional[str]): Filter by trigger ID
            is_active (Optional[bool]): Filter by active status
            
        Returns:
            List[Dict[str, Any]]: List of matching rules
        """
        # Build query
        query = {}
        if module_type:
            query["module_type"] = module_type
        if trigger_id:
            query["trigger_id"] = trigger_id
        if is_active is not None:
            query["is_active"] = is_active
            
        try:
            rules = list(self.db_client.config.automation_rules.find(query))
            # Convert ObjectId to string
            for rule in rules:
                if "_id" in rule:
                    del rule["_id"]
            return rules
        except Exception as e:
            logger.error(f"Error getting automation rules: {str(e)}")
            raise
            
    def get_automation_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific automation rule by ID.
        
        Args:
            rule_id (str): The ID of the rule
            
        Returns:
            Optional[Dict[str, Any]]: The rule if found, None otherwise
        """
        try:
            rule = self.db_client.config.automation_rules.find_one({"id": rule_id})
            if rule and "_id" in rule:
                del rule["_id"]
            return rule
        except Exception as e:
            logger.error(f"Error getting automation rule {rule_id}: {str(e)}")
            raise
            
    def update_rule_status(self, rule_id: str, is_active: bool) -> Optional[Dict[str, Any]]:
        """
        Update the active status of a rule.
        
        Args:
            rule_id (str): The ID of the rule
            is_active (bool): The new active status
            
        Returns:
            Optional[Dict[str, Any]]: The updated rule if found, None otherwise
        """
        try:
            now = datetime.now().isoformat()
            result = self.db_client.config.automation_rules.update_one(
                {"id": rule_id},
                {"$set": {"is_active": is_active, "updated_at": now}}
            )
            
            if result.matched_count == 0:
                return None
                
            return self.get_automation_rule(rule_id)
        except Exception as e:
            logger.error(f"Error updating automation rule {rule_id}: {str(e)}")
            raise
            
    def delete_automation_rule(self, rule_id: str) -> bool:
        """
        Delete an automation rule.
        
        Args:
            rule_id (str): The ID of the rule
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            result = self.db_client.config.automation_rules.delete_one({"id": rule_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting automation rule {rule_id}: {str(e)}")
            raise
            
    def process_event(self, event_type: str, event_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process an event to check if any automation rules should be triggered.
        
        Args:
            event_type (str): The type of event
            event_data (Dict[str, Any]): The event data
            
        Returns:
            List[Dict[str, Any]]: Results of any actions that were executed
        """
        # Get matching rules
        rules = self.get_automation_rules(trigger_id=event_type, is_active=True)
        
        results = []
        for rule in rules:
            try:
                # Get the module
                module_type = rule["module_type"]
                modules = ModuleRegistry.get_modules()
                
                if module_type not in modules:
                    logger.error(f"Module {module_type} not found for rule {rule['id']}")
                    continue
                    
                module = modules[module_type]
                
                # Evaluate conditions
                if hasattr(module, 'evaluate_trigger_condition'):
                    conditions_met = module.evaluate_trigger_condition(
                        rule["trigger_id"],
                        event_data,
                        rule["conditions"]
                    )
                    
                    if conditions_met:
                        # Execute actions
                        result = self.automation_engine.process_template({
                            "template_type": module_type,
                            "trigger": {"id": rule["trigger_id"]},
                            "actions": [a["type"] for a in rule["actions"]],
                            "context": event_data,
                            "notification": next(
                                (a["parameters"] for a in rule["actions"] if a["type"] == "send_notification"),
                                {}
                            )
                        })
                        
                        results.append({
                            "rule_id": rule["id"],
                            "result": result
                        })
            except Exception as e:
                logger.error(f"Error processing rule {rule['id']} for event {event_type}: {str(e)}")
                
        return results

# Singleton instance
_automation_service = None

def get_automation_service() -> AutomationService:
    """
    Get the singleton automation service instance.
    
    Returns:
        AutomationService: The automation service instance
    """
    global _automation_service
    if _automation_service is None:
        _automation_service = AutomationService()
    return _automation_service 