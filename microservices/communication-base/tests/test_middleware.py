"""
Unit tests for the middleware module.
"""

import unittest
from src.middleware import process_request

class TestMiddleware(unittest.TestCase):
    def test_process_request_missing_tag(self):
        data = {"message": "Test message"}
        with self.assertRaises(ValueError):
            process_request(data)
    
    def test_process_request_support(self):
        data = {"message": "Test message", "bot_tag": "support"}
        response = process_request(data)
        self.assertIn("Response from support", response["response"])
    
    def test_process_request_unknown_tag(self):
        data = {"message": "Test message", "bot_tag": "unknown"}
        with self.assertRaises(ValueError):
            process_request(data)

if __name__ == "__main__":
    unittest.main() 