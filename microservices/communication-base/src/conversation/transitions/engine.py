"""
Transition Engine

This module provides a mechanism for evaluating state transitions
based on conditions and rules defined in configuration.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Callable, Awaitable
import asyncio
import json

from src.config.config_integration import ConfigIntegration

logger = logging.getLogger(__name__)

# Type definition for condition evaluators
ConditionEvaluatorType = Callable[[str, Dict[str, Any], Dict[str, Any]], Awaitable[bool]]

class TransitionEngine:
    """
    Transition Engine
    
    Handles evaluation of conditions for state transitions,
    allowing for dynamic conversation flow control.
    """
    
    def __init__(self, config_integration: ConfigIntegration):
        """
        Initialize the transition engine.
        
        Args:
            config_integration: Configuration integration instance
        """
        self.config_integration = config_integration
        self.transition_rules: Dict[str, Dict[str, Any]] = {}
        self.condition_evaluators: Dict[str, ConditionEvaluatorType] = {}
        
        # Register built-in condition evaluators
        self._register_built_in_evaluators()
        
        # Load transition rules from configuration
        self._load_transition_rules()
        
        logger.info("Transition engine initialized")
    
    def _register_built_in_evaluators(self) -> None:
        """
        Register built-in condition evaluators.
        """
        # Intent-based condition
        self.register_condition_evaluator(
            "intent_match", self._evaluate_intent_match
        )
        
        # Keyword-based condition
        self.register_condition_evaluator(
            "keyword_match", self._evaluate_keyword_match
        )
        
        # Entity-based condition
        self.register_condition_evaluator(
            "entity_present", self._evaluate_entity_present
        )
        
        # State duration condition
        self.register_condition_evaluator(
            "state_duration", self._evaluate_state_duration
        )
        
        # Context value condition
        self.register_condition_evaluator(
            "context_value", self._evaluate_context_value
        )
        
        # Message count condition
        self.register_condition_evaluator(
            "message_count", self._evaluate_message_count
        )
        
        logger.info("Built-in condition evaluators registered")
    
    def _load_transition_rules(self) -> None:
        """
        Load transition rules from configuration.
        """
        try:
            for bot_type in ["sales", "consultancy", "support"]:
                rules = self.config_integration.get_config_section(
                    f"transitions.{bot_type}"
                )
                if rules:
                    self.transition_rules[bot_type] = rules
                else:
                    logger.warning(f"No transition rules found for bot type {bot_type}")
                    # Set empty rules as fallback
                    self.transition_rules[bot_type] = {}
            
            logger.info("Transition rules loaded from configuration")
        except Exception as e:
            logger.error(f"Error loading transition rules: {e}")
            # Initialize with empty rules as fallback
            self.transition_rules = {
                "sales": {},
                "consultancy": {},
                "support": {}
            }
    
    def register_condition_evaluator(
        self, 
        condition_type: str, 
        evaluator: ConditionEvaluatorType
    ) -> None:
        """
        Register a custom condition evaluator.
        
        Args:
            condition_type: Type identifier for the condition
            evaluator: Function to evaluate the condition
        """
        self.condition_evaluators[condition_type] = evaluator
        logger.info(f"Registered condition evaluator for {condition_type}")
    
    async def evaluate_transitions(
        self,
        current_state: str,
        bot_type: str,
        message: str,
        context: Dict[str, Any],
        response: Dict[str, Any]
    ) -> Optional[str]:
        """
        Evaluate transitions for the current state based on the message and context.
        
        Args:
            current_state: Current state name
            bot_type: Type of bot
            message: User message
            context: Conversation context
            response: Response from state execution
            
        Returns:
            Next state name or None if no transition applies
        """
        if bot_type not in self.transition_rules:
            logger.warning(f"No transition rules for bot type {bot_type}")
            return None
            
        # Get transitions for current state
        state_transitions = self.transition_rules[bot_type].get(current_state, [])
        if not state_transitions:
            logger.info(f"No transitions defined for state {current_state} in {bot_type}")
            return None
        
        # Evaluate each transition
        for transition in state_transitions:
            target_state = transition.get("target")
            conditions = transition.get("conditions", [])
            
            if not target_state:
                logger.warning(f"Transition missing target state for {current_state}")
                continue
                
            # Skip if there are no conditions (prevent unintended transitions)
            if not conditions:
                logger.warning(f"Transition has no conditions for {current_state} to {target_state}")
                continue
            
            # Evaluate all conditions
            all_conditions_met = True
            for condition in conditions:
                condition_type = condition.get("type")
                if not condition_type:
                    logger.warning(f"Condition missing type in {current_state} transition")
                    all_conditions_met = False
                    break
                
                # Skip if evaluator not available
                if condition_type not in self.condition_evaluators:
                    logger.warning(f"No evaluator for condition type {condition_type}")
                    all_conditions_met = False
                    break
                
                # Evaluate condition
                evaluator = self.condition_evaluators[condition_type]
                try:
                    result = await evaluator(message, context, condition)
                    if not result:
                        all_conditions_met = False
                        break
                except Exception as e:
                    logger.error(f"Error evaluating condition {condition_type}: {e}")
                    all_conditions_met = False
                    break
            
            # If all conditions are met, transition to the target state
            if all_conditions_met:
                logger.info(f"Transition conditions met: {current_state} -> {target_state}")
                return target_state
        
        # No transitions applicable
        return None
    
    # ----- Built-in condition evaluators -----
    
    async def _evaluate_intent_match(
        self, 
        message: str, 
        context: Dict[str, Any], 
        condition: Dict[str, Any]
    ) -> bool:
        """
        Evaluate if the detected intent matches the specified intent.
        
        Args:
            message: User message
            context: Conversation context
            condition: Condition configuration
            
        Returns:
            True if intent matches, False otherwise
        """
        target_intent = condition.get("intent")
        if not target_intent:
            return False
            
        # Get detected intent from context
        detected_intent = context.get("detected_intent", {}).get("name")
        if not detected_intent:
            return False
            
        # Check for intent match
        confidence = context.get("detected_intent", {}).get("confidence", 0)
        min_confidence = condition.get("min_confidence", 0.7)
        
        is_match = (detected_intent == target_intent and confidence >= min_confidence)
        logger.debug(f"Intent match evaluation: {detected_intent} == {target_intent}? {is_match}")
        return is_match
    
    async def _evaluate_keyword_match(
        self, 
        message: str, 
        context: Dict[str, Any], 
        condition: Dict[str, Any]
    ) -> bool:
        """
        Evaluate if any of the specified keywords are in the message.
        
        Args:
            message: User message
            context: Conversation context
            condition: Condition configuration
            
        Returns:
            True if any keyword matches, False otherwise
        """
        keywords = condition.get("keywords", [])
        if not keywords:
            return False
            
        # Case-insensitive check for each keyword
        message_lower = message.lower()
        for keyword in keywords:
            if keyword.lower() in message_lower:
                logger.debug(f"Keyword match found: {keyword}")
                return True
                
        return False
    
    async def _evaluate_entity_present(
        self, 
        message: str, 
        context: Dict[str, Any], 
        condition: Dict[str, Any]
    ) -> bool:
        """
        Evaluate if the specified entity is present in context.
        
        Args:
            message: User message
            context: Conversation context
            condition: Condition configuration
            
        Returns:
            True if entity is present, False otherwise
        """
        entity_name = condition.get("entity_name")
        if not entity_name:
            return False
            
        # Check for entity in context
        entities = context.get("entities", {})
        is_present = entity_name in entities
        logger.debug(f"Entity present evaluation: {entity_name} in context? {is_present}")
        return is_present
    
    async def _evaluate_state_duration(
        self, 
        message: str, 
        context: Dict[str, Any], 
        condition: Dict[str, Any]
    ) -> bool:
        """
        Evaluate if the current state duration exceeds the threshold.
        
        Args:
            message: User message
            context: Conversation context
            condition: Condition configuration
            
        Returns:
            True if duration exceeds threshold, False otherwise
        """
        from datetime import datetime
        
        threshold_seconds = condition.get("threshold_seconds", 300)  # 5 minutes default
        
        # Get state entry time
        entry_time_str = context.get("state_entry_time")
        if not entry_time_str:
            return False
            
        try:
            entry_time = datetime.fromisoformat(entry_time_str)
            current_time = datetime.utcnow()
            duration = (current_time - entry_time).total_seconds()
            
            exceeds_threshold = duration > threshold_seconds
            logger.debug(f"State duration evaluation: {duration} > {threshold_seconds}? {exceeds_threshold}")
            return exceeds_threshold
        except Exception as e:
            logger.error(f"Error evaluating state duration: {e}")
            return False
    
    async def _evaluate_context_value(
        self, 
        message: str, 
        context: Dict[str, Any], 
        condition: Dict[str, Any]
    ) -> bool:
        """
        Evaluate if a context value matches the specified value.
        
        Args:
            message: User message
            context: Conversation context
            condition: Condition configuration
            
        Returns:
            True if context value matches, False otherwise
        """
        path = condition.get("context_path")
        expected_value = condition.get("expected_value")
        operator = condition.get("operator", "eq")  # eq, neq, gt, lt, contains
        
        if not path:
            return False
            
        # Navigate context path (support dot notation)
        parts = path.split(".")
        current = context
        for part in parts:
            if part in current:
                current = current[part]
            else:
                return False
                
        # Perform comparison based on operator
        if operator == "eq":
            return current == expected_value
        elif operator == "neq":
            return current != expected_value
        elif operator == "gt":
            return current > expected_value
        elif operator == "lt":
            return current < expected_value
        elif operator == "contains":
            return expected_value in current
        else:
            logger.warning(f"Unknown operator {operator} in context value condition")
            return False
    
    async def _evaluate_message_count(
        self, 
        message: str, 
        context: Dict[str, Any], 
        condition: Dict[str, Any]
    ) -> bool:
        """
        Evaluate if the message count in the current state exceeds the threshold.
        
        Args:
            message: User message
            context: Conversation context
            condition: Condition configuration
            
        Returns:
            True if message count exceeds threshold, False otherwise
        """
        threshold = condition.get("threshold", 5)
        current_state = context.get("current_state")
        
        if not current_state:
            return False
            
        # Count messages since entering current state
        state_entry_time = context.get("state_entry_time")
        if not state_entry_time:
            return False
            
        # Count messages after state entry time
        try:
            from datetime import datetime
            entry_time = datetime.fromisoformat(state_entry_time)
            
            # Count messages
            message_count = 0
            for msg in context.get("messages", []):
                if msg.get("role") == "user":
                    msg_time = datetime.fromisoformat(msg.get("timestamp", "1970-01-01T00:00:00"))
                    if msg_time >= entry_time:
                        message_count += 1
            
            exceeds_threshold = message_count >= threshold
            logger.debug(f"Message count evaluation: {message_count} >= {threshold}? {exceeds_threshold}")
            return exceeds_threshold
        except Exception as e:
            logger.error(f"Error evaluating message count: {e}")
            return False 