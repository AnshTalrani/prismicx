"""
Support-specific LLM Manager implementation.
Specializes in handling technical support, issue classification, and troubleshooting.
"""

from langchain.llms import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer
import os
import structlog
from typing import Dict, Any, List, Optional, Union
from src.models.llm.base_llm_manager import BaseLLMManager

# Configure logger
logger = structlog.get_logger(__name__)

class SupportLLMManager(BaseLLMManager):
    """
    Support-specialized LLM Manager for handling technical support and issue resolution.
    
    Features:
    - Optimized smaller models for faster response times
    - Issue-specific adapter loading
    - Support tier optimization
    """
    
    def __init__(self):
        """Initialize the Support LLM Manager."""
        super().__init__(bot_type="support")
        
        # Initialize issue-specific adapters registry
        self.issue_adapters = {}
        self.active_issue_type = None
        
        # Load available support adapters
        self._initialize_support_adapters()
        
        logger.info("SupportLLMManager initialized")
    
    def _initialize_support_adapters(self):
        """Initialize and register available support adapters."""
        adapters_base_path = self.config.get("models.adapters_path", "models/support/adapters")
        
        # Register product support adapters
        product_types = self.config.get("product_types", ["app", "service", "hardware"])
        for prod_type in product_types:
            adapter_path = os.path.join(adapters_base_path, f"product_{prod_type}")
            if os.path.exists(adapter_path):
                self.issue_adapters[f"product_{prod_type}"] = adapter_path
                logger.info(f"Registered product support adapter: {prod_type}")
        
        # Register issue-specific adapters
        issue_types = self.config.get("issue_types", ["technical", "billing", "access"])
        for issue_type in issue_types:
            adapter_path = os.path.join(adapters_base_path, f"issue_{issue_type}")
            if os.path.exists(adapter_path):
                self.issue_adapters[f"issue_{issue_type}"] = adapter_path
                logger.info(f"Registered issue adapter: {issue_type}")
    
    def _load_specific_model(self, model_path: str) -> Any:
        """
        Load a specific support model implementation.
        
        Args:
            model_path: Path to the support model
            
        Returns:
            The loaded model
        """
        try:
            # For support, we might use a smaller/faster model
            use_4bit = self.config.get("model_params.use_4bit", True)
            use_8bit = self.config.get("model_params.use_8bit", False)
            
            # Load model with quantization for faster responses
            load_kwargs = {}
            if use_4bit:
                load_kwargs["load_in_4bit"] = True
            elif use_8bit:
                load_kwargs["load_in_8bit"] = True
            
            # Load the model and tokenizer
            model = AutoModelForCausalLM.from_pretrained(model_path, **load_kwargs)
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            
            # Store tokenizer for later use
            model.tokenizer = tokenizer
            
            logger.info(f"Successfully loaded support model from {model_path}")
            return model
        except Exception as e:
            logger.error(f"Error loading support model: {e}")
            raise
    
    def load_issue_adapter(self, issue_type: str, product_type: str, urgency: str) -> bool:
        """
        Load appropriate adapters for a specific support issue.
        
        Args:
            issue_type: Type of issue (technical, billing, access)
            product_type: Type of product (app, service, hardware)
            urgency: Urgency level (low, medium, high)
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Loading adapters for issue: type={issue_type}, product={product_type}, urgency={urgency}")
        
        # Get default model or load if needed
        model_name = "default"
        if model_name not in self.models:
            model_path = self.config.get("models.default_path", "models/support/base_model")
            self.load_model(model_name, model_path)
        
        if model_name not in self.models:
            logger.error(f"Cannot load issue adapters: Model {model_name} not available")
            return False
        
        model = self.models[model_name]
        
        # Activate product type adapter
        product_adapter_name = f"product_{product_type}"
        if product_adapter_name in self.issue_adapters:
            adapter_path = self.issue_adapters[product_adapter_name]
            try:
                model.load_adapter(adapter_path)
                logger.info(f"Loaded product adapter: {product_adapter_name}")
            except Exception as e:
                logger.error(f"Failed to load product adapter {product_adapter_name}: {e}")
        
        # Activate issue type adapter
        issue_adapter_name = f"issue_{issue_type}"
        if issue_adapter_name in self.issue_adapters:
            adapter_path = self.issue_adapters[issue_adapter_name]
            try:
                model.load_adapter(adapter_path)
                logger.info(f"Loaded issue adapter: {issue_adapter_name}")
            except Exception as e:
                logger.error(f"Failed to load issue adapter {issue_adapter_name}: {e}")
        
        # Set the active issue type
        self.active_issue_type = {
            "type": issue_type,
            "product": product_type,
            "urgency": urgency
        }
        
        return True
    
    def create_langchain_wrapper(self, model_name: str) -> HuggingFacePipeline:
        """
        Create a LangChain wrapper for the specified model.
        
        Args:
            model_name: Name of the model to wrap
            
        Returns:
            LangChain HuggingFacePipeline wrapper
        """
        if model_name not in self.models:
            logger.warning(f"Model {model_name} not loaded, loading now")
            self.load_model(model_name)
        
        model = self.models[model_name]
        tokenizer = getattr(model, "tokenizer", None)
        
        if not tokenizer:
            raise ValueError(f"Model {model_name} does not have an associated tokenizer")
        
        # For support, we optimize for faster responses with shorter generation
        generation_config = {
            "max_new_tokens": 256,
            "do_sample": True,
            "temperature": 0.5,  # More deterministic for support
            "top_p": 0.85
        }
        
        return HuggingFacePipeline.from_model_id(
            model_id=model_name,
            task="text-generation",
            model=model,
            tokenizer=tokenizer,
            model_kwargs={"generation_config": generation_config}
        )
    
    def prepare_inference_params(self, model_name: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare parameters for model inference, optimized for support contexts.
        
        Args:
            model_name: Name of the model to use
            **kwargs: Additional parameters
            
        Returns:
            Dictionary of parameters for inference
        """
        # Get base parameters from config - optimized for technical support responses
        params = {
            "temperature": self.config.get("model_params.temperature", 0.5),  # More deterministic for support
            "max_length": self.config.get("model_params.max_length", 384),  # Shorter responses for support
            "top_p": self.config.get("model_params.top_p", 0.85),
            "top_k": self.config.get("model_params.top_k", 40)
        }
        
        # Adjust parameters based on active issue if available
        if self.active_issue_type:
            urgency = self.active_issue_type.get("urgency")
            issue_type = self.active_issue_type.get("type")
            
            # Urgency-specific adjustments
            if urgency == "high":
                # More concise and direct for high urgency
                params["temperature"] = 0.4
                params["max_length"] = 256
            elif urgency == "medium":
                # Balanced approach for medium urgency
                params["temperature"] = 0.5
                params["max_length"] = 384
            elif urgency == "low":
                # More detailed for low urgency
                params["temperature"] = 0.6
                params["max_length"] = 512
            
            # Issue type specific adjustments
            if issue_type == "technical":
                # More precise for technical issues
                params["top_p"] = 0.8
            elif issue_type == "billing":
                # More formal for billing issues
                params["temperature"] = 0.45
            elif issue_type == "access":
                # Standard settings for access issues
                pass
        
        # Override with any explicitly provided kwargs
        params.update(kwargs)
        
        return params
    
    def classify_issue(self, prompt: str) -> str:
        """
        Classify the type of support issue from the prompt.
        
        Args:
            prompt: User's prompt
            
        Returns:
            Classified issue type
        """
        # This would be implemented with a classifier model or rules
        # Placeholder implementation
        keywords = {
            "technical": ["error", "bug", "not working", "broken", "fix"],
            "billing": ["charge", "payment", "invoice", "refund", "credit card"],
            "account": ["password", "login", "account", "email", "access"],
            "product": ["how to", "feature", "use", "missing", "where is"],
            "complaint": ["unhappy", "disappointed", "frustrating", "poor", "bad"]
        }
        
        prompt_lower = prompt.lower()
        for issue_type, words in keywords.items():
            for word in words:
                if word in prompt_lower:
                    return issue_type
        
        return "general"
    
    def should_escalate(self, prompt: str, history: List[str] = None) -> bool:
        """
        Determine if an issue should be escalated to a human agent.
        
        Args:
            prompt: Current user prompt
            history: Conversation history
            
        Returns:
            True if the issue should be escalated, False otherwise
        """
        # Check for explicit escalation requests
        escalation_phrases = [
            "speak to a human", 
            "talk to a person", 
            "real person", 
            "manager", 
            "supervisor",
            "agent",
            "this is not helping"
        ]
        
        prompt_lower = prompt.lower()
        for phrase in escalation_phrases:
            if phrase in prompt_lower:
                return True
        
        # Check for repeated similar questions (indicating frustration)
        if history and len(history) > 3:
            last_two = [h.lower() for h in history[-2:]]
            if any(prompt_lower in h for h in last_two):
                return True
        
        return False 