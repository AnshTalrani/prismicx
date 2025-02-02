"""
End-to-end integration test for the processing pipeline
"""

import unittest
from src.generative_main import GenerativeMicroservice
from src.template import Template

class TestIntegration(unittest.TestCase):
    def test_full_processing_flow(self):
        """Test complete request handling flow"""
        service = GenerativeMicroservice()
        test_request = {
            "purpose_id": "social_media_post",
            "context": {
                "user_id": "123",
                "sources": ["news", "blogs"],
                "social_params": {"platform": "twitter"}
            }
        }
        
        template = service.initialize_template(test_request)
        service.execute_modules(template)
        
        self.assertIn("content", template.generated_output)
        self.assertIn("expert_review", template.generated_output) 