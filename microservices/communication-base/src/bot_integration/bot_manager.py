"""
Bot Manager Module

This module provides a manager for handling bot conversations,
including message processing, response generation, and context management.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import structlog
import asyncio
import uuid

from src.clients.system_users_repository_client import SystemUsersRepositoryClient
from src.clients.campaign_users_repository_client import CampaignUsersRepositoryClient
from src.storage.entity_repository_manager import EntityRepositoryManager
from src.config.settings import get_settings
from src.config.config_manager import ConfigManager

logger = structlog.get_logger(__name__)

class BotManager:
    """
    Manager for bot conversations.
    
    This class handles the processing of messages, maintains conversation context,
    and manages the generation of bot responses using appropriate models and templates.
    """
    
    def __init__(
        self,
        system_users_repository: SystemUsersRepositoryClient,
        campaign_users_repository: CampaignUsersRepositoryClient,
        entity_repository_manager: Optional[EntityRepositoryManager] = None,
        config_manager: Optional[ConfigManager] = None
    ):
        """
        Initialize the bot manager.
        
        Args:
            system_users_repository: Repository for system users
            campaign_users_repository: Repository for campaign users
            entity_repository_manager: Manager for entity repositories
            config_manager: Configuration manager
        """
        self.system_users_repository = system_users_repository
        self.campaign_users_repository = campaign_users_repository
        self.entity_repository_manager = entity_repository_manager or EntityRepositoryManager()
        self.config_manager = config_manager or ConfigManager()
        self.settings = get_settings()
        
        # Load NLP components as needed
        self._sentiment_analyzer = None
        self._intent_classifier = None
        self._entity_extractor = None
        
        logger.info("Bot manager initialized")
    
    async def handle_message(
        self,
        message: str,
        user_id: str,
        campaign_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle an incoming message from a user.
        
        Args:
            message: The message text
            user_id: ID of the user
            campaign_id: Optional ID of the campaign (required if session_id not provided)
            session_id: Optional session ID (required if campaign_id not provided)
            metadata: Optional additional metadata about the message
            
        Returns:
            Dictionary with processing results and response
            
        Raises:
            ValueError: If neither campaign_id nor session_id is provided
        """
        if not (campaign_id or session_id):
            raise ValueError("Either campaign_id or session_id must be provided")
            
        # Get or create conversation state
        conversation = await self._get_conversation_state(user_id, campaign_id, session_id)
        
        if not conversation:
            logger.error(
                "Failed to get or create conversation state",
                user_id=user_id,
                campaign_id=campaign_id,
                session_id=session_id
            )
            return {
                "success": False,
                "error": "Failed to get or create conversation state"
            }
            
        # Ensure we have campaign_id and session_id
        campaign_id = conversation.get("campaign_id")
        session_id = conversation.get("session_id")
        
        # Get campaign data if available
        campaign = None
        if campaign_id:
            campaign = await self.campaign_users_repository.get_campaign(campaign_id)
        
        # Add message to conversation history
        message_data = {
            "content": message,
            "direction": "incoming",
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        if campaign_id:
            await self.campaign_users_repository.add_message_to_history(
                user_id=user_id,
                campaign_id=campaign_id,
                session_id=session_id,
                message=message_data
            )
        else:
            await self.system_users_repository.add_message_to_history(
                user_id=user_id,
                session_id=session_id,
                message=message_data
            )
        
        # Analyze message
        analysis_results = await self._analyze_message(message, conversation)
        
        # Store analysis results
        await self.entity_repository_manager.store_entities(
            user_id=user_id,
            session_id=session_id,
            bot_type="default",
            entities=analysis_results,
            campaign_id=campaign_id
        )
        
        # Update conversation context with extracted information
        context_updates = self._extract_context_from_analysis(analysis_results)
        if context_updates:
            if campaign_id:
                await self.campaign_users_repository.update_conversation_context(
                    user_id=user_id,
                    campaign_id=campaign_id,
                    session_id=session_id,
                    context_updates=context_updates
                )
            else:
                await self.system_users_repository.update_conversation_context(
                    user_id=user_id,
                    session_id=session_id,
                    context_updates=context_updates
                )
        
        # Generate response
        response = await self._generate_response(
            conversation=conversation,
            message=message,
            analysis_results=analysis_results
        )
        
        # Add response to conversation history
        response_data = {
            "content": response.get("text", ""),
            "direction": "outgoing",
            "timestamp": datetime.utcnow(),
            "metadata": {
                "response_type": response.get("type", "text"),
                "template_id": response.get("template_id"),
                "processed_by": "bot_manager"
            }
        }
        
        if campaign_id:
            await self.campaign_users_repository.add_message_to_history(
                user_id=user_id,
                campaign_id=campaign_id,
                session_id=session_id,
                message=response_data
            )
        else:
            await self.system_users_repository.add_message_to_history(
                user_id=user_id,
                session_id=session_id,
                message=response_data
            )
        
        # Update conversation summary if needed
        if len(conversation.get("message_history", [])) % 5 == 0:
            summary = self._generate_conversation_summary(conversation)
            if summary:
                if campaign_id:
                    await self.campaign_users_repository.update_conversation_summary(
                        user_id=user_id,
                        campaign_id=campaign_id,
                        session_id=session_id,
                        summary=summary.get("summary", ""),
                        key_points=summary.get("key_points", [])
                    )
                else:
                    await self.system_users_repository.update_conversation_summary(
                        user_id=user_id,
                        session_id=session_id,
                        summary=summary.get("summary", ""),
                        key_points=summary.get("key_points", [])
                    )
        
        # Return processing results
        return {
            "success": True,
            "response": response.get("text", ""),
            "response_type": response.get("type", "text"),
            "session_id": session_id,
            "campaign_id": campaign_id,
            "user_id": user_id,
            "analysis": analysis_results
        }
    
    async def _get_conversation_state(
        self,
        user_id: str,
        campaign_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get or create a conversation state.
        
        Args:
            user_id: ID of the user
            campaign_id: Optional ID of the campaign
            session_id: Optional session ID
            
        Returns:
            Conversation state or None if failed
        """
        # Try to get existing conversation state
        try:
            if session_id:
                if campaign_id:
                    conversation = await self.campaign_users_repository.get_conversation_state(
                        user_id=user_id,
                        campaign_id=campaign_id,
                        session_id=session_id
                    )
                else:
                    conversation = await self.system_users_repository.get_conversation_state(
                        user_id=user_id,
                        session_id=session_id
                    )
                
                if conversation:
                    return conversation
            
            if campaign_id:
                conversation = await self.campaign_users_repository.get_conversation_state(
                    user_id=user_id,
                    campaign_id=campaign_id
                )
                
                if conversation:
                    return conversation
                
                # If no conversation exists but we have campaign_id, create one
                campaign = await self.campaign_users_repository.get_campaign(campaign_id)
                if campaign:
                    # Get campaign type and config
                    campaign_type = campaign.get("type", "unknown")
                    config = campaign.get("config", {})
                    
                    # Get stages for this campaign type
                    all_stages = self._get_stages_for_campaign_type(campaign_type, config)
                    initial_stage = all_stages[0] if all_stages else "initial"
                    
                    # Create new session ID if not provided
                    new_session_id = session_id or f"session_{uuid.uuid4()}"
                    
                    # Create conversation state
                    conversation_id = await self.campaign_users_repository.create_conversation_state({
                        "user_id": user_id,
                        "campaign_id": campaign_id,
                        "session_id": new_session_id,
                        "current_stage": initial_stage,
                        "all_stages": all_stages,
                        "stages": [{
                            "name": initial_stage,
                            "entered_at": datetime.utcnow(),
                            "exited_at": None,
                            "completed": False
                        }],
                        "context": {
                            "campaign_type": campaign_type,
                            "campaign_name": campaign.get("name", ""),
                            "initial_config": config
                        },
                        "status": "active",
                        "message_history": [],
                        "progress_percentage": 0
                    })
                    
                    # Get the created conversation
                    return await self.campaign_users_repository.get_conversation_state(
                        user_id=user_id,
                        campaign_id=campaign_id
                    )
            
            # If we reach here, we couldn't get or create a conversation state
            return None
            
        except Exception as e:
            logger.error(
                "Error getting conversation state",
                user_id=user_id,
                campaign_id=campaign_id,
                session_id=session_id,
                error=str(e)
            )
            return None
    
    async def _analyze_message(
        self,
        message: str,
        conversation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a message to extract intent, sentiment, and other information.
        
        Args:
            message: The message to analyze
            conversation: The conversation state
            
        Returns:
            Dictionary with analysis results
        """
        # Get campaign type
        context = conversation.get("context", {})
        campaign_type = context.get("campaign_type", "unknown")
        
        # Initialize results
        results = {}
        
        # Analyze sentiment
        results["sentiment"] = self._analyze_sentiment(message)
        
        # Analyze intent
        results["intent"] = self._analyze_intent(message, campaign_type)
        
        # Extract entities
        results["entities"] = self._extract_entities(message)
        
        # Add campaign-specific analysis
        if campaign_type == "sales":
            results["buying_signals"] = self._analyze_buying_signals(message, conversation)
            results["objections"] = self._analyze_objections(message, conversation)
        elif campaign_type == "support":
            results["issue_classification"] = self._classify_support_issue(message)
            results["urgency"] = self._determine_urgency(message, conversation)
        elif campaign_type == "consultancy":
            results["needs"] = self._analyze_consultancy_needs(message, conversation)
            results["expertise_areas"] = self._identify_expertise_areas(message)
        
        logger.debug(
            "Message analysis completed",
            campaign_type=campaign_type,
            analysis_types=list(results.keys())
        )
        
        return results
    
    def _analyze_sentiment(self, message: str) -> Dict[str, Any]:
        """
        Analyze sentiment in a message.
        
        Args:
            message: The message to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        # Simple implementation - would be replaced with actual NLP model
        # Placeholder for demo purposes
        positive_words = ["good", "great", "excellent", "happy", "interested", "like", "love"]
        negative_words = ["bad", "poor", "unhappy", "disappointed", "dislike", "hate", "problem"]
        
        message_lower = message.lower()
        
        # Count positive and negative words
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        # Calculate score (-1 to 1)
        total = positive_count + negative_count
        if total == 0:
            score = 0
        else:
            score = (positive_count - negative_count) / total
        
        # Determine sentiment
        if score > 0.2:
            sentiment = "positive"
        elif score < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "score": score,
            "sentiment": sentiment,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def _analyze_intent(
        self,
        message: str,
        campaign_type: str
    ) -> Dict[str, Any]:
        """
        Analyze intent in a message.
        
        Args:
            message: The message to analyze
            campaign_type: Type of campaign
            
        Returns:
            Dictionary with intent analysis results
        """
        # Simple implementation - would be replaced with actual NLP model
        # Placeholder for demo purposes
        message_lower = message.lower()
        
        # Common intents
        intents = []
        
        # Check for question intent
        if "?" in message or any(word in message_lower for word in ["what", "how", "when", "where", "why", "who"]):
            intents.append("question")
        
        # Check for greeting intent
        if any(word in message_lower for word in ["hello", "hi", "hey", "greetings"]):
            intents.append("greeting")
        
        # Campaign-specific intents
        if campaign_type == "sales":
            # Check for pricing intent
            if any(word in message_lower for word in ["price", "cost", "expensive", "cheap", "discount", "offer"]):
                intents.append("pricing")
            
            # Check for interest intent
            if any(word in message_lower for word in ["interested", "tell me more", "want to know", "learn more"]):
                intents.append("interest")
                is_interested = True
            else:
                is_interested = False
                
        elif campaign_type == "support":
            # Check for problem intent
            if any(word in message_lower for word in ["problem", "issue", "error", "bug", "doesn't work", "broken"]):
                intents.append("problem")
                
            # Check for thank intent
            if any(word in message_lower for word in ["thank", "thanks", "appreciate", "helpful"]):
                intents.append("thank")
        
        # Determine primary intent
        primary_intent = intents[0] if intents else "unknown"
        
        return {
            "intents": intents,
            "primary_intent": primary_intent,
            "is_interested": is_interested if campaign_type == "sales" else None,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def _extract_entities(self, message: str) -> Dict[str, Any]:
        """
        Extract entities from a message.
        
        Args:
            message: The message to analyze
            
        Returns:
            Dictionary with extracted entities
        """
        # Simple implementation - would be replaced with actual NLP model
        # Placeholder for demo purposes
        entities = {
            "names": [],
            "dates": [],
            "numbers": [],
            "custom_entities": []
        }
        
        # In a real implementation, this would use an NLP entity extractor
        
        return {
            "entities": entities,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def _analyze_buying_signals(
        self,
        message: str,
        conversation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze buying signals in a sales conversation.
        
        Args:
            message: The message to analyze
            conversation: The conversation state
            
        Returns:
            Dictionary with buying signal analysis
        """
        # Simple implementation - would be replaced with actual NLP model
        # Placeholder for demo purposes
        message_lower = message.lower()
        
        # Check for buying signals
        buying_signal_phrases = [
            "interested in buying",
            "want to purchase",
            "how do i get",
            "how can i buy",
            "pricing options",
            "payment methods",
            "when can i start",
            "ready to move forward",
            "sign up",
            "get started"
        ]
        
        found_signals = [signal for signal in buying_signal_phrases if signal in message_lower]
        has_buying_signals = len(found_signals) > 0
        
        return {
            "has_buying_signals": has_buying_signals,
            "signals_found": found_signals,
            "signal_strength": len(found_signals) * 0.2,  # Simple measure of strength
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def _analyze_objections(
        self,
        message: str,
        conversation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze sales objections in a message.
        
        Args:
            message: The message to analyze
            conversation: The conversation state
            
        Returns:
            Dictionary with objection analysis
        """
        # Simple implementation - would be replaced with actual NLP model
        # Placeholder for demo purposes
        message_lower = message.lower()
        
        # Common objection types
        objection_types = {
            "price": ["expensive", "costs too much", "too costly", "can't afford", "budget"],
            "need": ["don't need", "not necessary", "why would i need", "don't see the value"],
            "time": ["not now", "later", "not ready", "need time", "too soon"],
            "trust": ["not sure", "need to think", "uncertain", "don't know if"],
            "competitor": ["another option", "competitor", "other solution", "already using"]
        }
        
        # Find objections
        found_objections = {}
        for objection_type, phrases in objection_types.items():
            matches = [phrase for phrase in phrases if phrase in message_lower]
            if matches:
                found_objections[objection_type] = matches
        
        has_objections = len(found_objections) > 0
        
        return {
            "has_objections": has_objections,
            "objection_types": list(found_objections.keys()),
            "objections_found": found_objections,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def _classify_support_issue(self, message: str) -> Dict[str, Any]:
        """
        Classify the type of support issue in a message.
        
        Args:
            message: The message to analyze
            
        Returns:
            Dictionary with issue classification
        """
        # Simple implementation - would be replaced with actual NLP model
        # In a real implementation, this would use a trained classifier
        return {
            "issue_type": "technical",  # Placeholder
            "confidence": 0.8,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def _determine_urgency(
        self,
        message: str,
        conversation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine the urgency of a support request.
        
        Args:
            message: The message to analyze
            conversation: The conversation state
            
        Returns:
            Dictionary with urgency assessment
        """
        # Simple implementation - would be replaced with actual NLP model
        message_lower = message.lower()
        
        # Urgency indicators
        high_urgency = ["urgent", "emergency", "immediately", "asap", "critical"]
        medium_urgency = ["soon", "today", "important"]
        
        # Check for urgency phrases
        if any(word in message_lower for word in high_urgency):
            urgency = "high"
        elif any(word in message_lower for word in medium_urgency):
            urgency = "medium"
        else:
            urgency = "low"
        
        return {
            "urgency": urgency,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def _analyze_consultancy_needs(
        self,
        message: str,
        conversation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze consultancy needs in a message.
        
        Args:
            message: The message to analyze
            conversation: The conversation state
            
        Returns:
            Dictionary with needs analysis
        """
        # Simple implementation - would be replaced with actual NLP model
        # In a real implementation, this would use more sophisticated analysis
        return {
            "identified_needs": ["strategy", "implementation"],  # Placeholder
            "confidence": 0.7,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def _identify_expertise_areas(self, message: str) -> Dict[str, Any]:
        """
        Identify areas of expertise relevant to a consultancy message.
        
        Args:
            message: The message to analyze
            
        Returns:
            Dictionary with identified expertise areas
        """
        # Simple implementation - would be replaced with actual NLP model
        # In a real implementation, this would use domain-specific analysis
        return {
            "expertise_areas": ["financial", "strategic"],  # Placeholder
            "confidence": 0.6,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def _extract_context_from_analysis(
        self,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract context updates from analysis results.
        
        Args:
            analysis_results: The analysis results
            
        Returns:
            Dictionary with context updates
        """
        context_updates = {}
        
        # Extract from sentiment
        sentiment = analysis_results.get("sentiment", {})
        if sentiment:
            context_updates["sentiment_trend"] = sentiment.get("sentiment")
            context_updates["last_sentiment_score"] = sentiment.get("score")
        
        # Extract from intent
        intent = analysis_results.get("intent", {})
        if intent:
            context_updates["last_intent"] = intent.get("primary_intent")
            context_updates["expressed_intents"] = intent.get("intents", [])
            
            # Track if user is interested (for sales)
            if "is_interested" in intent and intent["is_interested"] is not None:
                context_updates["is_interested"] = intent["is_interested"]
        
        # Extract from buying signals (for sales)
        buying_signals = analysis_results.get("buying_signals", {})
        if buying_signals and buying_signals.get("has_buying_signals"):
            context_updates["has_buying_signals"] = True
            context_updates["buying_signals"] = buying_signals.get("signals_found", [])
        
        # Extract from objections (for sales)
        objections = analysis_results.get("objections", {})
        if objections and objections.get("has_objections"):
            context_updates["has_objections"] = True
            context_updates["objection_types"] = objections.get("objection_types", [])
        
        # Extract from support issue classification
        issue_classification = analysis_results.get("issue_classification", {})
        if issue_classification:
            context_updates["issue_type"] = issue_classification.get("issue_type")
        
        # Extract from urgency assessment
        urgency = analysis_results.get("urgency", {})
        if urgency:
            context_updates["request_urgency"] = urgency.get("urgency")
        
        # Extract from consultancy needs
        needs = analysis_results.get("needs", {})
        if needs:
            context_updates["identified_needs"] = needs.get("identified_needs", [])
        
        return context_updates
    
    async def _generate_response(
        self,
        conversation: Dict[str, Any],
        message: str,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a response to a user message.
        
        Args:
            conversation: The conversation state
            message: The user message
            analysis_results: Message analysis results
            
        Returns:
            Response containing text and metadata
        """
        # Get campaign type and stage
        context = conversation.get("context", {})
        campaign_type = context.get("campaign_type", "unknown")
        current_stage = conversation.get("current_stage", "unknown")
        
        # Get user profile info for context
        user_info = {
            "user_id": conversation.get("user_id"),
            "first_name": context.get("user_first_name", "there"),
            "last_name": context.get("user_last_name", "")
        }
        
        # For sales bot, use direct LLM generation without templates
        if campaign_type == "sales":
            # Prepare context for LLM
            llm_context = {
                "user": user_info,
                "current_stage": current_stage,
                "campaign_type": campaign_type,
                "analysis": analysis_results,
                "conversation_history": conversation.get("messages", [])[-5:],  # Last 5 messages for context
            }
            
            # Get any product info from context
            if "product_info" in context:
                llm_context["product_info"] = context["product_info"]
            
            # Direct LLM generation through appropriate bot service
            from src.bot_integration.sales_bot.sales_bot import handle_request
            
            response_text = handle_request(
                prompt=self._create_sales_prompt(message, llm_context),
            )
            
            return {
                "text": response_text,
                "type": "llm_generated",
                "stage": current_stage
            }
        
        # For other bot types, use template-based approach (fallback)
        # Find appropriate template
        template = self._find_appropriate_template(campaign_type, current_stage, analysis_results)
        
        if template:
            # Fill template with context data
            template_data = self._prepare_template_data(conversation, analysis_results)
            response_text = self._fill_template(template["content"], template_data)
            
            response = {
                "text": response_text,
                "type": "template",
                "template_id": template.get("_id")
            }
        else:
            # Fallback to hardcoded responses
            if campaign_type == "sales":
                if current_stage == "awareness":
                    response_text = "Thanks for your message! Would you like to learn more about our products?"
                elif current_stage == "interest":
                    response_text = "Great to hear your interest. What specific features are you looking for?"
                elif current_stage == "consideration":
                    response_text = "We have options that might fit your needs. Would you like to see pricing information?"
                elif current_stage == "decision":
                    response_text = "Ready to get started? I can help you with the next steps."
                else:
                    response_text = "Thank you for your message. How can I help you today?"
            else:
                response_text = "Thank you for your message. I'll help you with that."
                
            response = {
                "text": response_text,
                "type": "fallback"
            }
        
        return response
    
    def _create_sales_prompt(self, message: str, context: Dict[str, Any]) -> str:
        """
        Create a sales-specific prompt for the LLM.
        
        Args:
            message: The user message
            context: The context information
            
        Returns:
            Formatted prompt for the sales bot
        """
        stage = context.get("current_stage", "unknown")
        user = context.get("user", {})
        name = user.get("first_name", "there")
        
        # Create a prompt based on the sales stage
        prompt = f"You are a sales representative. The user ({name}) is in the {stage} stage "
        
        if stage == "awareness":
            prompt += "and needs to be introduced to our product's value proposition. "
        elif stage == "interest":
            prompt += "and has shown interest. Focus on specific benefits and features. "
        elif stage == "consideration":
            prompt += "and is considering options. Address specific questions and provide comparisons. "
        elif stage == "decision":
            prompt += "and is close to making a decision. Focus on removing final obstacles and encouraging commitment. "
        
        # Add analysis insights if available
        analysis = context.get("analysis", {})
        if "sentiment" in analysis:
            prompt += f"Their sentiment appears to be {analysis['sentiment']}. "
        
        if "buying_signals" in analysis:
            prompt += "They've shown buying signals about: " + ", ".join(analysis.get("buying_signals", [])) + ". "
            
        # Include product info if available
        if "product_info" in context:
            product = context["product_info"]
            prompt += f"Relevant product: {product.get('name')} - {product.get('description')}. "
        
        # Add the user's message
        prompt += f"\nUser message: {message}\n\nYour response:"
        
        return prompt
    
    def _find_appropriate_template(
        self,
        campaign_type: str,
        current_stage: str,
        analysis_results: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Find an appropriate template for a given campaign type and stage.
        
        Args:
            campaign_type: Type of campaign
            current_stage: Current conversation stage
            analysis_results: Message analysis results
            
        Returns:
            Template dictionary if found, None otherwise
        """
        # Attempt to get templates from different sources
        
        # First, try campaign-specific templates
        campaign = self.campaign_users_repository.get_campaign_sync(campaign_type)
        if campaign:
            config = campaign.get("config", {})
            templates = config.get("templates", {})
            
            # Look for stage-specific template
            stage_templates = templates.get(current_stage, [])
            if stage_templates:
                # Select appropriate template based on analysis
                return self._select_template(stage_templates, analysis_results)
        
        # Next, try global templates
        global_templates = self.get_global_templates(campaign_type, current_stage)
        if global_templates:
            return self._select_template(global_templates, analysis_results)
            
        # Finally, fallback to default template
        return self._get_default_template(campaign_type, current_stage)
    
    def _select_template(self, templates: List[Dict[str, Any]], analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Select the most appropriate template from a list based on analysis results.
        
        Args:
            templates: List of template options
            analysis_results: Analysis results to match against
            
        Returns:
            Best matching template or None if no templates provided
        """
        if not templates:
            return None
            
        # For now, just return the first template
        # In a real implementation, would match based on intent, sentiment, etc.
        return templates[0]
    
    def get_global_templates(self, campaign_type: str, stage: str) -> List[Dict[str, Any]]:
        """
        Get global templates for a campaign type and stage.
        
        Args:
            campaign_type: Type of campaign
            stage: Conversation stage
            
        Returns:
            List of matching templates
        """
        # In a real implementation, would fetch from a template repository
        # For now, return empty list as we're focusing on direct LLM generation
        return []
        
    def _get_default_template(self, campaign_type: str, stage: str) -> Optional[Dict[str, Any]]:
        """
        Get a default template for a campaign type and stage.
        
        Args:
            campaign_type: Type of campaign
            stage: Conversation stage
            
        Returns:
            Default template or None
        """
        # Basic hardcoded templates for fallback
        default_templates = {
            "sales": {
                "awareness": {
                    "content": "Hello! I'm here to tell you about our products. Would you like to learn more?",
                    "type": "default"
                },
                "interest": {
                    "content": "Thanks for your interest! What specific aspects would you like to know more about?",
                    "type": "default"
                }
            },
            "support": {
                "inquiry": {
                    "content": "Hello! I'm here to help. What issue are you experiencing?",
                    "type": "default"
                }
            }
        }
        
        # Try to get template for specific campaign type and stage
        campaign_templates = default_templates.get(campaign_type, {})
        template = campaign_templates.get(stage)
        
        return template
    
    def _prepare_template_data(
        self,
        conversation: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare data for template filling.
        
        Args:
            conversation: The conversation state
            analysis_results: Message analysis results
            
        Returns:
            Dictionary with template data
        """
        # Get user information
        user_id = conversation.get("user_id")
        context = conversation.get("context", {})
        
        # Basic template data
        template_data = {
            "user": {
                "id": user_id,
                "first_name": context.get("user_first_name", "there"),
                "last_name": context.get("user_last_name", "")
            },
            "conversation": {
                "stage": conversation.get("current_stage", "initial"),
                "progress": conversation.get("progress_percentage", 0)
            },
            "campaign": {
                "name": context.get("campaign_name", ""),
                "type": context.get("campaign_type", "")
            }
        }
        
        # Add context data
        for key, value in context.items():
            if key not in ["user_first_name", "user_last_name", "campaign_name", "campaign_type"]:
                template_data[key] = value
        
        # Add sentiment data
        sentiment = analysis_results.get("sentiment", {})
        if sentiment:
            template_data["sentiment"] = sentiment.get("sentiment")
        
        # Add intent data
        intent = analysis_results.get("intent", {})
        if intent:
            template_data["intent"] = intent.get("primary_intent")
        
        return template_data
    
    def _fill_template(self, template_content: str, template_data: Dict[str, Any]) -> str:
        """
        Fill a template with data.
        
        Args:
            template_content: The template content
            template_data: The data to fill the template with
            
        Returns:
            Filled template
        """
        # Simple template filling - would be replaced with proper template engine
        # This is a basic implementation for demonstration
        filled_content = template_content
        
        # Replace {{variable}} patterns
        import re
        
        def replace_var(match):
            var_path = match.group(1).strip()
            parts = var_path.split('.')
            
            # Navigate the template_data dictionary
            value = template_data
            for part in parts:
                if part in value:
                    value = value[part]
                else:
                    # Variable not found, leave as is
                    return match.group(0)
            
            # Convert to string
            return str(value)
        
        # Replace all variables
        filled_content = re.sub(r'\{\{(.*?)\}\}', replace_var, filled_content)
        
        return filled_content
    
    def _generate_conversation_summary(
        self,
        conversation: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a summary of the conversation.
        
        Args:
            conversation: The conversation state
            
        Returns:
            Dictionary with summary and key points or None if failed
        """
        try:
            # Get message history
            message_history = conversation.get("message_history", [])
            if not message_history or len(message_history) < 3:
                # Not enough messages to summarize
                return None
                
            # Simple implementation - would be replaced with LLM-based summarization
            # This is a placeholder implementation
            
            # Count messages by direction
            incoming_count = sum(1 for m in message_history if m.get("direction") == "incoming")
            outgoing_count = sum(1 for m in message_history if m.get("direction") == "outgoing")
            
            # Get the most recent messages
            recent_messages = message_history[-5:]
            recent_content = "\n".join([
                f"{'User' if m.get('direction') == 'incoming' else 'Bot'}: {m.get('content', '')}"
                for m in recent_messages
            ])
            
            # Create a simple summary
            summary = (
                f"Conversation with {incoming_count} user messages and {outgoing_count} bot responses. "
                f"Most recent exchange includes discussion about {conversation.get('current_stage', 'unknown')} stage topics."
            )
            
            # Extract key points (placeholder)
            key_points = [
                f"User is in {conversation.get('current_stage', 'unknown')} stage",
                f"Conversation has {len(message_history)} total messages"
            ]
            
            # Add sentiment information if available
            context = conversation.get("context", {})
            if "sentiment_trend" in context:
                key_points.append(f"User sentiment is {context['sentiment_trend']}")
                
            # Add intent information if available
            if "last_intent" in context:
                key_points.append(f"Last expressed intent: {context['last_intent']}")
            
            return {
                "summary": summary,
                "key_points": key_points,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(
                "Error generating conversation summary",
                error=str(e)
            )
            return None
    
    def _get_stages_for_campaign_type(
        self, 
        campaign_type: str, 
        config: Dict[str, Any]
    ) -> List[str]:
        """
        Get the appropriate stages for a campaign type.
        
        Args:
            campaign_type: Type of campaign
            config: Campaign configuration
            
        Returns:
            List of stage names
        """
        # Check if stages are explicitly defined in config
        if "stages" in config:
            return config["stages"]
        
        # Otherwise, use defaults based on campaign type
        if campaign_type == "sales":
            return ["awareness", "interest", "consideration", "decision"]
        elif campaign_type == "support":
            return ["inquiry", "investigation", "resolution", "feedback"]
        elif campaign_type == "consultancy":
            return ["discovery", "analysis", "recommendation", "implementation"]
        
        # Default for unknown campaign types
        return ["initial", "processing", "completed"] 