"""
Unit tests for the communication_main module.
"""

import os
import unittest
from src.communication_main import main

class TestCommunicationMain(unittest.TestCase):
    """
    Test suite for communication_main.py
    """

    def test_main_success(self):
        """Test that main() runs successfully when the environment variable is set."""
        os.environ["COMM_BASE_API_KEY"] = "dummy_api_key"
        try:
            main()
        except Exception as e:
            self.fail(f"main() raised an exception: {e}")

    def test_main_missing_env(self):
        """
        Test that main() raises an EnvironmentError when the environment variable is missing.
        """
        if "COMM_BASE_API_KEY" in os.environ:
            del os.environ["COMM_BASE_API_KEY"]
        with self.assertRaises(EnvironmentError):
            main()

if __name__ == "__main__":
    unittest.main() 