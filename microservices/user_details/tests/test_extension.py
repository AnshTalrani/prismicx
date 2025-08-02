import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the parent directory to the path so we can import the application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.extension import Extension, ExtensionType, ExtensionStatus
from services.extension_service import ExtensionService


class TestExtension(unittest.TestCase):
    """Test cases for Extension functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.user_id = "test_user_123"
        self.tenant_id = "test_tenant_456"
        
        # Create a mock repository
        self.mock_repo = MagicMock()
        
        # Create extension service with mock repository
        self.extension_service = ExtensionService(self.mock_repo)
        
    def test_extension_creation(self):
        """Test creating an Extension object."""
        extension = Extension(
            extension_id="ext_123",
            name="Test Extension",
            description="This is a test extension",
            extension_type=ExtensionType.AI_ASSISTANT,
            status=ExtensionStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            config={"api_key": "test_key"},
            version="1.0.0"
        )
        
        self.assertEqual(extension.extension_id, "ext_123")
        self.assertEqual(extension.name, "Test Extension")
        self.assertEqual(extension.description, "This is a test extension")
        self.assertEqual(extension.extension_type, ExtensionType.AI_ASSISTANT)
        self.assertEqual(extension.status, ExtensionStatus.ACTIVE)
        self.assertEqual(extension.user_id, self.user_id)
        self.assertEqual(extension.tenant_id, self.tenant_id)
        self.assertEqual(extension.config, {"api_key": "test_key"})
        self.assertEqual(extension.version, "1.0.0")
        
    def test_register_extension(self):
        """Test registering a new extension."""
        # Set up parameters
        name = "Test Extension"
        description = "This is a test extension"
        extension_type = ExtensionType.AI_ASSISTANT
        config = {"api_key": "test_key"}
        version = "1.0.0"
        
        # Call the service method
        result = self.extension_service.register_extension(
            self.user_id,
            self.tenant_id,
            name,
            description,
            extension_type,
            config,
            version
        )
        
        # Verify repository was called
        self.mock_repo.save.assert_called_once()
        
        # Get the extension that was saved
        saved_extension = self.mock_repo.save.call_args[0][0]
        
        # Verify extension properties
        self.assertIsNotNone(saved_extension.extension_id)
        self.assertEqual(saved_extension.name, name)
        self.assertEqual(saved_extension.description, description)
        self.assertEqual(saved_extension.extension_type, extension_type)
        self.assertEqual(saved_extension.status, ExtensionStatus.ACTIVE)
        self.assertEqual(saved_extension.user_id, self.user_id)
        self.assertEqual(saved_extension.tenant_id, self.tenant_id)
        self.assertEqual(saved_extension.config, config)
        self.assertEqual(saved_extension.version, version)
        
    def test_get_extension(self):
        """Test getting an extension."""
        # Create a sample extension
        extension_id = "ext_test_1"
        mock_extension = self._create_sample_extension(extension_id)
        
        # Set up the mock to return the sample extension
        self.mock_repo.find_by_id.return_value = mock_extension
        
        # Call the service method
        result = self.extension_service.get_extension(extension_id, self.user_id, self.tenant_id)
        
        # Verify results
        self.assertEqual(result.extension_id, extension_id)
        self.assertEqual(result.user_id, self.user_id)
        self.assertEqual(result.tenant_id, self.tenant_id)
        
        # Verify repository was called
        self.mock_repo.find_by_id.assert_called_once_with(extension_id, self.user_id, self.tenant_id)
        
    def test_get_all_extensions(self):
        """Test getting all extensions for a user."""
        # Create sample extensions
        extensions = [
            self._create_sample_extension("ext1"),
            self._create_sample_extension("ext2"),
            self._create_sample_extension("ext3")
        ]
        
        # Set up the mock to return sample extensions
        self.mock_repo.find_by_user.return_value = extensions
        
        # Call the service method
        result = self.extension_service.get_all_extensions(self.user_id, self.tenant_id)
        
        # Verify results
        self.assertEqual(len(result), 3)
        self.assertIn("ext1", [ext.extension_id for ext in result])
        self.assertIn("ext2", [ext.extension_id for ext in result])
        self.assertIn("ext3", [ext.extension_id for ext in result])
        
        # Verify repository was called
        self.mock_repo.find_by_user.assert_called_once_with(self.user_id, self.tenant_id)
        
    def test_update_extension(self):
        """Test updating an extension."""
        # Create a sample extension
        extension_id = "ext_test_1"
        mock_extension = self._create_sample_extension(extension_id)
        
        # Set up the mock to return the sample extension
        self.mock_repo.find_by_id.return_value = mock_extension
        
        # Set up parameters
        new_name = "Updated Extension"
        new_description = "This is an updated extension"
        new_config = {"api_key": "new_test_key"}
        new_version = "1.1.0"
        
        # Call the service method
        result = self.extension_service.update_extension(
            extension_id,
            self.user_id,
            self.tenant_id,
            name=new_name,
            description=new_description,
            config=new_config,
            version=new_version
        )
        
        # Verify repository was called twice (once to find, once to save)
        self.assertEqual(self.mock_repo.find_by_id.call_count, 1)
        self.assertEqual(self.mock_repo.save.call_count, 1)
        
        # Get the extension that was saved
        updated_extension = self.mock_repo.save.call_args[0][0]
        
        # Verify extension properties
        self.assertEqual(updated_extension.extension_id, extension_id)
        self.assertEqual(updated_extension.name, new_name)
        self.assertEqual(updated_extension.description, new_description)
        self.assertEqual(updated_extension.config, new_config)
        self.assertEqual(updated_extension.version, new_version)
        
    def test_activate_extension(self):
        """Test activating an extension."""
        # Create a sample extension with INACTIVE status
        extension_id = "ext_test_1"
        mock_extension = self._create_sample_extension(extension_id, status=ExtensionStatus.INACTIVE)
        
        # Set up the mock to return the sample extension
        self.mock_repo.find_by_id.return_value = mock_extension
        
        # Call the service method
        result = self.extension_service.activate_extension(extension_id, self.user_id, self.tenant_id)
        
        # Verify repository was called twice (once to find, once to save)
        self.assertEqual(self.mock_repo.find_by_id.call_count, 1)
        self.assertEqual(self.mock_repo.save.call_count, 1)
        
        # Get the extension that was saved
        updated_extension = self.mock_repo.save.call_args[0][0]
        
        # Verify extension status was updated
        self.assertEqual(updated_extension.status, ExtensionStatus.ACTIVE)
        
    def test_deactivate_extension(self):
        """Test deactivating an extension."""
        # Create a sample extension with ACTIVE status
        extension_id = "ext_test_1"
        mock_extension = self._create_sample_extension(extension_id, status=ExtensionStatus.ACTIVE)
        
        # Set up the mock to return the sample extension
        self.mock_repo.find_by_id.return_value = mock_extension
        
        # Call the service method
        result = self.extension_service.deactivate_extension(extension_id, self.user_id, self.tenant_id)
        
        # Verify repository was called twice (once to find, once to save)
        self.assertEqual(self.mock_repo.find_by_id.call_count, 1)
        self.assertEqual(self.mock_repo.save.call_count, 1)
        
        # Get the extension that was saved
        updated_extension = self.mock_repo.save.call_args[0][0]
        
        # Verify extension status was updated
        self.assertEqual(updated_extension.status, ExtensionStatus.INACTIVE)
        
    def test_unregister_extension(self):
        """Test unregistering an extension."""
        # Create a sample extension
        extension_id = "ext_test_1"
        
        # Call the service method
        result = self.extension_service.unregister_extension(extension_id, self.user_id, self.tenant_id)
        
        # Verify repository was called
        self.mock_repo.delete.assert_called_once_with(extension_id, self.user_id, self.tenant_id)
        
    def _create_sample_extension(self, extension_id, status=ExtensionStatus.ACTIVE):
        """Create a sample extension for testing."""
        return Extension(
            extension_id=extension_id,
            name="Test Extension",
            description="This is a test extension",
            extension_type=ExtensionType.AI_ASSISTANT,
            status=status,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            config={"api_key": "test_key"},
            version="1.0.0"
        )


if __name__ == '__main__':
    unittest.main() 