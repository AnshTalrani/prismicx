"""
ExpertBase orchestrator for routing requests to appropriate ExpertBots.
"""

from typing import Dict, Any
from src.expert_bots.instagram_bot import InstagramBot
# Import other ExpertBots as needed
from src.utils.logger import Logger
from src.knowledge_base.knowledge_base_component import KnowledgeBaseComponent

class ExpertBase:
    def __init__(self, expert_bots: Dict[str, Any], logger: Logger):
        """
        Initializes the ExpertBase with a mapping of intent_tags to ExpertBot instances.

        Args:
            expert_bots (Dict[str, Any]): Mapping of intent_tags to ExpertBot instances.
            logger (Logger): Logger instance for logging interactions.
        """
        self.expert_bots = expert_bots  # e.g., {"instagram_post": InstagramBot, ...}
        self.logger = logger

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes the request to the appropriate ExpertBot based on intent_tag.

        Args:
            request (Dict[str, Any]): Incoming request containing intent_tag and parameters.

        Returns:
            Dict[str, Any]: Response from the ExpertBot or error message.
        """
        intent_tag = request.get("intent_tag")
        bot = self.expert_bots.get(intent_tag)
        if not bot:
            self.logger.log_error(f"No bot found for intent_tag: {intent_tag}")
            return {"error": "No bot for this intent_tag"}

        try:
            # Delegate to ExpertBot
            response = bot.process(request)
            # Log interaction for RL/fine-tuning
            self.log_data(request, response)
            return response
        except Exception as e:
            self.logger.log_error(f"Error processing request: {e}")
            return {"error": "Failed to process the request"}

    def log_data(self, request: Dict[str, Any], response: Dict[str, Any]) -> None:
        """
        Logs the interaction between the request and response.

        Args:
            request (Dict[str, Any]): The incoming request.
            response (Dict[str, Any]): The response from the ExpertBot.
        """
        log_entry = {
            "request": request,
            "response": response
        }
        self.logger.log_activity(f"Interaction logged: {log_entry}") 