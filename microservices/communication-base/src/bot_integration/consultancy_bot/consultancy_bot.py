"""
Consultancy Bot implementation with specialized LLM, adapters, and MLOps integration.
Handles business consulting, legal advice, and strategic planning queries.
"""

from langchain.llms import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer
from src.clients.system_users_repository_client import SystemUsersRepositoryClient
from src.session.session_manager import session_manager
from src.integrations.mlops_integration import mlops
from src.bot_integration.agent_client import AgentClient
from src.bot_integration.consultancy_bot.config import CONSULTANCY_BOT_CONFIG
from src.bot_integration.consultancy_bot.nlp_utils import get_nlp_processor
from src.bot_integration.consultancy_bot.response_enhancer import get_response_enhancer
import os
import structlog
from typing import Dict, Any, Tuple, List, Optional
import asyncio

# Configure logger
logger = structlog.get_logger(__name__)

class ConsultancyBot:
    def __init__(self):
        self.model_path = "models/consultancy/base_model"
        self.adapters_path = "models/consultancy/adapters"
        self.initialize_model()
        self.config = CONSULTANCY_BOT_CONFIG
        self.nlp_processor = get_nlp_processor(self.config)
        self.response_enhancer = get_response_enhancer(self.config)
        self.active_adapter = None
        self.user_repository = SystemUsersRepositoryClient()
        
        # Initialize action handlers registry
        self.action_handlers = {}
        self.register_default_actions()
        
        logger.info("ConsultancyBot initialized")
        
    def initialize_model(self):
        """Initialize the specialized consultancy model and adapters."""
        # Load the fine-tuned consultancy model
        self.model = AutoModelForCausalLM.from_pretrained(self.model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        
        # Load specialized adapters
        self.adapters = {
            "legal": f"{self.adapters_path}/legal",
            "finance": f"{self.adapters_path}/finance",
            "strategy": f"{self.adapters_path}/strategy"
        }
        self.load_adapters()
        
        # Create LangChain wrapper
        self.llm = HuggingFacePipeline.from_model_id(
            model_id=self.model_path,
            task="text-generation",
            model=self.model,
            tokenizer=self.tokenizer
        )
    
    def load_adapters(self):
        """Load all available LoRA adapters."""
        for adapter_name, adapter_path in self.adapters.items():
            if os.path.exists(adapter_path):
                self.model.load_adapter(adapter_path)
                
    def register_default_actions(self):
        """Register default action handlers."""
        self.register_action("delegate_to_agent", self.handle_agent_delegation)
        self.register_action("use_legal_adapter", self.handle_adapter_selection)
        self.register_action("use_finance_adapter", self.handle_adapter_selection)
        self.register_action("use_strategy_adapter", self.handle_adapter_selection)
        self.register_action("enhance_response", self.handle_response_enhancement)
        
    def register_action(self, action_name: str, handler_function):
        """
        Register an action handler function.
        
        Args:
            action_name: Name of the action
            handler_function: Function that handles the action
        """
        self.action_handlers[action_name] = handler_function
        logger.info(f"Registered handler for action: {action_name}")
    
    async def execute_action(self, 
                           action_name: str, 
                           context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute an action using the registered handler.
        
        Args:
            action_name: Name of the action to execute
            context: Context information for the action
            
        Returns:
            Result of the action, or None if action failed or not found
        """
        if action_name in self.action_handlers:
            try:
                logger.info(f"Executing action: {action_name}")
                return await self.action_handlers[action_name](context)
            except Exception as e:
                logger.exception(f"Error executing action {action_name}", error=str(e))
                return None
        else:
            logger.warning(f"No handler registered for action: {action_name}")
            return None
    
    async def update_model(self, new_model_path: str):
        """MLOps pipeline calls this to update the base model."""
        try:
            new_model = AutoModelForCausalLM.from_pretrained(new_model_path)
            new_tokenizer = AutoTokenizer.from_pretrained(new_model_path)
            
            # Update model components
            self.model = new_model
            self.tokenizer = new_tokenizer
            
            # Reload adapters with new model
            self.load_adapters()
            
            # Update LangChain wrapper
            self.llm = HuggingFacePipeline.from_model_id(
                model_id=new_model_path,
                task="text-generation",
                model=self.model,
                tokenizer=self.tokenizer
            )
            
            # Log successful update
            await mlops.log_interaction(
                "consultancy",
                {"event": "model_update", "status": "success"}
            )
            
        except Exception as e:
            await mlops.log_interaction(
                "consultancy",
                {"event": "model_update", "status": "failed", "error": str(e)}
            )
            raise
    
    async def update_adapter(self, adapter_name: str, new_adapter_path: str):
        """MLOps pipeline calls this to update specific adapters."""
        try:
            self.model.load_adapter(new_adapter_path)
            self.adapters[adapter_name] = new_adapter_path
            
            await mlops.log_interaction(
                "consultancy",
                {"event": "adapter_update", "adapter": adapter_name, "status": "success"}
            )
            
        except Exception as e:
            await mlops.log_interaction(
                "consultancy",
                {"event": "adapter_update", "adapter": adapter_name, "status": "failed", "error": str(e)}
            )
            raise
    
    def process_message_with_rules(self, text: str, 
                                  memory_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a message using the detection rules from configuration.
        Uses NLP features for enhanced rule matching.
        
        Args:
            text: The message text to process
            memory_context: Optional memory context for contextual rule matching
            
        Returns:
            Dictionary with detection results for each rule
        """
        results = {}
        detection_rules = self.config.get("detection_rules", {})
        
        # Extract NLP features for enhanced matching
        nlp_features = self.nlp_processor.process_text(text)
        
        # Process text with each enabled rule
        for rule_name, rule in detection_rules.items():
            if rule.get("enabled", False):
                confidence = 0.0
                matched_items = []
                
                # Keyword matching
                if "keywords" in rule:
                    keywords = rule.get("keywords", [])
                    text_lower = text.lower()
                    
                    keyword_matches = []
                    for keyword in keywords:
                        if keyword.lower() in text_lower:
                            keyword_matches.append(keyword)
                    
                    if keyword_matches:
                        keyword_confidence = min(1.0, len(keyword_matches) / max(1, len(keywords) * 0.25))
                        confidence += keyword_confidence * 0.6  # Weight keyword matches at 60%
                        matched_items.extend([{"type": "keyword", "value": k} for k in keyword_matches])
                
                # Entity matching
                if "required_entities" in rule:
                    required_entities = rule.get("required_entities", [])
                    entity_matches = [e for e in nlp_features.get("entities", []) 
                                     if e["type"] in required_entities]
                    
                    if entity_matches:
                        entity_confidence = min(1.0, len(entity_matches) / len(required_entities))
                        confidence += entity_confidence * 0.3  # Weight entity matches at 30%
                        matched_items.extend([{"type": "entity", "value": e["text"]} for e in entity_matches])
                
                # Sentiment matching
                if "sentiment_range" in rule:
                    sentiment = nlp_features.get("sentiment", 0.5)
                    min_sentiment, max_sentiment = rule["sentiment_range"]
                    
                    if min_sentiment <= sentiment <= max_sentiment:
                        sentiment_confidence = 0.1  # Fixed contribution
                        confidence += sentiment_confidence
                        matched_items.append({"type": "sentiment", "value": sentiment})
                
                # Apply memory context boosts if available
                if memory_context and "contextual_boost" in rule:
                    boost_config = rule["contextual_boost"]
                    boost_topics = boost_config.get("previous_topics", [])
                    boost_factor = boost_config.get("boost_factor", 0.1)
                    
                    if any(topic in memory_context.get("topics", []) for topic in boost_topics):
                        confidence += boost_factor
                        matched_items.append({"type": "context_boost", "value": boost_factor})
                
                # Calculate final match
                threshold = rule.get("confidence_threshold", 0.5)
                is_match = confidence >= threshold
                
                # Determine action
                action = rule.get("action") if is_match else None
                
                # Get enhancement type if applicable
                enhancement_type = rule.get("enhancement_type") if is_match else None
                
                # Store results
                results[rule_name] = {
                    "is_match": is_match,
                    "confidence": confidence,
                    "matched_items": matched_items,
                    "action": action,
                    "enhancement_type": enhancement_type,
                    "threshold": threshold
                }
                
                # Log detection results if there's a match
                if is_match:
                    logger.info(
                        f"Detected {rule_name}",
                        confidence=confidence,
                        matched_items=matched_items,
                        threshold=threshold
                    )
        
        return results
    
    async def handle_agent_delegation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle delegation to agent.
        
        Args:
            context: Action context
            
        Returns:
            Result of delegation
        """
        try:
            prompt = context.get("prompt")
            user_id = context.get("user_id")
            session_id = context.get("session_id")
            rule_name = context.get("rule_name")
            memory = context.get("memory")
            
            # Get action config
            action_config = self.config.get("actions", {}).get("delegate_to_agent", {})
            
            # Create agent client
            agent_client = AgentClient()
            
            # Get agent urgency from config
            urgency = action_config.get("urgency", "normal")
            
            # Send to agent
            agent_response = await agent_client.send_request(
                text=prompt,
                user_id=user_id,
                session_id=session_id,
                urgency=urgency
            )
            
            # Check success criteria
            success_criteria = action_config.get("success_criteria", {})
            success = True
            
            if "status" in success_criteria and agent_response.get("status") != success_criteria["status"]:
                success = False
            
            if "content_present" in success_criteria and success_criteria["content_present"]:
                if not agent_response.get("content"):
                    success = False
            
            # Log the delegation result
            await mlops.log_interaction(
                "consultancy",
                {
                    "event": f"{rule_name}_delegated",
                    "session_id": session_id,
                    "agent_response_status": agent_response.get("status"),
                    "success": success
                }
            )
            
            if success:
                # Store this interaction in memory
                if memory:
                    memory.save_context(
                        {"input": prompt},
                        {"output": agent_response.get("content")}
                    )
                
                return {
                    "status": "success",
                    "content": agent_response.get("content"),
                    "action_taken": "delegate_to_agent",
                    "rule_name": rule_name
                }
            else:
                # If delegation failed but there's a fallback action
                fallback_action = action_config.get("fallback_action")
                if fallback_action:
                    logger.info(f"Delegation failed, using fallback action: {fallback_action}")
                    return {
                        "status": "fallback",
                        "fallback_action": fallback_action,
                        "original_action": "delegate_to_agent",
                        "error": "Agent delegation failed"
                    }
                else:
                    return {
                        "status": "error",
                        "error": "Agent delegation failed",
                        "action_taken": "delegate_to_agent",
                        "rule_name": rule_name
                    }
        
        except Exception as e:
            logger.exception(f"Error in agent delegation", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "action_taken": "delegate_to_agent"
            }
    
    async def handle_adapter_selection(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle adapter selection.
        
        Args:
            context: Action context
            
        Returns:
            Result of adapter selection
        """
        try:
            action_name = context.get("action")
            rule_name = context.get("rule_name")
            
            # Get action config
            action_config = self.config.get("actions", {}).get(action_name, {})
            
            # Get adapter name
            adapter_name = action_config.get("adapter")
            
            if adapter_name and adapter_name in self.adapters:
                # Set the active adapter for use in chain creation
                self.active_adapter = adapter_name
                
                logger.info(f"Selected adapter: {adapter_name}", 
                           rule_name=rule_name,
                           action=action_name)
                
                return {
                    "status": "success",
                    "adapter": adapter_name,
                    "action_taken": action_name,
                    "rule_name": rule_name
                }
            else:
                logger.warning(f"Invalid adapter: {adapter_name}")
                return {
                    "status": "error",
                    "error": f"Invalid adapter: {adapter_name}",
                    "action_taken": action_name,
                    "rule_name": rule_name
                }
                
        except Exception as e:
            logger.exception(f"Error in adapter selection", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "action_taken": context.get("action")
            }
    
    async def handle_response_enhancement(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle response enhancement.
        
        Args:
            context: Action context including response to enhance
            
        Returns:
            Result with enhanced response
        """
        try:
            response = context.get("response")
            rule_name = context.get("rule_name")
            enhancement_type = context.get("enhancement_type")
            
            if not response or not enhancement_type:
                logger.warning("Missing response or enhancement_type for enhancement")
                return {
                    "status": "error",
                    "error": "Missing response or enhancement_type",
                    "action_taken": "enhance_response"
                }
            
            # Determine domain from active adapter or rule
            domain = None
            if self.active_adapter:
                domain = self.active_adapter
            
            # Enhance the response
            enhanced_response = await self.response_enhancer.enhance_response(
                response=response,
                enhancement_type=enhancement_type,
                domain=domain
            )
            
            return {
                "status": "success",
                "original_response": response,
                "enhanced_response": enhanced_response,
                "action_taken": "enhance_response",
                "rule_name": rule_name,
                "enhancement_type": enhancement_type
            }
            
        except Exception as e:
            logger.exception(f"Error in response enhancement", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "action_taken": "enhance_response"
            }

# Global instance
consultancy_bot = ConsultancyBot()

async def handle_request(prompt: str, session_id: str, user_id: str) -> str:
    """Handle a consultancy request with specialized model and adapters."""
    try:
        # Store actions taken during processing
        actions_taken = []
        
        # Reset active adapter at start of request
        consultancy_bot.active_adapter = None
        
        # Get or create session
        session = await session_manager.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
            bot_type="consultancy"
        )
        
        # Get user profile
        user_profile = await consultancy_bot.user_repository.get_user_profile(user_id)
        
        # Get conversation memory
        memory = session_manager.get_session_memory(session_id)
        
        # Create memory context for contextual rule matching
        memory_context = None
        if memory and memory.chat_memory.messages:
            # Simple topic extraction from recent messages
            recent_messages = memory.chat_memory.messages[-5:]  # Last 5 messages
            topics = []
            for msg in recent_messages:
                msg_content = getattr(msg, "content", "")
                # Extract possible topics from message content
                if "legal" in msg_content.lower():
                    topics.append("legal")
                if "finance" in msg_content.lower() or "financial" in msg_content.lower():
                    topics.append("finance")
                if "strategy" in msg_content.lower() or "strategic" in msg_content.lower():
                    topics.append("strategy")
            
            memory_context = {
                "topics": list(set(topics)),  # Deduplicate
                "message_count": len(memory.chat_memory.messages)
            }
        
        # Process message with detection rules
        detection_results = consultancy_bot.process_message_with_rules(
            prompt, memory_context=memory_context)
        
        # Track if we should early return
        early_return = False
        early_return_content = None
        
        # Process pre-LLM actions
        for rule_name, result in detection_results.items():
            if result["is_match"] and result["action"]:
                action_name = result["action"]
                action_config = consultancy_bot.config.get("actions", {}).get(action_name, {})
                
                if action_config.get("enabled", False):
                    # Execute the action
                    action_result = await consultancy_bot.execute_action(
                        action_name=action_name,
                        context={
                            "rule_name": rule_name,
                            "action": action_name,
                            "prompt": prompt,
                            "user_id": user_id,
                            "session_id": session_id,
                            "confidence": result["confidence"],
                            "memory": memory
                        }
                    )
                    
                    # Record action
                    if action_result:
                        actions_taken.append(action_result)
                        
                        # Check if we should return early
                        if action_name == "delegate_to_agent" and action_result.get("status") == "success":
                            early_return = True
                            early_return_content = action_result.get("content")
                        
                        # Check if we should use a fallback action
                        if action_result.get("status") == "fallback" and action_result.get("fallback_action"):
                            fallback_action = action_result.get("fallback_action")
                            logger.info(f"Using fallback action: {fallback_action}")
                            
                            # Execute fallback action
                            fallback_result = await consultancy_bot.execute_action(
                                action_name=fallback_action,
                                context={
                                    "rule_name": rule_name,
                                    "action": fallback_action,
                                    "prompt": prompt,
                                    "user_id": user_id,
                                    "session_id": session_id,
                                    "memory": memory
                                }
                            )
                            
                            if fallback_result:
                                actions_taken.append(fallback_result)
        
        # Early return if appropriate
        if early_return and early_return_content:
            return early_return_content
        
        # Create chain with specialized components (possibly with an adapter selected)
        chain = create_specialized_chain(
            llm=consultancy_bot.llm,
            memory=memory,
            user_profile=user_profile,
            adapter=consultancy_bot.active_adapter
        )
        
        # Generate response
        response = await chain.ainvoke({
            "question": prompt,
            "chat_history": memory.chat_memory.messages if memory else [],
            "user_profile": user_profile
        })
        
        # Post-process the generated response
        # Check if we need to enhance the response based on post-processing rules
        post_processing_results = consultancy_bot.process_message_with_rules(response["answer"])
        
        final_response = response["answer"]
        
        # Process post-LLM actions
        for rule_name, result in post_processing_results.items():
            if result["is_match"] and result["action"] == "enhance_response":
                enhancement_type = result.get("enhancement_type")
                if enhancement_type:
                    # Execute the enhancement
                    enhancement_result = await consultancy_bot.execute_action(
                        action_name="enhance_response",
                        context={
                            "rule_name": rule_name,
                            "action": "enhance_response",
                            "response": final_response,
                            "enhancement_type": enhancement_type,
                            "user_id": user_id,
                            "session_id": session_id
                        }
                    )
                    
                    if enhancement_result and enhancement_result.get("status") == "success":
                        actions_taken.append(enhancement_result)
                        final_response = enhancement_result.get("enhanced_response", final_response)
        
        # Save the final response to memory
        if memory:
            memory.save_context(
                {"input": prompt},
                {"output": final_response}
            )
        
        # Log interaction for monitoring
        await mlops.log_interaction(
            "consultancy",
            {
                "event": "request",
                "session_id": session_id,
                "status": "success",
                "actions_taken": [a.get("action_taken") for a in actions_taken if a],
                "response_length": len(final_response)
            }
        )
        
        return final_response
        
    except Exception as e:
        # Log error
        await mlops.log_interaction(
            "consultancy",
            {
                "event": "request",
                "session_id": session_id,
                "status": "failed",
                "error": str(e)
            }
        )
        logger.exception("Error handling consultancy request", 
                       session_id=session_id,
                       error=str(e))
        raise