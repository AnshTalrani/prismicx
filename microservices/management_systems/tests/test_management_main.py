"""
Unit tests for management_main.py
"""

import os
import unittest
from unittest.mock import patch
from src.management_main import main

class TestManagementMain(unittest.TestCase):
    """
    Test suite for the management_systems microservice main function.
    """

    @patch.dict(os.environ, {"MANAGEMENT_API_KEY": "dummy_api_key", "USER_ID": "test_user"})
    def test_main_success(self):
        try:
            main()
        except Exception as e:
            self.fail(f"main() raised an unexpected exception: {e}")

    @patch.dict(os.environ, {"MANAGEMENT_API_KEY": "dummy_api_key"}, clear=True)
    def test_main_missing_user(self):
        with self.assertRaises(EnvironmentError):
            main()

if __name__ == "__main__":
    unittest.main() 