"""
Conversation Service

Handles all business logic related to conversations within campaigns.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from src.models.conversation import Conversation, ConversationStatus

from src.services.stt_service import STTService
from src.services.llm_service import LLMService
from src.services.tts_service import TTSService

class ConversationService:
    def __init__(self, conversation_repository, stt_service: STTService = None, llm_service: LLMService = None, tts_service: TTSService = None):
        self.conversation_repo = conversation_repository
        self.stt_service = stt_service
        self.llm_service = llm_service
        self.tts_service = tts_service

    async def start_conversation(self, *args, **kwargs) -> Conversation:
        """
        Start a conversation. Accepts either (conversation: Conversation) or (campaign_id, contact_id, context=None).
        """
        # (campaign_id, contact_id, context) signature
        from src.models.conversation import Conversation as ConversationModel
        if len(args) == 1 and isinstance(args[0], ConversationModel):
            conversation = args[0]
        elif len(args) >= 2:
            campaign_id = args[0]
            contact_id = args[1]
            context = kwargs.get('context', {})
            conversation = ConversationModel(
                id=uuid4(),
                campaign_id=campaign_id,
                contact_id=contact_id,
                status=ConversationStatus.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata=context
            )
        else:
            raise ValueError("Invalid arguments for start_conversation")
        conversation = conversation.copy(update={"status": ConversationStatus.ACTIVE, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()})
        return await self.conversation_repo.create(conversation)
    
    async def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        return await self.conversation_repo.get(conversation_id)

    async def update_conversation(self, conversation_id: UUID, update_data: dict) -> Optional[Conversation]:
        update_data['updated_at'] = datetime.utcnow()
        return await self.conversation_repo.update(conversation_id, update_data)

    async def end_conversation(self, conversation_id: UUID, status: ConversationStatus = ConversationStatus.COMPLETED) -> Optional[Conversation]:
        return await self.conversation_repo.update(
            conversation_id,
            {"status": status, "ended_at": datetime.utcnow()}
        )

    async def list_conversations(self, filters: Optional[dict] = None) -> List[Conversation]:
        return await self.conversation_repo.list(filters or {})

    async def add_message(self, conversation_id: UUID, sender_type: str, content: str, metadata: dict = None, input_audio: bytes = None, use_tts: bool = False):
        """
        Add a message to a conversation, optionally using STT/LLM/TTS for AI-driven logic.
        """
        # If input_audio is provided and STT is available, transcribe
        if input_audio and self.stt_service:
            content = await self.stt_service.transcribe(input_audio)
        # If sender is user and LLM is available, generate AI response
        ai_response = None
        if sender_type == 'user' and self.llm_service:
            ai_response = await self.llm_service.generate_response({'conversation_id': str(conversation_id)}, content)
        # If use_tts is True and TTS is available, synthesize response
        tts_audio = None
        if use_tts and self.tts_service and ai_response:
            tts_audio = await self.tts_service.synthesize(ai_response)
        message = {
            'id': str(uuid4()),
            'sender_type': sender_type,
            'content': content,
            'timestamp': datetime.utcnow(),
            'metadata': metadata or {}
        }
        result = await self.conversation_repo.add_message(conversation_id, message)
        # Optionally add AI/ML response as system message
        if ai_response:
            ai_message = {
                'id': str(uuid4()),
                'sender_type': 'system',
                'content': ai_response,
                'timestamp': datetime.utcnow(),
                'metadata': {'tts_audio': tts_audio} if tts_audio else {}
            }
            await self.conversation_repo.add_message(conversation_id, ai_message)
        return result
