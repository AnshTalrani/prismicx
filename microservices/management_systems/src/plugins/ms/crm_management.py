"""
CRMManagementModule:
A management system module for Customer Relationship Management (CRM).
This module processes CRM-related templates, validates CRM-specific configuration,
and handles domain events pertinent to customer relationship management.
"""

from typing import List, Dict, Any
from ..base_management_module import BaseManagementModule
from ..dispatcher import EventDispatcher

class CRMManagementModule(BaseManagementModule):
    def __init__(self):
        # Optionally subscribe to CRM-related events
        EventDispatcher.subscribe("contact_updated", self.handle_contact_update)
        EventDispatcher.subscribe("lead_created", self.handle_lead_created)

    def process_template(self, template_data: dict) -> dict:
        """
        Process the CRM template.
        For example, this could involve updating customer contact details,
        scheduling follow-ups, or triggering reminder notifications.
        """
        # Implement your CRM processing logic.
        result = {
            "status": "CRM template processed",
            "template": template_data,
            "action": "Updated customer records, scheduled follow-ups."
        }
        return result

    def validate_configuration(self, config: dict) -> bool:
        """
        Validate CRM-specific configuration.
        For instance, ensure required fields like `contact_fields` or `lead_sources` are provided.
        """
        required_keys = ["contact_fields", "lead_sources"]
        return all(key in config for key in required_keys)

    def handle_event(self, event: dict) -> None:
        """
        General event handler for CRM events.
        """
        print("CRMManagementModule handling general event:", event)

    def handle_contact_update(self, event: dict):
        """
        Specific handler for the 'contact_updated' event.
        """
        print("CRMManagementModule received contact update:", event)
        
        # Example: If this is a status change, we could further dispatch a specialized event
        if "old_status" in event and "new_status" in event:
            if event["old_status"] != event["new_status"]:
                EventDispatcher.publish("contact_status_changed", {
                    "contact_id": event.get("contact_id"),
                    "old_status": event["old_status"],
                    "new_status": event["new_status"]
                })

    def handle_lead_created(self, event: dict):
        """
        Specific handler for the 'lead_created' event.
        """
        print("CRMManagementModule received new lead:", event)
        
    def get_available_triggers(self) -> List[Dict[str, Any]]:
        """
        Returns the available triggers for CRM automation.
        """
        return [
            {
                "id": "contact_created",
                "name": "Contact Created",
                "description": "Triggered when a new contact is created in the CRM system",
                "required_data": []
            },
            {
                "id": "contact_updated",
                "name": "Contact Updated",
                "description": "Triggered when a contact's information is updated",
                "required_data": ["contact_id"]
            },
            {
                "id": "contact_status_changed",
                "name": "Contact Status Changed",
                "description": "Triggered when a contact's status changes (e.g., lead to customer)",
                "required_data": ["contact_id", "old_status", "new_status"]
            },
            {
                "id": "lead_created",
                "name": "Lead Created",
                "description": "Triggered when a new lead is created in the CRM system",
                "required_data": ["lead_id"]
            }
        ]
        
    def evaluate_trigger_condition(self, trigger_id: str, event_data: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
        """
        Evaluates whether the conditions for a CRM trigger are met.
        """
        if trigger_id == "contact_status_changed":
            # Check if the status change matches what we're looking for
            if "status_transition" in conditions:
                required_old = conditions["status_transition"].get("from")
                required_new = conditions["status_transition"].get("to")
                
                actual_old = event_data.get("old_status")
                actual_new = event_data.get("new_status")
                
                if required_old and actual_old != required_old:
                    return False
                if required_new and actual_new != required_new:
                    return False
                    
            # Check if the contact is in a specific group
            if "contact_group" in conditions:
                required_group = conditions["contact_group"]
                # This would look up the contact's group in a real implementation
                # For now, we just assume it doesn't match
                return False
                
        elif trigger_id == "lead_created":
            # Check if the lead source matches
            if "lead_source" in conditions:
                required_source = conditions["lead_source"]
                actual_source = event_data.get("source")
                if required_source != actual_source:
                    return False
                    
        # If we made it here, all conditions passed
        return True 