import unittest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user_insight import UserInsight, Topic, Subtopic
from repositories.user_insight_repo import UserInsightRepository
from services.insight_service import InsightService


class TestUserInsight(unittest.TestCase):
    """Test cases for User Insight models and services."""

    def setUp(self):
        """Set up test fixtures."""
        self.user_id = "test_user_123"
        self.tenant_id = "test_tenant_456"
        
    def test_user_insight_creation(self):
        """Test creating a UserInsight object."""
        insight = UserInsight(self.user_id, self.tenant_id)
        
        self.assertEqual(insight.user_id, self.user_id)
        self.assertEqual(insight.tenant_id, self.tenant_id)
        self.assertEqual(len(insight.topics), 0)
        self.assertEqual(insight.metadata, {})
        
    def test_topic_addition(self):
        """Test adding a topic to a UserInsight."""
        insight = UserInsight(self.user_id, self.tenant_id)
        topic = Topic(
            topic_id="topic_123",
            name="Test Topic",
            description="A test topic"
        )
        
        insight.add_topic(topic)
        
        self.assertEqual(len(insight.topics), 1)
        self.assertEqual(insight.topics[0].topic_id, "topic_123")
        self.assertEqual(insight.topics[0].name, "Test Topic")
        
    def test_subtopic_addition(self):
        """Test adding a subtopic to a topic."""
        topic = Topic(
            topic_id="topic_123",
            name="Test Topic",
            description="A test topic"
        )
        subtopic = Subtopic(
            subtopic_id="subtopic_123",
            name="Test Subtopic",
            content={"key": "value"}
        )
        
        topic.add_subtopic(subtopic)
        
        self.assertEqual(len(topic.subtopics), 1)
        self.assertEqual(topic.subtopics[0].subtopic_id, "subtopic_123")
        self.assertEqual(topic.subtopics[0].name, "Test Subtopic")
        self.assertEqual(topic.subtopics[0].content, {"key": "value"})
        
    def test_to_dict_serialization(self):
        """Test serializing UserInsight to dictionary."""
        insight = UserInsight(self.user_id, self.tenant_id)
        topic = Topic(
            topic_id="topic_123",
            name="Test Topic",
            description="A test topic"
        )
        subtopic = Subtopic(
            subtopic_id="subtopic_123",
            name="Test Subtopic",
            content={"key": "value"}
        )
        
        topic.add_subtopic(subtopic)
        insight.add_topic(topic)
        
        insight_dict = insight.to_dict()
        
        self.assertEqual(insight_dict["user_id"], self.user_id)
        self.assertEqual(insight_dict["tenant_id"], self.tenant_id)
        self.assertEqual(len(insight_dict["topics"]), 1)
        self.assertEqual(insight_dict["topics"][0]["topic_id"], "topic_123")
        self.assertEqual(len(insight_dict["topics"][0]["subtopics"]), 1)
        self.assertEqual(insight_dict["topics"][0]["subtopics"][0]["subtopic_id"], "subtopic_123")


if __name__ == '__main__':
    unittest.main() 