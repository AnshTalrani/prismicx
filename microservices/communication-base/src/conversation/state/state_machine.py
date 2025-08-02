"""
Conversation State Machine

This module provides the state machine that manages conversation states,
state transitions, and state-specific logic.
"""

import logging
from typing import Dict, Any, List, Optional

from src.config.config_integration import ConfigIntegration

logger = logging.getLogger(__name__)

class ConversationStateMachine:
    """
    Conversation State Machine
    
    Manages conversation states, including their definition, 
    initialization, and execution of state-specific logic.
    """
    
    def __init__(self, bot_type: str, config_integration: ConfigIntegration):
        """
        Initialize the conversation state machine.
        
        Args:
            bot_type: Type of bot
            config_integration: Configuration integration instance
        """
        self.bot_type = bot_type
        self.config_integration = config_integration
        
        # Load states from configuration
        self.states = self._load_states()
        
        # Initialize state handlers
        self.state_handlers = {}
        self._register_state_handlers()
        
        logger.info(f"Initialized conversation state machine for {bot_type} bot")
    
    def _load_states(self) -> Dict[str, Any]:
        """
        Load state definitions from bot-specific configuration.
        
        Returns:
            Dictionary of state definitions
        """
        # Get bot-specific configuration
        bot_config = self.config_integration.get_config(self.bot_type)
        
        # Try to get conversation states from bot configuration
        # The path should match the structure in bot config files
        states = bot_config.get("conversation.states")
        
        if not states:
            # Alternative paths to check in bot config
            alternative_paths = [
                f"{self.bot_type}_bot_config.conversation.states",
                f"{self.bot_type.upper()}_BOT_CONFIG.conversation.states",
                "conversation_flow.states"
            ]
            
            for path in alternative_paths:
                states = self.config_integration.get_config_section(path)
                if states:
                    logger.info(f"Loaded states from {path}")
                    break
        
        if not states:
            # If no states defined, log error and return empty states
            logger.error(f"No states defined for {self.bot_type} bot in configuration. Please check the config file.")
            states = {}
            
            # Check if the common states can be used as fallback
            from src.conversation.states import COMMON_STATES
            if COMMON_STATES:
                logger.info(f"Using common states as fallback for {self.bot_type} bot")
                states = COMMON_STATES.copy()
        
        return states
    
    def _register_state_handlers(self) -> None:
        """Register state-specific handlers based on bot type and loaded states."""
        # Register common state handlers first
        self.state_handlers["greeting"] = self._handle_greeting_state
        self.state_handlers["information_gathering"] = self._handle_information_gathering_state
        self.state_handlers["closing"] = self._handle_closing_state
        self.state_handlers["error"] = self._handle_error_state
        
        # Register state handlers for all states in the config
        for state_name in self.states.keys():
            if state_name not in self.state_handlers:
                # Get the handler method name based on state name
                handler_method_name = f"_handle_{state_name}"
                
                # Check if we have a specific handler method for this state
                if hasattr(self, handler_method_name):
                    self.state_handlers[state_name] = getattr(self, handler_method_name)
                else:
                    # If no specific handler, use the generic handler
                    logger.debug(f"No specific handler for state {state_name}, using generic handler")
                    self.state_handlers[state_name] = self._execute_generic_state
        
        # Register additional bot-specific handlers
        self._register_bot_specific_handlers()
        
        logger.info(f"Registered {len(self.state_handlers)} state handlers for {self.bot_type} bot")
    
    def _register_bot_specific_handlers(self) -> None:
        """Register additional bot-specific handlers."""
        # Sales bot specific handlers
        if self.bot_type == "sales":
            sales_states = [
                "discovery", "qualification", "presentation", 
                "objection_handling", "closing_deal", "follow_up"
            ]
            
            for state in sales_states:
                handler_method = f"_handle_sales_{state}"
                if state in self.states and hasattr(self, handler_method):
                    self.state_handlers[state] = getattr(self, handler_method)
        
        # Consultancy bot specific handlers
        elif self.bot_type == "consultancy":
            consultancy_states = [
                "problem_identification", "analysis", "recommendation",
                "implementation_planning", "follow_up"
            ]
            
            for state in consultancy_states:
                handler_method = f"_handle_consultancy_{state}"
                if state in self.states and hasattr(self, handler_method):
                    self.state_handlers[state] = getattr(self, handler_method)
        
        # Support bot specific handlers
        elif self.bot_type == "support":
            support_states = [
                "issue_identification", "troubleshooting", "resolution",
                "confirmation", "escalation"
            ]
            
            for state in support_states:
                handler_method = f"_handle_support_{state}"
                if state in self.states and hasattr(self, handler_method):
                    self.state_handlers[state] = getattr(self, handler_method)
    
    def get_initial_state(self) -> str:
        """
        Get the initial state for the conversation.
        
        Returns:
            Name of the initial state
        """
        # Check bot-specific configuration for initial state
        bot_config = self.config_integration.get_config(self.bot_type)
        
        # Try different possible paths for the initial state in configuration
        paths_to_check = [
            "conversation.initial_state",
            f"{self.bot_type}_bot_config.conversation.initial_state",
            f"{self.bot_type.upper()}_BOT_CONFIG.conversation.initial_state",
            "conversation_flow.initial_state"
        ]
        
        initial_state = None
        for path in paths_to_check:
            initial_state = self.config_integration.get_config_value(path)
            if initial_state:
                logger.info(f"Found initial state '{initial_state}' at config path: {path}")
                break
        
        # Default to "greeting" if no initial state specified in config
        if not initial_state:
            initial_state = "greeting"
            logger.info(f"No initial state specified in config, using default: {initial_state}")
        
        # Ensure the state exists
        if initial_state not in self.states:
            logger.warning(f"Configured initial state '{initial_state}' not found in available states, falling back to greeting")
            # Try to find a greeting-like state in our states
            greeting_alternatives = ["greeting", "welcome", "start", "initial", "hello"]
            for alt in greeting_alternatives:
                if alt in self.states:
                    initial_state = alt
                    logger.info(f"Found alternative initial state: {initial_state}")
                    break
            else:
                # If no greeting-like state exists, use the first state
                if self.states:
                    initial_state = next(iter(self.states))
                    logger.info(f"Using first available state as initial: {initial_state}")
                else:
                    # This should never happen as we always have default states
                    logger.error("No states available for conversation")
                    initial_state = "error"
        
        return initial_state
    
    def get_state(self, state_name: str) -> Optional[Dict[str, Any]]:
        """
        Get state definition by name.
        
        Args:
            state_name: Name of the state
            
        Returns:
            State definition or None if not found
        """
        return self.states.get(state_name)
    
    async def execute_state(
        self,
        state_name: str,
        message: str,
        context: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Execute state-specific logic.
        
        Args:
            state_name: Name of the state to execute
            message: User message
            context: Conversation context
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Response from state execution
        """
        logger.info(f"Executing state {state_name} for {self.bot_type} bot")
        
        # Check if state exists
        if state_name not in self.states:
            logger.error(f"State {state_name} not found for {self.bot_type} bot")
            return {
                "response": "I'm sorry, something went wrong. Let's start over.",
                "context_updates": {"current_state": self.get_initial_state()}
            }
        
        # Get state definition
        state = self.states[state_name]
        
        # Check for handler function from bot config if defined
        handler_config_key = f"handlers.{state_name}"
        custom_handler_name = self.config_integration.get_config_value(
            f"{self.bot_type}_bot_config.{handler_config_key}")
        
        if custom_handler_name:
            logger.info(f"Found custom handler configuration: {custom_handler_name}")
            # This could integrate with a handler registry or plugins system
            # For now, we'll still use our internal handlers
        
        # Check if there's a handler for this state
        if state_name in self.state_handlers:
            try:
                # Execute the handler
                handler = self.state_handlers[state_name]
                result = await handler(
                    message=message,
                    context=context,
                    state=state,
                    user_id=user_id,
                    session_id=session_id
                )
                logger.debug(f"State handler execution successful for {state_name}")
                return result
            except Exception as e:
                logger.exception(f"Error in state handler for {state_name}: {e}")
                return {
                    "response": "I'm sorry, I encountered an error. Let's try something else.",
                    "context_updates": {"error": str(e)}
                }
        else:
            # Use generic state execution
            logger.info(f"No specific handler for state {state_name}, using generic execution")
            return await self._execute_generic_state(
                state_name=state_name,
                message=message,
                context=context,
                state=state
            )
    
    async def execute_state_entry(
        self,
        state_name: str,
        context: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Execute actions when entering a state.
        
        Args:
            state_name: Name of the state
            context: Conversation context
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Response from state entry actions
        """
        logger.info(f"Entering state {state_name} for {self.bot_type} bot")
        
        # Check if state exists
        if state_name not in self.states:
            logger.error(f"State {state_name} not found for {self.bot_type} bot")
            return {}
        
        # Get state definition
        state = self.states[state_name]
        
        # Execute entry actions
        entry_actions = state.get("on_entry", {})
        response = {}
        
        # Process entry message
        if "message" in entry_actions:
            response["response"] = entry_actions["message"]
        
        # Process context updates
        if "context_updates" in entry_actions:
            response["context_updates"] = entry_actions["context_updates"]
        
        # Process adapter activation
        if "adapters" in entry_actions:
            response["adapters"] = entry_actions["adapters"]
        
        # Process RAG configuration
        if "use_rag" in entry_actions:
            response["use_rag"] = entry_actions["use_rag"]
        
        return response
    
    async def execute_state_exit(
        self,
        state_name: str,
        context: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """
        Execute actions when exiting a state.
        
        Args:
            state_name: Name of the state
            context: Conversation context
            session_id: Session identifier
            
        Returns:
            Response from state exit actions
        """
        logger.info(f"Exiting state {state_name} for {self.bot_type} bot")
        
        # Check if state exists
        if state_name not in self.states:
            logger.error(f"State {state_name} not found for {self.bot_type} bot")
            return {}
        
        # Get state definition
        state = self.states[state_name]
        
        # Execute exit actions
        exit_actions = state.get("on_exit", {})
        response = {}
        
        # Process context updates
        if "context_updates" in exit_actions:
            response["context_updates"] = exit_actions["context_updates"]
        
        # Process actions
        if "actions" in exit_actions:
            response["actions"] = exit_actions["actions"]
        
        return response
    
    async def _execute_generic_state(
        self,
        state_name: str,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute generic state logic.
        
        Args:
            state_name: Name of the state
            message: User message
            context: Conversation context
            state: State definition
            
        Returns:
            Response from state execution
        """
        logger.info(f"Executing generic state handler for {state_name}")
        
        # Default response
        response = state.get("default_response", "I'm not sure how to respond to that.")
        
        # Check for keyword-based responses
        keyword_responses = state.get("keyword_responses", {})
        for keyword, resp in keyword_responses.items():
            if keyword.lower() in message.lower():
                response = resp
                break
        
        # Check for RAG usage
        use_rag = state.get("use_rag", False)
        
        # Get adapters to use
        adapters = state.get("adapters", [])
        
        # Actions to take
        actions = state.get("actions", [])
        
        return {
            "response": response,
            "use_rag": use_rag,
            "adapters": adapters,
            "actions": actions
        }
    
    # Common state handlers
    
    async def _handle_greeting_state(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle greeting state logic."""
        # Personalized greeting if user is known
        if context.get("user_name"):
            response = f"Hello {context['user_name']}! How can I help you today?"
        else:
            response = "Hello! How can I help you today?"
        
        # Use RAG if configured
        use_rag = state.get("use_rag", False)
        
        # No special adapters for greeting, use defaults
        adapters = state.get("adapters", [])
        
        return {
            "response": response,
            "use_rag": use_rag,
            "adapters": adapters,
            "context_updates": {
                "greeted": True,
                "greeting_time": context.get("state_entry_time")
            }
        }
    
    async def _handle_information_gathering_state(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle information gathering state logic."""
        # Get information to gather from context
        needed_info = context.get("needed_info", [])
        
        if not needed_info:
            # Move to next state if no info needed
            return {
                "response": "I think I have all the information I need. Let me help you with that.",
                "use_rag": True,
                "context_updates": {
                    "information_complete": True
                }
            }
        
        # Generate question for next needed info
        next_info = needed_info[0]
        question = f"To help you better, could you tell me about your {next_info}?"
        
        return {
            "response": question,
            "use_rag": False,
            "context_updates": {
                "current_question": next_info
            }
        }
    
    async def _handle_closing_state(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle closing state logic."""
        # Generate personalized closing message
        if context.get("user_name"):
            response = f"Thank you for chatting with me today, {context['user_name']}! Is there anything else I can help you with?"
        else:
            response = "Thank you for chatting with me today! Is there anything else I can help you with?"
        
        return {
            "response": response,
            "use_rag": False,
            "context_updates": {
                "closing_initiated": True
            },
            "actions": [{
                "type": "summary",
                "params": {
                    "session_id": session_id
                }
            }]
        }
    
    async def _handle_error_state(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle error state logic."""
        # Get error information
        error_type = context.get("error_type", "unknown")
        
        # Generate response based on error type
        if error_type == "authentication":
            response = "I'm sorry, but there seems to be an authentication issue. Please try logging in again."
        elif error_type == "timeout":
            response = "I apologize for the delay. Let's continue our conversation."
        else:
            response = "I apologize for the confusion. Let's try a different approach."
        
        return {
            "response": response,
            "use_rag": False,
            "context_updates": {
                "error_acknowledged": True
            },
            "actions": [{
                "type": "error_report",
                "params": {
                    "error_type": error_type,
                    "session_id": session_id
                }
            }]
        }
    
    # Sales bot state handlers
    
    async def _handle_sales_discovery(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle sales discovery state logic."""
        # Check if we have enough discovery information
        pain_points = context.get("pain_points", [])
        
        if not pain_points:
            response = "What challenges are you currently facing that our solution might help with?"
            return {
                "response": response,
                "use_rag": False,
                "adapters": ["sales"],
                "context_updates": {
                    "discovery_started": True
                }
            }
        
        # If we already have pain points, dig deeper
        response = "Tell me more about how these challenges are affecting your business."
        
        return {
            "response": response,
            "use_rag": True,
            "adapters": ["sales"],
            "context_updates": {
                "discovery_progressed": True
            }
        }
    
    async def _handle_sales_qualification(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle sales qualification state logic."""
        # Check what qualification questions have been asked
        asked_questions = context.get("asked_qualification_questions", [])
        
        qualification_questions = [
            "What's your timeline for implementing a solution?",
            "Who else is involved in the decision-making process?",
            "What budget range have you allocated for this solution?",
            "Have you tried similar solutions in the past?"
        ]
        
        # Ask next qualification question
        next_questions = [q for q in qualification_questions if q not in asked_questions]
        
        if not next_questions:
            # All questions asked, move to next phase
            return {
                "response": "Thank you for sharing that information. Based on what you've told me, I think our solution would be a great fit for your needs.",
                "use_rag": True,
                "adapters": ["sales"],
                "context_updates": {
                    "qualification_complete": True
                }
            }
        
        next_question = next_questions[0]
        
        return {
            "response": next_question,
            "use_rag": False,
            "adapters": ["sales"],
            "context_updates": {
                "asked_qualification_questions": asked_questions + [next_question]
            }
        }
    
    async def _handle_sales_presentation(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle sales presentation state logic."""
        # Tailor presentation to pain points
        pain_points = context.get("pain_points", [])
        
        if pain_points:
            response = f"Based on your challenges with {', '.join(pain_points)}, our solution provides specific benefits that address these exact issues."
        else:
            response = "Our solution offers several key benefits that I think would be valuable for your business."
        
        return {
            "response": response,
            "use_rag": True,
            "adapters": ["sales"],
            "context_updates": {
                "presentation_delivered": True
            }
        }
    
    async def _handle_sales_objection_handling(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle sales objection handling state logic."""
        # Identify objection type from message
        objection_type = "unknown"
        
        if "expensive" in message.lower() or "cost" in message.lower() or "price" in message.lower():
            objection_type = "price"
        elif "competitor" in message.lower() or "alternative" in message.lower():
            objection_type = "competition"
        elif "time" in message.lower() or "long" in message.lower() or "implementation" in message.lower():
            objection_type = "implementation"
        
        # Handle based on objection type
        if objection_type == "price":
            response = "I understand your concern about the investment. When you consider the ROI our customers typically see, the solution pays for itself within 6-8 months."
        elif objection_type == "competition":
            response = "That's a good point. While there are alternatives, our solution is unique because it offers [specific differentiator] that others don't provide."
        elif objection_type == "implementation":
            response = "The implementation timeline is a common concern. We've streamlined our process so most customers are up and running within just 2-3 weeks."
        else:
            response = "I understand your concern. Could you tell me more about what's holding you back?"
        
        return {
            "response": response,
            "use_rag": True,
            "adapters": ["sales", "persuasion"],
            "context_updates": {
                "objection_handled": objection_type
            }
        }
    
    async def _handle_sales_closing(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle sales closing state logic."""
        # Check if we've tried closing before
        closing_attempts = context.get("closing_attempts", 0)
        
        if closing_attempts == 0:
            response = "Based on our conversation, I think the next best step would be to schedule a demo with one of our specialists. Would Tuesday or Thursday work better for you?"
        elif closing_attempts == 1:
            response = "I understand you might need more time. Would you like me to send over some case studies of companies similar to yours who have implemented our solution?"
        else:
            response = "Is there any other information I can provide to help you make a decision?"
        
        return {
            "response": response,
            "use_rag": False,
            "adapters": ["sales", "persuasion"],
            "context_updates": {
                "closing_attempts": closing_attempts + 1
            },
            "actions": [{
                "type": "update_crm",
                "params": {
                    "stage": "closing",
                    "attempt": closing_attempts + 1
                }
            }]
        }
    
    async def _handle_sales_follow_up(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle sales follow-up state logic."""
        # Check follow-up type
        follow_up_type = context.get("follow_up_type", "general")
        
        if follow_up_type == "demo_scheduled":
            response = "I've scheduled your demo for [demo_time]. Is there anything specific you'd like the specialist to focus on during the demo?"
        elif follow_up_type == "materials_sent":
            response = "I've sent over the materials you requested. Have you had a chance to review them?"
        else:
            response = "I wanted to follow up on our previous conversation. Have you given any more thought to our solution?"
        
        return {
            "response": response,
            "use_rag": False,
            "adapters": ["sales"],
            "context_updates": {
                "follow_up_completed": True
            },
            "actions": [{
                "type": "update_crm",
                "params": {
                    "stage": "follow_up",
                    "status": "active"
                }
            }]
        }
    
    # Consultancy bot state handlers
    
    async def _handle_consultancy_problem_identification(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle consultancy problem identification state logic."""
        # Check if we've identified the problem area
        if not context.get("problem_areas"):
            response = "Can you tell me more about the specific challenges or issues you're facing in your business?"
            use_rag = False
        else:
            response = "Let's dig deeper into these issues. What do you think is causing these problems?"
            use_rag = True
        
        return {
            "response": response,
            "use_rag": use_rag,
            "adapters": ["consultant", "active_listening"],
            "context_updates": {
                "problem_identification_started": True
            }
        }
    
    async def _handle_consultancy_analysis(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle consultancy analysis state logic."""
        # Use RAG to get industry-specific insights
        return {
            "response": "Based on what you've shared, I'm analyzing similar situations in your industry. What specific outcomes are you hoping to achieve?",
            "use_rag": True,
            "adapters": ["consultant", "hypnosis"],
            "context_updates": {
                "analysis_started": True
            }
        }
    
    async def _handle_consultancy_recommendation(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle consultancy recommendation state logic."""
        # Tailor recommendation to problem areas
        problem_areas = context.get("problem_areas", [])
        
        if problem_areas:
            response = f"Based on my analysis of your situation with {', '.join(problem_areas)}, I recommend a phased approach that addresses each area systematically."
        else:
            response = "Based on my analysis, I have several recommendations that could help improve your situation."
        
        return {
            "response": response,
            "use_rag": True,
            "adapters": ["consultant", "persuasion"],
            "context_updates": {
                "recommendations_provided": True
            }
        }
    
    async def _handle_consultancy_implementation_planning(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle consultancy implementation planning state logic."""
        return {
            "response": "Let's develop an implementation plan for these recommendations. What timeline are you considering?",
            "use_rag": True,
            "adapters": ["consultant"],
            "context_updates": {
                "implementation_planning_started": True
            }
        }
    
    async def _handle_consultancy_follow_up(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle consultancy follow-up state logic."""
        return {
            "response": "I'd like to schedule a follow-up session to discuss your progress and address any new challenges that have arisen. Would that be helpful?",
            "use_rag": False,
            "adapters": ["consultant"],
            "context_updates": {
                "follow_up_proposed": True
            }
        }
    
    # Support bot state handlers
    
    async def _handle_support_issue_identification(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle support issue identification state logic."""
        # Check if we've identified the issue
        if not context.get("issue_type"):
            response = "I'm sorry to hear you're having an issue. Could you please describe what's happening in detail?"
            use_rag = False
        else:
            response = f"I understand you're experiencing an issue with {context['issue_type']}. Let me help you resolve this."
            use_rag = True
        
        return {
            "response": response,
            "use_rag": use_rag,
            "adapters": ["support"],
            "context_updates": {
                "issue_identification_started": True
            }
        }
    
    async def _handle_support_troubleshooting(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle support troubleshooting state logic."""
        # Get issue type and troubleshooting steps
        issue_type = context.get("issue_type", "general")
        steps_tried = context.get("troubleshooting_steps_tried", [])
        
        # If no steps tried, suggest first step
        if not steps_tried:
            response = "Let's try some troubleshooting steps. First, could you try [first_step_for_issue_type]?"
        else:
            response = "Thanks for trying that. Let's try another approach. Could you [next_step_for_issue_type]?"
        
        return {
            "response": response,
            "use_rag": True,
            "adapters": ["support", "technical"],
            "context_updates": {
                "troubleshooting_in_progress": True,
                "troubleshooting_steps_tried": steps_tried + ["latest_step"]
            }
        }
    
    async def _handle_support_resolution(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle support resolution state logic."""
        return {
            "response": "Great! It seems like the issue is resolved. Is everything working correctly now?",
            "use_rag": False,
            "adapters": ["support"],
            "context_updates": {
                "resolution_proposed": True
            },
            "actions": [{
                "type": "update_ticket",
                "params": {
                    "status": "resolved_pending_confirmation"
                }
            }]
        }
    
    async def _handle_support_confirmation(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle support confirmation state logic."""
        return {
            "response": "I'm glad we could resolve your issue. Is there anything else you need help with today?",
            "use_rag": False,
            "adapters": ["support"],
            "context_updates": {
                "resolution_confirmed": True
            },
            "actions": [{
                "type": "update_ticket",
                "params": {
                    "status": "resolved"
                }
            }]
        }
    
    async def _handle_support_escalation(
        self,
        message: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Handle support escalation state logic."""
        return {
            "response": "I understand this issue requires additional assistance. I'm escalating this to our specialized support team. They'll contact you within the next 4 hours. Is there a specific time that works best for you?",
            "use_rag": False,
            "adapters": ["support"],
            "context_updates": {
                "escalation_initiated": True
            },
            "actions": [{
                "type": "escalate_ticket",
                "params": {
                    "priority": "high",
                    "reason": "Complex issue requiring specialist"
                }
            }]
        } 