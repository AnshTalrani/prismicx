"""
Hypnosis Adapter

Implements an adapter that applies hypnosis and persuasion techniques to language models.
This adapter enhances responses with subtle persuasive patterns and mirroring techniques.

Basic usage:
    adapter = HypnosisAdapter("hypnosis", path="/path/to/weights")
    adapter.initialize()
    adapter.apply_to_model(model, {"intensity": 0.7})
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union
import json

from src.models.adapters.base_adapter import BaseAdapter, AdapterError


class HypnosisAdapterError(AdapterError):
    """Exception raised for hypnosis adapter-specific errors."""
    pass


class HypnosisAdapter(BaseAdapter):
    """
    Adapter that applies hypnosis and persuasion techniques to language models.
    
    Implements three main techniques:
    1. Covert commands embedding - subtle embedded directives
    2. Pacing and leading - matching then guiding language patterns
    3. User vocabulary mirroring - adapts to user's speech patterns
    """
    
    DEFAULT_CONFIG = {
        "intensity": 0.5,  # Overall intensity of hypnosis techniques (0.0-1.0)
        "techniques": {
            "covert_commands": {
                "enabled": True,
                "strength": 0.6
            },
            "pacing_leading": {
                "enabled": True,
                "strength": 0.5
            },
            "vocabulary_mirroring": {
                "enabled": True,
                "strength": 0.7
            }
        },
        "persona": "friendly_expert"  # Type of persona to adopt
    }
    
    def __init__(self, name: str = "hypnosis", 
                 path: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the hypnosis adapter.
        
        Args:
            name: The name of this adapter (default: "hypnosis")
            path: Optional path to adapter files/weights
            config: Optional configuration parameters
        """
        super().__init__(
            name=name, 
            adapter_type="persuasion",
            path=path,
            config=config or {}
        )
        
        # Merge provided config with defaults
        self._merge_config_with_defaults()
        
        # State tracking
        self.models_applied_to = {}  # model_id -> config applied
        
    def _initialize(self) -> None:
        """
        Initialize the hypnosis adapter.
        
        Loads required resources and validates configuration.
        """
        # Validate configuration
        self._validate_config()
        
        # Load patterns file if exists
        patterns_path = os.path.join(self.path, "patterns.json") if self.path else None
        if patterns_path and os.path.exists(patterns_path):
            try:
                with open(patterns_path, "r") as f:
                    self.patterns = json.load(f)
                self.logger.info(f"Loaded patterns from {patterns_path}")
            except Exception as e:
                self.logger.warning(f"Failed to load patterns from {patterns_path}: {e}")
                self.patterns = self._get_default_patterns()
        else:
            self.patterns = self._get_default_patterns()
    
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
        
    def apply_to_model(self, model: Any, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Apply the hypnosis adapter to a model.
        
        This implementation works by:
        1. Setting appropriate hooks in the model generation pipeline
        2. Configuring the adapter with the provided config (merged with defaults)
        
        Args:
            model: The language model to apply the adapter to
            config: Optional configuration overrides
            
        Returns:
            True if successfully applied, False otherwise
            
        Raises:
            HypnosisAdapterError: If application fails
        """
        if not self._is_loaded and not self.load():
            raise HypnosisAdapterError(f"Cannot apply unloaded adapter: {self.name}")
        
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
                    self._create_hypnosis_logits_processor(apply_config)
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
            raise HypnosisAdapterError(f"Failed to apply adapter: {e}")
    
    def remove_from_model(self, model: Any) -> bool:
        """
        Remove the hypnosis adapter from a model.
        
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
            HypnosisAdapterError: If the configuration is invalid
        """
        # Validate intensity is between 0 and 1
        intensity = self.config.get("intensity", 0.5)
        if not isinstance(intensity, (float, int)) or intensity < 0 or intensity > 1:
            raise HypnosisAdapterError(f"Invalid intensity value: {intensity}. Must be between 0 and 1")
            
        # Validate techniques configuration
        techniques = self.config.get("techniques", {})
        if not isinstance(techniques, dict):
            raise HypnosisAdapterError(f"Invalid techniques configuration: {techniques}")
            
        for technique, settings in techniques.items():
            if not isinstance(settings, dict):
                raise HypnosisAdapterError(f"Invalid settings for technique {technique}: {settings}")
                
            if "enabled" in settings and not isinstance(settings["enabled"], bool):
                raise HypnosisAdapterError(f"Invalid 'enabled' value for technique {technique}: {settings['enabled']}")
                
            if "strength" in settings:
                strength = settings["strength"]
                if not isinstance(strength, (float, int)) or strength < 0 or strength > 1:
                    raise HypnosisAdapterError(f"Invalid strength value for technique {technique}: {strength}")
    
    def _get_default_patterns(self) -> Dict[str, Any]:
        """
        Get the default language patterns for hypnosis techniques.
        
        Returns:
            Dictionary containing default patterns
        """
        return {
            "covert_commands": [
                "consider {x}",
                "imagine {x}",
                "as you {x}",
                "you might find yourself {x}",
                "you'll notice {x}"
            ],
            "pacing_phrases": [
                "and as you're {x}",
                "while you're {x}",
                "because you're {x}",
                "since you've {x}"
            ],
            "leading_phrases": [
                "which means {x}",
                "and that leads to {x}",
                "naturally resulting in {x}",
                "creating a sense of {x}"
            ],
            "personas": {
                "friendly_expert": {
                    "style": "warm yet authoritative",
                    "tone": "conversational but knowledgeable"
                },
                "trusted_advisor": {
                    "style": "professional and reassuring",
                    "tone": "calm and confident"
                },
                "supportive_guide": {
                    "style": "encouraging and positive",
                    "tone": "enthusiastic but measured"
                }
            }
        }
    
    def _create_hypnosis_logits_processor(self, config: Dict[str, Any]) -> Any:
        """
        Create a logits processor that implements hypnosis techniques.
        
        This is a placeholder implementation that would be replaced with
        an actual implementation based on the model framework.
        
        Args:
            config: Configuration for the processor
            
        Returns:
            A logits processor object
        """
        # This is just a placeholder - actual implementation would depend on the framework
        class HypnosisLogitsProcessor:
            def __init__(self, config):
                self.config = config
                self.name = f"{self.name}_processor"
                
            def __call__(self, input_ids, scores):
                # Apply hypnosis techniques to the scores
                # Implementation depends on the specific model framework
                return scores
                
        return HypnosisLogitsProcessor(config)
    
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
        class HypnosisAdapterModule:
            def __init__(self, config):
                self.config = config
                
            # Additional methods would be implemented based on the framework
                
        return HypnosisAdapterModule(config)
    
    def _monkey_patch_model(self, model: Any, config: Dict[str, Any]) -> None:
        """
        Monkey patch a model's methods to apply hypnosis techniques.
        
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
                # Apply hypnosis techniques to the generation process
                result = model._original_methods["generate"](*args, **kwargs)
                # Process the result based on config
                return self._apply_hypnosis_techniques(result, config)
                
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
    
    def _apply_hypnosis_techniques(self, text: Union[str, List[str]], 
                                  config: Dict[str, Any]) -> Union[str, List[str]]:
        """
        Apply hypnosis techniques to text.
        
        Args:
            text: The text to process (string or list of strings)
            config: Configuration for the techniques
            
        Returns:
            Processed text with hypnosis techniques applied
        """
        # This is a placeholder implementation
        # In a real implementation, this would apply the actual techniques
        # based on the config settings
        
        # Handle list of strings
        if isinstance(text, list):
            return [self._apply_hypnosis_techniques(item, config) for item in text]
            
        # Process single string
        return text  # In a real implementation, the text would be modified here 