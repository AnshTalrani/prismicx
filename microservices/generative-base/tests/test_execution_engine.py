"""
Tests for the execution engine.
"""

import pytest
import json
import asyncio
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from microservices.generative_base.src.execution_engine import (
    ExecutionEngine, BatchPipeline, ProcessingStep, ExecutionError
)
from microservices.generative_base.src.template import ValidatedTemplate
from microservices.agent.src.error_handling.error_types import ErrorType

# Sample template for testing
VALID_TEMPLATE = ValidatedTemplate(
    id="test-template",
    name="Test Template",
    description="Template for testing",
    steps=[
        {
            "service": "test-service",
            "operation": "test-operation",
            "input_map": {"test_input": "test_value"},
            "output_map": {"test_output": "test_result"}
        }
    ]
)

# Sample items for testing
VALID_ITEMS = [
    {"test_value": "item1"},
    {"test_value": "item2"},
    {"test_value": "item3"}
]

@pytest.fixture
def execution_engine():
    """Create an execution engine for testing."""
    engine = ExecutionEngine(max_workers=2)
    engine.register_service("test-service", "http://test-service:8000")
    return engine

@pytest.fixture
def mock_response():
    """Create a mock response for testing."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json.return_value = {
        "test_output": "test_output_value"
    }
    return mock_resp

@pytest.mark.asyncio
async def test_execute_batch(execution_engine):
    """Test executing a batch of items."""
    with patch.object(BatchPipeline, "process_chunk") as mock_process_chunk:
        mock_process_chunk.side_effect = lambda items: asyncio.Future().set_result(
            [{"test_value": item["test_value"], "test_result": f"result-{item['test_value']}"} for item in items]
        )
        
        results = await execution_engine.execute_batch(VALID_TEMPLATE, VALID_ITEMS)
        
        assert len(results) == 3
        assert results[0]["test_value"] == "item1"
        assert results[0]["test_result"] == "result-item1"
        assert results[1]["test_value"] == "item2"
        assert results[1]["test_result"] == "result-item2"
        assert results[2]["test_value"] == "item3"
        assert results[2]["test_result"] == "result-item3"

@pytest.mark.asyncio
async def test_process_item(execution_engine):
    """Test processing a single item."""
    with patch.object(BatchPipeline, "_execute_step") as mock_execute_step:
        mock_execute_step.side_effect = lambda step, context: asyncio.Future().set_result(
            {"test_result": f"result-{context['test_value']}"}
        )
        
        pipeline = BatchPipeline(VALID_TEMPLATE, execution_engine._service_registry)
        result = await pipeline.process_item({"test_value": "item1"})
        
        assert result["test_value"] == "item1"
        assert result["test_result"] == "result-item1"

@pytest.mark.asyncio
async def test_execute_step(execution_engine, mock_response):
    """Test executing a step."""
    with patch("aiohttp.ClientSession.post") as mock_post:
        # Setup the context manager returns
        mock_post.return_value.__aenter__.return_value = mock_response
        
        pipeline = BatchPipeline(VALID_TEMPLATE, execution_engine._service_registry)
        step = ProcessingStep(
            service="test-service",
            operation="test-operation",
            input_map={"test_input": "test_value"},
            output_map={"test_output": "test_result"}
        )
        
        result = await pipeline._execute_step(step, {"test_value": "item1"})
        
        assert result == {"test_result": "test_output_value"}
        mock_post.assert_called_once()

@pytest.mark.asyncio
async def test_execute_step_service_not_found(execution_engine):
    """Test executing a step with a service that doesn't exist."""
    pipeline = BatchPipeline(VALID_TEMPLATE, execution_engine._service_registry)
    step = ProcessingStep(
        service="nonexistent-service",
        operation="test-operation",
        input_map={"test_input": "test_value"},
        output_map={"test_output": "test_result"}
    )
    
    with pytest.raises(ExecutionError) as excinfo:
        await pipeline._execute_step(step, {"test_value": "item1"})
    
    assert excinfo.value.type == ErrorType.SERVICE_NOT_FOUND

@pytest.mark.asyncio
async def test_execute_step_timeout(execution_engine):
    """Test executing a step that times out."""
    with patch("aiohttp.ClientSession.post") as mock_post:
        # Setup to raise a timeout error
        mock_post.side_effect = asyncio.TimeoutError()
        
        pipeline = BatchPipeline(VALID_TEMPLATE, execution_engine._service_registry)
        step = ProcessingStep(
            service="test-service",
            operation="test-operation",
            input_map={"test_input": "test_value"},
            output_map={"test_output": "test_result"},
            retry_count=1
        )
        
        with pytest.raises(ExecutionError) as excinfo:
            await pipeline._execute_step(step, {"test_value": "item1"})
        
        assert excinfo.value.type == ErrorType.TIMEOUT

@pytest.mark.asyncio
async def test_handle_error(execution_engine):
    """Test handling errors."""
    pipeline = BatchPipeline(VALID_TEMPLATE, execution_engine._service_registry)
    
    error = ExecutionError(ErrorType.PROCESSING_ERROR, {"error": "test-error"})
    result = pipeline._handle_error({"test_value": "item1"}, error)
    
    assert result["test_value"] == "item1"
    assert result["status"] == "error"
    assert "error" in result

@pytest.mark.asyncio
async def test_create_chunks(execution_engine):
    """Test creating chunks."""
    items = [{"id": i} for i in range(10)]
    
    # Test with default chunk size
    chunks = execution_engine._create_chunks(items, 3)
    assert len(chunks) == 4
    assert len(chunks[0]) == 3
    assert len(chunks[1]) == 3
    assert len(chunks[2]) == 3
    assert len(chunks[3]) == 1
    
    # Test with chunk size larger than the number of items
    chunks = execution_engine._create_chunks(items, 20)
    assert len(chunks) == 1
    assert len(chunks[0]) == 10 