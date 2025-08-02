"""
Tests for the Expert Orchestrator module.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.api.models import ExpertRequest, ExpertResponse
from src.modules.expert_orchestrator import ExpertOrchestrator
from src.common.exceptions import ExpertNotFoundException, IntentNotSupportedException, ProcessingException


@pytest.fixture
def mock_expert_registry():
    """Create a mock Expert Registry."""
    registry = Mock()
    
    # Configure has_expert method
    registry.has_expert = Mock(side_effect=lambda expert_id: expert_id == "instagram")
    
    # Configure supports_intent method
    def supports_intent_mock(expert_id, intent):
        if expert_id != "instagram":
            return False
        return intent in ["generate", "analyze"]
    
    registry.supports_intent = Mock(side_effect=supports_intent_mock)
    
    # Configure get_core_config method
    registry.get_core_config = Mock(return_value={
        "model_id": "instagram-model",
        "base_parameters": {
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "adapters": {
            "default": "instagram_adapter"
        },
        "capabilities": ["generate", "analyze"]
    })
    
    # Configure get_mode_config method
    def get_mode_config_mock(expert_id, intent):
        if expert_id != "instagram":
            raise ExpertNotFoundException(expert_id)
        
        if intent not in ["generate", "analyze"]:
            raise IntentNotSupportedException(expert_id, intent)
        
        if intent == "generate":
            return {
                "processor": "content_generation_pipeline",
                "parameters": {
                    "creativity": "high"
                },
                "knowledge_filters": {
                    "domain": "instagram_posts"
                }
            }
        else:
            return {
                "processor": "content_analysis_pipeline",
                "parameters": {
                    "depth": "detailed"
                },
                "knowledge_filters": {
                    "domain": "instagram_metrics"
                }
            }
    
    registry.get_mode_config = Mock(side_effect=get_mode_config_mock)
    
    return registry


@pytest.fixture
def mock_processor_factory():
    """Create a mock Processor Factory."""
    factory = Mock()
    
    # Configure create_processor method to return a mock processor
    mock_processor = AsyncMock()
    mock_processor.process = AsyncMock(return_value={
        "content": "Processed content",
        "feedback": {
            "quality_score": 0.9
        },
        "metadata": {
            "processing_time": 0.5
        }
    })
    
    factory.create_processor = Mock(return_value=mock_processor)
    
    return factory


@pytest.fixture
def mock_knowledge_hub():
    """Create a mock Knowledge Hub."""
    hub = Mock()
    
    # Configure retrieve_knowledge method
    hub.retrieve_knowledge = AsyncMock(return_value="Relevant knowledge for processing")
    
    return hub


@pytest.fixture
def orchestrator(mock_expert_registry, mock_processor_factory, mock_knowledge_hub):
    """Create an Expert Orchestrator with mock dependencies."""
    return ExpertOrchestrator(
        expert_registry=mock_expert_registry,
        processor_factory=mock_processor_factory,
        knowledge_hub=mock_knowledge_hub
    )


@pytest.mark.asyncio
async def test_process_request_success(orchestrator):
    """Test successful processing of a request."""
    # Create a request
    request = ExpertRequest(
        expert="instagram",
        intent="generate",
        content="Create a post about travel",
        parameters={"hashtags": True},
        metadata={"user_id": "user123"},
        tracking_id="test-tracking-id"
    )
    
    # Process the request
    response = await orchestrator.process_request(request)
    
    # Check response
    assert isinstance(response, ExpertResponse)
    assert response.expert_id == "instagram"
    assert response.intent == "generate"
    assert response.content == "Processed content"
    assert response.feedback == {"quality_score": 0.9}
    assert response.tracking_id == "test-tracking-id"
    
    # Verify method calls
    orchestrator.expert_registry.has_expert.assert_called_with("instagram")
    orchestrator.expert_registry.supports_intent.assert_called_with("instagram", "generate")
    orchestrator.expert_registry.get_core_config.assert_called_with("instagram")
    orchestrator.expert_registry.get_mode_config.assert_called_with("instagram", "generate")
    
    orchestrator.knowledge_hub.retrieve_knowledge.assert_called_once()
    
    processor = orchestrator.processor_factory.create_processor.return_value
    processor.process.assert_called_once()


@pytest.mark.asyncio
async def test_process_request_expert_not_found(orchestrator):
    """Test processing a request for a non-existent expert."""
    # Create a request
    request = ExpertRequest(
        expert="twitter",
        intent="generate",
        content="Create a tweet",
        parameters={},
        metadata={}
    )
    
    # Test that it raises ExpertNotFoundException
    with pytest.raises(ExpertNotFoundException):
        await orchestrator.process_request(request)
    
    # Verify method calls
    orchestrator.expert_registry.has_expert.assert_called_with("twitter")
    orchestrator.knowledge_hub.retrieve_knowledge.assert_not_called()
    
    processor = orchestrator.processor_factory.create_processor.return_value
    processor.process.assert_not_called()


@pytest.mark.asyncio
async def test_process_request_intent_not_supported(orchestrator):
    """Test processing a request with an unsupported intent."""
    # Create a request
    request = ExpertRequest(
        expert="instagram",
        intent="review",
        content="Review this post",
        parameters={},
        metadata={}
    )
    
    # Test that it raises IntentNotSupportedException
    with pytest.raises(IntentNotSupportedException):
        await orchestrator.process_request(request)
    
    # Verify method calls
    orchestrator.expert_registry.has_expert.assert_called_with("instagram")
    orchestrator.expert_registry.supports_intent.assert_called_with("instagram", "review")
    orchestrator.knowledge_hub.retrieve_knowledge.assert_not_called()
    
    processor = orchestrator.processor_factory.create_processor.return_value
    processor.process.assert_not_called()


@pytest.mark.asyncio
async def test_process_request_processing_error(orchestrator, mock_processor_factory):
    """Test handling of processing errors."""
    # Configure the mock processor to raise an exception
    mock_processor = mock_processor_factory.create_processor.return_value
    mock_processor.process.side_effect = Exception("Processing failed")
    
    # Create a request
    request = ExpertRequest(
        expert="instagram",
        intent="generate",
        content="Create a post about travel",
        parameters={},
        metadata={}
    )
    
    # Test that it raises ProcessingException
    with pytest.raises(ProcessingException):
        await orchestrator.process_request(request)
    
    # Verify method calls
    orchestrator.expert_registry.has_expert.assert_called_with("instagram")
    orchestrator.expert_registry.supports_intent.assert_called_with("instagram", "generate")
    orchestrator.knowledge_hub.retrieve_knowledge.assert_called_once()
    mock_processor.process.assert_called_once()


def test_merge_configurations(orchestrator):
    """Test merging configurations from different sources."""
    # Define test configurations
    core_config = {
        "model_id": "test-model",
        "base_parameters": {
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "adapters": {
            "default": "default_adapter"
        }
    }
    
    mode_config = {
        "parameters": {
            "creativity": "high",
            "temperature": 0.8  # Should override core config
        }
    }
    
    user_parameters = {
        "max_tokens": 500,  # Should override core config
        "custom_param": "value"  # Should be added
    }
    
    # Merge configurations
    result = orchestrator._merge_configurations(core_config, mode_config, user_parameters)
    
    # Check result
    assert result["model_id"] == "test-model"
    assert result["adapters"] == {"default": "default_adapter"}
    
    # Mode config should override core config
    assert result["creativity"] == "high"
    assert result["temperature"] == 0.8  # From mode_config, overrides core_config
    
    # User parameters should override all
    assert result["max_tokens"] == 500  # From user_parameters, overrides core_config
    assert result["custom_param"] == "value"  # From user_parameters 