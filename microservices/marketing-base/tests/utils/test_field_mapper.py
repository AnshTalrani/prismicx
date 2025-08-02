"""
Unit tests for the field_mapper utility.

These tests validate the functionality of the FieldMapper class, 
which handles field mapping between different schemas.
"""

import unittest
from unittest.mock import Mock, patch
import logging

from src.utils.field_mapper import FieldMapper
from src.config.field_mappings import get_mapping_config

class TestFieldMapper(unittest.TestCase):
    """Test suite for the FieldMapper class."""

    def setUp(self):
        """Set up test fixtures."""
        self.field_mapper = FieldMapper()
        
        # Register some custom transformers
        self.field_mapper.register_transformer('to_uppercase', lambda x: str(x).upper())
        self.field_mapper.register_transformer('add_prefix', lambda x, prefix: f"{prefix}{x}")
        
        # Sample source data for testing
        self.sample_campaign = {
            "name": "Summer Sale 2023",
            "description": "A summer promotion for all products",
            "status": "active",
            "budget": {
                "amount": 5000,
                "currency": "USD"
            },
            "start_date": "2023-06-01",
            "end_date": "2023-08-31",
            "audience": {
                "segments": ["new_customers", "existing_customers"],
                "targeting": {
                    "age_range": [18, 65],
                    "locations": ["US", "CA"]
                }
            },
            "distribution_channels": ["email", "social_media", "website"],
            "metadata": {
                "created_by": "john.doe",
                "updated_by": "jane.smith",
                "created_at": "2023-05-15T10:00:00Z",
                "updated_at": "2023-05-16T14:30:00Z"
            },
            "tags": ["summer", "promotion", "sale"],
            "priority": 1,
            "active": True,
            "_id": "60c72b2f8f11b543a9be1234",
            "template_id": "template123",
            "is_template": False
        }
        
        # Simple mapping config for testing
        self.simple_mapping = {
            "field_mappings": {
                "campaign_name": "name",
                "campaign_description": "description",
                "campaign_status": {
                    "field": "status",
                    "transform": "to_uppercase"
                },
                "budget_amount": "budget.amount",
                "budget_currency": "budget.currency",
                "audience_segments": "audience.segments",
                "creator": {
                    "field": "metadata.created_by",
                    "transform": "add_prefix",
                    "transform_args": {"prefix": "user:"}
                }
            },
            "copy_fields": ["tags", "priority"],
            "exclude_fields": ["_id", "template_id", "is_template"],
            "copy_remaining": False,
            "include_nulls": False
        }
        
    def test_map_fields_with_simple_config(self):
        """Test mapping fields with a simple configuration."""
        result = self.field_mapper.map_fields(self.sample_campaign, self.simple_mapping)
        
        # Test direct mappings
        self.assertEqual(result["campaign_name"], "Summer Sale 2023")
        self.assertEqual(result["campaign_description"], "A summer promotion for all products")
        
        # Test transformed values
        self.assertEqual(result["campaign_status"], "ACTIVE")
        self.assertEqual(result["creator"], "user:john.doe")
        
        # Test nested field access
        self.assertEqual(result["budget_amount"], 5000)
        self.assertEqual(result["budget_currency"], "USD")
        
        # Test array field mapping
        self.assertEqual(result["audience_segments"], ["new_customers", "existing_customers"])
        
        # Test copied fields
        self.assertEqual(result["tags"], ["summer", "promotion", "sale"])
        self.assertEqual(result["priority"], 1)
        
        # Test excluded fields
        self.assertNotIn("_id", result)
        self.assertNotIn("template_id", result)
        self.assertNotIn("is_template", result)
        
        # Test fields not mentioned in mapping should not be included when copy_remaining is False
        self.assertNotIn("distribution_channels", result)
        
    def test_map_fields_with_default_value(self):
        """Test mapping with default values for missing fields."""
        mapping_with_defaults = {
            "field_mappings": {
                "campaign_name": "name",
                "budget_type": {
                    "field": "budget.type",
                    "default": "fixed"
                },
                "campaign_goal": {
                    "field": "goal",
                    "default": "awareness"
                }
            },
            "copy_remaining": False,
            "include_nulls": True
        }
        
        result = self.field_mapper.map_fields(self.sample_campaign, mapping_with_defaults)
        
        # Test default values for missing fields
        self.assertEqual(result["budget_type"], "fixed")
        self.assertEqual(result["campaign_goal"], "awareness")
        
    def test_copy_remaining_fields(self):
        """Test the copy_remaining option."""
        mapping_with_copy_remaining = {
            "field_mappings": {
                "campaign_name": "name"
            },
            "exclude_fields": ["_id", "metadata"],
            "copy_remaining": True
        }
        
        result = self.field_mapper.map_fields(self.sample_campaign, mapping_with_copy_remaining)
        
        # Explicitly mapped fields
        self.assertEqual(result["campaign_name"], "Summer Sale 2023")
        
        # Fields copied due to copy_remaining: True
        self.assertEqual(result["description"], "A summer promotion for all products")
        self.assertEqual(result["status"], "active")
        self.assertEqual(result["distribution_channels"], ["email", "social_media", "website"])
        
        # Excluded fields should not be present
        self.assertNotIn("_id", result)
        self.assertNotIn("metadata", result)
        
    def test_include_nulls_option(self):
        """Test the include_nulls option."""
        # Map a non-existent field
        mapping = {
            "field_mappings": {
                "campaign_name": "name",
                "non_existent_field": "does_not_exist"
            },
            "copy_remaining": False
        }
        
        # With include_nulls=False (default)
        mapping["include_nulls"] = False
        result_without_nulls = self.field_mapper.map_fields(self.sample_campaign, mapping)
        self.assertNotIn("non_existent_field", result_without_nulls)
        
        # With include_nulls=True
        mapping["include_nulls"] = True
        result_with_nulls = self.field_mapper.map_fields(self.sample_campaign, mapping)
        self.assertIn("non_existent_field", result_with_nulls)
        self.assertIsNone(result_with_nulls["non_existent_field"])
        
    def test_register_and_use_custom_transformer(self):
        """Test registering and using a custom transformer."""
        # Register a custom transformer
        self.field_mapper.register_transformer('multiply', lambda x, factor: x * factor)
        
        # Mapping with the custom transformer
        mapping = {
            "field_mappings": {
                "doubled_budget": {
                    "field": "budget.amount",
                    "transform": "multiply",
                    "transform_args": {"factor": 2}
                }
            }
        }
        
        result = self.field_mapper.map_fields(self.sample_campaign, mapping)
        self.assertEqual(result["doubled_budget"], 10000)  # 5000 * 2
        
    def test_with_default_transformers(self):
        """Test using the default transformers."""
        mapping = {
            "field_mappings": {
                "budget_as_string": {
                    "field": "budget.amount",
                    "transform": "to_string"
                },
                "status_as_int": {
                    "field": "status",
                    "transform": "to_int",
                    "default": 0
                }
            }
        }
        
        result = self.field_mapper.map_fields(self.sample_campaign, mapping)
        
        # String conversion should work on the budget amount
        self.assertEqual(result["budget_as_string"], "5000")
        
        # Since 'active' is not a number, it should use a default or return 0
        # In our case, the FieldMapper's to_int transformer should handle non-int inputs
        # The specific behavior depends on the implementation
        self.assertEqual(result["status_as_int"], 0)
        
    def test_integration_with_config_mappings(self):
        """Test integration with the mapping configurations from field_mappings.py."""
        # Get the default campaign mapping config
        default_mapping = get_mapping_config("campaign")
        
        # Map fields using the default config
        result = self.field_mapper.map_fields(self.sample_campaign, default_mapping)
        
        # Check some key fields
        self.assertEqual(result["campaign_name"], "Summer Sale 2023")
        self.assertEqual(result["description"], "A summer promotion for all products")
        self.assertEqual(result["target_audience"], ["new_customers", "existing_customers"])
        self.assertEqual(result["channels"], ["email", "social_media", "website"])
        self.assertEqual(result["created_by"], "john.doe")
        self.assertEqual(result["updated_by"], "jane.smith")
        
        # Now test with client A's mapping
        client_a_mapping = get_mapping_config("campaign", "client_a")
        result_a = self.field_mapper.map_fields(self.sample_campaign, client_a_mapping)
        
        # Check client A specific mappings
        self.assertEqual(result_a["campaign_title"], "Summer Sale 2023")
        self.assertEqual(result_a["campaign_description"], "A summer promotion for all products")
        self.assertEqual(result_a["audience_segments"], ["new_customers", "existing_customers"])
        self.assertEqual(result_a["marketing_channels"], ["email", "social_media", "website"])
        
        # Check that dates were converted to strings (if the transformer works)
        if self.field_mapper._transformers.get("to_string"):
            self.assertIsInstance(result_a["start_timestamp"], str)
            self.assertIsInstance(result_a["end_timestamp"], str)

if __name__ == '__main__':
    unittest.main() 