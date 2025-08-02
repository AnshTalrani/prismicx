"""
Extraction Schema Registry for NLP Processing.

This module provides a central registry for extraction schemas used by the NLP pipeline.
It loads schemas from bot configs, as described in the implementation plan.
"""

import logging
from typing import Dict, Any, Optional, List
import json

from src.config.bot_configs import BOT_CONFIGS
from src.config.config_inheritance import ConfigInheritance

class ExtractionRegistry:
    """
    Central registry for extraction schemas used by the NLP pipeline.
    
    This class manages extraction schemas for different bot types, loading them
    from configuration files and providing access through a unified interface.
    """
    
    def __init__(self):
        """Initialize the extraction registry."""
        self.logger = logging.getLogger(__name__)
        self.config_inheritance = ConfigInheritance()
        self.schemas = {}
        self._load_schemas()
    
    def _load_schemas(self) -> None:
        """
        Load extraction schemas from bot configurations.
        
        This method iterates through available bot types, loads their extraction
        schemas from configuration, and registers them in the central registry.
        """
        for bot_type, config in BOT_CONFIGS.items():
            try:
                # Get NLP config section
                nlp_config = config.get("analysis_config", {}).get("nlp_features", {})
                
                # Get required and optional entity types
                required_entities = nlp_config.get("required", [])
                optional_entities = nlp_config.get("optional", [])
                
                # Create schema for this bot type
                schema = {
                    "entity_types": required_entities + optional_entities,
                    "required": required_entities,
                    "optional": optional_entities,
                    "extraction_patterns": self._load_extraction_patterns(bot_type, config)
                }
                
                # Store schema
                self.schemas[bot_type] = schema
                
                self.logger.info(f"Loaded extraction schema for bot type: {bot_type}")
            except Exception as e:
                self.logger.error(f"Failed to load extraction schema for bot type {bot_type}: {e}")
    
    def _load_extraction_patterns(self, bot_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load extraction patterns for a specific bot type.
        
        This method loads extraction patterns from configuration files or 
        predefined patterns in the configuration.
        
        Args:
            bot_type: Type of bot
            config: Bot configuration
            
        Returns:
            Dictionary of extraction patterns
        """
        patterns = {}
        
        try:
            # Check for patterns in config
            analysis_config = config.get("analysis_config", {})
            
            # Get pattern types based on bot type
            if bot_type == "consultancy":
                pattern_types = analysis_config.get("patterns", {}).get("covert", []) + \
                               analysis_config.get("patterns", {}).get("expert", [])
            elif bot_type == "sales":
                pattern_types = analysis_config.get("patterns", {}).get("sales", []) + \
                               analysis_config.get("patterns", {}).get("campaign", [])
            elif bot_type == "support":
                pattern_types = analysis_config.get("patterns", {}).get("support", []) if \
                               "patterns" in analysis_config else []
            else:
                pattern_types = []
            
            # Load each pattern type
            for pattern_type in pattern_types:
                # Try to load from file if specified
                pattern_path = analysis_config.get("templates", {}).get(pattern_type, {}).get("path", None)
                
                if pattern_path:
                    try:
                        with open(pattern_path, 'r') as f:
                            patterns[pattern_type] = json.load(f)
                    except Exception as e:
                        self.logger.error(f"Failed to load pattern from file {pattern_path}: {e}")
                        # Fall back to default patterns
                        patterns[pattern_type] = self._get_default_patterns(pattern_type)
                else:
                    # Use default patterns
                    patterns[pattern_type] = self._get_default_patterns(pattern_type)
        
        except Exception as e:
            self.logger.error(f"Error loading extraction patterns for {bot_type}: {e}")
        
        return patterns
    
    def _get_default_patterns(self, pattern_type: str) -> Dict[str, Any]:
        """
        Get default patterns for a specific pattern type.
        
        Args:
            pattern_type: Type of pattern
            
        Returns:
            Dictionary of default patterns
        """
        default_patterns = {
            # Covert patterns
            "pacing": {
                "anchoring": [r"as you ([a-z]+)", r"while you ([a-z]+)", r"when you ([a-z]+)"],
                "presuppositions": [r"you (know|understand|realize|see) that", r"it's (clear|obvious|evident) that"]
            },
            "leading": {
                "future_pace": [r"you will (find|discover|see|feel)", r"as you (continue to|begin to)"],
                "embedded_commands": [r"you can (easily|simply|just) ([a-z]+)", r"you might (want to|like to) ([a-z]+)"]
            },
            "embedded": {
                "quotes": [r"'([^']*)'", r"\"([^\"]*)\""],
                "negation": [r"don't (think about|worry about|consider) ([a-z]+)"]
            },
            
            # Expert patterns
            "terminology": {
                "business": [r"ROI", r"KPI", r"revenue stream", r"value proposition"],
                "technical": [r"implementation", r"integration", r"deployment", r"architecture"]
            },
            "frameworks": {
                "business": [r"SWOT", r"Porter's Five Forces", r"PESTEL", r"BCG matrix"],
                "strategy": [r"strategic planning", r"roadmap", r"milestone", r"objective"]
            },
            
            # Sales patterns
            "closing": {
                "assumptive": [r"when you (get|receive|start using)", r"after you (purchase|buy|invest in)"],
                "urgency": [r"limited time", r"special offer", r"exclusive opportunity"]
            },
            "objection_handling": {
                "price": [r"investment", r"value", r"return on investment", r"cost-effective"],
                "timing": [r"perfect timing", r"right moment", r"opportunity cost"]
            },
            
            # Support patterns
            "support": {
                "issue_types": [r"error", r"bug", r"problem", r"isn't working", r"doesn't work"],
                "urgency": [r"urgent", r"critical", r"emergency", r"as soon as possible"]
            }
        }
        
        return default_patterns.get(pattern_type, {})
    
    def get_schema(self, bot_type: str) -> Dict[str, Any]:
        """
        Get the extraction schema for a specific bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            Extraction schema for the specified bot type
        """
        if bot_type not in self.schemas:
            self.logger.warning(f"Extraction schema not found for bot type: {bot_type}")
            return {}
        
        return self.schemas[bot_type]
    
    def get_entity_types(self, bot_type: str) -> List[str]:
        """
        Get entity types for a specific bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            List of entity types
        """
        if bot_type not in self.schemas:
            return []
        
        return self.schemas[bot_type].get("entity_types", [])
    
    def get_required_entities(self, bot_type: str) -> List[str]:
        """
        Get required entity types for a specific bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            List of required entity types
        """
        if bot_type not in self.schemas:
            return []
        
        return self.schemas[bot_type].get("required", [])
    
    def get_optional_entities(self, bot_type: str) -> List[str]:
        """
        Get optional entity types for a specific bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            List of optional entity types
        """
        if bot_type not in self.schemas:
            return []
        
        return self.schemas[bot_type].get("optional", [])
    
    def get_extraction_patterns(self, bot_type: str, pattern_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get extraction patterns for a specific bot type and pattern type.
        
        Args:
            bot_type: Type of bot
            pattern_type: Optional type of pattern
            
        Returns:
            Dictionary of extraction patterns
        """
        if bot_type not in self.schemas:
            return {}
        
        patterns = self.schemas[bot_type].get("extraction_patterns", {})
        
        if pattern_type:
            return patterns.get(pattern_type, {})
        
        return patterns


# Create singleton instance
extraction_registry = ExtractionRegistry() 