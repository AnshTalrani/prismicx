"""
API client for user details extraction
"""

import requests
from ..common.utils import Utils
from ..common.config import Config

class APIClient:
    """Handles API communication for user insights"""
    
    def __init__(self):
        self.config = Config()
        self.base_url = self.config.user_details_url
        self.utils = Utils()

    @Utils.retry_operation
    def fetch_user_insights(self, user_id: str, purpose_id: str) -> dict:
        """Direct template fetching without phase mapping"""
        try:
            response = requests.post(
                f"{self.base_url}/processTemplate",
                json={
                    "templateID": purpose_id,
                    "userID": user_id
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.utils.log_error(f"User Insights API failed: {e}")
            return {"error": str(e)} 