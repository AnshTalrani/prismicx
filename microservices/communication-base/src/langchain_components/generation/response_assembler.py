"""
Response assembler for integrating multiple components to produce enhanced responses.

This module provides a response assembler that integrates parsed components,
applies enhancements, and formats the final response according to bot-specific
requirements.
"""

import logging
from typing import Dict, Any, List, Optional, Union

class ResponseAssembler:
    """
    Response assembler for integrating multiple components to produce enhanced responses.
    
    This class coordinates the integration of various response components,
    applies enhancements, and produces the final formatted response based on
    bot-specific configurations.
    """
    
    def __init__(
        self,
        config_integration: Any = None,
        llm: Any = None,
        entity_parser: Any = None,
        action_parser: Any = None,
        confidence_parser: Any = None,
        enhancers: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize response assembler.
        
        Args:
            config_integration: Integration with the config system
            llm: Language model for dynamically enhancing responses
            entity_parser: Parser for extracting entities
            action_parser: Parser for extracting actions
            confidence_parser: Parser for assessing confidence
            enhancers: Dictionary of enhancement components
        """
        self.config_integration = config_integration
        self.llm = llm
        self.entity_parser = entity_parser
        self.action_parser = action_parser
        self.confidence_parser = confidence_parser
        self.enhancers = enhancers or {}
        self.logger = logging.getLogger(__name__)
    
    def assemble_response(
        self,
        original_response: str,
        bot_type: str,
        context: Optional[Dict[str, Any]] = None,
        enhancement_options: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        """
        Assemble the complete enhanced response.
        
        Args:
            original_response: Original LLM response
            bot_type: Type of bot
            context: Additional context for enhancements
            enhancement_options: Options for which enhancements to apply
            
        Returns:
            Assembled response with additional components
        """
        context = context or {}
        enhancement_options = enhancement_options or {}
        
        # Get bot-specific enhancement configuration
        enhancement_config = self._get_enhancement_config(bot_type)
        
        # Merge provided options with config
        for option, enabled in enhancement_config.get("options", {}).items():
            if option not in enhancement_options:
                enhancement_options[option] = enabled
        
        # Initialize result with original response
        result = {
            "original_response": original_response,
            "enhanced_response": original_response,
            "metadata": {}
        }
        
        # Parse components from response
        parsed_components = self._parse_components(original_response, bot_type, enhancement_options)
        result.update(parsed_components)
        
        # Apply enhancements
        enhanced_response = self._apply_enhancements(
            original_response,
            bot_type,
            parsed_components,
            context,
            enhancement_options
        )
        result["enhanced_response"] = enhanced_response
        
        # Apply format adapters
        formatted_response = self._apply_format_adapters(
            enhanced_response,
            bot_type,
            parsed_components,
            enhancement_config
        )
        result["formatted_response"] = formatted_response
        
        return result
    
    def _get_enhancement_config(self, bot_type: str) -> Dict[str, Any]:
        """
        Get bot-specific enhancement configuration.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            Enhancement configuration dictionary
        """
        # If no config integration available, return default config
        if not self.config_integration:
            return {
                "options": {
                    "parse_entities": True,
                    "parse_actions": True,
                    "assess_confidence": True,
                    "apply_anti_ai": True
                },
                "format": "default",
                "priority": ["confidence", "entities", "actions"]
            }
        
        try:
            # Get config from integration
            bot_config = self.config_integration.get_config(bot_type)
            return bot_config.get("response_enhancement", {})
        except Exception as e:
            self.logger.warning(f"Failed to get enhancement config for {bot_type}: {e}")
            return {
                "options": {
                    "parse_entities": True,
                    "parse_actions": True,
                    "assess_confidence": True,
                    "apply_anti_ai": True
                },
                "format": "default",
                "priority": ["confidence", "entities", "actions"]
            }
    
    def _parse_components(
        self,
        response: str,
        bot_type: str,
        enhancement_options: Dict[str, bool]
    ) -> Dict[str, Any]:
        """
        Parse components from the response.
        
        Args:
            response: Original response
            bot_type: Type of bot
            enhancement_options: Options for which components to parse
            
        Returns:
            Dictionary of parsed components
        """
        components = {}
        
        # Parse entities if enabled
        if enhancement_options.get("parse_entities", True) and self.entity_parser:
            try:
                entities = self.entity_parser.parse(response)
                components["entities"] = entities
            except Exception as e:
                self.logger.warning(f"Entity parsing failed: {e}")
                components["entities"] = {}
        
        # Parse actions if enabled
        if enhancement_options.get("parse_actions", True) and self.action_parser:
            try:
                actions = self.action_parser.extract_actions(response)
                components["actions"] = actions
            except Exception as e:
                self.logger.warning(f"Action parsing failed: {e}")
                components["actions"] = []
        
        # Assess confidence if enabled
        if enhancement_options.get("assess_confidence", True) and self.confidence_parser:
            try:
                confidence = self.confidence_parser.process_response(response)
                components["confidence"] = confidence
            except Exception as e:
                self.logger.warning(f"Confidence assessment failed: {e}")
                components["confidence"] = {"overall_confidence": 1.0, "confidence_level": "HIGH"}
        
        return components
    
    def _apply_enhancements(
        self,
        response: str,
        bot_type: str,
        parsed_components: Dict[str, Any],
        context: Dict[str, Any],
        enhancement_options: Dict[str, bool]
    ) -> str:
        """
        Apply enhancements to the response.
        
        Args:
            response: Original response
            bot_type: Type of bot
            parsed_components: Dictionary of parsed components
            context: Additional context for enhancements
            enhancement_options: Options for which enhancements to apply
            
        Returns:
            Enhanced response
        """
        enhanced = response
        
        # Apply bot-specific enhancers
        if bot_type in self.enhancers:
            try:
                bot_enhancer = self.enhancers[bot_type]
                enhanced = bot_enhancer.enhance(
                    enhanced,
                    parsed_components,
                    context
                )
            except Exception as e:
                self.logger.warning(f"Bot-specific enhancement failed: {e}")
        
        # Apply anti-AI detection if enabled
        if enhancement_options.get("apply_anti_ai", True) and "anti_ai" in self.enhancers:
            try:
                anti_ai = self.enhancers["anti_ai"]
                enhanced = anti_ai.enhance(enhanced, bot_type)
            except Exception as e:
                self.logger.warning(f"Anti-AI enhancement failed: {e}")
        
        # Apply polishing if enabled
        if enhancement_options.get("apply_polish", True) and "polisher" in self.enhancers:
            try:
                polisher = self.enhancers["polisher"]
                enhanced = polisher.enhance(enhanced, bot_type)
            except Exception as e:
                self.logger.warning(f"Polishing enhancement failed: {e}")
        
        return enhanced
    
    def _apply_format_adapters(
        self,
        response: str,
        bot_type: str,
        parsed_components: Dict[str, Any],
        enhancement_config: Dict[str, Any]
    ) -> str:
        """
        Apply format adapters to the response.
        
        Args:
            response: Enhanced response
            bot_type: Type of bot
            parsed_components: Dictionary of parsed components
            enhancement_config: Enhancement configuration
            
        Returns:
            Formatted response
        """
        # Get format type from config
        format_type = enhancement_config.get("format", "default")
        
        # Apply format-specific formatting
        if format_type == "default":
            return response
        elif format_type == "structured":
            return self._format_structured_response(response, parsed_components, enhancement_config)
        elif format_type == "markdown":
            return self._format_markdown_response(response, parsed_components, enhancement_config)
        elif format_type == "html":
            return self._format_html_response(response, parsed_components, enhancement_config)
        else:
            self.logger.warning(f"Unknown format type: {format_type}")
            return response
    
    def _format_structured_response(
        self,
        response: str,
        parsed_components: Dict[str, Any],
        enhancement_config: Dict[str, Any]
    ) -> str:
        """
        Format response as structured text with sections.
        
        Args:
            response: Enhanced response
            parsed_components: Dictionary of parsed components
            enhancement_config: Enhancement configuration
            
        Returns:
            Structured response
        """
        sections = [response]
        
        # Get component priority from config
        priority = enhancement_config.get("priority", ["confidence", "entities", "actions"])
        
        # Add sections based on priority
        for component in priority:
            if component == "entities" and "entities" in parsed_components:
                entities = parsed_components["entities"]
                if entities:
                    entity_section = self._format_entity_section(entities)
                    if entity_section:
                        sections.append("\nEntities Identified:\n" + entity_section)
            
            elif component == "actions" and "actions" in parsed_components:
                actions = parsed_components["actions"]
                if actions:
                    action_section = self._format_action_section(actions)
                    if action_section:
                        sections.append("\nSuggested Actions:\n" + action_section)
            
            elif component == "confidence" and "confidence" in parsed_components:
                confidence = parsed_components["confidence"]
                if confidence and confidence.get("confidence_level") != "HIGH":
                    confidence_section = self._format_confidence_section(confidence)
                    if confidence_section:
                        sections.append("\nConfidence Assessment:\n" + confidence_section)
        
        return "\n".join(sections)
    
    def _format_markdown_response(
        self,
        response: str,
        parsed_components: Dict[str, Any],
        enhancement_config: Dict[str, Any]
    ) -> str:
        """
        Format response as Markdown.
        
        Args:
            response: Enhanced response
            parsed_components: Dictionary of parsed components
            enhancement_config: Enhancement configuration
            
        Returns:
            Markdown-formatted response
        """
        sections = [response]
        
        # Get component priority from config
        priority = enhancement_config.get("priority", ["confidence", "entities", "actions"])
        
        # Add sections based on priority
        for component in priority:
            if component == "entities" and "entities" in parsed_components:
                entities = parsed_components["entities"]
                if entities:
                    entity_section = self._format_entity_section_markdown(entities)
                    if entity_section:
                        sections.append("\n## Entities Identified\n" + entity_section)
            
            elif component == "actions" and "actions" in parsed_components:
                actions = parsed_components["actions"]
                if actions:
                    action_section = self._format_action_section_markdown(actions)
                    if action_section:
                        sections.append("\n## Suggested Actions\n" + action_section)
            
            elif component == "confidence" and "confidence" in parsed_components:
                confidence = parsed_components["confidence"]
                if confidence and confidence.get("confidence_level") != "HIGH":
                    confidence_section = self._format_confidence_section_markdown(confidence)
                    if confidence_section:
                        sections.append("\n## Confidence Assessment\n" + confidence_section)
        
        return "\n".join(sections)
    
    def _format_html_response(
        self,
        response: str,
        parsed_components: Dict[str, Any],
        enhancement_config: Dict[str, Any]
    ) -> str:
        """
        Format response as HTML.
        
        Args:
            response: Enhanced response
            parsed_components: Dictionary of parsed components
            enhancement_config: Enhancement configuration
            
        Returns:
            HTML-formatted response
        """
        sections = [f"<div class='response-main'>{response}</div>"]
        
        # Get component priority from config
        priority = enhancement_config.get("priority", ["confidence", "entities", "actions"])
        
        # Add sections based on priority
        for component in priority:
            if component == "entities" and "entities" in parsed_components:
                entities = parsed_components["entities"]
                if entities:
                    entity_section = self._format_entity_section_html(entities)
                    if entity_section:
                        sections.append(f"<div class='entities-section'><h3>Entities Identified</h3>{entity_section}</div>")
            
            elif component == "actions" and "actions" in parsed_components:
                actions = parsed_components["actions"]
                if actions:
                    action_section = self._format_action_section_html(actions)
                    if action_section:
                        sections.append(f"<div class='actions-section'><h3>Suggested Actions</h3>{action_section}</div>")
            
            elif component == "confidence" and "confidence" in parsed_components:
                confidence = parsed_components["confidence"]
                if confidence and confidence.get("confidence_level") != "HIGH":
                    confidence_section = self._format_confidence_section_html(confidence)
                    if confidence_section:
                        sections.append(f"<div class='confidence-section'><h3>Confidence Assessment</h3>{confidence_section}</div>")
        
        return "\n".join(sections)
    
    def _format_entity_section(self, entities: Dict[str, Any]) -> str:
        """
        Format entities as plain text.
        
        Args:
            entities: Extracted entities
            
        Returns:
            Formatted entities section
        """
        formatted = []
        
        for entity_type, entity_data in entities.items():
            if isinstance(entity_data, list):
                # Multiple instances of this entity type
                for instance in entity_data:
                    formatted.append(f"- {entity_type.capitalize()}: {self._format_entity_instance(instance)}")
            else:
                # Single instance
                formatted.append(f"- {entity_type.capitalize()}: {self._format_entity_instance(entity_data)}")
        
        return "\n".join(formatted)
    
    def _format_entity_instance(self, instance: Dict[str, Any]) -> str:
        """
        Format a single entity instance.
        
        Args:
            instance: Entity instance data
            
        Returns:
            Formatted entity instance
        """
        if "name" in instance:
            return instance["name"]
        elif "id" in instance:
            return instance["id"]
        else:
            # Convert attributes to string
            attributes = []
            for key, value in instance.items():
                if isinstance(value, (str, int, float, bool)):
                    attributes.append(f"{key}={value}")
            return ", ".join(attributes)
    
    def _format_entity_section_markdown(self, entities: Dict[str, Any]) -> str:
        """
        Format entities as Markdown.
        
        Args:
            entities: Extracted entities
            
        Returns:
            Markdown-formatted entities section
        """
        formatted = []
        
        for entity_type, entity_data in entities.items():
            formatted.append(f"### {entity_type.capitalize()}")
            
            if isinstance(entity_data, list):
                # Multiple instances of this entity type
                for instance in entity_data:
                    formatted.append(f"- **{self._format_entity_instance(instance)}**")
                    # Add details
                    for key, value in instance.items():
                        if key not in ["name", "id"] and isinstance(value, (str, int, float, bool)):
                            formatted.append(f"  - {key}: {value}")
            else:
                # Single instance
                formatted.append(f"- **{self._format_entity_instance(entity_data)}**")
                # Add details
                for key, value in entity_data.items():
                    if key not in ["name", "id"] and isinstance(value, (str, int, float, bool)):
                        formatted.append(f"  - {key}: {value}")
        
        return "\n".join(formatted)
    
    def _format_entity_section_html(self, entities: Dict[str, Any]) -> str:
        """
        Format entities as HTML.
        
        Args:
            entities: Extracted entities
            
        Returns:
            HTML-formatted entities section
        """
        formatted = ["<ul class='entity-list'>"]
        
        for entity_type, entity_data in entities.items():
            formatted.append(f"<li class='entity-type'><strong>{entity_type.capitalize()}</strong>")
            
            if isinstance(entity_data, list):
                # Multiple instances of this entity type
                formatted.append("<ul>")
                for instance in entity_data:
                    formatted.append(f"<li><strong>{self._format_entity_instance(instance)}</strong>")
                    # Add details
                    details = []
                    for key, value in instance.items():
                        if key not in ["name", "id"] and isinstance(value, (str, int, float, bool)):
                            details.append(f"<li>{key}: {value}</li>")
                    
                    if details:
                        formatted.append("<ul class='entity-details'>")
                        formatted.extend(details)
                        formatted.append("</ul>")
                    
                    formatted.append("</li>")
                formatted.append("</ul>")
            else:
                # Single instance
                formatted.append(f"<p><strong>{self._format_entity_instance(entity_data)}</strong></p>")
                # Add details
                details = []
                for key, value in entity_data.items():
                    if key not in ["name", "id"] and isinstance(value, (str, int, float, bool)):
                        details.append(f"<li>{key}: {value}</li>")
                
                if details:
                    formatted.append("<ul class='entity-details'>")
                    formatted.extend(details)
                    formatted.append("</ul>")
            
            formatted.append("</li>")
        
        formatted.append("</ul>")
        return "\n".join(formatted)
    
    def _format_action_section(self, actions: List[Dict[str, Any]]) -> str:
        """
        Format actions as plain text.
        
        Args:
            actions: Extracted actions
            
        Returns:
            Formatted actions section
        """
        formatted = []
        
        for action in actions:
            action_type = action.get("action_type", "unknown")
            description = action.get("description", "")
            
            if description:
                formatted.append(f"- {action_type.capitalize()}: {description}")
            else:
                # Format parameters
                params = action.get("parameters", {})
                if not params:
                    # Check if parameters are directly in the action
                    params = {k: v for k, v in action.items() 
                              if k not in ["action_type", "priority", "confidence", "description"]}
                
                param_str = ", ".join(f"{k}={v}" for k, v in params.items())
                formatted.append(f"- {action_type.capitalize()}: {param_str}")
        
        return "\n".join(formatted)
    
    def _format_action_section_markdown(self, actions: List[Dict[str, Any]]) -> str:
        """
        Format actions as Markdown.
        
        Args:
            actions: Extracted actions
            
        Returns:
            Markdown-formatted actions section
        """
        formatted = []
        
        for action in actions:
            action_type = action.get("action_type", "unknown")
            description = action.get("description", "")
            
            if description:
                formatted.append(f"- **{action_type.capitalize()}**: {description}")
            else:
                # Format parameters
                formatted.append(f"- **{action_type.capitalize()}**")
                
                # Get parameters
                params = action.get("parameters", {})
                if not params:
                    # Check if parameters are directly in the action
                    params = {k: v for k, v in action.items() 
                              if k not in ["action_type", "priority", "confidence", "description"]}
                
                for key, value in params.items():
                    formatted.append(f"  - {key}: `{value}`")
        
        return "\n".join(formatted)
    
    def _format_action_section_html(self, actions: List[Dict[str, Any]]) -> str:
        """
        Format actions as HTML.
        
        Args:
            actions: Extracted actions
            
        Returns:
            HTML-formatted actions section
        """
        formatted = ["<ul class='action-list'>"]
        
        for action in actions:
            action_type = action.get("action_type", "unknown")
            description = action.get("description", "")
            
            formatted.append(f"<li class='action-item'>")
            formatted.append(f"<strong>{action_type.capitalize()}</strong>")
            
            if description:
                formatted.append(f"<p>{description}</p>")
            else:
                # Get parameters
                params = action.get("parameters", {})
                if not params:
                    # Check if parameters are directly in the action
                    params = {k: v for k, v in action.items() 
                              if k not in ["action_type", "priority", "confidence", "description"]}
                
                if params:
                    formatted.append("<ul class='action-params'>")
                    for key, value in params.items():
                        formatted.append(f"<li>{key}: <code>{value}</code></li>")
                    formatted.append("</ul>")
            
            formatted.append("</li>")
        
        formatted.append("</ul>")
        return "\n".join(formatted)
    
    def _format_confidence_section(self, confidence: Dict[str, Any]) -> str:
        """
        Format confidence assessment as plain text.
        
        Args:
            confidence: Confidence assessment data
            
        Returns:
            Formatted confidence section
        """
        confidence_level = confidence.get("confidence_level", "UNKNOWN")
        confidence_score = confidence.get("confidence_metrics", {}).get("overall_confidence", 0.0)
        requires_verification = confidence.get("confidence_metrics", {}).get("requires_verification", False)
        
        formatted = [f"- Confidence Level: {confidence_level} ({confidence_score:.2f})"]
        
        if requires_verification:
            formatted.append("- This response may require verification.")
            uncertain_topics = confidence.get("uncertain_topics", [])
            if uncertain_topics:
                formatted.append("- Uncertain topics: " + ", ".join(uncertain_topics))
        
        return "\n".join(formatted)
    
    def _format_confidence_section_markdown(self, confidence: Dict[str, Any]) -> str:
        """
        Format confidence assessment as Markdown.
        
        Args:
            confidence: Confidence assessment data
            
        Returns:
            Markdown-formatted confidence section
        """
        confidence_level = confidence.get("confidence_level", "UNKNOWN")
        confidence_score = confidence.get("confidence_metrics", {}).get("overall_confidence", 0.0)
        requires_verification = confidence.get("confidence_metrics", {}).get("requires_verification", False)
        
        if confidence_level == "LOW":
            formatted = [f"- **Confidence Level**: ❗ {confidence_level} ({confidence_score:.2f})"]
        elif confidence_level == "MEDIUM":
            formatted = [f"- **Confidence Level**: ⚠️ {confidence_level} ({confidence_score:.2f})"]
        else:
            formatted = [f"- **Confidence Level**: ✓ {confidence_level} ({confidence_score:.2f})"]
        
        if requires_verification:
            formatted.append("- ⚠️ **This response may require verification**")
            uncertain_topics = confidence.get("uncertain_topics", [])
            if uncertain_topics:
                formatted.append("- **Uncertain topics**: " + ", ".join(uncertain_topics))
        
        return "\n".join(formatted)
    
    def _format_confidence_section_html(self, confidence: Dict[str, Any]) -> str:
        """
        Format confidence assessment as HTML.
        
        Args:
            confidence: Confidence assessment data
            
        Returns:
            HTML-formatted confidence section
        """
        confidence_level = confidence.get("confidence_level", "UNKNOWN")
        confidence_score = confidence.get("confidence_metrics", {}).get("overall_confidence", 0.0)
        requires_verification = confidence.get("confidence_metrics", {}).get("requires_verification", False)
        
        if confidence_level == "LOW":
            icon = "❗"
            color_class = "confidence-low"
        elif confidence_level == "MEDIUM":
            icon = "⚠️"
            color_class = "confidence-medium"
        else:
            icon = "✓"
            color_class = "confidence-high"
        
        formatted = [f"<div class='confidence-box {color_class}'>"]
        formatted.append(f"<p><strong>Confidence Level</strong>: {icon} {confidence_level} ({confidence_score:.2f})</p>")
        
        if requires_verification:
            formatted.append("<p class='verification-warning'>⚠️ This response may require verification</p>")
            uncertain_topics = confidence.get("uncertain_topics", [])
            if uncertain_topics:
                formatted.append("<p><strong>Uncertain topics</strong>: " + ", ".join(uncertain_topics) + "</p>")
        
        formatted.append("</div>")
        return "\n".join(formatted) 