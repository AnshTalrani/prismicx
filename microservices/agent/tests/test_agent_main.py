"""
Unit tests for agent_main.py
"""

import os
import unittest
from unittest.mock import patch
from src.agent_main import main

class TestAgentMain(unittest.TestCase):
    """
    Test suite for the agent microservice main function.
    """

    @patch.dict(os.environ, {"AGENT_API_KEY": "dummy_api_key"})
    def test_main_success(self):
        try:
            main()
        except Exception as e:
            self.fail(f"main() raised an unexpected exception: {e}")

    @patch.dict(os.environ, {}, clear=True)
    def test_main_missing_env_var(self):
        with self.assertRaises(EnvironmentError):
            main()

if __name__ == "__main__":
    unittest.main() 