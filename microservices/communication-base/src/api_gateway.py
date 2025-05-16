"""
API Gateway layer for the communication-base microservice.
Defines endpoints and routes incoming requests through middleware.
"""

from fastapi import FastAPI, Request, HTTPException
from src.middleware import process_request
from src.campaign.campaign_manager import CampaignManager
from src.bot_manager import BotManager
from typing import Dict, Optional, List
from pydantic import BaseModel

app = FastAPI(title="Communication-Base API")
campaign_manager = CampaignManager()
bot_manager = BotManager()

class CampaignBatchRequest(BaseModel):
    """Campaign batch processing request model."""
    campaign_id: str
    batch_id: str
    bot_type: str = "sales"
    platform: str = "web"
    users: List[Dict]
    metadata: Optional[Dict] = None

@app.post("/process")
async def process_endpoint(request: Request):
    try:
        json_data = await request.json()
        response = process_request(json_data)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-campaign-batch")
async def process_campaign_batch(campaign_data: CampaignBatchRequest):
    try:
        # Validate campaign data
        validated_data = await campaign_manager.validate_campaign_data(campaign_data.dict())
        
        # Initialize bot with campaign context
        bot = bot_manager.get_bot(campaign_data.bot_type)
        
        # Process campaign batch
        result = await campaign_manager.process_batch(
            validated_data,
            bot
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 