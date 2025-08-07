"""
Language Model (LLM) Integration

This package provides interfaces and implementations for various
language model providers (OpenAI, Anthropic, local models, etc.)
"""

# Export public API
__all__ = ['BaseLLM', 'OpenAIClient', 'AnthropicClient', 'LocalLLM']
