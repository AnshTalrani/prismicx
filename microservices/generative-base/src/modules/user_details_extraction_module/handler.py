"""
User details extraction handler
"""

from .client import APIClient
from ..common.utils import Utils

class UserDetailsExtractor:
    """Orchestrates user details extraction process"""
    
    def __init__(self, template):
        self.template = template
        self.api_client = APIClient()
        self.utils = Utils()

    @Utils.retry_operation
    def extract_user_details(self):
        """Execute user details extraction pipeline"""
        try:
            user_id = self.template.context.get('user_id')
            if not user_id:
                raise ValueError("Missing user_id in template context")
                
            insights = self.api_client.fetch_user_insights(
                user_id, self.template.purpose_id
            )
            self.template.user_details = insights.get('data', {})
            
        except Exception as e:
            self.utils.log_error(f"User details extraction failed: {e}")
            raise 