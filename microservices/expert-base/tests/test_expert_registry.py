"""
Tests for the Expert Registry module.
"""

import os
import pytest
import yaml
from unittest.mock import patch, mock_open

from src.modules.expert_registry import ExpertRegistry
from src.common.exceptions import ExpertNotFoundException, IntentNotSupportedException, ConfigurationException


# Sample expert configuration for testing
SAMPLE_CONFIG = {
    "instagram": {
        "core_config": {
            "model_id": "instagram-model",
            "base_parameters": {
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "capabilities": ["generate", "analyze"]
        },
        "modes": {
            "generate": {
                "processor": "content_generation_pipeline",
                "parameters": {
                    "creativity": "high"
                }
            },
            "analyze": {
                "processor": "content_analysis_pipeline",
                "parameters": {
                    "depth": "detailed"
                }
            }
        }
    }
}


@pytest.fixture
def expert_registry():
    """Create an expert registry with sample configuration."""
    yaml_content = yaml.dump(SAMPLE_CONFIG)
    with patch("builtins.open", mock_open(read_data=yaml_content)):
        registry = ExpertRegistry(config_path="test_config.yaml")
        return registry


@pytest.mark.asyncio
async def test_load_configurations(expert_registry):
    """Test loading configurations from a YAML file."""
    await expert_registry.load_configurations()
    
    # Check that experts were loaded
    assert "instagram" in expert_registry.experts
    assert expert_registry.has_expert("instagram")
    
    # Check core config
    core_config = expert_registry.get_core_config("instagram")
    assert core_config["model_id"] == "instagram-model"
    assert core_config["base_parameters"]["temperature"] == 0.7
    
    # Check mode config
    mode_config = expert_registry.get_mode_config("instagram", "generate")
    assert mode_config["processor"] == "content_generation_pipeline"
    assert mode_config["parameters"]["creativity"] == "high"


def test_has_expert(expert_registry):
    """Test checking if an expert exists."""
    expert_registry.experts = SAMPLE_CONFIG
    
    assert expert_registry.has_expert("instagram")
    assert not expert_registry.has_expert("twitter")


def test_supports_intent(expert_registry):
    """Test checking if an expert supports an intent."""
    expert_registry.experts = SAMPLE_CONFIG
    
    assert expert_registry.supports_intent("instagram", "generate")
    assert expert_registry.supports_intent("instagram", "analyze")
    assert not expert_registry.supports_intent("instagram", "review")
    assert not expert_registry.supports_intent("twitter", "generate")


def test_get_core_config(expert_registry):
    """Test getting core configuration for an expert."""
    expert_registry.experts = SAMPLE_CONFIG
    
    core_config = expert_registry.get_core_config("instagram")
    assert core_config["model_id"] == "instagram-model"
    assert core_config["capabilities"] == ["generate", "analyze"]
    
    with pytest.raises(ExpertNotFoundException):
        expert_registry.get_core_config("twitter")


def test_get_mode_config(expert_registry):
    """Test getting mode configuration for an expert and intent."""
    expert_registry.experts = SAMPLE_CONFIG
    
    mode_config = expert_registry.get_mode_config("instagram", "generate")
    assert mode_config["processor"] == "content_generation_pipeline"
    
    with pytest.raises(ExpertNotFoundException):
        expert_registry.get_mode_config("twitter", "generate")
    
    with pytest.raises(IntentNotSupportedException):
        expert_registry.get_mode_config("instagram", "review")


def test_get_capabilities(expert_registry):
    """Test getting capabilities for experts."""
    expert_registry.experts = SAMPLE_CONFIG
    
    # Test for a specific expert
    capabilities = expert_registry.get_capabilities("instagram")
    assert "instagram" in capabilities
    assert capabilities["instagram"]["capabilities"] == ["generate", "analyze"]
    assert set(capabilities["instagram"]["supported_intents"]) == {"generate", "analyze"}
    
    # Test for all experts
    all_capabilities = expert_registry.get_capabilities()
    assert "experts" in all_capabilities
    assert "instagram" in all_capabilities["experts"]
    
    # Test for non-existent expert
    with pytest.raises(ExpertNotFoundException):
        expert_registry.get_capabilities("twitter")


@pytest.mark.asyncio
async def test_add_expert(expert_registry):
    """Test adding a new expert."""
    expert_registry.experts = {}
    
    new_expert = {
        "core_config": {
            "model_id": "twitter-model",
            "capabilities": ["tweet"]
        },
        "modes": {
            "generate": {
                "processor": "tweet_generator"
            }
        }
    }
    
    await expert_registry.add_expert("twitter", new_expert)
    
    assert expert_registry.has_expert("twitter")
    assert expert_registry.supports_intent("twitter", "generate")


@pytest.mark.asyncio
async def test_remove_expert(expert_registry):
    """Test removing an expert."""
    expert_registry.experts = SAMPLE_CONFIG
    
    await expert_registry.remove_expert("instagram")
    
    assert not expert_registry.has_expert("instagram")
    
    with pytest.raises(ExpertNotFoundException):
        await expert_registry.remove_expert("twitter")


@pytest.mark.asyncio
async def test_update_expert(expert_registry):
    """Test updating an expert."""
    expert_registry.experts = SAMPLE_CONFIG
    
    updated_expert = {
        "core_config": {
            "model_id": "instagram-v2",
            "capabilities": ["generate", "analyze", "review"]
        },
        "modes": {
            "generate": {
                "processor": "content_generation_pipeline_v2"
            },
            "analyze": {
                "processor": "content_analysis_pipeline"
            },
            "review": {
                "processor": "content_review_pipeline"
            }
        }
    }
    
    await expert_registry.update_expert("instagram", updated_expert)
    
    assert expert_registry.has_expert("instagram")
    assert expert_registry.supports_intent("instagram", "review")
    
    core_config = expert_registry.get_core_config("instagram")
    assert core_config["model_id"] == "instagram-v2"
    
    with pytest.raises(ExpertNotFoundException):
        await expert_registry.update_expert("twitter", updated_expert) 