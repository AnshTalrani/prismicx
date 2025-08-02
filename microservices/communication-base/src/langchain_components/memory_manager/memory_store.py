"""Persistent memory storage implementation."""

from typing import Dict, Optional
from redis import Redis
from langchain_core.messages import BaseMessage
from langchain.memory import RedisChatMessageHistory
from pydantic import BaseModel

class MemoryConfig(BaseModel):
    """Configuration for memory management."""
    window_size: int
    summary_interval: int
    max_tokens: int
    timeout: int
    summarization_prompt: str

class RedisMemoryStore:
    """Stores active conversations and real-time data"""
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = Redis.from_url(redis_url)
    
    Stores:
    - Active chat messages (TTL-based)
    - Real-time insights
    - Session context
    - Current conversation window
    
    def get_history(self, session_id: str, bot_config: Dict) -> RedisChatMessageHistory:
        """Get chat history for a session with bot-specific configuration."""
        history = RedisChatMessageHistory(
            session_id=session_id,
            url=self.redis_client.connection_pool.connection_kwargs,
            ttl=bot_config["memory"]["timeout"]
        )
        return history
    
    def save_message(self, session_id: str, message: BaseMessage, bot_config: Dict):
        """Save a message to history with bot-specific settings."""
        history = self.get_history(session_id, bot_config)
        history.add_message(message) 