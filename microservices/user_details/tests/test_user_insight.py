import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the parent directory to the path so we can import the application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user_insight import UserInsight, InsightType, InsightPriority
from services.insight_service import InsightService


class TestUserInsight(unittest.TestCase):
    """Test cases for UserInsight functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.user_id = "test_user_123"
        self.tenant_id = "test_tenant_456"
        
        # Create a mock repository
        self.mock_repo = MagicMock()
        
        # Create insight service with mock repository
        self.insight_service = InsightService(self.mock_repo)
        
    def test_user_insight_creation(self):
        """Test creating a UserInsight object."""
        insight = UserInsight(
            insight_id="ins_123",
            title="Test Insight",
            description="This is a test insight",
            insight_type=InsightType.BEHAVIOR,
            priority=InsightPriority.HIGH,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            metadata={"source": "test"},
            tags=["test", "behavior"]
        )
        
        self.assertEqual(insight.insight_id, "ins_123")
        self.assertEqual(insight.title, "Test Insight")
        self.assertEqual(insight.description, "This is a test insight")
        self.assertEqual(insight.insight_type, InsightType.BEHAVIOR)
        self.assertEqual(insight.priority, InsightPriority.HIGH)
        self.assertEqual(insight.user_id, self.user_id)
        self.assertEqual(insight.tenant_id, self.tenant_id)
        self.assertEqual(insight.metadata, {"source": "test"})
        self.assertEqual(insight.tags, ["test", "behavior"])
        
    def test_create_insight(self):
        """Test creating a new insight."""
        # Set up parameters
        title = "Test Insight"
        description = "This is a test insight"
        insight_type = InsightType.BEHAVIOR
        priority = InsightPriority.HIGH
        metadata = {"source": "test"}
        tags = ["test", "behavior"]
        
        # Call the service method
        result = self.insight_service.create_insight(
            self.user_id,
            self.tenant_id,
            title,
            description,
            insight_type,
            priority,
            metadata,
            tags
        )
        
        # Verify repository was called
        self.mock_repo.save.assert_called_once()
        
        # Get the insight that was saved
        saved_insight = self.mock_repo.save.call_args[0][0]
        
        # Verify insight properties
        self.assertIsNotNone(saved_insight.insight_id)
        self.assertEqual(saved_insight.title, title)
        self.assertEqual(saved_insight.description, description)
        self.assertEqual(saved_insight.insight_type, insight_type)
        self.assertEqual(saved_insight.priority, priority)
        self.assertEqual(saved_insight.user_id, self.user_id)
        self.assertEqual(saved_insight.tenant_id, self.tenant_id)
        self.assertEqual(saved_insight.metadata, metadata)
        self.assertEqual(saved_insight.tags, tags)
        
    def test_get_insight(self):
        """Test getting an insight."""
        # Create a sample insight
        insight_id = "ins_test_1"
        mock_insight = self._create_sample_insight(insight_id)
        
        # Set up the mock to return the sample insight
        self.mock_repo.find_by_id.return_value = mock_insight
        
        # Call the service method
        result = self.insight_service.get_insight(insight_id, self.user_id, self.tenant_id)
        
        # Verify results
        self.assertEqual(result.insight_id, insight_id)
        self.assertEqual(result.user_id, self.user_id)
        self.assertEqual(result.tenant_id, self.tenant_id)
        
        # Verify repository was called
        self.mock_repo.find_by_id.assert_called_once_with(insight_id, self.user_id, self.tenant_id)
        
    def test_get_all_insights(self):
        """Test getting all insights for a user."""
        # Create sample insights
        insights = [
            self._create_sample_insight("ins1"),
            self._create_sample_insight("ins2"),
            self._create_sample_insight("ins3")
        ]
        
        # Set up the mock to return sample insights
        self.mock_repo.find_by_user.return_value = insights
        
        # Call the service method
        result = self.insight_service.get_all_insights(self.user_id, self.tenant_id)
        
        # Verify results
        self.assertEqual(len(result), 3)
        self.assertIn("ins1", [ins.insight_id for ins in result])
        self.assertIn("ins2", [ins.insight_id for ins in result])
        self.assertIn("ins3", [ins.insight_id for ins in result])
        
        # Verify repository was called
        self.mock_repo.find_by_user.assert_called_once_with(self.user_id, self.tenant_id)
        
    def test_get_insights_by_type(self):
        """Test getting insights by type."""
        # Create sample insights of different types
        behavior_insights = [
            self._create_sample_insight("ins1", InsightType.BEHAVIOR),
            self._create_sample_insight("ins2", InsightType.BEHAVIOR)
        ]
        
        # Set up the mock to return sample insights
        self.mock_repo.find_by_type.return_value = behavior_insights
        
        # Call the service method
        result = self.insight_service.get_insights_by_type(InsightType.BEHAVIOR, self.user_id, self.tenant_id)
        
        # Verify results
        self.assertEqual(len(result), 2)
        self.assertIn("ins1", [ins.insight_id for ins in result])
        self.assertIn("ins2", [ins.insight_id for ins in result])
        
        # Verify repository was called
        self.mock_repo.find_by_type.assert_called_once_with(InsightType.BEHAVIOR, self.user_id, self.tenant_id)
        
    def test_get_insights_by_priority(self):
        """Test getting insights by priority."""
        # Create sample insights with different priorities
        high_priority_insights = [
            self._create_sample_insight("ins1", priority=InsightPriority.HIGH),
            self._create_sample_insight("ins2", priority=InsightPriority.HIGH)
        ]
        
        # Set up the mock to return sample insights
        self.mock_repo.find_by_priority.return_value = high_priority_insights
        
        # Call the service method
        result = self.insight_service.get_insights_by_priority(InsightPriority.HIGH, self.user_id, self.tenant_id)
        
        # Verify results
        self.assertEqual(len(result), 2)
        self.assertIn("ins1", [ins.insight_id for ins in result])
        self.assertIn("ins2", [ins.insight_id for ins in result])
        
        # Verify repository was called
        self.mock_repo.find_by_priority.assert_called_once_with(InsightPriority.HIGH, self.user_id, self.tenant_id)
        
    def test_get_insights_by_tag(self):
        """Test getting insights by tag."""
        # Create sample insights with different tags
        tagged_insights = [
            self._create_sample_insight("ins1", tags=["important", "test"]),
            self._create_sample_insight("ins2", tags=["important", "behavior"])
        ]
        
        # Set up the mock to return sample insights
        self.mock_repo.find_by_tag.return_value = tagged_insights
        
        # Call the service method
        result = self.insight_service.get_insights_by_tag("important", self.user_id, self.tenant_id)
        
        # Verify results
        self.assertEqual(len(result), 2)
        self.assertIn("ins1", [ins.insight_id for ins in result])
        self.assertIn("ins2", [ins.insight_id for ins in result])
        
        # Verify repository was called
        self.mock_repo.find_by_tag.assert_called_once_with("important", self.user_id, self.tenant_id)
        
    def test_update_insight(self):
        """Test updating an insight."""
        # Create a sample insight
        insight_id = "ins_test_1"
        mock_insight = self._create_sample_insight(insight_id)
        
        # Set up the mock to return the sample insight
        self.mock_repo.find_by_id.return_value = mock_insight
        
        # Set up parameters
        new_title = "Updated Insight"
        new_description = "This is an updated insight"
        new_priority = InsightPriority.CRITICAL
        new_metadata = {"source": "updated_test"}
        new_tags = ["updated", "critical"]
        
        # Call the service method
        result = self.insight_service.update_insight(
            insight_id,
            self.user_id,
            self.tenant_id,
            title=new_title,
            description=new_description,
            priority=new_priority,
            metadata=new_metadata,
            tags=new_tags
        )
        
        # Verify repository was called twice (once to find, once to save)
        self.assertEqual(self.mock_repo.find_by_id.call_count, 1)
        self.assertEqual(self.mock_repo.save.call_count, 1)
        
        # Get the insight that was saved
        updated_insight = self.mock_repo.save.call_args[0][0]
        
        # Verify insight properties
        self.assertEqual(updated_insight.insight_id, insight_id)
        self.assertEqual(updated_insight.title, new_title)
        self.assertEqual(updated_insight.description, new_description)
        self.assertEqual(updated_insight.priority, new_priority)
        self.assertEqual(updated_insight.metadata, new_metadata)
        self.assertEqual(updated_insight.tags, new_tags)
        
    def test_delete_insight(self):
        """Test deleting an insight."""
        # Create a sample insight
        insight_id = "ins_test_1"
        
        # Call the service method
        result = self.insight_service.delete_insight(insight_id, self.user_id, self.tenant_id)
        
        # Verify repository was called
        self.mock_repo.delete.assert_called_once_with(insight_id, self.user_id, self.tenant_id)
        
    def _create_sample_insight(self, insight_id, insight_type=InsightType.BEHAVIOR, 
                              priority=InsightPriority.HIGH, tags=None):
        """Create a sample insight for testing."""
        if tags is None:
            tags = ["test", "behavior"]
            
        return UserInsight(
            insight_id=insight_id,
            title="Test Insight",
            description="This is a test insight",
            insight_type=insight_type,
            priority=priority,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            metadata={"source": "test"},
            tags=tags
        )


if __name__ == '__main__':
    unittest.main() 