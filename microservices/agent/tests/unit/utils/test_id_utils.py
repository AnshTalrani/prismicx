"""Unit tests for the ID utilities module."""
import pytest
import re
from src.utils.id_utils import (
    generate_request_id,
    generate_batch_id,
    is_valid_request_id,
    is_valid_batch_id,
    extract_timestamp_from_id,
    extract_source_from_id
)

class TestIdUtils:
    """Tests for ID utilities functions."""
    
    def test_generate_request_id(self):
        """Test the generate_request_id function."""
        # Test with default parameters
        request_id = generate_request_id()
        assert request_id.startswith("req_")
        assert is_valid_request_id(request_id)
        
        # Test with custom source
        source = "test_source"
        request_id = generate_request_id(source=source)
        assert request_id.startswith("req_")
        assert extract_source_from_id(request_id) == source
        
    def test_generate_batch_id(self):
        """Test the generate_batch_id function."""
        # Test with default parameters
        batch_id = generate_batch_id()
        assert batch_id.startswith("bat_")
        assert is_valid_batch_id(batch_id)
        
        # Test with custom source
        source = "test_source"
        batch_id = generate_batch_id(source=source)
        assert batch_id.startswith("bat_")
        assert extract_source_from_id(batch_id) == source
    
    def test_id_validation(self):
        """Test the ID validation functions."""
        # Valid IDs
        valid_request_id = generate_request_id()
        valid_batch_id = generate_batch_id()
        
        assert is_valid_request_id(valid_request_id)
        assert is_valid_batch_id(valid_batch_id)
        
        # Invalid IDs
        assert not is_valid_request_id("invalid_id")
        assert not is_valid_batch_id("invalid_id")
        assert not is_valid_request_id(valid_batch_id)  # Batch ID is not a valid request ID
        assert not is_valid_batch_id(valid_request_id)  # Request ID is not a valid batch ID
    
    def test_extract_timestamp(self):
        """Test the timestamp extraction function."""
        request_id = generate_request_id()
        timestamp = extract_timestamp_from_id(request_id)
        
        # Timestamp should be a string of 14 digits (YYYYMMDDHHmmss)
        assert isinstance(timestamp, str)
        assert len(timestamp) == 14
        assert re.match(r'^\d{14}$', timestamp)
    
    def test_extract_source(self):
        """Test the source extraction function."""
        source = "test_source"
        request_id = generate_request_id(source=source)
        extracted_source = extract_source_from_id(request_id)
        
        assert extracted_source == source
        
    def test_id_uniqueness(self):
        """Test that generated IDs are unique."""
        # Generate multiple IDs and check for uniqueness
        id_set = {generate_request_id() for _ in range(100)}
        assert len(id_set) == 100
        
        id_set = {generate_batch_id() for _ in range(100)}
        assert len(id_set) == 100 