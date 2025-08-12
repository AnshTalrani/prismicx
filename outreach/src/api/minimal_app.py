from fastapi import FastAPI, HTTPException
from uuid import uuid4, UUID
from typing import List
from datetime import datetime
from src.models.campaign import Campaign, CampaignStatus, CampaignType

from src.api.endpoints.conversations import router as conversations_router
from src.api.endpoints.stt_tts import router as stt_tts_router

app = FastAPI()
app.include_router(conversations_router)
app.include_router(stt_tts_router)

# In-memory stores for demo
campaigns = {}
conversations = {}

@app.post("/campaigns", response_model=Campaign)
def create_campaign(campaign: Campaign):
    cid = campaign.id if campaign.id else uuid4()
    obj = campaign.copy(update={"id": cid, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()})
    campaigns[cid] = obj
    return obj

@app.get("/campaigns", response_model=List[Campaign])
def list_campaigns():
    return list(campaigns.values())

from src.models.conversation import Conversation

@app.post("/conversations", response_model=Conversation)
def start_conversation(conv: Conversation):
    coid = conv.id if conv.id else uuid4()
    obj = conv.copy(update={"id": coid, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()})
    conversations[coid] = obj
    return obj

@app.get("/conversations", response_model=List[Conversation])
def list_conversations():
    return list(conversations.values())
