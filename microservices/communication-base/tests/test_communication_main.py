"""
Unit tests for the communication_main module.
"""

import os
import unittest
from unittest.mock import patch
from src.communication_main import main

class TestCommunicationMain(unittest.TestCase):
    """
    Test suite for communication_main.py
    """

    @patch.dict(os.environ, {"COMM_BASE_API_KEY": "dummy_api_key"})
    def test_main_success(self):
        """Test that main() runs successfully when the environment variable is set."""
        try:
            main()
        except Exception as e:
            self.fail(f"main() raised an unexpected exception: {e}")

    @patch.dict(os.environ, {}, clear=True)
    def test_main_missing_env_var(self):
        """
        Test that main() raises an EnvironmentError when the environment variable is missing.
        """
        with self.assertRaises(EnvironmentError):
            main()

if __name__ == "__main__":
    unittest.main() 