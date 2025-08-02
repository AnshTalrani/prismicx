"""
SalesManagementModule:
An example implementation of a management module for Sales Automation.
"""

from typing import List, Dict, Any
from ..base_management_module import BaseManagementModule
from ..dispatcher import EventDispatcher

class SalesManagementModule(BaseManagementModule):
    def __init__(self):
        # Subscribe to sales-related events
        EventDispatcher.subscribe("opportunity_created", self.handle_opportunity_created)
        EventDispatcher.subscribe("opportunity_stage_changed", self.handle_opportunity_stage_changed)
        EventDispatcher.subscribe("deal_closed", self.handle_deal_closed)

    def process_template(self, template_data: dict) -> dict:
        # Implement your sales-specific template processing logic here.
        return {"status": "Sales template processed", "data": template_data}

    def validate_configuration(self, config: dict) -> bool:
        # Validate sales automation configuration
        required_keys = ["opportunity_stages", "sales_pipelines"]
        return all(key in config for key in required_keys)

    def handle_event(self, event: dict) -> None:
        # Handle domain events relevant to sales automation.
        print("SalesManagementModule received event:", event)
        
    def handle_opportunity_created(self, event: dict) -> None:
        """
        Handle a new opportunity being created.
        """
        print(f"New opportunity created: {event.get('opportunity_name')} - Value: {event.get('value')}")
        
    def handle_opportunity_stage_changed(self, event: dict) -> None:
        """
        Handle an opportunity changing stages in the pipeline.
        """
        print(f"Opportunity {event.get('opportunity_id')} moved from {event.get('old_stage')} to {event.get('new_stage')}")
        
    def handle_deal_closed(self, event: dict) -> None:
        """
        Handle a deal being closed (won or lost).
        """
        status = event.get('status', 'unknown')
        print(f"Deal {event.get('opportunity_id')} closed as {status} - Value: {event.get('value')}")
        
    def get_available_triggers(self) -> List[Dict[str, Any]]:
        """
        Returns the available triggers for Sales automation.
        """
        return [
            {
                "id": "opportunity_created",
                "name": "Opportunity Created",
                "description": "Triggered when a new sales opportunity is created",
                "required_data": ["opportunity_id", "opportunity_name"]
            },
            {
                "id": "opportunity_stage_changed",
                "name": "Opportunity Stage Changed",
                "description": "Triggered when an opportunity moves to a different stage in the pipeline",
                "required_data": ["opportunity_id", "old_stage", "new_stage"]
            },
            {
                "id": "deal_closed_won",
                "name": "Deal Closed (Won)",
                "description": "Triggered when a deal is successfully closed",
                "required_data": ["opportunity_id", "value"]
            },
            {
                "id": "deal_closed_lost",
                "name": "Deal Closed (Lost)",
                "description": "Triggered when a deal is lost",
                "required_data": ["opportunity_id", "reason"]
            },
            {
                "id": "high_value_opportunity",
                "name": "High Value Opportunity",
                "description": "Triggered when an opportunity value exceeds a threshold",
                "required_data": ["opportunity_id", "value"]
            }
        ]
        
    def evaluate_trigger_condition(self, trigger_id: str, event_data: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
        """
        Evaluates whether the conditions for a Sales trigger are met.
        """
        if trigger_id == "opportunity_stage_changed":
            # Check if the stage transition matches what we're looking for
            if "stage_transition" in conditions:
                required_old = conditions["stage_transition"].get("from")
                required_new = conditions["stage_transition"].get("to")
                
                actual_old = event_data.get("old_stage")
                actual_new = event_data.get("new_stage")
                
                if required_old and actual_old != required_old:
                    return False
                if required_new and actual_new != required_new:
                    return False
        
        elif trigger_id == "high_value_opportunity":
            # Check if the opportunity value exceeds the threshold
            if "value_threshold" in conditions:
                threshold = conditions["value_threshold"]
                actual_value = event_data.get("value", 0)
                
                if actual_value < threshold:
                    return False
                    
        elif trigger_id in ["deal_closed_won", "deal_closed_lost"]:
            # Additional conditions for closed deals
            if "min_value" in conditions:
                min_value = conditions["min_value"]
                actual_value = event_data.get("value", 0)
                
                if actual_value < min_value:
                    return False
                    
        # If we made it here, all conditions passed
        return True 