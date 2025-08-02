"""
Field Mapping Configurations

This module contains sample field mapping configurations for different entities
across client schemas. These mappings define how fields should be transformed
when transferring data between different database schemas.
"""

# Campaign field mapping configuration
# This defines how campaign data should be mapped between different client schemas
CAMPAIGN_FIELD_MAPPINGS = {
    # Default mapping used when no client-specific mapping is provided
    "default": {
        "field_mappings": {
            # Maps template campaign fields to client-specific fields
            "campaign_name": "name",
            "description": "description",
            "client_id": "client_id",
            "status": {
                "field": "status",
                "default": "draft",
                "transform": "to_string"
            },
            "budget": {
                "field": "budget.amount",
                "default": 0.0,
                "transform": "to_float"
            },
            "currency": {
                "field": "budget.currency",
                "default": "USD"
            },
            "start_date": "start_date",
            "end_date": "end_date",
            "target_audience": "audience.segments",
            "channels": "distribution_channels",
            "created_by": "metadata.created_by",
            "updated_by": "metadata.updated_by"
        },
        # Fields to copy without transformation
        "copy_fields": [
            "tags",
            "priority",
            "active"
        ],
        # Fields to exclude from copying
        "exclude_fields": [
            "_id",  # MongoDB ID will be regenerated
            "created_at",  # Timestamps will be regenerated
            "updated_at",
            "template_id",
            "is_template"
        ],
        # Whether to copy fields not explicitly mapped
        "copy_remaining": False,
        # Whether to include null values in the output
        "include_nulls": False
    },
    
    # Client-specific mappings override the default mapping
    "client_a": {
        "field_mappings": {
            "campaign_title": "name",  # Client A uses campaign_title instead of campaign_name
            "campaign_description": "description",
            "budget_allocation": {
                "field": "budget.amount",
                "transform": "to_float"
            },
            "currency_code": {
                "field": "budget.currency"
            },
            "audience_segments": "audience.segments",
            "marketing_channels": "distribution_channels",
            "start_timestamp": {
                "field": "start_date",
                "transform": "to_string"  # Convert date to string format for this client
            },
            "end_timestamp": {
                "field": "end_date",
                "transform": "to_string"
            }
        },
        "copy_fields": [
            "priority",
            "active"
        ],
        "exclude_fields": [
            "_id",
            "created_at",
            "updated_at",
            "template_id",
            "is_template"
        ],
        "copy_remaining": False,
        "include_nulls": False
    },
    
    "client_b": {
        "field_mappings": {
            "name": "name",
            "desc": "description",  # Client B uses shortened field names
            "budget_amt": {
                "field": "budget.amount",
                "transform": "to_float"
            },
            "budget_cur": {
                "field": "budget.currency"
            },
            "segments": "audience.segments",
            "channels": "distribution_channels",
            "start_dt": "start_date",
            "end_dt": "end_date",
            "status_code": {
                "field": "status",
                "transform": "to_int",  # Client B uses numeric status codes
                "default": 0  # Default to 0 (draft)
            }
        },
        "copy_fields": [
            "tags",
            "priority"
        ],
        "exclude_fields": [
            "_id",
            "created_at",
            "updated_at",
            "template_id",
            "is_template"
        ],
        "copy_remaining": False,
        "include_nulls": False
    }
}

# Add more entity mappings as needed
CUSTOMER_FIELD_MAPPINGS = {
    "default": {
        # Default mapping for customer data
        "field_mappings": {
            "customer_name": "name",
            "email_address": "contact.email",
            "phone_number": "contact.phone",
            "customer_segment": "segment"
        },
        "copy_fields": [
            "tags",
            "preferences"
        ],
        "exclude_fields": [
            "_id",
            "created_at",
            "updated_at"
        ],
        "copy_remaining": False,
        "include_nulls": False
    }
}

# Function to retrieve field mappings for a specific entity and client
def get_mapping_config(entity_type: str, client_id: str = None):
    """
    Get field mapping configuration for a specific entity type and client.
    
    Args:
        entity_type: Type of entity (e.g., 'campaign', 'customer')
        client_id: Client identifier for client-specific mappings
        
    Returns:
        Mapping configuration dictionary
    """
    mappings = {
        "campaign": CAMPAIGN_FIELD_MAPPINGS,
        "customer": CUSTOMER_FIELD_MAPPINGS
    }
    
    if entity_type not in mappings:
        raise ValueError(f"Unknown entity type: {entity_type}")
    
    entity_mappings = mappings[entity_type]
    
    # Return client-specific mapping if available, otherwise use default
    if client_id and client_id in entity_mappings:
        return entity_mappings[client_id]
    return entity_mappings["default"] 