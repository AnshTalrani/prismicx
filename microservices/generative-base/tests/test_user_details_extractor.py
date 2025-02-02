"""
Tests for user details extraction
"""

import unittest
from unittest.mock import patch, MagicMock
from src.user_details_extraction_module.handler import UserDetailsExtractor
from src.template import Template

class TestUserDetailsExtractor(unittest.TestCase):
    
    @patch('src.user_details_extraction_module.handler.APIClient')
    def test_extraction_success(self, mock_client):
        template = Template("test_purpose")
        template.context = {'user_id': '123'}
        
        mock_instance = mock_client.return_value
        mock_instance.fetch_user_insights.return_value = {'data': {'name': 'test'}}
        
        extractor = UserDetailsExtractor(template)
        extractor.extract_user_details()
        
        self.assertEqual(template.user_details.get('name'), 'test') 