"""
Model provider for the Expert Base microservice.

This module provides a model provider for LLM inference using open source
HuggingFace models through the LangChain framework.
"""

import os
from typing import Dict, Any, Optional
from loguru import logger

try:
    from langchain_community.llms import HuggingFacePipeline
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    HF_AVAILABLE = True
except ImportError:
    logger.warning("HuggingFace/LangChain not available. Using placeholder model.")
    HF_AVAILABLE = False


class ModelProvider:
    """
    Model provider for LLM inference.
    
    This class provides a unified interface for accessing different LLM models.
    It currently supports HuggingFace models through LangChain.
    """
    
    def __init__(self):
        """
        Initialize the model provider.
        """
        self.models = {}
        self.default_models = {
            "default": "google/flan-t5-base",
            "instagram": "google/flan-t5-base",
            "etsy": "google/flan-t5-base",
            "marketing": "google/flan-t5-base",
            "branding": "google/flan-t5-base"
        }
        logger.info("Initialized ModelProvider")
    
    def get_model(self, model_id: str):
        """
        Get a model by ID.
        
        Args:
            model_id: The ID of the model to get.
            
        Returns:
            A model instance.
        """
        # If the model is already loaded, return it
        if model_id in self.models:
            return self.models[model_id]
        
        # If the model is not in the defaults, use the default model
        if model_id not in self.default_models:
            logger.warning(f"Model {model_id} not found, using default model")
            model_id = "default"
        
        # Get the actual HF model ID
        hf_model_id = self.default_models[model_id]
        
        # Create and cache the model
        model = self._create_model(hf_model_id)
        self.models[model_id] = model
        
        return model
    
    def _create_model(self, hf_model_id: str):
        """
        Create a model from a HuggingFace model ID.
        
        Args:
            hf_model_id: The HuggingFace model ID.
            
        Returns:
            A model instance.
        """
        if HF_AVAILABLE:
            try:
                # Initialize a real HuggingFace model
                return HuggingFaceModel(hf_model_id)
            except Exception as e:
                logger.error(f"Error initializing HuggingFace model: {e}")
                # Fall back to the placeholder model
                return PlaceholderModel(hf_model_id)
        else:
            # Use a placeholder model if HuggingFace is not available
            return PlaceholderModel(hf_model_id)


class BaseModel:
    """
    Base class for all models.
    
    This class defines the interface that all models must implement.
    """
    
    async def generate(self, prompt: str, params: Dict[str, Any] = None) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: The prompt to generate from.
            params: The generation parameters.
            
        Returns:
            The generated text.
        """
        raise NotImplementedError("Subclasses must implement generate()")


class HuggingFaceModel(BaseModel):
    """
    HuggingFace model.
    
    This class wraps a HuggingFace model for use in the Expert Base microservice.
    """
    
    def __init__(self, hf_model_id: str):
        """
        Initialize the HuggingFace model.
        
        Args:
            hf_model_id: The HuggingFace model ID.
        """
        self.hf_model_id = hf_model_id
        self.llm = self._initialize_hf_model(hf_model_id)
    
    def _initialize_hf_model(self, hf_model_id: str):
        """
        Initialize a HuggingFace model.
        
        Args:
            hf_model_id: The HuggingFace model ID.
            
        Returns:
            A LangChain LLM instance.
        """
        try:
            # Load the model and tokenizer
            tokenizer = AutoTokenizer.from_pretrained(hf_model_id)
            model = AutoModelForCausalLM.from_pretrained(hf_model_id)
            
            # Create a HuggingFace pipeline
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_length=512
            )
            
            # Create a LangChain LLM
            llm = HuggingFacePipeline(pipeline=pipe)
            
            return llm
        except Exception as e:
            logger.error(f"Error initializing HuggingFace model {hf_model_id}: {e}")
            raise
    
    async def generate(self, prompt: str, params: Dict[str, Any] = None) -> str:
        """
        Generate text from a prompt using the HuggingFace model.
        
        Args:
            prompt: The prompt to generate from.
            params: The generation parameters.
            
        Returns:
            The generated text.
        """
        try:
            # Set default parameters
            default_params = {
                "temperature": 0.7,
                "max_tokens": 512,
                "top_p": 0.9,
            }
            
            # Merge with user parameters
            generation_params = {**default_params, **(params or {})}
            
            # Clean the generation parameters to match HuggingFace's expected format
            if "max_tokens" in generation_params:
                generation_params["max_length"] = generation_params.pop("max_tokens")
            
            # Generate text
            result = self.llm(prompt)
            
            return result
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            # Return a fallback response
            return f"Failed to generate text due to an error: {e}"


class PlaceholderModel(BaseModel):
    """
    Placeholder model for when real models are not available.
    
    This class provides a simple placeholder that returns static responses.
    """
    
    def __init__(self, model_id: str):
        """
        Initialize the placeholder model.
        
        Args:
            model_id: The ID of the model.
        """
        self.model_id = model_id
        logger.warning(f"Using placeholder model for {model_id}")
    
    async def generate(self, prompt: str, params: Dict[str, Any] = None) -> str:
        """
        Generate text from a prompt using the placeholder model.
        
        Args:
            prompt: The prompt to generate from.
            params: The generation parameters.
            
        Returns:
            A placeholder response.
        """
        # Return a simple template response
        expert_type = params.get("expert_type", "general") if params else "general"
        
        # Extract the content from the prompt
        content_start = prompt.find("Content to enhance:") + len("Content to enhance:")
        content_end = prompt.find("Enhanced content:")
        
        if content_start > 0 and content_end > content_start:
            original_content = prompt[content_start:content_end].strip()
        else:
            original_content = "Sample content"
        
        # Generate a placeholder response based on expert type
        if expert_type == "instagram":
            return f"{original_content}\n\n#instagram #contentcreator #engagement"
        elif expert_type == "etsy":
            return f"{original_content}\n\nHandcrafted with care. Satisfaction guaranteed!"
        elif expert_type == "marketing":
            return f"{original_content}\n\nLimited time offer! Contact us today."
        elif expert_type == "branding":
            return f"{original_content}\n\nConsistent with our brand values and messaging."
        else:
            return f"{original_content}\n\nThis content has been enhanced by the Expert Base service."


def get_model_provider():
    """
    Get a model provider instance.
    
    Returns:
        A ModelProvider instance.
    """
    return ModelProvider() 