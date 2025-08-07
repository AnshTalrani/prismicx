"""
OpenAI LLM Adapter

This module provides an adapter for OpenAI's language models.
"""

import asyncio
from typing import List, Optional, Dict, Any, AsyncGenerator
import openai
from openai import AsyncOpenAI

from ...llm.base_llm import BaseLLM, Message, MessageRole, GenerationResult, EmbeddingResult


class OpenAIAdapter(BaseLLM):
    """OpenAI language model adapter."""
    
    def __init__(self, config: dict):
        """Initialize the OpenAI adapter."""
        super().__init__()
        self.api_key = config.get("api_key")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.max_tokens = config.get("max_tokens", 1000)
        self.temperature = config.get("temperature", 0.7)
        self.client = None
        self.is_loaded = False
        
    async def load_model(self):
        """Initialize the OpenAI client."""
        try:
            if not self.api_key:
                raise ValueError("OpenAI API key is required")
            
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.is_loaded = True
            self.logger.info(f"OpenAI client initialized with model: {self.model}")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise
    
    async def generate(self, messages: List[Message], **kwargs) -> GenerationResult:
        """Generate text using OpenAI."""
        if not self.is_loaded:
            await self.load_model()
        
        try:
            # Convert messages to OpenAI format
            openai_messages = []
            for msg in messages:
                openai_messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
            
            # Get generation parameters
            max_tokens = kwargs.get("max_tokens", self.max_tokens)
            temperature = kwargs.get("temperature", self.temperature)
            
            # Generate response
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False
            )
            
            # Extract response
            content = response.choices[0].message.content
            usage = response.usage
            
            return GenerationResult(
                text=content,
                finish_reason=response.choices[0].finish_reason,
                usage={
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                },
                metadata={
                    "model": self.model,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
        except Exception as e:
            self.logger.error(f"OpenAI generation failed: {str(e)}")
            raise
    
    async def generate_stream(self, messages: List[Message], **kwargs) -> AsyncGenerator[GenerationResult, None]:
        """Generate streaming text using OpenAI."""
        if not self.is_loaded:
            await self.load_model()
        
        try:
            # Convert messages to OpenAI format
            openai_messages = []
            for msg in messages:
                openai_messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
            
            # Get generation parameters
            max_tokens = kwargs.get("max_tokens", self.max_tokens)
            temperature = kwargs.get("temperature", self.temperature)
            
            # Generate streaming response
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield GenerationResult(
                        text=chunk.choices[0].delta.content,
                        finish_reason=chunk.choices[0].finish_reason,
                        usage=None,
                        metadata={
                            "model": self.model,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            "streaming": True
                        }
                    )
                    
        except Exception as e:
            self.logger.error(f"OpenAI streaming generation failed: {str(e)}")
            raise
    
    async def embed(self, texts: List[str], **kwargs) -> EmbeddingResult:
        """Generate embeddings using OpenAI."""
        if not self.is_loaded:
            await self.load_model()
        
        try:
            # Generate embeddings
            response = await self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=texts
            )
            
            # Extract embeddings
            embeddings = [embedding.embedding for embedding in response.data]
            usage = response.usage
            
            return EmbeddingResult(
                embeddings=embeddings,
                usage={
                    "prompt_tokens": usage.prompt_tokens,
                    "total_tokens": usage.total_tokens
                },
                metadata={
                    "model": "text-embedding-ada-002",
                    "dimensions": len(embeddings[0]) if embeddings else 0
                }
            )
            
        except Exception as e:
            self.logger.error(f"OpenAI embedding failed: {str(e)}")
            raise
    
    def get_model_info(self) -> dict:
        """Get model information."""
        return {
            "name": "OpenAI",
            "model": self.model,
            "api_key_set": bool(self.api_key),
            "is_loaded": self.is_loaded,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        } 