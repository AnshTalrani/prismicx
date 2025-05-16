"""
Abstract interface for a management system module.
All management system plugins must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseManagementModule(ABC):
    @abstractmethod
    def process_template(self, template_data: dict) -> dict:
        """
        Process the provided automation template configuration and data.

        Args:
            template_data (dict): Template configuration and data.

        Returns:
            dict: Process result and status.
        """
        pass

    @abstractmethod
    def validate_configuration(self, config: dict) -> bool:
        """
        Validate the tenant-specific configuration for this management module.

        Args:
            config (dict): Configuration data.

        Returns:
            bool: True if configuration is valid, otherwise False.
        """
        pass

    @abstractmethod
    def handle_event(self, event: dict) -> None:
        """
        Process a domain event received from the central event bus.

        Args:
            event (dict): Event data.
        """
        pass
        
    def get_available_triggers(self) -> List[Dict[str, Any]]:
        """
        Returns a list of available triggers that can be used for automation.
        
        Each trigger is a dictionary with the following fields:
        - id: Unique identifier for the trigger
        - name: Display name for the trigger
        - description: Description of when the trigger fires
        - required_data: List of data fields required for this trigger
        
        Returns:
            List[Dict[str, Any]]: List of available triggers
        """
        # Default implementation returns an empty list.
        # Subclasses should override this method to provide their triggers.
        return []
        
    def create_automation(self, trigger_id: str, conditions: Dict[str, Any], actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Creates a new automation rule based on a trigger, conditions, and actions.
        
        Args:
            trigger_id (str): The ID of the trigger that will activate this automation
            conditions (Dict[str, Any]): Conditions that must be met for the automation to execute
            actions (List[Dict[str, Any]]): Actions to perform when the automation executes
            
        Returns:
            Dict[str, Any]: The created automation rule
        """
        # Default implementation - subclasses may override
        return {
            "trigger_id": trigger_id,
            "conditions": conditions,
            "actions": actions,
            "status": "active"
        }
        
    def evaluate_trigger_condition(self, trigger_id: str, event_data: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
        """
        Evaluates whether the conditions for a trigger are met given the event data.
        
        Args:
            trigger_id (str): The ID of the trigger being evaluated
            event_data (Dict[str, Any]): Data from the event that triggered the automation
            conditions (Dict[str, Any]): Conditions that must be met
            
        Returns:
            bool: True if conditions are met, False otherwise
        """
        # Default implementation always returns True
        # Subclasses should override with specific condition evaluation
        return True 