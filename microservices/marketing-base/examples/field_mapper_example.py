#!/usr/bin/env python3
"""
Field Mapper Usage Example

This script demonstrates how to use the FieldMapper utility 
with various field mapping configurations for transforming
campaign data between different client schemas.
"""

import json
import logging
from typing import Dict, Any

from src.utils.field_mapper import FieldMapper
from src.config.field_mappings import get_mapping_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_json(data: Dict[str, Any], title: str = None):
    """
    Print dict as formatted JSON with an optional title.
    
    Args:
        data: Dictionary to print as JSON
        title: Optional title to print before the JSON
    """
    if title:
        print(f"\n{title}")
        print("=" * len(title))
    print(json.dumps(data, indent=2))
    print()

def register_custom_transformers(field_mapper: FieldMapper):
    """
    Register custom transformers for demonstration purposes.
    
    Args:
        field_mapper: FieldMapper instance to register transformers with
    """
    # Register a transformer to add a prefix to a string
    field_mapper.register_transformer(
        'add_prefix', 
        lambda x, prefix: f"{prefix}_{x}" if x else None
    )
    
    # Register a transformer to calculate a percentage
    field_mapper.register_transformer(
        'calculate_percentage',
        lambda x, total: (float(x) / float(total)) * 100 if x and total else 0
    )
    
    # Register a transformer to join a list into a string
    field_mapper.register_transformer(
        'join_list',
        lambda x, separator=',': separator.join(x) if isinstance(x, list) else x
    )
    
    logger.info("Custom transformers registered")

def main():
    """Main entry point for the example."""
    # Sample campaign data
    sample_campaign = {
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
    
    # Initialize the FieldMapper
    field_mapper = FieldMapper()
    
    # Register some custom transformers
    register_custom_transformers(field_mapper)
    
    # Print the original campaign data
    print_json(sample_campaign, "Original Campaign Data")
    
    # Example 1: Map using default campaign mapping
    logger.info("Example 1: Using default campaign mapping")
    default_mapping = get_mapping_config("campaign")
    default_result = field_mapper.map_fields(sample_campaign, default_mapping)
    print_json(default_result, "Example 1: Default Campaign Mapping")
    
    # Example 2: Map using client A specific mapping
    logger.info("Example 2: Using client A specific mapping")
    client_a_mapping = get_mapping_config("campaign", "client_a")
    client_a_result = field_mapper.map_fields(sample_campaign, client_a_mapping)
    print_json(client_a_result, "Example 2: Client A Campaign Mapping")
    
    # Example 3: Map using client B specific mapping
    logger.info("Example 3: Using client B specific mapping")
    client_b_mapping = get_mapping_config("campaign", "client_b")
    client_b_result = field_mapper.map_fields(sample_campaign, client_b_mapping)
    print_json(client_b_result, "Example 3: Client B Campaign Mapping")
    
    # Example 4: Custom mapping with new transformers
    logger.info("Example 4: Using custom mapping with transformers")
    custom_mapping = {
        "field_mappings": {
            "campaign_id": {
                "field": "name",
                "transform": "add_prefix",
                "transform_args": {"prefix": "campaign"}
            },
            "budget_percentage": {
                "field": "budget.amount",
                "transform": "calculate_percentage",
                "transform_args": {"total": 10000}
            },
            "channels_list": {
                "field": "distribution_channels",
                "transform": "join_list",
                "transform_args": {"separator": " | "}
            },
            "audience_segments_list": {
                "field": "audience.segments",
                "transform": "join_list"
            }
        },
        "copy_fields": ["tags", "priority", "status"],
        "exclude_fields": ["_id", "template_id", "metadata"],
        "copy_remaining": False,
        "include_nulls": False
    }
    custom_result = field_mapper.map_fields(sample_campaign, custom_mapping)
    print_json(custom_result, "Example 4: Custom Mapping with Transformers")
    
    # Example 5: Combining mappings (default plus custom)
    logger.info("Example 5: Combining default and custom mappings")
    # Start with a copy of the default mapping
    combined_mapping = json.loads(json.dumps(default_mapping))
    
    # Add custom field mappings that override or extend the default mapping
    combined_mapping["field_mappings"].update({
        "campaign_id": {
            "field": "name",
            "transform": "add_prefix",
            "transform_args": {"prefix": "campaign"}
        },
        "channels_list": {
            "field": "distribution_channels",
            "transform": "join_list",
            "transform_args": {"separator": ", "}
        }
    })
    
    # Use the combined mapping
    combined_result = field_mapper.map_fields(sample_campaign, combined_mapping)
    print_json(combined_result, "Example 5: Combined Mapping")
    
    logger.info("Field mapper examples completed")

if __name__ == "__main__":
    main() 