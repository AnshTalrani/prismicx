"""
Context Models

This module defines the data structures for conversation context,
ensuring consistent typing and structure throughout the system.
"""

from typing import Dict, List, Any, Optional, Union
from enum import Enum
from datetime import datetime
import json
from dataclasses import dataclass, field, asdict


class MessageRole(str, Enum):
    """
    Enum for message roles in conversation.
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(str, Enum):
    """
    Enum for conversation status.
    """
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    TRANSFERRED = "transferred"


@dataclass
class EntityValue:
    """
    Entity value extracted from conversation.
    """
    value: Any
    confidence: float = 1.0
    source: str = "user"  # user, system, external
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)


@dataclass
class DetectedIntent:
    """
    Intent detected in user message.
    """
    name: str
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)


@dataclass
class Message:
    """
    Message in conversation.
    """
    text: str
    role: MessageRole
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    message_id: str = field(default_factory=lambda: f"msg_{int(datetime.utcnow().timestamp())}")
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "text": self.text,
            "role": self.role.value if isinstance(self.role, MessageRole) else self.role,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
            "metadata": self.metadata
        }


@dataclass
class UserInfo:
    """
    User information for context.
    """
    user_id: str
    profile: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    history: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)


@dataclass
class ConversationContext:
    """
    Full conversation context.
    """
    session_id: str
    user_id: str
    bot_type: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    conversation_status: ConversationStatus = ConversationStatus.ACTIVE
    messages: List[Union[Dict[str, Any], Message]] = field(default_factory=list)
    entities: Dict[str, EntityValue] = field(default_factory=dict)
    user_info: Optional[Union[Dict[str, Any], UserInfo]] = None
    current_state: Optional[str] = None
    previous_state: Optional[str] = None
    state_entry_time: Optional[str] = None
    detected_intent: Optional[Union[Dict[str, Any], DetectedIntent]] = None
    platform: str = "web"
    metadata: Dict[str, Any] = field(default_factory=dict)
    conversation_summary: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "bot_type": self.bot_type,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "conversation_status": self.conversation_status.value if isinstance(self.conversation_status, ConversationStatus) else self.conversation_status,
            "messages": [
                msg.to_dict() if isinstance(msg, Message) else msg
                for msg in self.messages
            ],
            "entities": {
                k: v.to_dict() if isinstance(v, EntityValue) else v
                for k, v in self.entities.items()
            },
            "current_state": self.current_state,
            "previous_state": self.previous_state,
            "state_entry_time": self.state_entry_time,
            "platform": self.platform,
            "metadata": self.metadata,
            "conversation_summary": self.conversation_summary
        }
        
        if self.user_info:
            result["user_info"] = self.user_info.to_dict() if isinstance(self.user_info, UserInfo) else self.user_info
            
        if self.detected_intent:
            result["detected_intent"] = self.detected_intent.to_dict() if isinstance(self.detected_intent, DetectedIntent) else self.detected_intent
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """
        Create a ConversationContext instance from a dictionary.
        
        Args:
            data: Dictionary with context data
            
        Returns:
            ConversationContext instance
        """
        # Deep copy to avoid modifying the original
        context_data = json.loads(json.dumps(data))
        
        # Convert dictionaries to dataclass instances
        if "user_info" in context_data and context_data["user_info"]:
            user_info_data = context_data["user_info"]
            if isinstance(user_info_data, dict):
                context_data["user_info"] = UserInfo(**user_info_data)
                
        if "detected_intent" in context_data and context_data["detected_intent"]:
            intent_data = context_data["detected_intent"]
            if isinstance(intent_data, dict):
                context_data["detected_intent"] = DetectedIntent(**intent_data)
                
        # Convert message dictionaries to Message instances
        if "messages" in context_data:
            messages = []
            for msg in context_data["messages"]:
                if isinstance(msg, dict):
                    # Convert string role to enum
                    if "role" in msg and isinstance(msg["role"], str):
                        try:
                            msg["role"] = MessageRole(msg["role"])
                        except ValueError:
                            # Keep as string if not a valid enum value
                            pass
                    messages.append(Message(**msg))
                else:
                    messages.append(msg)
            context_data["messages"] = messages
            
        # Convert entity dictionaries to EntityValue instances
        if "entities" in context_data:
            entities = {}
            for key, value in context_data["entities"].items():
                if isinstance(value, dict):
                    entities[key] = EntityValue(**value)
                else:
                    entities[key] = value
            context_data["entities"] = entities
            
        # Convert string status to enum
        if "conversation_status" in context_data and isinstance(context_data["conversation_status"], str):
            try:
                context_data["conversation_status"] = ConversationStatus(context_data["conversation_status"])
            except ValueError:
                # Keep as string if not a valid enum value
                pass
                
        return cls(**context_data)
    
    def add_message(self, message: Union[Message, Dict[str, Any]]) -> None:
        """
        Add a message to the conversation.
        
        Args:
            message: Message to add
        """
        if isinstance(message, dict):
            # Convert role string to enum if needed
            if "role" in message and isinstance(message["role"], str):
                try:
                    message["role"] = MessageRole(message["role"])
                except ValueError:
                    # Keep as string if not a valid enum value
                    pass
            message_obj = Message(**message)
        else:
            message_obj = message
            
        self.messages.append(message_obj)
        self.last_accessed = datetime.utcnow().isoformat()
    
    def add_entity(self, name: str, value: Any, confidence: float = 1.0, source: str = "user") -> None:
        """
        Add or update an entity in the conversation.
        
        Args:
            name: Entity name
            value: Entity value
            confidence: Confidence score
            source: Source of the entity
        """
        self.entities[name] = EntityValue(
            value=value,
            confidence=confidence,
            source=source,
            timestamp=datetime.utcnow().isoformat()
        )
        self.last_accessed = datetime.utcnow().isoformat()
    
    def set_intent(self, name: str, confidence: float, parameters: Dict[str, Any] = None) -> None:
        """
        Set the detected intent.
        
        Args:
            name: Intent name
            confidence: Confidence score
            parameters: Intent parameters
        """
        self.detected_intent = DetectedIntent(
            name=name,
            confidence=confidence,
            parameters=parameters or {}
        )
        self.last_accessed = datetime.utcnow().isoformat()
    
    def update_state(self, new_state: str) -> None:
        """
        Update the conversation state.
        
        Args:
            new_state: New state name
        """
        self.previous_state = self.current_state
        self.current_state = new_state
        self.state_entry_time = datetime.utcnow().isoformat()
        self.last_accessed = datetime.utcnow().isoformat()
    
    def get_message_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent message history.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of recent messages
        """
        messages = [
            msg.to_dict() if isinstance(msg, Message) else msg 
            for msg in self.messages
        ]
        return messages[-limit:] if messages else [] 