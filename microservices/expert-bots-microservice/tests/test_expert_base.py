"""
Unit tests for expert_base.py
"""

import unittest
from unittest.mock import MagicMock
from src.expert_base.expert_base import ExpertBase
from src.utils.logger import Logger

class TestExpertBase(unittest.TestCase):
    def setUp(self):
        self.logger = Logger()
        self.mock_bot = MagicMock()
        self.mock_bot.process.return_value = {"content": "Test Content"}
        self.expert_bots = {"test_intent": self.mock_bot}
        self.expert_base = ExpertBase(expert_bots=self.expert_bots, logger=self.logger)

    def test_handle_request_success(self):
        request = {"intent_tag": "test_intent", "theme": "test_theme", "details": "test_details"}
        response = self.expert_base.handle_request(request)
        self.mock_bot.process.assert_called_once_with(request)
        self.assertEqual(response, {"content": "Test Content"})

    def test_handle_request_no_bot(self):
        request = {"intent_tag": "unknown_intent", "theme": "test_theme", "details": "test_details"}
        response = self.expert_base.handle_request(request)
        self.assertEqual(response, {"error": "No bot for this intent_tag"})

    def test_handle_request_exception(self):
        self.mock_bot.process.side_effect = Exception("Processing Error")
        request = {"intent_tag": "test_intent", "theme": "test_theme", "details": "test_details"}
        response = self.expert_base.handle_request(request)
        self.assertEqual(response, {"error": "Failed to process the request"})

if __name__ == "__main__":
    unittest.main() 