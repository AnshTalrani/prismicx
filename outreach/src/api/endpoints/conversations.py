"""
Conversation API endpoints.

This module handles real-time conversation interactions,
including message sending, receiving, and conversation state management.
"""

from fastapi import APIRouter, HTTPException
from uuid import uuid4, UUID
from typing import List, Dict
from datetime import datetime

from src.models.conversation import Conversation, ConversationStatus
from src.services.conversation_service import ConversationService
from src.services.llm_service_gpt20b import GPT20BLLMService

router = APIRouter()

# In-memory stores for demo
conversations: Dict[UUID, Conversation] = {}
messages: Dict[UUID, List[dict]] = {}

# Inject LLM service
llm_service = GPT20BLLMService()
conversation_service = ConversationService(conversation_repository=None, llm_service=llm_service)

@router.post("/conversations", response_model=Conversation)
async def start_conversation(conv: Conversation):
    coid = conv.id if conv.id else uuid4()
    obj = conv.copy(update={"id": coid, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()})
    conversations[coid] = obj
    messages[coid] = []
    return obj

@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: UUID):
    conv = conversations.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@router.post("/conversations/{conversation_id}/messages")
async def send_message(conversation_id: UUID, sender_type: str, content: str):
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    # Use LLM for system reply if sender is user
    message = {
        'id': str(uuid4()),
        'sender_type': sender_type,
        'content': content,
        'timestamp': datetime.utcnow(),
        'metadata': {}
    }
    messages[conversation_id].append(message)
    ai_message = None
    if sender_type == 'user':
        ai_content = await llm_service.generate_response({'conversation_id': str(conversation_id)}, content)
        ai_message = {
            'id': str(uuid4()),
            'sender_type': 'system',
            'content': ai_content,
            'timestamp': datetime.utcnow(),
            'metadata': {}
        }
        messages[conversation_id].append(ai_message)
    return {"user_message": message, "system_message": ai_message}

@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: UUID):
    if conversation_id not in messages:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return messages[conversation_id]
