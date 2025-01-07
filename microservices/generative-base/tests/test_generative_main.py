"""
Unit tests for the generative_base microservice main module.
"""

import os
import unittest
from unittest.mock import patch
from src.generative_main import main

class TestGenerativeMain(unittest.TestCase):
    """
    Test suite for the main function in generative_main.py
    """

    @patch.dict(os.environ, {"GEN_BASE_API_KEY": "dummy_api_key"})
    def test_main_function_success(self):
        """
        Test that main() runs successfully when environment variables are set.
        """
        try:
            main()
        except Exception as e:
            self.fail(f"main() raised an unexpected exception: {e}")

    @patch.dict(os.environ, {}, clear=True)
    def test_main_function_missing_env_var(self):
        """
        Test that main() raises an EnvironmentError if required env var is missing.
        """
        with self.assertRaises(EnvironmentError):
            main()

if __name__ == "__main__":
    unittest.main() 