"""
automation_engine module for the management_systems microservice.

Handles automation processes including:
- Template condition evaluation
- Event-driven trigger processing
- Periodic tasks processing
- Notifications
- Integration with management plugins

Follows MACH architecture principles.
"""

import logging
from typing import Dict, List, Any, Callable
from ..plugins.dispatcher import EventDispatcher

class AutomationEngine:
    """
    Class for processing automation templates and executing corresponding actions
    based on triggers and conditions.
    """

    def __init__(self, user_id: str, api_key: str):
        """
        Initializes the AutomationEngine for a given user with an API key.
        
        Args:
            user_id (str): Identifier of the user.
            api_key (str): API key for authenticating third-party integrations.
        """
        self.user_id = user_id
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.registered_triggers = {}
        
        # Subscribe to relevant events from the EventDispatcher
        self._register_event_listeners()

    def _register_event_listeners(self):
        """
        Register event listeners with the EventDispatcher for automation triggers.
        """
        # Register for common events that might trigger automations
        EventDispatcher.subscribe("contact_updated", self._handle_contact_updated)
        EventDispatcher.subscribe("lead_created", self._handle_lead_created)
        EventDispatcher.subscribe("data_changed", self._handle_data_changed)
        # Additional events can be subscribed here

    def register_trigger(self, trigger_id: str, handler: Callable[[Dict[str, Any]], None]):
        """
        Registers a trigger handler for a specific trigger ID.
        
        Args:
            trigger_id (str): The unique identifier for the trigger.
            handler (Callable): The function to call when the trigger conditions are met.
        """
        self.registered_triggers[trigger_id] = handler
        self.logger.info(f"Registered trigger handler for '{trigger_id}'")

    def process_template(self, template_data: dict) -> str:
        """
        Processes a given automation template data dict.

        Evaluates conditions from template data and triggers actions accordingly.

        Args:
            template_data (dict): Template data containing conditions and actions.

        Returns:
            str: A message or status after processing the template.
        """
        try:
            self.logger.info("Processing template for user %s", self.user_id)
            
            # Get template type and trigger information
            template_type = template_data.get("template_type", "")
            trigger_info = template_data.get("trigger", {})
            conditions = template_data.get("conditions", {})
            actions = template_data.get("actions", [])
            
            # Log template processing
            self.logger.info(f"Processing {template_type} template with trigger: {trigger_info.get('id', 'none')}")
            
            # Check if conditions are met
            if self._evaluate_conditions(conditions, template_data.get("context", {})):
                return self._execute_actions(actions, template_data)
            
            return "No conditions met for automation."
        except Exception as e:
            self.logger.error("Error processing template: %s", e)
            return f"Error processing template: {str(e)}"

    def _evaluate_conditions(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Evaluates the conditions based on the provided context.
        
        Args:
            conditions (Dict[str, Any]): The conditions to evaluate.
            context (Dict[str, Any]): The context data to evaluate against.
            
        Returns:
            bool: True if all conditions are met, False otherwise.
        """
        if not conditions:
            return True  # No conditions means always execute
            
        # Field value condition
        if "field_equals" in conditions:
            field = conditions["field_equals"]["field"]
            value = conditions["field_equals"]["value"]
            if context.get(field) != value:
                return False
                
        # Numeric threshold condition
        if "field_below" in conditions:
            field = conditions["field_below"]["field"]
            threshold = conditions["field_below"]["value"]
            if not context.get(field) or context.get(field) >= threshold:
                return False
                
        # Status change condition
        if "status_changed" in conditions:
            old_status = context.get("old_status")
            new_status = context.get("new_status")
            expected_old = conditions["status_changed"].get("from")
            expected_new = conditions["status_changed"].get("to")
            
            if (expected_old and old_status != expected_old) or \
               (expected_new and new_status != expected_new):
                return False
        
        return True  # All conditions passed

    def _execute_actions(self, actions: List[str], template_data: Dict[str, Any]) -> str:
        """
        Executes the specified actions.
        
        Args:
            actions (List[str]): List of action IDs to execute.
            template_data (Dict[str, Any]): The template data for context.
            
        Returns:
            str: Status message after executing actions.
        """
        results = []
        
        for action in actions:
            if action == "send_notification":
                recipient = template_data.get("notification", {}).get("recipient", "admin@example.com")
                message = template_data.get("notification", {}).get("message", "Automation triggered")
                self.send_notification(message, recipient)
                results.append(f"Notification sent to {recipient}")
                
            elif action == "update_status":
                # Logic to update status would go here
                entity_id = template_data.get("entity_id")
                new_status = template_data.get("new_status")
                results.append(f"Status updated for {entity_id} to {new_status}")
                
            elif action == "create_task":
                # Logic to create a task would go here
                task_title = template_data.get("task", {}).get("title", "Follow-up")
                results.append(f"Task created: {task_title}")
                
        return f"Actions executed: {', '.join(results)}"

    def _handle_contact_updated(self, event: Dict[str, Any]):
        """
        Handle a contact updated event from the CRM module.
        
        Args:
            event (Dict[str, Any]): The event data.
        """
        self.logger.info(f"Received contact_updated event: {event.get('contact_id')}")
        # Find and process any automation templates that might be triggered by this event
        self._process_event_triggered_templates("contact_updated", event)

    def _handle_lead_created(self, event: Dict[str, Any]):
        """
        Handle a lead created event from the CRM module.
        
        Args:
            event (Dict[str, Any]): The event data.
        """
        self.logger.info(f"Received lead_created event: {event.get('lead_id')}")
        # Find and process any automation templates that might be triggered by this event
        self._process_event_triggered_templates("lead_created", event)

    def _handle_data_changed(self, event: Dict[str, Any]):
        """
        Handle a generic data changed event.
        
        Args:
            event (Dict[str, Any]): The event data.
        """
        self.logger.info(f"Received data_changed event for {event.get('entity_type')}")
        # Find and process any automation templates that might be triggered by this event
        self._process_event_triggered_templates("data_changed", event)

    def _process_event_triggered_templates(self, event_type: str, event_data: Dict[str, Any]):
        """
        Process any automation templates that should be triggered by this event.
        
        Args:
            event_type (str): The type of event that occurred.
            event_data (Dict[str, Any]): The event data.
        """
        # In a real implementation, this would query the database for templates
        # that have a trigger matching this event type and then process them
        self.logger.info(f"Checking for automations triggered by {event_type}")
        
        # This is a placeholder - in reality you'd fetch matching templates from storage
        # For example, if we had automation templates for each event type:
        if event_type in self.registered_triggers:
            self.registered_triggers[event_type](event_data)

    def send_notification(self, message: str, recipient: str):
        """
        Sends a notification to a given recipient.
        
        Args:
            message (str): The message to send.
            recipient (str): The recipient's contact.
        """
        try:
            # Dummy notification processing: Just log the notification.
            self.logger.info("Sending notification '%s' to %s", message, recipient)
            # In a real implementation, integrate with an email/SMS service.
        except Exception as e:
            self.logger.error("Error sending notification: %s", e)
            raise

    def run_periodic_tasks(self):
        """
        Executes periodic operations such as scheduled template processing.
        
        Raises:
            Exception: If any task fails.
        """
        try:
            self.logger.info("Running periodic tasks for user %s", self.user_id)
            # Place holder for periodic operations logic.
        except Exception as e:
            self.logger.error("Error running periodic tasks: %s", e)
            raise
