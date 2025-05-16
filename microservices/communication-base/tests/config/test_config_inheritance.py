"""
Tests for the ConfigInheritance class.

Tests the core functionality of config inheritance, including merging configs
and accessing values using dot notation.
"""

import unittest
from src.config.config_inheritance import ConfigInheritance

class TestConfigInheritance(unittest.TestCase):
    """Test cases for the ConfigInheritance class."""
    
    def setUp(self):
        """Set up for each test."""
        self.inheritance = ConfigInheritance()
        
        # Sample configs for testing
        self.base_config = {
            "models": {
                "llm": {
                    "model_name": "gpt-3.5-turbo",
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            },
            "rag": {
                "enabled": True,
                "vector_store": {
                    "similarity": "cosine",
                    "top_k": 5
                }
            },
            "list_value": [1, 2, 3],
            "simple_value": "base"
        }
        
        self.specific_config = {
            "models": {
                "llm": {
                    "model_name": "gpt-4",
                    "temperature": 0.8
                }
            },
            "rag": {
                "vector_store": {
                    "top_k": 10,
                    "collections": ["products", "campaigns"]
                }
            },
            "list_value": [4, 5, 6],
            "new_value": "specific only"
        }
    
    def test_merge_configs_basic(self):
        """Test basic merging of configurations."""
        merged = self.inheritance.merge_configs(self.base_config, self.specific_config)
        
        # Check that specific values override base values
        self.assertEqual(merged["models"]["llm"]["model_name"], "gpt-4")
        self.assertEqual(merged["models"]["llm"]["temperature"], 0.8)
        
        # Check that non-overridden values are preserved
        self.assertEqual(merged["models"]["llm"]["max_tokens"], 1000)
        
        # Check that nested dictionaries are merged
        self.assertEqual(merged["rag"]["vector_store"]["top_k"], 10)
        self.assertEqual(merged["rag"]["vector_store"]["similarity"], "cosine")
        self.assertEqual(merged["rag"]["vector_store"]["collections"], ["products", "campaigns"])
        
        # Check that new values are added
        self.assertEqual(merged["new_value"], "specific only")
        
        # Check that lists are replaced completely, not merged
        self.assertEqual(merged["list_value"], [4, 5, 6])
        
        # Check that base values without overrides remain
        self.assertEqual(merged["simple_value"], "base")
        self.assertEqual(merged["rag"]["enabled"], True)
    
    def test_merge_configs_empty(self):
        """Test merging with empty configs."""
        # Empty base config
        merged = self.inheritance.merge_configs({}, self.specific_config)
        self.assertEqual(merged, self.specific_config)
        
        # Empty specific config
        merged = self.inheritance.merge_configs(self.base_config, {})
        self.assertEqual(merged, self.base_config)
        
        # Both empty
        merged = self.inheritance.merge_configs({}, {})
        self.assertEqual(merged, {})
    
    def test_merge_configs_invalid_input(self):
        """Test merging with invalid input types."""
        # None values
        merged = self.inheritance.merge_configs(None, self.specific_config)
        self.assertEqual(merged, self.specific_config)
        
        merged = self.inheritance.merge_configs(self.base_config, None)
        self.assertEqual(merged, self.base_config)
        
        # Non-dict values
        merged = self.inheritance.merge_configs("not a dict", self.specific_config)
        self.assertEqual(merged, self.specific_config)
        
        merged = self.inheritance.merge_configs(self.base_config, "not a dict")
        self.assertEqual(merged, self.base_config)
    
    def test_get_value(self):
        """Test getting values using dot notation."""
        config = {
            "models": {
                "llm": {
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            },
            "simple_value": "test"
        }
        
        # Simple path
        self.assertEqual(
            self.inheritance.get_value(config, "simple_value"),
            "test"
        )
        
        # Nested path
        self.assertEqual(
            self.inheritance.get_value(config, "models.llm.temperature"),
            0.7
        )
        
        # Path not found
        self.assertIsNone(
            self.inheritance.get_value(config, "nonexistent.path")
        )
        
        # Default value
        self.assertEqual(
            self.inheritance.get_value(config, "nonexistent.path", default="default"),
            "default"
        )
        
        # Invalid path
        self.assertIsNone(
            self.inheritance.get_value(config, "models.nonexistent.key")
        )
        
        # Empty path
        self.assertIsNone(
            self.inheritance.get_value(config, "")
        )
    
    def test_set_value(self):
        """Test setting values using dot notation."""
        config = {
            "models": {
                "llm": {
                    "temperature": 0.7
                }
            }
        }
        
        # Update existing value
        config = self.inheritance.set_value(config, "models.llm.temperature", 0.8)
        self.assertEqual(config["models"]["llm"]["temperature"], 0.8)
        
        # Add new nested value
        config = self.inheritance.set_value(config, "models.llm.max_tokens", 1000)
        self.assertEqual(config["models"]["llm"]["max_tokens"], 1000)
        
        # Add completely new path
        config = self.inheritance.set_value(config, "new.path.value", "test")
        self.assertEqual(config["new"]["path"]["value"], "test")
        
        # Empty path should not change anything
        original = config.copy()
        config = self.inheritance.set_value(config, "", "ignored")
        self.assertEqual(config, original)

if __name__ == '__main__':
    unittest.main() 