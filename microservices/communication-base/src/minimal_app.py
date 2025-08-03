"""
Minimal Working FastAPI App for Communication Base Microservice

This is a simplified version that works without import issues,
providing core functionality for testing and validation.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import structlog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title="Communication Base API",
    description="Core communication and campaign management microservice",
    version="1.0.0"
)

# Pydantic models for API
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    components: Dict[str, Dict[str, Any]]

class CampaignRequest(BaseModel):
    name: str
    template_type: str
    recipients: List[Dict[str, Any]]
    scheduled_at: Optional[str] = None

class CampaignResponse(BaseModel):
    campaign_id: str
    name: str
    status: str
    created_at: str
    recipients_count: int

class ConversationRequest(BaseModel):
    user_id: str
    message: str
    session_id: Optional[str] = None
    bot_type: Optional[str] = "support"

class ConversationResponse(BaseModel):
    response: str
    session_id: str
    bot_type: str
    timestamp: str

# In-memory storage for testing (replace with proper database in production)
campaigns_store = {}
conversations_store = {}

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "Communication Base API",
        "version": "1.0.0",
        "description": "Core communication and campaign management microservice"
    }

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    try:
        # Check core components
        components = {
            "api": {"status": "healthy"},
            "campaigns": {"status": "healthy", "count": len(campaigns_store)},
            "conversations": {"status": "healthy", "count": len(conversations_store)},
            "mongodb": {"status": "unhealthy", "error": "Not connected (expected in local testing)"},
            "redis": {"status": "unhealthy", "error": "Not connected (expected in local testing)"}
        }
        
        # Determine overall status
        api_healthy = components["api"]["status"] == "healthy"
        overall_status = "healthy" if api_healthy else "unhealthy"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            components=components
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.post("/api/v1/campaigns", response_model=CampaignResponse)
async def create_campaign(campaign: CampaignRequest, background_tasks: BackgroundTasks):
    """Create a new campaign."""
    try:
        campaign_id = f"campaign_{len(campaigns_store) + 1}_{int(datetime.now().timestamp())}"
        
        campaign_data = {
            "id": campaign_id,
            "name": campaign.name,
            "template_type": campaign.template_type,
            "recipients": campaign.recipients,
            "scheduled_at": campaign.scheduled_at,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "recipients_count": len(campaign.recipients)
        }
        
        campaigns_store[campaign_id] = campaign_data
        
        # Schedule background processing
        background_tasks.add_task(process_campaign, campaign_id)
        
        logger.info(f"Campaign created: {campaign_id}")
        
        return CampaignResponse(
            campaign_id=campaign_id,
            name=campaign.name,
            status="pending",
            created_at=campaign_data["created_at"],
            recipients_count=len(campaign.recipients)
        )
    except Exception as e:
        logger.error(f"Campaign creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Campaign creation failed")

@app.get("/api/v1/campaigns", response_model=List[CampaignResponse])
async def list_campaigns():
    """List all campaigns."""
    try:
        campaigns = []
        for campaign_data in campaigns_store.values():
            campaigns.append(CampaignResponse(
                campaign_id=campaign_data["id"],
                name=campaign_data["name"],
                status=campaign_data["status"],
                created_at=campaign_data["created_at"],
                recipients_count=campaign_data["recipients_count"]
            ))
        
        return campaigns
    except Exception as e:
        logger.error(f"Campaign listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Campaign listing failed")

@app.get("/api/v1/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str):
    """Get campaign details."""
    try:
        if campaign_id not in campaigns_store:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign_data = campaigns_store[campaign_id]
        return CampaignResponse(
            campaign_id=campaign_data["id"],
            name=campaign_data["name"],
            status=campaign_data["status"],
            created_at=campaign_data["created_at"],
            recipients_count=campaign_data["recipients_count"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Campaign retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Campaign retrieval failed")

@app.post("/api/v1/conversations", response_model=ConversationResponse)
async def create_conversation(conversation: ConversationRequest):
    """Create a new conversation or continue existing one."""
    try:
        session_id = conversation.session_id or f"session_{int(datetime.now().timestamp())}"
        
        # Simple bot response logic (replace with actual bot integration)
        bot_responses = {
            "support": f"Thank you for your message: '{conversation.message}'. Our support team will assist you shortly.",
            "sales": f"Hello! I understand you're interested in: '{conversation.message}'. Let me help you with that.",
            "consultancy": f"I've received your inquiry: '{conversation.message}'. Let's discuss your needs in detail."
        }
        
        response_text = bot_responses.get(conversation.bot_type, "Thank you for your message. How can I help you?")
        
        conversation_data = {
            "user_id": conversation.user_id,
            "session_id": session_id,
            "message": conversation.message,
            "response": response_text,
            "bot_type": conversation.bot_type,
            "timestamp": datetime.now().isoformat()
        }
        
        conversations_store[session_id] = conversation_data
        
        logger.info(f"Conversation created: {session_id}")
        
        return ConversationResponse(
            response=response_text,
            session_id=session_id,
            bot_type=conversation.bot_type,
            timestamp=conversation_data["timestamp"]
        )
    except Exception as e:
        logger.error(f"Conversation creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Conversation creation failed")

@app.get("/api/v1/conversations/{session_id}")
async def get_conversation(session_id: str):
    """Get conversation details."""
    try:
        if session_id not in conversations_store:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return conversations_store[session_id]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversation retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Conversation retrieval failed")

@app.get("/api/v1/stats")
async def get_stats():
    """Get service statistics."""
    try:
        return {
            "campaigns": {
                "total": len(campaigns_store),
                "by_status": {
                    "pending": len([c for c in campaigns_store.values() if c["status"] == "pending"]),
                    "active": len([c for c in campaigns_store.values() if c["status"] == "active"]),
                    "completed": len([c for c in campaigns_store.values() if c["status"] == "completed"])
                }
            },
            "conversations": {
                "total": len(conversations_store),
                "by_bot_type": {
                    "support": len([c for c in conversations_store.values() if c["bot_type"] == "support"]),
                    "sales": len([c for c in conversations_store.values() if c["bot_type"] == "sales"]),
                    "consultancy": len([c for c in conversations_store.values() if c["bot_type"] == "consultancy"])
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Stats retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Stats retrieval failed")

async def process_campaign(campaign_id: str):
    """Background task to process campaigns."""
    try:
        await asyncio.sleep(2)  # Simulate processing time
        
        if campaign_id in campaigns_store:
            campaigns_store[campaign_id]["status"] = "active"
            logger.info(f"Campaign {campaign_id} status updated to active")
            
            # Simulate completion after some time
            await asyncio.sleep(5)
            campaigns_store[campaign_id]["status"] = "completed"
            logger.info(f"Campaign {campaign_id} completed")
            
    except Exception as e:
        logger.error(f"Campaign processing failed for {campaign_id}: {str(e)}")
        if campaign_id in campaigns_store:
            campaigns_store[campaign_id]["status"] = "failed"

# Add startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application."""
    logger.info("Communication Base API starting up...")
    logger.info("Minimal FastAPI app initialized successfully")

# Add shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources."""
    logger.info("Communication Base API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
