"""
OpenAI OSS LLM Adapter

This module provides an adapter for OpenAI's open source language models.
"""

import asyncio
from typing import List, Optional, Dict, Any, AsyncGenerator
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from .base_llm import BaseLLM, Message, MessageRole, GenerationResult, EmbeddingResult
from src.config.logging_config import get_logger


class OpenAIOSSAdapter(BaseLLM):
    """OpenAI open source language model adapter."""
    
    def __init__(self, config: dict):
        """Initialize the OpenAI OSS adapter."""
        super().__init__(config)
        self.logger = get_logger(self.__class__.__name__)
        self.model_name = config.get("model_name", "openai/gpt2")
        self.max_tokens = config.get("max_tokens", 1000)
        self.temperature = config.get("temperature", 0.7)
        self.device = config.get("device", "cpu")
        self.tokenizer = None
        self.model = None
        self.is_loaded = False
        
    async def load_model(self):
        """Load the OpenAI OSS model."""
        try:
            self.logger.info(f"Loading OpenAI OSS model: {self.model_name}")
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map=self.device
            )
            
            # Set pad token if not set
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.is_loaded = True
            self.logger.info(f"OpenAI OSS model loaded successfully: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Failed to load OpenAI OSS model: {str(e)}")
            raise
    
    async def generate(self, messages: List[Message], **kwargs) -> GenerationResult:
        """Generate text using OpenAI OSS model."""
        if not self.is_loaded:
            await self.load_model()
        
        try:
            # Convert messages to text prompt
            prompt = self._messages_to_prompt(messages)
            
            # Get generation parameters
            max_tokens = kwargs.get("max_tokens", self.max_tokens)
            temperature = kwargs.get("temperature", self.temperature)
            
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the new part
            response_text = generated_text[len(prompt):].strip()
            
            return GenerationResult(
                text=response_text,
                finish_reason="stop",
                usage={
                    "prompt_tokens": len(inputs["input_ids"][0]),
                    "completion_tokens": len(outputs[0]) - len(inputs["input_ids"][0]),
                    "total_tokens": len(outputs[0])
                },
                metadata={
                    "model": self.model_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
        except Exception as e:
            self.logger.error(f"OpenAI OSS generation failed: {str(e)}")
            raise
    
    async def generate_stream(self, messages: List[Message], **kwargs) -> AsyncGenerator[GenerationResult, None]:
        """Generate streaming text using OpenAI OSS model."""
        if not self.is_loaded:
            await self.load_model()
        
        try:
            # Convert messages to text prompt
            prompt = self._messages_to_prompt(messages)
            
            # Get generation parameters
            max_tokens = kwargs.get("max_tokens", self.max_tokens)
            temperature = kwargs.get("temperature", self.temperature)
            
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate with streaming
            with torch.no_grad():
                streamer = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    streamer=None,  # We'll handle streaming manually
                    return_dict_in_generate=True,
                    output_scores=False
                )
            
            # Stream the response
            generated_tokens = []
            for i in range(max_tokens):
                # Generate next token
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=1,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
                
                # Get the new token
                new_token = outputs[0][-1:]
                generated_tokens.append(new_token)
                
                # Decode the new token
                new_text = self.tokenizer.decode(new_token, skip_special_tokens=True)
                
                if new_text:
                    yield GenerationResult(
                        text=new_text,
                        finish_reason="stop" if i == max_tokens - 1 else None,
                        usage=None,
                        metadata={
                            "model": self.model_name,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            "streaming": True
                        }
                    )
                
                # Update inputs for next iteration
                inputs["input_ids"] = outputs
                
        except Exception as e:
            self.logger.error(f"OpenAI OSS streaming generation failed: {str(e)}")
            raise
    
    async def embed(self, texts: List[str], **kwargs) -> EmbeddingResult:
        """Generate embeddings using OpenAI OSS model."""
        if not self.is_loaded:
            await self.load_model()
        
        try:
            # For now, we'll use a simple approach
            # In production, you might want to use a dedicated embedding model
            embeddings = []
            
            for text in texts:
                # Tokenize and get hidden states
                inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = self.model(**inputs, output_hidden_states=True)
                    # Use the last hidden state as embedding
                    embedding = outputs.hidden_states[-1].mean(dim=1).squeeze()
                    embeddings.append(embedding.cpu().numpy())
            
            return EmbeddingResult(
                embeddings=embeddings,
                usage={
                    "prompt_tokens": sum(len(self.tokenizer.encode(text)) for text in texts),
                    "total_tokens": sum(len(self.tokenizer.encode(text)) for text in texts)
                },
                metadata={
                    "model": self.model_name,
                    "dimensions": embeddings[0].shape[0] if embeddings else 0
                }
            )
            
        except Exception as e:
            self.logger.error(f"OpenAI OSS embedding failed: {str(e)}")
            raise
    
    def _messages_to_prompt(self, messages: List[Message]) -> str:
        """Convert messages to a text prompt."""
        prompt = ""
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                prompt += f"System: {msg.content}\n"
            elif msg.role == MessageRole.USER:
                prompt += f"User: {msg.content}\n"
            elif msg.role == MessageRole.ASSISTANT:
                prompt += f"Assistant: {msg.content}\n"
        
        prompt += "Assistant: "
        return prompt
    
    def get_model_info(self) -> dict:
        """Get model information."""
        return {
            "name": "OpenAI OSS",
            "model": self.model_name,
            "is_loaded": self.is_loaded,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "device": self.device
        } 