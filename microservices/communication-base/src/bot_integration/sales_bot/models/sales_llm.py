"""
Sales-specific LLM Manager implementation.
Specializes in handling product knowledge and campaign stage processing.
"""

from langchain.llms import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer
import os
import structlog
from typing import Dict, Any, List, Optional, Union
from src.models.llm.base_llm_manager import BaseLLMManager

# Configure logger
logger = structlog.get_logger(__name__)

class SalesLLMManager(BaseLLMManager):
    """
    Sales-specialized LLM Manager for handling product knowledge and campaign processing.
    
    Features:
    - Campaign-specific model and adapter loading
    - Product domain knowledge integration
    - Campaign stage optimization
    """
    
    def __init__(self):
        """Initialize the Sales LLM Manager."""
        super().__init__(bot_type="sales")
        
        # Initialize campaign-specific adapters registry
        self.campaign_adapters = {}
        self.active_campaign = None
        
        # Load available campaign adapters
        self._initialize_campaign_adapters()
        
        logger.info("SalesLLMManager initialized")
    
    def _initialize_campaign_adapters(self):
        """Initialize and register available campaign adapters."""
        adapters_base_path = self.config.get("models.adapters_path", "models/sales/adapters")
        
        # Register product domain adapters
        product_domains = self.config.get("product_domains", ["clothing", "jewelry", "accessories"])
        for domain in product_domains:
            adapter_path = os.path.join(adapters_base_path, f"product_{domain}")
            if os.path.exists(adapter_path):
                self.campaign_adapters[f"product_{domain}"] = adapter_path
                logger.info(f"Registered product adapter: {domain}")
        
        # Register campaign stage adapters
        campaign_stages = self.config.get("campaign_stages", ["awareness", "interest", "decision"])
        for stage in campaign_stages:
            adapter_path = os.path.join(adapters_base_path, f"stage_{stage}")
            if os.path.exists(adapter_path):
                self.campaign_adapters[f"stage_{stage}"] = adapter_path
                logger.info(f"Registered campaign stage adapter: {stage}")
    
    def _load_specific_model(self, model_path: str) -> Any:
        """
        Load a specific sales model implementation.
        
        Args:
            model_path: Path to the sales model
            
        Returns:
            The loaded model
        """
        try:
            # Load the model and tokenizer
            model = AutoModelForCausalLM.from_pretrained(model_path)
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            
            # Store tokenizer for later use
            model.tokenizer = tokenizer
            
            logger.info(f"Successfully loaded sales model from {model_path}")
            return model
        except Exception as e:
            logger.error(f"Error loading sales model: {e}")
            raise
    
    def load_campaign_adapter(self, campaign_id: str, product_domain: str, stage: str) -> bool:
        """
        Load appropriate adapters for a specific campaign.
        
        Args:
            campaign_id: ID of the campaign
            product_domain: Product domain for the campaign (clothing, jewelry, etc.)
            stage: Current campaign stage (awareness, interest, decision)
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Loading adapters for campaign {campaign_id}: domain={product_domain}, stage={stage}")
        
        # Get default model or load if needed
        model_name = "default"
        if model_name not in self.models:
            model_path = self.config.get("models.default_path", "models/sales/base_model")
            self.load_model(model_name, model_path)
        
        if model_name not in self.models:
            logger.error(f"Cannot load campaign adapters: Model {model_name} not available")
            return False
        
        model = self.models[model_name]
        
        # Activate product domain adapter
        product_adapter_name = f"product_{product_domain}"
        if product_adapter_name in self.campaign_adapters:
            adapter_path = self.campaign_adapters[product_adapter_name]
            try:
                model.load_adapter(adapter_path)
                logger.info(f"Loaded product adapter: {product_adapter_name}")
            except Exception as e:
                logger.error(f"Failed to load product adapter {product_adapter_name}: {e}")
        
        # Activate campaign stage adapter
        stage_adapter_name = f"stage_{stage}"
        if stage_adapter_name in self.campaign_adapters:
            adapter_path = self.campaign_adapters[stage_adapter_name]
            try:
                model.load_adapter(adapter_path)
                logger.info(f"Loaded stage adapter: {stage_adapter_name}")
            except Exception as e:
                logger.error(f"Failed to load stage adapter {stage_adapter_name}: {e}")
        
        # Set the active campaign
        self.active_campaign = {
            "id": campaign_id,
            "product_domain": product_domain,
            "stage": stage
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
        
        return HuggingFacePipeline.from_model_id(
            model_id=model_name,
            task="text-generation",
            model=model,
            tokenizer=tokenizer
        )
    
    def prepare_inference_params(self, model_name: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare parameters for model inference, optimized for sales contexts.
        
        Args:
            model_name: Name of the model to use
            **kwargs: Additional parameters
            
        Returns:
            Dictionary of parameters for inference
        """
        # Get base parameters from config
        params = {
            "temperature": self.config.get("model_params.temperature", 0.7),
            "max_length": self.config.get("model_params.max_length", 512),
            "top_p": self.config.get("model_params.top_p", 0.9),
            "top_k": self.config.get("model_params.top_k", 50)
        }
        
        # Adjust parameters based on active campaign stage if available
        if self.active_campaign:
            stage = self.active_campaign.get("stage")
            stage_params = self.config.get(f"campaign_stages.{stage}.model_params", {})
            
            # Apply stage-specific parameter adjustments
            if stage == "awareness":
                # More informative and educational
                params["temperature"] = stage_params.get("temperature", 0.6)
                params["top_p"] = stage_params.get("top_p", 0.85)
            elif stage == "interest":
                # More engaging and detailed
                params["temperature"] = stage_params.get("temperature", 0.7)
                params["max_length"] = stage_params.get("max_length", 640)
            elif stage == "decision":
                # More persuasive and confident
                params["temperature"] = stage_params.get("temperature", 0.8)
                params["top_p"] = stage_params.get("top_p", 0.95)
        
        # Override with any explicitly provided kwargs
        params.update(kwargs)
        
        return params 