"""
Agent API Client for Consultancy Bot

Provides functionality to send requests to the Agent microservice from the consultancy bot.
"""
import httpx
import structlog
from typing import Dict, Any, Optional
import os

# Configure logger
logger = structlog.get_logger(__name__)

class AgentClient:
    """
    Client for interacting with the Agent microservice.
    
    This client sends requests to the Agent's consultancy bot API.
    """
    
    def __init__(self):
        """Initialize the agent client."""
        self.agent_base_url = os.getenv("AGENT_API_URL", "http://agent:8000")
        self.api_key = os.getenv("AGENT_API_KEY", "")
        self.timeout = int(os.getenv("AGENT_API_TIMEOUT", "30"))
        
        logger.info("Initialized Agent API client", base_url=self.agent_base_url)
    
    async def send_request(self, 
                         text: str, 
                         user_id: str, 
                         session_id: str,
                         urgency: str = "high") -> Dict[str, Any]:
        """
        Send a request to the Agent microservice.
        
        Args:
            text: Text of the request
            user_id: User ID
            session_id: Session ID
            urgency: Request urgency (default: high)
            
        Returns:
            Response from the Agent microservice
        """
        try:
            url = f"{self.agent_base_url}/bot/request"
            
            payload = {
                "text": text,
                "user_id": user_id,
                "session_id": session_id,
                "urgency": urgency
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
            }
            
            logger.info("Sending sample request to Agent", 
                       session_id=session_id, 
                       text_preview=text[:100])
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    response_data = response.json()
                    logger.info("Received response from Agent", 
                              session_id=session_id,
                              status=response_data.get("status"))
                    return response_data
                else:
                    logger.error("Error from Agent API", 
                                status_code=response.status_code, 
                                response=response.text)
                    return {
                        "status": "error",
                        "error": f"Agent API returned {response.status_code}",
                        "session_id": session_id,
                        "user_id": user_id,
                        "content": "I apologize, but I'm having trouble retrieving a sample at the moment."
                    }
                    
        except Exception as e:
            logger.exception("Error sending request to Agent API", error=str(e))
            return {
                "status": "error",
                "error": f"Failed to send request to Agent: {str(e)}",
                "session_id": session_id,
                "user_id": user_id,
                "content": "I apologize, but I'm experiencing technical difficulties retrieving a sample."
            } 