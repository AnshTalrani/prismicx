"""
User Insight Models

This module defines data models for user insights within the User Data Service.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional


class Subtopic:
    """
    Represents a specific knowledge element within a topic.
    
    Attributes:
        subtopic_id (str): Unique identifier for the subtopic
        name (str): Name of the subtopic
        content (dict): Flexible content storage
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
    """
    
    def __init__(self, subtopic_id: str, name: str, content: Dict[str, Any]):
        self.subtopic_id = subtopic_id
        self.name = name
        self.content = content
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def update_content(self, new_content: Dict[str, Any]) -> None:
        """Update the content of the subtopic."""
        self.content = new_content
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the subtopic to a dictionary."""
        return {
            "subtopic_id": self.subtopic_id,
            "name": self.name,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Subtopic':
        """Create a Subtopic instance from a dictionary."""
        subtopic = cls(
            subtopic_id=data["subtopic_id"],
            name=data["name"],
            content=data["content"]
        )
        if "created_at" in data and isinstance(data["created_at"], str):
            subtopic.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            subtopic.updated_at = datetime.fromisoformat(data["updated_at"])
        return subtopic


class Topic:
    """
    Represents a major knowledge area for a user.
    
    Attributes:
        topic_id (str): Unique identifier for the topic
        name (str): Name of the topic
        description (str): Description of the topic
        subtopics (List[Subtopic]): List of subtopics
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
    """
    
    def __init__(self, topic_id: str, name: str, description: str):
        self.topic_id = topic_id
        self.name = name
        self.description = description
        self.subtopics: List[Subtopic] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_subtopic(self, subtopic: Subtopic) -> None:
        """Add a subtopic to the topic."""
        self.subtopics.append(subtopic)
        self.updated_at = datetime.now()
    
    def remove_subtopic(self, subtopic_id: str) -> None:
        """Remove a subtopic by its ID."""
        self.subtopics = [s for s in self.subtopics if s.subtopic_id != subtopic_id]
        self.updated_at = datetime.now()
    
    def get_subtopic(self, subtopic_id: str) -> Optional[Subtopic]:
        """Get a subtopic by its ID."""
        for subtopic in self.subtopics:
            if subtopic.subtopic_id == subtopic_id:
                return subtopic
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the topic to a dictionary."""
        return {
            "topic_id": self.topic_id,
            "name": self.name,
            "description": self.description,
            "subtopics": [s.to_dict() for s in self.subtopics],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Topic':
        """Create a Topic instance from a dictionary."""
        topic = cls(
            topic_id=data["topic_id"],
            name=data["name"],
            description=data["description"]
        )
        if "subtopics" in data:
            topic.subtopics = [Subtopic.from_dict(s) for s in data["subtopics"]]
        if "created_at" in data and isinstance(data["created_at"], str):
            topic.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            topic.updated_at = datetime.fromisoformat(data["updated_at"])
        return topic


class UserInsight:
    """
    Core user insight model representing knowledge structure.
    
    Attributes:
        user_id (str): Unique identifier for the user
        tenant_id (str): Identifier for the tenant
        topics (List[Topic]): List of topics
        metadata (Dict[str, Any]): Additional metadata
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
    """
    
    def __init__(self, user_id: str, tenant_id: str):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.topics: List[Topic] = []
        self.metadata: Dict[str, Any] = {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_topic(self, topic: Topic) -> None:
        """Add a topic to the user insight."""
        self.topics.append(topic)
        self.updated_at = datetime.now()
    
    def remove_topic(self, topic_id: str) -> None:
        """Remove a topic by its ID."""
        self.topics = [t for t in self.topics if t.topic_id != topic_id]
        self.updated_at = datetime.now()
    
    def get_topic(self, topic_id: str) -> Optional[Topic]:
        """Get a topic by its ID."""
        for topic in self.topics:
            if topic.topic_id == topic_id:
                return topic
        return None
    
    def get_topic_by_name(self, name: str) -> Optional[Topic]:
        """Get a topic by its name."""
        for topic in self.topics:
            if topic.name == name:
                return topic
        return None
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """Update the metadata of the user insight."""
        self.metadata.update(metadata)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the user insight to a dictionary."""
        return {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "topics": [t.to_dict() for t in self.topics],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserInsight':
        """Create a UserInsight instance from a dictionary."""
        insight = cls(
            user_id=data["user_id"],
            tenant_id=data["tenant_id"]
        )
        if "topics" in data:
            insight.topics = [Topic.from_dict(t) for t in data["topics"]]
        if "metadata" in data:
            insight.metadata = data["metadata"]
        if "created_at" in data and isinstance(data["created_at"], str):
            insight.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            insight.updated_at = datetime.fromisoformat(data["updated_at"])
        return insight 