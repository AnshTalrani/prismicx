"""
ExpertBase orchestrator for routing and processing requests using modular components.
"""

import os
import yaml
from typing import Dict, Any
from src.expert_bots.instagram_bot import InstagramBot
# Import other ExpertBots as needed
from src.utils.logger import Logger
from src.knowledge_base.knowledge_base_component import KnowledgeBaseComponent
from src.prompting.prompt_templates import PromptTemplates
from src.fusion.fusion_module import FusionModule
from src.feedback.evaluation_module import FeedbackModule

class ExpertBase:
    def __init__(self, expert_bots: Dict[str, Any], logger: Logger, config_path: str = "config/config.yaml"):
        """
        Initializes the ExpertBase with a mapping of expert bots and loads a centralized configuration.

        Args:
            expert_bots (Dict[str, Any]): Mapping of expert identifiers to ExpertBot instances.
            logger (Logger): Logger instance for logging interactions.
            config_path (str): Path to the configuration file.
        """
        self.expert_bots = expert_bots  # e.g., {"instagram_bot": InstagramBot, ...}
        self.logger = logger

        # Load dynamic config from file
        with open(config_path, "r") as file:
            self.configurations = yaml.safe_load(file)

        # Create a mapping from purpose ID to expert configuration
        self.purpose_to_config = self.configurations.get("experts", {})

    def parse_input(self, request: Dict) -> Dict:
        """
        Parses and validates the user query, ensuring required keys exist.
        
        Args:
            request (Dict): The incoming request.
        
        Returns:
            Dict: The parsed request with defaults set.
        """
        required_keys = ["intent", "purpose", "content"]
        for key in required_keys:
            if key not in request:
                raise KeyError(f"Missing required field: {key}")
        # Set default metadata if not provided
        if "metadata" not in request:
            request["metadata"] = {}
        return request

    def select_expert_profile(self, metadata: Dict, purpose: str) -> Dict:
        """
        Based on the metadata and purpose, retrieves the expert configuration.
        
        Args:
            metadata (Dict): Additional metadata from the request.
            purpose (str): The purpose ID.
        
        Returns:
            Dict: Configuration for the selected expert.
        
        Raises:
            ValueError: If no configuration is found for the given purpose.
        """
        config = self.purpose_to_config.get(purpose)
        if not config:
            raise ValueError(f"No configuration available for purpose {purpose}.")
        return config

    def handle_request(self, request: Dict) -> Dict:
        """
        Processes the incoming request by parsing input, selecting appropriate configuration,
        retrieving context, fusing context with the query, and then dispatching to the expert bot for generation.
        
        Expected request keys:
           - 'intent': Specifies if the request is "pre", "pro", or "post".
           - 'purpose': The purpose ID (e.g., "c1") to select the expert.
           - 'content': The user content or query.
           - 'metadata': Optional additional metadata.
        
        Returns:
            Dict: Generated response(s) from the expert bot.
        """
        try:
            # 1. Parse the unified query input
            parsed_input = self.parse_input(request)

            # 2. Select configuration based on metadata and purpose
            purpose = parsed_input["purpose"]
            expert_config = self.select_expert_profile(parsed_input.get("metadata", {}), purpose)

            # 3. Use retrieval layer (KnowledgeBase) with provided retrieval_config.
            kb = KnowledgeBaseComponent(vector_db="chroma")
            retrieved_context = kb.retrieve(purpose, expert_config.get("retrieval_config"))

            # 4. Use fusion layer to merge the query with the retrieved context.
            fused_prompt = FusionModule.fuse_context(
                parsed_input["content"],
                retrieved_context,
                expert_config.get("fusion_config")
            )

            # 5. Select Expert Bot based on configuration: use the 'bot' field from expert_config.
            bot_key = expert_config.get("bot")
            bot = self.expert_bots.get(bot_key)
            if not bot:
                error_message = f"No expert bot instance for configuration: {bot_key}"
                self.logger.log_error(error_message)
                return {"error": error_message}

            # 6. Dispatch the fused prompt & generation config to the expert bot.
            response = bot.process({
                **parsed_input,
                "formatted_prompt": fused_prompt,
                "llm_config": expert_config.get("llm_generation_params", {})
            })

            # 7. Feedback: log the interaction for continuous improvement.
            FeedbackModule.log_feedback(request, response)

            return response

        except KeyError as e:
            self.logger.log_error(f"Missing required field: {e}")
            return {"error": "Invalid request structure"}
        except Exception as e:
            self.logger.log_error(f"Error handling request: {e}")
            return {"error": str(e)}
            
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