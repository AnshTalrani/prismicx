"""
Workflow Orchestrator

This module provides the main workflow orchestration functionality,
coordinating between different AI models and services to execute
conversation flows and campaign workflows.
"""

import asyncio
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime

from ..config.logging_config import get_logger, LoggerMixin
from ..models.schemas import MessageCreate, MessageResponse
from ..models.llm.base_llm import Message, MessageRole
from ..services.campaign_service import CampaignService
from ..services.conversation_service import ConversationService
from ..services.analytics_service import AnalyticsService

logger = get_logger(__name__)


class WorkflowOrchestrator(LoggerMixin):
    """Main workflow orchestrator for the outreach system."""
    
    def __init__(self):
        """Initialize the workflow orchestrator."""
        self.campaign_service = CampaignService(db_session=None)
        self.conversation_service = ConversationService(db_session=None)
        self.analytics_service = AnalyticsService(db_session=None)
        self.active_workflows: Dict[UUID, Dict] = {}
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the orchestrator and load required models."""
        try:
            self.logger.info("Initializing Workflow Orchestrator...")
            
            # Initialize services
            await self.campaign_service.initialize()
            await self.conversation_service.initialize()
            await self.analytics_service.initialize()
            
            # Load AI models
            await self._load_ai_models()
            
            self.is_initialized = True
            self.logger.info("Workflow Orchestrator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Workflow Orchestrator: {str(e)}")
            raise
    
    async def _load_ai_models(self):
        """Load all required AI models."""
        try:
            # Load ASR model (Whisper)
            from ..models.asr.whisper.wrapper import WhisperRecognizer
            from ..config.settings import settings
            
            self.asr_model = WhisperRecognizer({
                "model_size": settings.whisper_model_size,
                "device": settings.whisper_device,
                "language": settings.whisper_language
            })
            await self.asr_model.load_model()
            
            # Load LLM model (OpenAI or OpenAI OSS)
            if settings.llm_provider == "openai":
                from ..models.llm.openai_adapter import OpenAIAdapter
                self.llm_model = OpenAIAdapter({
                    "api_key": settings.openai_api_key,
                    "model": settings.openai_model,
                    "max_tokens": 1000,
                    "temperature": 0.7
                })
            elif settings.llm_provider == "openai_oss":
                from ..models.llm.openai_oss_adapter import OpenAIOSSAdapter
                self.llm_model = OpenAIOSSAdapter({
                    "model_name": "gpt2",  # Using standard GPT-2 model from Hugging Face
                    "max_tokens": 1000,
                    "temperature": 0.7,
                    "device": "cpu"
                })
            else:
                # Default to OpenAI
                from ..models.llm.openai_adapter import OpenAIAdapter
                self.llm_model = OpenAIAdapter({
                    "api_key": settings.openai_api_key,
                    "model": settings.openai_model,
                    "max_tokens": 1000,
                    "temperature": 0.7
                })
            
            await self.llm_model.load_model()
            
            # Load TTS model (Kokoro)
            from ..models.tts.kokoro.wrapper import KokoroSynthesizer
            self.tts_model = KokoroSynthesizer({
                "model_path": settings.kokoro_model_path,
                "device": settings.kokoro_device,
                "voice_profile": settings.kokoro_voice_profile,
                "sample_rate": 22050
            })
            await self.tts_model.load_model()
            
            # Load Emotion model (Multimodal)
            from ..models.emotion.multimodal_analyzer import MultimodalEmotionAnalyzer
            self.emotion_model = MultimodalEmotionAnalyzer({
                "model_path": settings.emotion_model_path,
                "confidence_threshold": settings.emotion_confidence_threshold,
                "device": "cpu"
            })
            await self.emotion_model.load_model()
            
            self.logger.info("All AI models loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load AI models: {str(e)}")
            raise
    
    async def execute_campaign_workflow(
        self, 
        campaign_id: UUID, 
        contact_id: UUID
    ) -> Dict[str, Any]:
        """Execute a campaign workflow for a specific contact."""
        try:
            self.logger.info(f"Executing campaign workflow: {campaign_id} for contact: {contact_id}")
            
            # Get campaign details
            campaign = await self.campaign_service.get_campaign(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign not found: {campaign_id}")
            
            # Create conversation
            conversation = await self.conversation_service.create_conversation({
                "campaign_id": campaign_id,
                "contact_id": contact_id
            })
            
            # Start workflow execution
            workflow_result = await self._execute_workflow(
                conversation_id=conversation.id,
                workflow_definition=campaign.workflow_definition,
                contact_id=contact_id
            )
            
            # Update conversation with workflow result
            await self.conversation_service.update_conversation_state(
                conversation.id, 
                workflow_result
            )
            
            self.logger.info(f"Campaign workflow executed successfully: {campaign_id}")
            return workflow_result
            
        except Exception as e:
            self.logger.error(f"Failed to execute campaign workflow: {str(e)}")
            raise
    
    async def _execute_workflow(
        self, 
        conversation_id: UUID, 
        workflow_definition: Dict, 
        contact_id: UUID
    ) -> Dict[str, Any]:
        """Execute a specific workflow."""
        try:
            self.logger.info(f"Executing workflow for conversation: {conversation_id}")
            
            # Initialize workflow state
            workflow_state = {
                "conversation_id": conversation_id,
                "contact_id": contact_id,
                "current_node": workflow_definition.get("start_node_id"),
                "variables": {},
                "history": []
            }
            
            # Execute workflow nodes
            while workflow_state["current_node"]:
                node_id = workflow_state["current_node"]
                node = workflow_definition["nodes"].get(node_id)
                
                if not node:
                    self.logger.error(f"Node not found: {node_id}")
                    break
                
                # Execute node
                node_result = await self._execute_workflow_node(
                    node, workflow_state
                )
                
                # Update workflow state
                workflow_state["history"].append({
                    "node_id": node_id,
                    "result": node_result,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Determine next node
                workflow_state["current_node"] = await self._determine_next_node(
                    node, node_result, workflow_definition
                )
            
            self.logger.info(f"Workflow execution completed: {conversation_id}")
            return workflow_state
            
        except Exception as e:
            self.logger.error(f"Failed to execute workflow: {str(e)}")
            raise
    
    async def _execute_workflow_node(
        self, 
        node: Dict, 
        workflow_state: Dict
    ) -> Dict[str, Any]:
        """Execute a single workflow node."""
        try:
            node_type = node.get("type")
            self.logger.info(f"Executing node: {node.get('id')} of type: {node_type}")
            
            if node_type == "message":
                return await self._execute_message_node(node, workflow_state)
            elif node_type == "decision":
                return await self._execute_decision_node(node, workflow_state)
            elif node_type == "action":
                return await self._execute_action_node(node, workflow_state)
            elif node_type == "ai_response":
                return await self._execute_ai_response_node(node, workflow_state)
            else:
                self.logger.warning(f"Unknown node type: {node_type}")
                return {"status": "unknown_node_type"}
                
        except Exception as e:
            self.logger.error(f"Failed to execute node: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def _execute_message_node(
        self, 
        node: Dict, 
        workflow_state: Dict
    ) -> Dict[str, Any]:
        """Execute a message node."""
        try:
            message_content = node.get("content", {}).get("text", "")
            
            # Send message through conversation service
            message = MessageCreate(
                content=message_content,
                content_type="text/plain"
            )
            
            sent_message = await self.conversation_service.send_message(
                workflow_state["conversation_id"], 
                message
            )
            
            return {
                "status": "success",
                "message_id": sent_message.id,
                "content": message_content
            }
            
        except Exception as e:
            self.logger.error(f"Failed to execute message node: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def _execute_decision_node(
        self, 
        node: Dict, 
        workflow_state: Dict
    ) -> Dict[str, Any]:
        """Execute a decision node."""
        try:
            # Get conversation context
            conversation = await self.conversation_service.get_conversation(
                workflow_state["conversation_id"]
            )
            
            # Analyze recent messages for decision making
            recent_messages = await self.conversation_service.get_conversation_messages(
                workflow_state["conversation_id"],
                limit=5
            )
            
            # Use LLM to make decision
            decision_prompt = self._build_decision_prompt(node, recent_messages)
            decision_response = await self.llm_model.generate([
                Message(role=MessageRole.SYSTEM, content="You are a decision-making assistant."),
                Message(role=MessageRole.USER, content=decision_prompt)
            ])
            
            # Parse decision
            decision = self._parse_decision_response(decision_response.text)
            
            return {
                "status": "success",
                "decision": decision,
                "reasoning": decision_response.text
            }
            
        except Exception as e:
            self.logger.error(f"Failed to execute decision node: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def _execute_action_node(
        self, 
        node: Dict, 
        workflow_state: Dict
    ) -> Dict[str, Any]:
        """Execute an action node."""
        try:
            action_type = node.get("content", {}).get("action_type")
            
            if action_type == "update_contact":
                # Update contact information
                contact_data = node.get("content", {}).get("contact_data", {})
                # Implementation would update contact in database
                return {"status": "success", "action": "contact_updated"}
            
            elif action_type == "schedule_followup":
                # Schedule follow-up
                followup_data = node.get("content", {}).get("followup_data", {})
                # Implementation would schedule follow-up
                return {"status": "success", "action": "followup_scheduled"}
            
            else:
                return {"status": "unknown_action", "action_type": action_type}
                
        except Exception as e:
            self.logger.error(f"Failed to execute action node: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def _execute_ai_response_node(
        self, 
        node: Dict, 
        workflow_state: Dict
    ) -> Dict[str, Any]:
        """Execute an AI response node."""
        try:
            # Get conversation context
            recent_messages = await self.conversation_service.get_conversation_messages(
                workflow_state["conversation_id"],
                limit=10
            )
            
            # Build context for AI
            context = self._build_conversation_context(recent_messages)
            
            # Generate AI response
            ai_response = await self.llm_model.generate([
                Message(role=MessageRole.SYSTEM, content="You are a helpful outreach assistant."),
                Message(role=MessageRole.USER, content=context)
            ])
            
            # Send AI response
            message = MessageCreate(
                content=ai_response.text,
                content_type="text/plain"
            )
            
            sent_message = await self.conversation_service.send_message(
                workflow_state["conversation_id"], 
                message
            )
            
            return {
                "status": "success",
                "message_id": sent_message.id,
                "ai_response": ai_response.text
            }
            
        except Exception as e:
            self.logger.error(f"Failed to execute AI response node: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def _determine_next_node(
        self, 
        node: Dict, 
        node_result: Dict, 
        workflow_definition: Dict
    ) -> Optional[str]:
        """Determine the next node based on current node result."""
        try:
            next_nodes = node.get("next_nodes", {})
            
            if not next_nodes:
                return None
            
            # Simple decision logic - can be enhanced
            if node_result.get("status") == "success":
                return next_nodes.get("success")
            elif node_result.get("status") == "error":
                return next_nodes.get("error")
            else:
                return next_nodes.get("default")
                
        except Exception as e:
            self.logger.error(f"Failed to determine next node: {str(e)}")
            return None
    
    def _build_decision_prompt(self, node: Dict, messages: List[MessageResponse]) -> str:
        """Build prompt for decision making."""
        decision_criteria = node.get("content", {}).get("criteria", [])
        
        prompt = f"Based on the following conversation, make a decision according to these criteria: {decision_criteria}\n\n"
        prompt += "Conversation:\n"
        
        for message in messages:
            prompt += f"{message.direction}: {message.content}\n"
        
        prompt += "\nRespond with a clear decision and reasoning."
        return prompt
    
    def _parse_decision_response(self, response: str) -> str:
        """Parse decision from AI response."""
        # Simple parsing - can be enhanced
        response_lower = response.lower()
        
        if "yes" in response_lower or "positive" in response_lower:
            return "yes"
        elif "no" in response_lower or "negative" in response_lower:
            return "no"
        else:
            return "neutral"
    
    def _build_conversation_context(self, messages: List[MessageResponse]) -> str:
        """Build conversation context for AI."""
        context = "Recent conversation:\n"
        
        for message in messages:
            context += f"{message.direction}: {message.content}\n"
        
        context += "\nGenerate an appropriate response based on this conversation."
        return context
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            self.logger.info("Cleaning up Workflow Orchestrator...")
            
            # Cleanup services
            await self.campaign_service.cleanup()
            await self.conversation_service.cleanup()
            await self.analytics_service.cleanup()
            
            # Cleanup AI models
            if hasattr(self, 'asr_model'):
                del self.asr_model
            if hasattr(self, 'llm_model'):
                del self.llm_model
            if hasattr(self, 'tts_model'):
                del self.tts_model
            if hasattr(self, 'emotion_model'):
                del self.emotion_model
            
            self.logger.info("Workflow Orchestrator cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}") 