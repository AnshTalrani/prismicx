"""
Unit tests for bot integration modules.
"""

import unittest
from src.bot_integration import support_bot, consultancy_bot, sales_bot

class TestBotIntegration(unittest.TestCase):
    def test_support_bot(self):
        prompt = "Issue with order delivery"
        response = support_bot.handle_request(prompt)
        self.assertIn("Response from support", response)
    
    def test_consultancy_bot(self):
        prompt = "Need legal advice on contract terms"
        response = consultancy_bot.handle_request(prompt)
        self.assertIn("Response from consultancy", response)
    
    def test_sales_bot(self):
        prompt = "How to start campaign?"
        response = sales_bot.handle_request(prompt)
        self.assertIn("Response from sales", response)

if __name__ == "__main__":
    unittest.main() 