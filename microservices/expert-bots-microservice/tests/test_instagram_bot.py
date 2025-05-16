"""
Unit tests for instagram_bot.py
"""

import unittest
from unittest.mock import MagicMock, patch
from src.expert_bots.instagram_bot import InstagramBot
from src.utils.logger import Logger

class TestInstagramBot(unittest.TestCase):
    def setUp(self):
        self.logger = Logger()
        self.mock_knowledge_base = MagicMock()
        self.mock_llm = MagicMock()
        with patch('src.expert_bots.instagram_bot.PeftModel.from_pretrained') as mock_load:
            mock_load.return_value = self.mock_llm
            self.instagram_bot = InstagramBot(
                lora_adapter="path/to/instagram_lora",
                knowledge_base=self.mock_knowledge_base,
                logger=self.logger
            )

    def test_process_success(self):
        request = {"intent_tag": "instagram_post", "theme": "nature", "details": "Beautiful sunset"}
        self.mock_knowledge_base.retrieve.return_value = "Nature themes guidelines."
        self.mock_llm.generate.return_value = "Generated Instagram Post"

        response = self.instagram_bot.process(request)
        self.mock_knowledge_base.retrieve.assert_called_once_with(
            intent_tag="instagram_post",
            filters={"theme": "nature"}
        )
        self.mock_llm.generate.assert_called_once_with(
            "Generate Instagram post with: Beautiful sunset. Guidelines: Nature themes guidelines."
        )
        self.assertEqual(response, {"content": "Generated Instagram Post"})

    def test_process_exception(self):
        request = {"intent_tag": "instagram_post", "theme": "nature", "details": "Beautiful sunset"}
        self.mock_knowledge_base.retrieve.side_effect = Exception("KnowledgeBase Error")

        response = self.instagram_bot.process(request)
        self.assertEqual(response, {"error": "Failed to generate Instagram post"})

if __name__ == "__main__":
    unittest.main() 