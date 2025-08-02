"""
Sales Adapter

Implements an adapter that enhances language models with sales and persuasion techniques.
This adapter applies proven sales methodologies to model outputs, helping to improve
conversion rates and customer engagement.

Basic usage:
    adapter = SalesAdapter("sales_expert", path="/path/to/weights")
    adapter.initialize()
    adapter.apply_to_model(model, {"intensity": 0.8})
"""

import os
import logging
import json
from typing import Dict, Any, Optional, List, Union

from src.models.adapters.base_adapter import BaseAdapter, AdapterError


class SalesAdapterError(AdapterError):
    """Exception raised for sales adapter-specific errors."""
    pass


class SalesAdapter(BaseAdapter):
    """
    Adapter that enhances language models with sales and persuasion techniques.
    
    Implements several key sales methodologies:
    1. AIDA - Attention, Interest, Desire, Action
    2. FAB - Features, Advantages, Benefits
    3. Value-based selling - Emphasizing value over price
    4. Objection handling - Addressing common customer concerns
    5. Social proof - Incorporating testimonials and success stories
    """
    
    DEFAULT_CONFIG = {
        "intensity": 0.6,  # Overall intensity of sales techniques (0.0-1.0)
        "techniques": {
            "aida": {
                "enabled": True,
                "strength": 0.7
            },
            "fab": {
                "enabled": True,
                "strength": 0.8
            },
            "value_based": {
                "enabled": True,
                "strength": 0.6
            },
            "objection_handling": {
                "enabled": True,
                "strength": 0.5
            },
            "social_proof": {
                "enabled": True,
                "strength": 0.7
            }
        },
        "tone": "consultative",  # consultative, assertive, friendly
        "target_audience": "general"  # can be customized per industry
    }
    
    def __init__(self, name: str = "sales", 
                 path: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the sales adapter.
        
        Args:
            name: The name of this adapter (default: "sales")
            path: Optional path to adapter files/weights
            config: Optional configuration parameters
        """
        super().__init__(
            name=name, 
            adapter_type="sales",
            path=path,
            config=config or {}
        )
        
        # Merge provided config with defaults
        self._merge_config_with_defaults()
        
        # State tracking
        self.models_applied_to = {}  # model_id -> config applied
        
    def _initialize(self) -> None:
        """
        Initialize the sales adapter.
        
        Loads required resources and validates configuration.
        """
        # Validate configuration
        self._validate_config()
        
        # Load sales patterns and templates if exists
        patterns_path = os.path.join(self.path, "sales_patterns.json") if self.path else None
        if patterns_path and os.path.exists(patterns_path):
            try:
                with open(patterns_path, "r") as f:
                    self.patterns = json.load(f)
                self.logger.info(f"Loaded sales patterns from {patterns_path}")
            except Exception as e:
                self.logger.warning(f"Failed to load sales patterns from {patterns_path}: {e}")
                self.patterns = self._get_default_patterns()
        else:
            self.patterns = self._get_default_patterns()
            
        # Load industry-specific data if available
        industry_path = os.path.join(self.path, "industries") if self.path else None
        self.industry_data = {}
        if industry_path and os.path.exists(industry_path):
            try:
                for filename in os.listdir(industry_path):
                    if filename.endswith(".json"):
                        industry_name = filename.replace(".json", "")
                        with open(os.path.join(industry_path, filename), "r") as f:
                            self.industry_data[industry_name] = json.load(f)
                self.logger.info(f"Loaded data for {len(self.industry_data)} industries")
            except Exception as e:
                self.logger.warning(f"Failed to load industry data: {e}")
    
    def _load(self) -> None:
        """Load additional resources if needed."""
        # If the adapter has specific weights, load them here
        weights_path = os.path.join(self.path, "weights") if self.path else None
        if weights_path and os.path.exists(weights_path):
            try:
                # Load weights (implementation depends on the actual framework used)
                self.logger.info(f"Loading weights from {weights_path}")
                # self.weights = load_weights(weights_path)  # Placeholder
            except Exception as e:
                self.logger.warning(f"Failed to load weights from {weights_path}: {e}")
    
    def _unload(self) -> None:
        """Unload resources to free memory."""
        # Clear any loaded resources
        self.patterns = None
        self.industry_data = {}
        
    def apply_to_model(self, model: Any, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Apply the sales adapter to a model.
        
        This implementation works by:
        1. Setting appropriate hooks in the model generation pipeline
        2. Configuring the adapter with the provided config (merged with defaults)
        
        Args:
            model: The language model to apply the adapter to
            config: Optional configuration overrides
            
        Returns:
            True if successfully applied, False otherwise
            
        Raises:
            SalesAdapterError: If application fails
        """
        if not self._is_loaded and not self.load():
            raise SalesAdapterError(f"Cannot apply unloaded adapter: {self.name}")
        
        # Get model ID for tracking
        model_id = self._get_model_id(model)
        
        # Merge provided config with the adapter's config
        apply_config = self._merge_apply_config(config)
        
        try:
            # The specific implementation depends on the model framework
            # Here's a general approach that works with common frameworks:
            
            # 1. For transformers models with PEFT support
            if hasattr(model, "peft_config") and hasattr(model, "load_adapter"):
                if self.path:
                    model.load_adapter(self.path)
                # Set the adapter as active
                if hasattr(model, "set_adapter"):
                    model.set_adapter(self.name)
                    
            # 2. For models with generation hooks
            elif hasattr(model, "generation_config") and hasattr(model.generation_config, "logits_processor"):
                # Add our custom logits processor
                model.generation_config.logits_processor.append(
                    self._create_sales_logits_processor(apply_config)
                )
                
            # 3. For custom model implementations
            elif hasattr(model, "add_adapter"):
                model.add_adapter(self.name, self._create_adapter_module(apply_config))
                
            # 4. Generic approach - monkey patch the forward/generate method
            else:
                self._monkey_patch_model(model, apply_config)
            
            # Track this model as having the adapter applied
            self.models_applied_to[model_id] = apply_config
            
            self.logger.info(f"Applied {self.name} adapter to model {model_id} with config: {apply_config}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply {self.name} adapter to model: {e}")
            raise SalesAdapterError(f"Failed to apply adapter: {e}")
    
    def remove_from_model(self, model: Any) -> bool:
        """
        Remove the sales adapter from a model.
        
        Args:
            model: The model to remove the adapter from
            
        Returns:
            True if successfully removed, False otherwise
        """
        # Get model ID for tracking
        model_id = self._get_model_id(model)
        
        # Check if this adapter is applied to the model
        if model_id not in self.models_applied_to:
            self.logger.warning(f"Adapter {self.name} not applied to model {model_id}")
            return True
            
        try:
            # The specific implementation depends on the model framework
            # Here's a general approach that works with common frameworks:
            
            # 1. For transformers models with PEFT support
            if hasattr(model, "disable_adapter"):
                model.disable_adapter()
                
            # 2. For models with generation hooks
            elif hasattr(model, "generation_config") and hasattr(model.generation_config, "logits_processor"):
                # Remove our custom logits processor
                model.generation_config.logits_processor = [
                    processor for processor in model.generation_config.logits_processors
                    if getattr(processor, "name", None) != f"{self.name}_processor"
                ]
                
            # 3. For custom model implementations
            elif hasattr(model, "remove_adapter"):
                model.remove_adapter(self.name)
                
            # 4. Generic approach - restore original methods
            else:
                self._restore_monkey_patched_model(model)
            
            # Remove from tracking
            del self.models_applied_to[model_id]
            
            self.logger.info(f"Removed {self.name} adapter from model {model_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove {self.name} adapter from model: {e}")
            return False
    
    def set_target_audience(self, industry: str) -> bool:
        """
        Set the target audience/industry for the sales adapter.
        
        This loads industry-specific terminology, value propositions,
        and common objections.
        
        Args:
            industry: The target industry (e.g., "healthcare", "finance")
            
        Returns:
            True if successful, False if industry data not available
        """
        if industry in self.industry_data:
            self.config["target_audience"] = industry
            self.logger.info(f"Set target audience to {industry}")
            return True
        elif industry == "general":
            self.config["target_audience"] = "general"
            self.logger.info("Reset target audience to general")
            return True
        else:
            self.logger.warning(f"Industry data for '{industry}' not found")
            return False
            
    def get_supported_industries(self) -> List[str]:
        """
        Get list of industries with specialized data available.
        
        Returns:
            List of industry names
        """
        return list(self.industry_data.keys())
    
    def _get_model_id(self, model: Any) -> str:
        """Get a unique identifier for a model."""
        # Use model's name attribute if available
        if hasattr(model, "name"):
            return str(model.name)
            
        # Use model's config name if available (transformers models)
        if hasattr(model, "config") and hasattr(model.config, "name_or_path"):
            return str(model.config.name_or_path)
            
        # Fall back to object ID
        return str(id(model))
    
    def _merge_config_with_defaults(self) -> None:
        """Merge the provided config with the default config."""
        merged_config = self.DEFAULT_CONFIG.copy()
        
        for key, value in self.config.items():
            if key in merged_config and isinstance(merged_config[key], dict) and isinstance(value, dict):
                # Recursively merge nested dicts
                for nested_key, nested_value in value.items():
                    merged_config[key][nested_key] = nested_value
            else:
                # For non-dict values or keys not in default, just override/add
                merged_config[key] = value
                
        self.config = merged_config
    
    def _merge_apply_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge the provided application config with the adapter's config.
        
        Args:
            config: The config to merge with the adapter's config
            
        Returns:
            The merged configuration dictionary
        """
        if not config:
            return self.config.copy()
            
        merged = self.config.copy()
        
        for key, value in config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # Recursively merge nested dicts
                for nested_key, nested_value in value.items():
                    merged[key][nested_key] = nested_value
            else:
                # For non-dict values or keys not in default, just override/add
                merged[key] = value
                
        return merged
    
    def _validate_config(self) -> None:
        """
        Validate the adapter configuration.
        
        Raises:
            SalesAdapterError: If the configuration is invalid
        """
        # Validate intensity is between 0 and 1
        intensity = self.config.get("intensity", 0.6)
        if not isinstance(intensity, (float, int)) or intensity < 0 or intensity > 1:
            raise SalesAdapterError(f"Invalid intensity value: {intensity}. Must be between 0 and 1")
            
        # Validate techniques configuration
        techniques = self.config.get("techniques", {})
        if not isinstance(techniques, dict):
            raise SalesAdapterError(f"Invalid techniques configuration: {techniques}")
            
        for technique, settings in techniques.items():
            if not isinstance(settings, dict):
                raise SalesAdapterError(f"Invalid settings for technique {technique}: {settings}")
                
            if "enabled" in settings and not isinstance(settings["enabled"], bool):
                raise SalesAdapterError(f"Invalid 'enabled' value for technique {technique}: {settings['enabled']}")
                
            if "strength" in settings:
                strength = settings["strength"]
                if not isinstance(strength, (float, int)) or strength < 0 or strength > 1:
                    raise SalesAdapterError(f"Invalid strength value for technique {technique}: {strength}")
                    
        # Validate tone
        valid_tones = ["consultative", "assertive", "friendly", "professional", "casual"]
        tone = self.config.get("tone", "consultative")
        if tone not in valid_tones:
            self.logger.warning(f"Unknown tone: {tone}. Using default 'consultative'")
            self.config["tone"] = "consultative"
    
    def _get_default_patterns(self) -> Dict[str, Any]:
        """
        Get the default sales patterns for different techniques.
        
        Returns:
            Dictionary containing default sales patterns
        """
        return {
            "aida": {
                "attention": [
                    "Did you know that {x}?",
                    "Imagine if you could {x}",
                    "{x} is changing the way businesses operate"
                ],
                "interest": [
                    "This matters because {x}",
                    "The impact of {x} on your business",
                    "You'll find that {x} directly affects your {y}"
                ],
                "desire": [
                    "By implementing {x}, you'll experience {y}",
                    "Clients who use {x} have seen {y} improvement",
                    "The real value of {x} is in how it {y}"
                ],
                "action": [
                    "Ready to get started with {x}?",
                    "Let me show you how to implement {x}",
                    "The next step is to {x}"
                ]
            },
            "fab": {
                "features": [
                    "{x} includes {y}",
                    "One key feature of {x} is {y}",
                    "{x} is designed with {y}"
                ],
                "advantages": [
                    "Unlike alternatives, {x} provides {y}",
                    "What makes {x} stand out is {y}",
                    "The advantage of {x} is {y}"
                ],
                "benefits": [
                    "This means you'll {x}",
                    "The bottom line impact is {x}",
                    "This translates to {x} for your business"
                ]
            },
            "objection_handling": {
                "price": [
                    "While considering the investment, think about {x}",
                    "Let's look at the value rather than just the cost: {x}",
                    "When we break it down, the cost is actually {x}"
                ],
                "timing": [
                    "Actually, now is an ideal time because {x}",
                    "Delaying could result in {x}",
                    "By starting now, you gain {x}"
                ],
                "competition": [
                    "What sets us apart is {x}",
                    "Unlike our competitors, we {x}",
                    "Our approach differs in that {x}"
                ],
                "need": [
                    "You mentioned {x}, which is exactly why {y}",
                    "Based on your situation with {x}, you'd benefit from {y}",
                    "Organizations like yours use this to solve {x}"
                ]
            },
            "social_proof": [
                "Clients like {x} have seen {y} results",
                "In a similar situation, {x} was able to {y}",
                "After implementing this, {x} reported {y}"
            ],
            "tones": {
                "consultative": {
                    "style": "thoughtful and solution-focused",
                    "questions": [
                        "What challenges are you facing with {x}?",
                        "How is {x} affecting your goals?",
                        "What would success look like for {x}?"
                    ]
                },
                "assertive": {
                    "style": "confident and direct",
                    "statements": [
                        "You need {x} to achieve {y}",
                        "The best approach is clearly {x}",
                        "{x} is the solution you're looking for"
                    ]
                },
                "friendly": {
                    "style": "approachable and conversational",
                    "phrases": [
                        "I think you'll really like how {x}",
                        "Many people find that {x} makes a big difference",
                        "Let's explore how {x} might help you"
                    ]
                }
            }
        }
    
    def _create_sales_logits_processor(self, config: Dict[str, Any]) -> Any:
        """
        Create a logits processor that implements sales techniques.
        
        This is a placeholder implementation that would be replaced with
        an actual implementation based on the model framework.
        
        Args:
            config: Configuration for the processor
            
        Returns:
            A logits processor object
        """
        # This is just a placeholder - actual implementation would depend on the framework
        class SalesLogitsProcessor:
            def __init__(self, config):
                self.config = config
                self.name = f"{self.name}_processor"
                
            def __call__(self, input_ids, scores):
                # Apply sales techniques to the scores
                # Implementation depends on the specific model framework
                return scores
                
        return SalesLogitsProcessor(config)
    
    def _create_adapter_module(self, config: Dict[str, Any]) -> Any:
        """
        Create an adapter module for custom model implementations.
        
        This is a placeholder implementation that would be replaced with
        an actual implementation based on the model framework.
        
        Args:
            config: Configuration for the adapter module
            
        Returns:
            An adapter module object
        """
        # This is just a placeholder - actual implementation would depend on the framework
        class SalesAdapterModule:
            def __init__(self, config):
                self.config = config
                
            # Additional methods would be implemented based on the framework
                
        return SalesAdapterModule(config)
    
    def _monkey_patch_model(self, model: Any, config: Dict[str, Any]) -> None:
        """
        Monkey patch a model's methods to apply sales techniques.
        
        This is a generic approach that works when no framework-specific
        integration is available.
        
        Args:
            model: The model to patch
            config: Configuration for the patching
        """
        # Store original methods for later restoration
        if not hasattr(model, "_original_methods"):
            model._original_methods = {}
            
        # Patch the generate method if it exists
        if hasattr(model, "generate") and "generate" not in model._original_methods:
            model._original_methods["generate"] = model.generate
            
            def patched_generate(*args, **kwargs):
                # Apply sales techniques to the generation process
                result = model._original_methods["generate"](*args, **kwargs)
                # Process the result based on config
                return self._apply_sales_techniques(result, config)
                
            model.generate = patched_generate
            
        # Patch other methods as needed
        # (implementation depends on the specific model)
    
    def _restore_monkey_patched_model(self, model: Any) -> None:
        """
        Restore a model's original methods after removing the adapter.
        
        Args:
            model: The model to restore
        """
        if hasattr(model, "_original_methods"):
            for method_name, original_method in model._original_methods.items():
                setattr(model, method_name, original_method)
            
            del model._original_methods
    
    def _apply_sales_techniques(self, text: Union[str, List[str]], 
                              config: Dict[str, Any]) -> Union[str, List[str]]:
        """
        Apply sales techniques to text.
        
        Args:
            text: The text to process (string or list of strings)
            config: Configuration for the techniques
            
        Returns:
            Processed text with sales techniques applied
        """
        # This is a placeholder implementation
        # In a real implementation, this would apply the actual techniques
        # based on the config settings
        
        # Handle list of strings
        if isinstance(text, list):
            return [self._apply_sales_techniques(item, config) for item in text]
            
        # Process single string
        return text  # In a real implementation, the text would be modified here 