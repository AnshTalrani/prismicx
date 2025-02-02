"""
Customer-support-bot microservice main entry point.

Demonstrates MACH principles and environment variable security checks.
"""

import os
import sys
from .handlers import SupportHandler
from .utils import logger
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from models.customer_request import CustomerRequest

def main():
    """
    Main function for the customer-support-bot microservice.

    Raises:
        EnvironmentError: If needed environment variables are not set.
    """
    required_env_var = "CS_BOT_API_KEY"
    api_key = os.getenv(required_env_var)

    if not api_key:
        raise EnvironmentError(
            f"The required environment variable '{required_env_var}' is not set."
        )
    
    try:
        print("Starting customer-support-bot microservice...")
        print(f"Using API key: {api_key[:4]}****")
        print("Customer-support-bot microservice is running.")
    except Exception as e:
        print(f"Error in customer-support-bot microservice: {e}", file=sys.stderr)
        sys.exit(1)

app = FastAPI()
handler = SupportHandler()

@app.post("/support")
async def support_request(req: CustomerRequest):
    try:
        response = await handler.handle(req)
        return JSONResponse(content=response)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    main()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 