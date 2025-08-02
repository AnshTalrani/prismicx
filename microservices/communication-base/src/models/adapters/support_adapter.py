"""
Support Adapter

Implements an adapter that enhances language models with customer support and
problem-solving capabilities. This adapter improves empathy, solution-finding,
and customer satisfaction in support interactions.

Basic usage:
    adapter = SupportAdapter("support", path="/path/to/weights")
    adapter.initialize()
    adapter.apply_to_model(model, {"empathy_level": 0.8})
"""

import os
import logging
import json
from typing import Dict, Any, Optional, List, Union, Set

from src.models.adapters.base_adapter import BaseAdapter, AdapterError


class SupportAdapterError(AdapterError):
    """Exception raised for support adapter-specific errors."""
    pass


class SupportAdapter(BaseAdapter):
    """
    Adapter that enhances language models with customer support capabilities.
    
    Implements several key support techniques:
    1. Empathy enhancement - Recognizes and responds to emotional cues
    2. Problem classification - Identifies issue types and categorizes problems
    3. Solution recommendation - Provides relevant solutions based on problem type
    4. Customer satisfaction focus - Ensures resolution and satisfaction
    5. Escalation awareness - Recognizes when to escalate issues to humans
    """
    
    DEFAULT_CONFIG = {
        "empathy_level": 0.7,  # Level of empathetic responses (0.0-1.0)
        "techniques": {
            "active_listening": {
                "enabled": True,
                "strength": 0.8
            },
            "problem_solving": {
                "enabled": True,
                "strength": 0.7
            },
            "emotional_intelligence": {
                "enabled": True,
                "strength": 0.7
            },
            "clarity_enhancement": {
                "enabled": True,
                "strength": 0.6
            },
            "follow_up_questions": {
                "enabled": True,
                "strength": 0.5
            }
        },
        "tone": "supportive",  # supportive, professional, friendly, technical
        "knowledge_base": "general"  # Can be updated with domain-specific knowledge
    }
    
    def __init__(self, name: str = "support", 
                 path: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the support adapter.
        
        Args:
            name: The name of this adapter (default: "support")
            path: Optional path to adapter files/weights
            config: Optional configuration parameters
        """
        super().__init__(
            name=name, 
            adapter_type="support",
            path=path,
            config=config or {}
        )
        
        # Merge provided config with defaults
        self._merge_config_with_defaults()
        
        # State tracking
        self.models_applied_to = {}  # model_id -> config applied
        self.detected_emotions: Set[str] = set()  # Track emotions detected in conversation
        self.identified_issues: List[Dict[str, Any]] = []  # Track identified issues
        
    def _initialize(self) -> None:
        """
        Initialize the support adapter.
        
        Loads required resources and validates configuration.
        """
        # Validate configuration
        self._validate_config()
        
        # Load support patterns and templates
        patterns_path = os.path.join(self.path, "support_patterns.json") if self.path else None
        if patterns_path and os.path.exists(patterns_path):
            try:
                with open(patterns_path, "r") as f:
                    self.patterns = json.load(f)
                self.logger.info(f"Loaded support patterns from {patterns_path}")
            except Exception as e:
                self.logger.warning(f"Failed to load support patterns: {e}")
                self.patterns = self._get_default_patterns()
        else:
            self.patterns = self._get_default_patterns()
            
        # Load knowledge bases if available
        kb_path = os.path.join(self.path, "knowledge_bases") if self.path else None
        self.knowledge_bases = {}
        if kb_path and os.path.exists(kb_path):
            try:
                for filename in os.listdir(kb_path):
                    if filename.endswith(".json"):
                        kb_name = filename.replace(".json", "")
                        with open(os.path.join(kb_path, filename), "r") as f:
                            self.knowledge_bases[kb_name] = json.load(f)
                self.logger.info(f"Loaded {len(self.knowledge_bases)} knowledge bases")
            except Exception as e:
                self.logger.warning(f"Failed to load knowledge bases: {e}")
    
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
                self.logger.warning(f"Failed to load weights: {e}")
    
    def _unload(self) -> None:
        """Unload resources to free memory."""
        # Clear any loaded resources
        self.patterns = None
        self.knowledge_bases = {}
        
    def apply_to_model(self, model: Any, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Apply the support adapter to a model.
        
        This implementation works by:
        1. Setting appropriate hooks in the model generation pipeline
        2. Configuring the adapter with the provided config (merged with defaults)
        
        Args:
            model: The language model to apply the adapter to
            config: Optional configuration overrides
            
        Returns:
            True if successfully applied, False otherwise
            
        Raises:
            SupportAdapterError: If application fails
        """
        if not self._is_loaded and not self.load():
            raise SupportAdapterError(f"Cannot apply unloaded adapter: {self.name}")
        
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
                    self._create_support_logits_processor(apply_config)
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
            raise SupportAdapterError(f"Failed to apply adapter: {e}")
    
    def remove_from_model(self, model: Any) -> bool:
        """
        Remove the support adapter from a model.
        
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
    
    def set_knowledge_base(self, kb_name: str) -> bool:
        """
        Set the knowledge base for the support adapter.
        
        This loads domain-specific information and solutions.
        
        Args:
            kb_name: The name of the knowledge base 
                     (e.g., "software", "hardware", "billing")
            
        Returns:
            True if successful, False if knowledge base not available
        """
        if kb_name in self.knowledge_bases:
            self.config["knowledge_base"] = kb_name
            self.logger.info(f"Set knowledge base to {kb_name}")
            return True
        elif kb_name == "general":
            self.config["knowledge_base"] = "general"
            self.logger.info("Reset knowledge base to general")
            return True
        else:
            self.logger.warning(f"Knowledge base '{kb_name}' not found")
            return False
    
    def analyze_user_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze a user query to extract emotions and categorize issues.
        
        This is a helper method that can be used to enhance support
        responses by tracking the emotional content and problems.
        
        Args:
            query: The user's query text
            
        Returns:
            Dict containing analysis results (emotions, issue types, etc.)
        """
        # This is a placeholder implementation that would be replaced
        # with actual NLP-based emotion and intent recognition
        
        # Check for emotional indicators
        emotions = set()
        for emotion, indicators in self.patterns.get("emotions", {}).items():
            if any(indicator.lower() in query.lower() for indicator in indicators):
                emotions.add(emotion)
        
        # Check for issue types
        issue_types = []
        for issue_type, keywords in self.patterns.get("issue_types", {}).items():
            if any(keyword.lower() in query.lower() for keyword in keywords):
                issue_types.append(issue_type)
                
        # Update the adapter's state
        self.detected_emotions.update(emotions)
        
        if issue_types:
            self.identified_issues.append({
                "query": query,
                "types": issue_types,
                "emotions": list(emotions)
            })
            
        return {
            "emotions": list(emotions),
            "issue_types": issue_types,
            "urgency": self._calculate_urgency(emotions, issue_types, query)
        }
    
    def get_detected_emotions(self) -> List[str]:
        """
        Get the emotions detected in the conversation so far.
        
        Returns:
            List of detected emotion names
        """
        return list(self.detected_emotions)
    
    def get_identified_issues(self) -> List[Dict[str, Any]]:
        """
        Get the issues identified in the conversation so far.
        
        Returns:
            List of issue dictionaries with types and emotions
        """
        return self.identified_issues.copy()
    
    def clear_conversation_state(self) -> None:
        """
        Clear the adapter's conversation state.
        
        This should be called at the beginning of a new conversation.
        """
        self.detected_emotions.clear()
        self.identified_issues.clear()
        self.logger.info("Cleared conversation state")
    
    def get_supported_knowledge_bases(self) -> List[str]:
        """
        Get list of available knowledge bases.
        
        Returns:
            List of knowledge base names
        """
        return list(self.knowledge_bases.keys())
    
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
            SupportAdapterError: If the configuration is invalid
        """
        # Validate empathy level is between 0 and 1
        empathy = self.config.get("empathy_level", 0.7)
        if not isinstance(empathy, (float, int)) or empathy < 0 or empathy > 1:
            raise SupportAdapterError(f"Invalid empathy level: {empathy}. Must be between 0 and 1")
            
        # Validate techniques configuration
        techniques = self.config.get("techniques", {})
        if not isinstance(techniques, dict):
            raise SupportAdapterError(f"Invalid techniques configuration: {techniques}")
            
        for technique, settings in techniques.items():
            if not isinstance(settings, dict):
                raise SupportAdapterError(f"Invalid settings for technique {technique}: {settings}")
                
            if "enabled" in settings and not isinstance(settings["enabled"], bool):
                raise SupportAdapterError(f"Invalid 'enabled' value for technique {technique}: {settings['enabled']}")
                
            if "strength" in settings:
                strength = settings["strength"]
                if not isinstance(strength, (float, int)) or strength < 0 or strength > 1:
                    raise SupportAdapterError(f"Invalid strength value for technique {technique}: {strength}")
                    
        # Validate tone
        valid_tones = ["supportive", "professional", "friendly", "technical", "empathetic"]
        tone = self.config.get("tone", "supportive")
        if tone not in valid_tones:
            self.logger.warning(f"Unknown tone: {tone}. Using default 'supportive'")
            self.config["tone"] = "supportive"
    
    def _get_default_patterns(self) -> Dict[str, Any]:
        """
        Get the default support patterns for different techniques.
        
        Returns:
            Dictionary containing default support patterns
        """
        return {
            "emotions": {
                "frustration": [
                    "frustrated", "annoying", "ridiculous", "waste of time",
                    "not working", "doesn't work", "broken", "useless"
                ],
                "confusion": [
                    "confused", "don't understand", "unclear", "how do I",
                    "can't figure out", "lost", "no idea", "what does this mean"
                ],
                "anger": [
                    "angry", "upset", "terrible", "awful", "worst",
                    "horrible", "unacceptable", "never", "always"
                ],
                "satisfaction": [
                    "happy", "glad", "works", "thank", "great",
                    "appreciate", "solved", "fixed", "excellent"
                ],
                "urgency": [
                    "immediately", "urgent", "asap", "emergency", "right now",
                    "critical", "deadline", "soon", "today", "quickly"
                ],
                "disappointment": [
                    "disappointed", "let down", "expected better", "not what I hoped",
                    "not good enough", "should be better"
                ]
            },
            "issue_types": {
                "technical_error": [
                    "error", "bug", "crash", "not working", "failed", 
                    "broken", "doesn't work", "problem", "glitch"
                ],
                "account_issue": [
                    "login", "password", "account", "profile", "sign in",
                    "can't access", "reset", "credentials", "username"
                ],
                "billing_inquiry": [
                    "bill", "charge", "payment", "refund", "subscription",
                    "price", "cost", "paid", "invoice", "credit"
                ],
                "feature_request": [
                    "feature", "add", "missing", "wish", "should have",
                    "would be nice", "recommend adding", "suggestion"
                ],
                "how_to": [
                    "how do I", "how to", "can I", "is it possible", "want to",
                    "trying to", "need to", "help me", "guide", "tutorial"
                ],
                "connectivity": [
                    "connection", "offline", "online", "internet", "connect",
                    "network", "wifi", "disconnected", "sync"
                ]
            },
            "resolution_phrases": {
                "empathy": [
                    "I understand how {x} that must be",
                    "I'm sorry you're experiencing {x}",
                    "That sounds {x}, let me help you with that",
                    "I can see why that would be {x}"
                ],
                "reassurance": [
                    "We'll get this sorted out for you",
                    "I'm here to help you resolve this",
                    "Let's work through this together",
                    "This is something we can definitely fix"
                ],
                "clarification": [
                    "Just to make sure I understand correctly, {x}",
                    "Let me confirm if I've understood your concern: {x}",
                    "To clarify, you're saying that {x}"
                ],
                "resolution": [
                    "Here's what you can do to fix this: {x}",
                    "To resolve this issue, please {x}",
                    "The solution is to {x}",
                    "Try following these steps: {x}"
                ],
                "follow_up": [
                    "Is there anything else I can help you with?",
                    "Did that resolve your issue?",
                    "Does that answer your question?",
                    "Let me know if this works for you"
                ]
            },
            "tones": {
                "supportive": {
                    "style": "empathetic and helpful",
                    "phrases": [
                        "I'm here to help you with {x}",
                        "Let's find a solution together for {x}",
                        "I understand your concern about {x}"
                    ]
                },
                "technical": {
                    "style": "precise and informative",
                    "phrases": [
                        "The technical explanation for {x} is {y}",
                        "This issue occurs because {x}",
                        "From a technical perspective, {x}"
                    ]
                },
                "professional": {
                    "style": "formal and efficient",
                    "phrases": [
                        "I'd be happy to assist you with {x}",
                        "We can resolve {x} by {y}",
                        "Our recommendation for {x} would be {y}"
                    ]
                }
            }
        }
    
    def _calculate_urgency(self, emotions: Set[str], issue_types: List[str], query: str) -> float:
        """
        Calculate urgency score based on emotions and issue type.
        
        Args:
            emotions: Set of detected emotions
            issue_types: List of identified issue types
            query: Original query text
            
        Returns:
            Urgency score between 0.0 and 1.0
        """
        urgency = 0.0
        
        # High urgency emotions
        if "anger" in emotions:
            urgency += 0.3
        if "urgency" in emotions:
            urgency += 0.4
        if "frustration" in emotions:
            urgency += 0.2
            
        # Issue type urgency
        urgent_issues = ["technical_error", "connectivity"]
        for issue in urgent_issues:
            if issue in issue_types:
                urgency += 0.2
        
        # Urgency keywords
        urgent_keywords = ["immediately", "urgent", "asap", "emergency", "now", "critical"]
        if any(keyword in query.lower() for keyword in urgent_keywords):
            urgency += 0.3
            
        # Cap at 1.0
        return min(urgency, 1.0)
    
    def _create_support_logits_processor(self, config: Dict[str, Any]) -> Any:
        """
        Create a logits processor that implements support techniques.
        
        This is a placeholder implementation that would be replaced with
        an actual implementation based on the model framework.
        
        Args:
            config: Configuration for the processor
            
        Returns:
            A logits processor object
        """
        # This is just a placeholder - actual implementation would depend on the framework
        class SupportLogitsProcessor:
            def __init__(self, config):
                self.config = config
                self.name = f"{self.name}_processor"
                
            def __call__(self, input_ids, scores):
                # Apply support techniques to the scores
                # Implementation depends on the specific model framework
                return scores
                
        return SupportLogitsProcessor(config)
    
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
        class SupportAdapterModule:
            def __init__(self, config):
                self.config = config
                
            # Additional methods would be implemented based on the framework
                
        return SupportAdapterModule(config)
    
    def _monkey_patch_model(self, model: Any, config: Dict[str, Any]) -> None:
        """
        Monkey patch a model's methods to apply support techniques.
        
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
                # Apply support techniques to the generation process
                result = model._original_methods["generate"](*args, **kwargs)
                # Process the result based on config
                return self._apply_support_techniques(result, config)
                
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
    
    def _apply_support_techniques(self, text: Union[str, List[str]], 
                               config: Dict[str, Any]) -> Union[str, List[str]]:
        """
        Apply support techniques to text.
        
        Args:
            text: The text to process (string or list of strings)
            config: Configuration for the techniques
            
        Returns:
            Processed text with support techniques applied
        """
        # This is a placeholder implementation
        # In a real implementation, this would apply the actual techniques
        # based on the config settings
        
        # Handle list of strings
        if isinstance(text, list):
            return [self._apply_support_techniques(item, config) for item in text]
            
        # Process single string
        return text  # In a real implementation, the text would be modified here 