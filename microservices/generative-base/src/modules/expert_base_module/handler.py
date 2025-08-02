"""
Expert review and validation components
"""

import requests
from ..common.config import Config
from ..common.utils import Utils

class ExpertBaseHandler:
    """Handles expert review process"""
    
    def __init__(self, template):
        self.template = template
        self.config = Config()
        self.utils = Utils()
        self.api_endpoint = f"{self.config.expert_bots_url}/generate-content"

    def review_content(self):
        """Updated to use template-provided intent tag"""
        try:
            intent_tag = self.template.selected_info.get("intent_tag", "post")
            
            request_data = {
                "intent_tag": intent_tag,
                "content": self.template.generated_output.get("content", ""),
                "template_metadata": self.template.context.get("metadata", {})
            }
            
            response = requests.post(
                self.api_endpoint,
                json=request_data,
                headers={"Authorization": f"Bearer {self.config.gen_base_api_key}"},
                timeout=20
            )
            response.raise_for_status()
            
            self.template.generated_output.update({
                "expert_review": response.json().get("feedback"),
                "approval_status": response.json().get("approved", False)
            })
            
        except requests.RequestException as e:
            self.utils.log_error(f"Expert review failed: {e}")
            self.template.generated_output["approval_status"] = False 