"""
Conversations API Routes

This module provides API endpoints for conversation management, including retrieving
and updating conversation states, managing conversation progression, and handling
conversation-specific actions.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime

from src.config.config_manager import get_settings
from src.repository.conversation_state_repository import ConversationStateRepository
from src.service.campaign_manager import CampaignManager
from src.models.conversation import (
    ConversationState, 
    ConversationResponse, 
    ConversationUpdate,
    ConversationProgressResponse
)
from src.models.common import SuccessResponse, ErrorResponse

# Create logger
logger = structlog.get_logger(__name__)

# Create router
router = APIRouter()

# Dependencies
async def get_conversation_repository():
    """Dependency to get the conversation repository instance."""
    repo = ConversationStateRepository()
    await repo.initialize()
    return repo

async def get_campaign_manager():
    """Dependency to get the campaign manager instance."""
    repo = await get_conversation_repository()
    manager = CampaignManager(None, repo)
    await manager.initialize()
    return manager

@router.get("/{conversation_id}", response_model=ConversationState)
async def get_conversation(
    conversation_id: str,
    repo: ConversationStateRepository = Depends(get_conversation_repository)
):
    """
    Get the state of a specific conversation.
    
    Args:
        conversation_id: ID of the conversation state to retrieve
        
    Returns:
        Conversation state information
    """
    try:
        conversation = await repo.get_conversation_state(conversation_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        logger.info("Conversation retrieved", conversation_id=conversation_id)
        
        return conversation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting conversation", conversation_id=conversation_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[ConversationState])
async def list_conversations(
    campaign_id: Optional[str] = None,
    recipient_id: Optional[str] = None,
    status: Optional[str] = None,
    current_stage: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    skip: int = Query(0, ge=0),
    repo: ConversationStateRepository = Depends(get_conversation_repository)
):
    """
    List conversation states with filtering and pagination.
    
    Args:
        campaign_id: Optional filter by campaign ID
        recipient_id: Optional filter by recipient ID
        status: Optional filter by status
        current_stage: Optional filter by current stage
        limit: Maximum number of conversations to return
        skip: Number of conversations to skip (for pagination)
        
    Returns:
        List of conversation states
    """
    try:
        filters = {}
        if campaign_id:
            filters["campaign_id"] = campaign_id
        if recipient_id:
            filters["recipient_id"] = recipient_id
        if status:
            filters["status"] = status
        if current_stage:
            filters["current_stage"] = current_stage
            
        conversations = await repo.get_conversation_states(filters, skip, limit)
        
        logger.info(
            "Conversations listed", 
            count=len(conversations), 
            filters=filters
        )
        
        return conversations
        
    except Exception as e:
        logger.error("Error listing conversations", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    updates: ConversationUpdate,
    repo: ConversationStateRepository = Depends(get_conversation_repository)
):
    """
    Update a conversation's state.
    
    Args:
        conversation_id: ID of the conversation to update
        updates: Fields to update
        
    Returns:
        Updated conversation information
    """
    try:
        # Get existing conversation
        existing_conversation = await repo.get_conversation_state(conversation_id)
        
        if not existing_conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        # Check if conversation can be updated
        if existing_conversation["status"] in ["completed", "canceled", "failed"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot update conversation with status '{existing_conversation['status']}'"
            )
        
        # Build update data (only include fields that are provided)
        update_data = {}
        for field, value in updates.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        # Add update timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        # Update conversation
        updated = await repo.update_conversation_state(conversation_id, update_data)
        
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update conversation")
        
        # Get updated conversation
        conversation = await repo.get_conversation_state(conversation_id)
        
        logger.info("Conversation updated", conversation_id=conversation_id, updates=update_data)
        
        return ConversationResponse(
            id=conversation_id,
            campaign_id=conversation["campaign_id"],
            recipient_id=conversation["recipient_id"],
            status=conversation["status"],
            current_stage=conversation["current_stage"],
            updated_at=conversation.get("updated_at"),
            message="Conversation updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating conversation", conversation_id=conversation_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{conversation_id}/progress", response_model=ConversationProgressResponse)
async def progress_conversation(
    conversation_id: str,
    data: Dict[str, Any] = Body(...),
    manager: CampaignManager = Depends(get_campaign_manager),
    repo: ConversationStateRepository = Depends(get_conversation_repository)
):
    """
    Progress a conversation to the next stage.
    
    Args:
        conversation_id: ID of the conversation to progress
        data: Additional data for the progression (if any)
        
    Returns:
        Updated conversation state with progression result
    """
    try:
        # Get existing conversation
        existing_conversation = await repo.get_conversation_state(conversation_id)
        
        if not existing_conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        # Check if conversation can be progressed
        if existing_conversation["status"] in ["completed", "canceled", "failed"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot progress conversation with status '{existing_conversation['status']}'"
            )
        
        # Attempt to progress the conversation
        result = await manager.evaluate_stage_progression(
            conversation_id, 
            existing_conversation["current_stage"],
            data
        )
        
        if not result["success"]:
            return ConversationProgressResponse(
                id=conversation_id,
                campaign_id=existing_conversation["campaign_id"],
                recipient_id=existing_conversation["recipient_id"],
                progressed=False,
                previous_stage=existing_conversation["current_stage"],
                current_stage=existing_conversation["current_stage"],
                status=existing_conversation["status"],
                message=result.get("message", "Failed to progress conversation")
            )
        
        # Get updated conversation after progression
        updated_conversation = await repo.get_conversation_state(conversation_id)
        
        logger.info(
            "Conversation progressed", 
            conversation_id=conversation_id, 
            from_stage=existing_conversation["current_stage"],
            to_stage=updated_conversation["current_stage"]
        )
        
        return ConversationProgressResponse(
            id=conversation_id,
            campaign_id=updated_conversation["campaign_id"],
            recipient_id=updated_conversation["recipient_id"],
            progressed=True,
            previous_stage=existing_conversation["current_stage"],
            current_stage=updated_conversation["current_stage"],
            status=updated_conversation["status"],
            message="Conversation progressed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error progressing conversation", conversation_id=conversation_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{conversation_id}/cancel", response_model=SuccessResponse)
async def cancel_conversation(
    conversation_id: str,
    repo: ConversationStateRepository = Depends(get_conversation_repository)
):
    """
    Cancel a conversation.
    
    Args:
        conversation_id: ID of the conversation to cancel
        
    Returns:
        Success response
    """
    try:
        # Get existing conversation
        existing_conversation = await repo.get_conversation_state(conversation_id)
        
        if not existing_conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        # Check if conversation can be canceled
        if existing_conversation["status"] in ["completed", "canceled", "failed"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel conversation with status '{existing_conversation['status']}'"
            )
        
        # Cancel the conversation
        update_data = {
            "status": "canceled",
            "updated_at": datetime.utcnow(),
            "metadata": {
                **(existing_conversation.get("metadata", {}) or {}),
                "canceled_at": datetime.utcnow().isoformat()
            }
        }
        
        updated = await repo.update_conversation_state(conversation_id, update_data)
        
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to cancel conversation")
        
        logger.info("Conversation canceled", conversation_id=conversation_id)
        
        return SuccessResponse(message="Conversation canceled successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error canceling conversation", conversation_id=conversation_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{conversation_id}/history", response_model=List[Dict[str, Any]])
async def get_conversation_history(
    conversation_id: str,
    repo: ConversationStateRepository = Depends(get_conversation_repository)
):
    """
    Get the history of a conversation.
    
    Args:
        conversation_id: ID of the conversation
        
    Returns:
        List of historical conversation states
    """
    try:
        history = await repo.get_conversation_history(conversation_id)
        
        if not history:
            raise HTTPException(status_code=404, detail="Conversation history not found")
            
        logger.info("Conversation history retrieved", conversation_id=conversation_id)
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting conversation history", conversation_id=conversation_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) 