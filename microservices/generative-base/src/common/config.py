"""
Configuration management for the generative-base microservice.
Handles environment variables and application settings securely.
"""

import os

class Config:
    """
    Manages application configuration and environment variables.
    
    Implements singleton pattern to ensure consistent configuration access.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.load_config()
        return cls._instance
    
    def load_config(self):
        """Enhanced security validation"""
        self.gen_base_api_key = os.getenv("GEN_BASE_API_KEY")
        self.expert_api_endpoint = os.getenv("EXPERT_API_ENDPOINT")
        
        if not self.gen_base_api_key:
            raise EnvironmentError("GEN_BASE_API_KEY environment variable is required")
        
        # Validate API endpoint format
        if self.expert_api_endpoint and not self.expert_api_endpoint.startswith("https"):
            raise ValueError("Expert API endpoint must use HTTPS")
        
        self.expert_bots_url = os.getenv("EXPERT_BOTS_URL", "http://expert-bots-service:8000")
        self.user_details_url = os.getenv("USER_DETAILS_URL", "http://user-details-service:5000")
        
        # Validate URLs
        if not all([self.expert_bots_url.startswith("http"), 
                   self.user_details_url.startswith("http")]):
            raise ValueError("Service URLs must specify protocol") 