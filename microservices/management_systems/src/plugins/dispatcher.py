"""
A simple in-process event dispatcher for decoupled event communication across modules.
In production, consider using a dedicated message broker (e.g., RabbitMQ, Kafka).
"""

class EventDispatcher:
    _subscribers = {}

    @classmethod
    def subscribe(cls, event_type: str, callback: callable):
        """
        Subscribe to a specific event type with a callback.
        
        Args:
            event_type (str): The type of event.
            callback (callable): Function to call when the event is published.
        """
        cls._subscribers.setdefault(event_type, []).append(callback)

    @classmethod
    def publish(cls, event_type: str, event_data: dict):
        """
        Publish an event to all subscribers of the given event type.
        
        Args:
            event_type (str): The event type.
            event_data (dict): The event data.
        """
        for callback in cls._subscribers.get(event_type, []):
            callback(event_data) 