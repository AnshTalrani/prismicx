"""
Session Manager's role in the new architecture:
1. Maintains active sessions
2. Links user_id with session_id
3. Manages session timeouts
4. Helps chain_builder maintain conversation state
"""

from langchain.memory import ConversationSummaryMemory
from langchain.chat_models import ChatOpenAI
from src.config.bot_configs import BOT_CONFIGS
import time

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.memory_store = {}  # Stores ConversationSummaryMemory instances
    
    async def get_or_create_session(self, session_id: str, user_id: str, bot_type: str):
        """Get existing session or create new one."""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "user_id": user_id,
                "bot_type": bot_type,
                "last_active": time.time()
            }
            # Create memory instance for this session
            self.memory_store[session_id] = ConversationSummaryMemory(
                llm=ChatOpenAI(temperature=0),
                memory_key="chat_history",
                return_messages=True,
                max_token_limit=BOT_CONFIGS[bot_type]["memory_tokens"]
            )
        
        return self.sessions[session_id]
    
    def get_session_memory(self, session_id: str) -> ConversationSummaryMemory:
        """Get the memory instance for a session."""
        return self.memory_store.get(session_id)
    
    def update_session_activity(self, session_id: str):
        """Update last activity time for session."""
        if session_id in self.sessions:
            self.sessions[session_id]["last_active"] = time.time()
    
    async def cleanup_inactive_sessions(self, timeout: int = 3600):
        """Clean up inactive sessions."""
        current_time = time.time()
        inactive_sessions = [
            session_id for session_id, session in self.sessions.items()
            if current_time - session["last_active"] > timeout
        ]
        
        for session_id in inactive_sessions:
            del self.sessions[session_id]
            if session_id in self.memory_store:
                del self.memory_store[session_id]
    
    async def cleanup_all_sessions(self):
        """Clean up all sessions."""
        self.sessions.clear()
        self.memory_store.clear()