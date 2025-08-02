"""
Content generation components for high-quality output
"""

import requests
from ..common.config import Config
from ..common.utils import Utils

class ContentGenerator:
    """Handles AI-powered content generation"""
    
    def __init__(self):
        self.config = Config()
        self.utils = Utils()
        self.api_endpoint = "https://api.contentgeneration.com/v1"

    @Utils.retry_operation
    def generate_content(self, prompt: str, params: dict) -> dict:
        """
        Generate content using AI service
        
        Args:
            prompt: uGeneration prompt text
            params: Generation parameters
            
        Returns:
            Dictionary with generated content and metadata
        """
        try:
            response = requests.post(
                f"{self.api_endpoint}/generate",
                headers={"Authorization": f"Bearer {self.config.gen_base_api_key}"},
                json={"prompt": prompt, "parameters": params},
                timeout=15
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.utils.log_error(f"Content generation failed: {e}")
            raise 