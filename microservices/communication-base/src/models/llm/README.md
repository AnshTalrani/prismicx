# LLM Integration Framework

## Overview

This directory contains the framework for integrating Large Language Models (LLMs) with the communication platform. The current implementation provides an abstract base class (`BaseLLMManager`) that defines the interface for model loading, management, and integration with the adapter system. Concrete implementations for specific model providers need to be added.

## Architecture

```
models/llm/
├── base_llm_manager.py    # Abstract base class for LLM managers
├── model_cache.py         # Caching mechanism for model instances
├── model_registry.py      # Registry for tracking LLM managers
├── mlops_integration.py   # Integration with MLOps monitoring
└── README.md              # This file
```

## Current Implementation Status

- ✅ Abstract `BaseLLMManager` class with common functionality
- ✅ Model caching system for efficient memory usage
- ✅ Model registry for centralized management
- ✅ MLOps integration for monitoring and logging
- ✅ Integration with configuration system
- ✅ Integration with adapter framework
- ❌ Concrete LLM manager implementations for specific providers

## Adding Model Implementations

To implement support for a specific LLM provider, follow these steps:

1. Create a new class that extends `BaseLLMManager`
2. Implement the required abstract methods
3. Add provider-specific functionality as needed
4. Register with the model registry

### Example Implementation Structure

```python
from src.models.llm.base_llm_manager import BaseLLMManager
from typing import Dict, Any, Optional

class OpenAILLMManager(BaseLLMManager):
    """LLM Manager for OpenAI models."""
    
    def __init__(self, bot_type: str):
        super().__init__(bot_type)
        # Provider-specific initialization
    
    def _load_specific_model(self, model_path: str) -> Any:
        """
        Load OpenAI model by ID or from local path.
        
        Args:
            model_path: Model identifier or path
            
        Returns:
            Model instance
        """
        # Implementation for loading OpenAI models
    
    def prepare_inference_params(self, model_name: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare parameters for OpenAI model inference.
        
        Args:
            model_name: Name of the model to use
            **kwargs: Additional parameters
            
        Returns:
            Dictionary of parameters for inference
        """
        # OpenAI-specific parameter preparation
    
    def generate_response(self, prompt: str, model=None, **kwargs) -> str:
        """
        Generate a response from the OpenAI model.
        
        Args:
            prompt: Input prompt for the model
            model: Optional specific model to use
            **kwargs: Additional parameters for generation
            
        Returns:
            Generated response
        """
        # Implementation for OpenAI response generation
```

### Required Implementations

At minimum, the following model providers should be implemented:

1. **OpenAI** (GPT-3.5, GPT-4)
2. **Anthropic** (Claude models)
3. **HuggingFace** (Various open-source models)
4. **Local models** (For self-hosted options)

## Integration with Adapters

The LLM managers should work seamlessly with the adapter system. Key integration points:

1. Each LLM manager automatically registers with the `AdapterManager`
2. The `activate_adapter()` method connects adapters to models
3. The `generate_response()` method should apply active adapters to model outputs

### Example Adapter Integration

```python
def activate_adapters_for_session(self, model_name: str, session_id: str) -> bool:
    """
    Activate all appropriate adapters for a session.
    
    Args:
        model_name: Name of the model to use
        session_id: Session identifier
        
    Returns:
        True if successful, False otherwise
    """
    # Get session context to determine which adapters to activate
    session_context = self.session_manager.get_session_context(session_id)
    bot_type = session_context.get("bot_type", self.bot_type)
    
    # Use adapter manager to activate appropriate adapters
    model = self.get_model(model_name)
    return self.adapter_manager.activate_adapters_for_bot(model, bot_type)
```

## Configuration Requirements

Each LLM manager implementation should load configurations from the config system:

```python
# Example configuration structure for LLM models
model_config = {
    "provider": "openai",
    "model_id": "gpt-4",
    "api_key": "${OPENAI_API_KEY}",  # Environment variable reference
    "default_params": {
        "temperature": 0.7,
        "max_tokens": 500,
        "top_p": 0.95
    },
    "fallback_model": "gpt-3.5-turbo"
}
```

## Testing New LLM Managers

When implementing a new LLM manager, create corresponding test files:

1. Unit tests for the specific manager functionality
2. Integration tests with the adapter system
3. Performance tests for response generation

Follow the existing test patterns in the `tests/models/llm/` directory.

## Best Practices

1. **Error Handling**: Implement robust error handling, especially for API calls
2. **Fallbacks**: Configure fallback models when primary models are unavailable
3. **Caching**: Utilize the model cache for efficient memory usage
4. **Resource Management**: Properly release model resources when no longer needed
5. **Monitoring**: Integrate with MLOps for tracking usage, performance, and costs
6. **Security**: Handle API keys securely through the configuration system 