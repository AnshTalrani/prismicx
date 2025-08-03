from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import structlog
import json
from datetime import datetime
from typing import Dict, List

from backend.api.dashboard_routes import router as dashboard_router
from backend.api.chatbot_routes import router as chatbot_router
from backend.models.dashboard_models import WebSocketMessage

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PrismicX Dashboard",
    description="Comprehensive business management dashboard with integrated chatbot",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connected", total_connections=len(self.active_connections))
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected", total_connections=len(self.active_connections))
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error("Failed to send WebSocket message", error=str(e))

manager = ConnectionManager()

# Include API routers
app.include_router(dashboard_router)
app.include_router(chatbot_router)

# Root endpoint
@app.get("/")
async def read_root():
    """Root endpoint with system information"""
    return {
        "message": "Welcome to PrismicX Dashboard!",
        "service": "monolith",
        "version": "1.0.0",
        "features": [
            "Dashboard Analytics",
            "CRM Management", 
            "Chatbot Integration",
            "Real-time Updates"
        ],
        "endpoints": {
            "dashboard": "/api/dashboard",
            "chatbot": "/api/chatbot",
            "docs": "/docs",
            "websocket": "/ws"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "prismicx-monolith",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "dashboard": "operational",
            "chatbot": "operational",
            "websocket": "operational"
        }
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Echo message back to sender
            response = WebSocketMessage(
                type="echo",
                data={"received": message_data}
            )
            await manager.send_personal_message(response.json(), websocket)
            
            # Broadcast certain message types
            if message_data.get("type") == "broadcast":
                broadcast_message = WebSocketMessage(
                    type="broadcast",
                    data=message_data.get("data", {})
                )
                await manager.broadcast(broadcast_message.json())
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        manager.disconnect(websocket)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("PrismicX Dashboard starting up")
    logger.info("Dashboard features initialized", 
                features=["CRM", "Analytics", "Chatbot", "WebSocket"])

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("PrismicX Dashboard shutting down") 