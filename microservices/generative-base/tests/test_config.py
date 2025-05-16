"""
Unit tests for configuration management
"""

import os
import unittest
from src.common.config import Config
from unittest.mock import patch

class TestConfig(unittest.TestCase):
    """Test configuration handling"""
    
    def test_missing_api_key(self):
        with self.assertRaises(EnvironmentError):
            Config()
    
    @patch.dict(os.environ, {"GEN_BASE_API_KEY": "test"})
    def test_valid_config(self):
        config = Config()
        self.assertEqual(config.gen_base_api_key, "test") 