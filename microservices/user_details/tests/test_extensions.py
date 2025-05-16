import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.extension import Extension, InsightExtension
from services.extension_service import ExtensionService


class TestExtensions(unittest.TestCase):
    """Test cases for Extension functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.user_id = "test_user_123"
        self.tenant_id = "test_tenant_456"
        
        # Create a mock extension repository
        self.mock_extension_repo = MagicMock()
        
        # Create a mock insight repository
        self.mock_insight_repo = MagicMock()
        self.mock_insight_repo.find_by_id.return_value = self._create_sample_user_insight()
        
        # Create extension service with mock repositories
        self.extension_service = ExtensionService(self.mock_extension_repo, self.mock_insight_repo)
        
        # Load extension templates from config
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, '..', 'config', 'templates.json')
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.extension_templates = config.get('extension_templates', {})
        except Exception as e:
            print(f"Warning: Could not load extension templates: {str(e)}")
            self.extension_templates = {}
        
    def _create_sample_user_insight(self):
        """Create a sample user insight for testing."""
        # This would typically return a UserInsight object
        # We're just mocking it for testing
        mock_insight = MagicMock()
        mock_insight.user_id = self.user_id
        mock_insight.tenant_id = self.tenant_id
        mock_insight.extensions = []
        
        return mock_insight
        
    def test_extension_creation(self):
        """Test creating an Extension object."""
        extension = Extension(
            extension_id="ext_123",
            name="Test Extension",
            description="This is a test extension",
            extension_type="social_media",
            metrics={
                "engagement_rate": 0.05,
                "followers": 1000,
                "post_frequency": 3
            }
        )
        
        self.assertEqual(extension.extension_id, "ext_123")
        self.assertEqual(extension.name, "Test Extension")
        self.assertEqual(extension.description, "This is a test extension")
        self.assertEqual(extension.extension_type, "social_media")
        self.assertEqual(extension.metrics["followers"], 1000)
        
    def test_insight_extension_creation(self):
        """Test creating an InsightExtension object."""
        extension = Extension(
            extension_id="ext_123",
            name="Test Extension",
            description="This is a test extension",
            extension_type="social_media",
            metrics={
                "engagement_rate": 0.05,
                "followers": 1000,
                "post_frequency": 3
            }
        )
        
        insight_extension = InsightExtension(
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            extension=extension,
            related_topics=["topic_1", "topic_2"]
        )
        
        self.assertEqual(insight_extension.user_id, self.user_id)
        self.assertEqual(insight_extension.tenant_id, self.tenant_id)
        self.assertEqual(insight_extension.extension.extension_id, "ext_123")
        self.assertEqual(len(insight_extension.related_topics), 2)
        
    def test_extension_service_add_extension(self):
        """Test adding an extension to a user insight."""
        # Set up mock to return a new extension ID
        self.mock_extension_repo.create.return_value = "ext_123"
        
        # Set up parameters
        extension_type = "social_media"
        extension_name = "My Social Media"
        extension_metrics = {
            "engagement_rate": 0.05,
            "followers": 1000,
            "post_frequency": 3
        }
        related_topics = ["topic_1"]
        
        # Call the service method
        result = self.extension_service.add_extension(
            self.user_id, 
            self.tenant_id,
            extension_type,
            extension_name,
            extension_metrics,
            related_topics
        )
        
        # Verify results
        self.assertEqual(result["extension_id"], "ext_123")
        self.assertEqual(result["name"], extension_name)
        
        # Verify repositories were called
        self.mock_insight_repo.find_by_id.assert_called_once_with(self.user_id, self.tenant_id)
        self.mock_extension_repo.create.assert_called_once()
        
    def test_extension_template_retrieval(self):
        """Test retrieving extension templates."""
        # Skip test if no templates were loaded
        if not self.extension_templates:
            self.skipTest("No extension templates available")
            
        # Call the service method
        templates = self.extension_service.get_extension_templates()
        
        # Verify we got templates
        self.assertIsNotNone(templates)
        self.assertTrue(len(templates) > 0)
        
        # Check structure of a template
        for template_type, template in templates.items():
            self.assertIn("metrics", template)
            self.assertIn("factors", template)
            
    def test_calculate_extension_score(self):
        """Test calculating score for an extension."""
        # Create test extension with metrics
        extension = Extension(
            extension_id="ext_123",
            name="Test Extension",
            description="This is a test extension",
            extension_type="social_media",
            metrics={
                "engagement_rate": 0.05,
                "followers": 1000,
                "post_frequency": 3
            }
        )
        
        # Skip if we don't have the template
        if "social_media" not in self.extension_templates:
            self.skipTest("Social media extension template not available")
            
        # Set up mock to return a template
        self.extension_service.get_extension_templates = MagicMock(
            return_value=self.extension_templates
        )
        
        # Call calculate score method
        score_data = self.extension_service.calculate_extension_score(extension)
        
        # Verify results
        self.assertIsNotNone(score_data)
        self.assertIn("overall_score", score_data)
        self.assertIn("factor_scores", score_data)
        self.assertTrue(0 <= score_data["overall_score"] <= 100)


if __name__ == '__main__':
    unittest.main() 