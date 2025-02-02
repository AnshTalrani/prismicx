from unittest.mock import patch
from generative_base.src.expert_base_module.handler import ExpertBaseHandler
from generative_base.src.template import Template

class TestExpertBaseHandler(unittest.TestCase):
    @patch('requests.post')
    def test_review_content_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"content": "Approved"}
        
        template = Template("social_media_post")
        template.generated_output = {"content": "Test content"}
        
        handler = ExpertBaseHandler(template)
        handler.review_content()
        
        self.assertTrue(template.generated_output["approval_status"]) 