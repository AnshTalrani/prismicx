from typing import List, Dict
from models.user import UserID  # Assuming UserID is defined
from clients.client_interface import Client  # Assuming a Client interface exists



#it will be connected with webisite chatbot instructions
class CommunicationBase:
    notification_channels: Dict[str, Client] = {}
    # Alternatively, using a specific ClientType Enum if defined
    # notification_channels: Dict[ClientType, Client] = {}

    def request_missing_data(self, user: UserID, fields: List[str]) -> bool:
        """
        Requests missing data from the user.
        """
        # Implementation for requesting missing data
        client = self.notification_channels.get(user.client_type)
        if client:
            client.request_data(user, fields)
            return True
        return False

    def send_progress_update(self, request_id: str, message: str) -> None:
        """
        Sends a progress update for the given request ID.
        """
        # Implementation for sending progress update
        pass

    def push_final_result(self, user: UserID, data: dict) -> bool:
        """
        Pushes the final result to the user.
        """
        # Implementation for pushing final result
        client = self.notification_channels.get(user.client_type)
        if client:
            client.send_data(user, data)
            return True
        return False

class ServiceRegistry:
    def __init__(self):
        self.services = {}
    
    def register_service(self, name: str, url: str):
        self.services[name] = url
    
    def get_service_url(self, name: str) -> str:
        if name not in self.services:
            raise ValueError(f"Service {name} not found")
        return self.services[name] 