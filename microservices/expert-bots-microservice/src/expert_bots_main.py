"""
expert-bots microservice main module.

Sets up FastAPI application and initializes ExpertBase orchestrator.
"""

import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.expert_base.expert_base import ExpertBase
from src.expert_bots.instagram_bot import InstagramBot
# Import other ExpertBots as needed
from src.utils.logger import Logger
from src.knowledge_base.knowledge_base_component import KnowledgeBaseComponent

app = FastAPI(title="Expert Bots Microservice")

class RequestModel(BaseModel):
    intent_tag: str  # pre/pro/post
    phase_details: dict
    content: str

def initialize_expert_base() -> ExpertBase:
    """
    Initializes the ExpertBase with all available ExpertBots.

    Returns:
        ExpertBase: Initialized ExpertBase instance.
    """
    logger = Logger()
    knowledge_base = KnowledgeBaseComponent(vector_db="chroma")  # Initialize with actual vector DB instance

    expert_bots = {
        "instagram_post": InstagramBot(
            lora_adapter="path/to/instagram_lora",
            knowledge_base=knowledge_base,
            logger=logger
        ),
        # Initialize other bots like "etsy_listing": EtsyBot(...), etc.
    }

    return ExpertBase(expert_bots=expert_bots, logger=logger)

expert_base = initialize_expert_base()

@app.post("/generate-content")
def generate_content(request: RequestModel):
    """
    Endpoint to generate content based on intent_tag and parameters.

    Args:
        request (RequestModel): Incoming request containing intent_tag and parameters.

    Returns:
        Dict[str, Any]: Generated content or error message.
    """
    response = expert_base.handle_request(request.dict())
    if "error" in response:
        raise HTTPException(status_code=400, detail=response["error"])
    return response

@app.get("/health")
def health_check():
    """
    Health check endpoint.

    Returns:
        Dict[str, str]: Health status.
    """
    return {"status": "expert-bots microservice is up and running."}

def main():
    """
    Main function for the expert-bots microservice.

    Raises:
        EnvironmentError: If the required environment variable is not set.
    """
    required_env_var = "EXPERT_BOTS_API_KEY"
    api_key = os.getenv(required_env_var)

    if not api_key:
        raise EnvironmentError(
            f"The required environment variable '{required_env_var}' is not set."
        )

    try:
        print("Starting expert-bots microservice with FastAPI...")
        # Uvicorn is used to run the FastAPI app
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        print(f"Error in expert-bots microservice: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 