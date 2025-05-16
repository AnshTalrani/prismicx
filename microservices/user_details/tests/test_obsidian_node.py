import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the parent directory to the path so we can import the application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.obsidian_node import ObsidianNode, NodeType
from services.obsidian_service import ObsidianService


class TestObsidianNode(unittest.TestCase):
    """Test cases for ObsidianNode functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.user_id = "test_user_123"
        self.tenant_id = "test_tenant_456"
        
        # Create a mock repository
        self.mock_repo = MagicMock()
        
        # Create obsidian service with mock repository
        self.obsidian_service = ObsidianService(self.mock_repo)
        
    def test_obsidian_node_creation(self):
        """Test creating an ObsidianNode object."""
        node = ObsidianNode(
            node_id="node_123",
            name="Test Node",
            content="This is test content",
            node_type=NodeType.NOTE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            tags=["test", "sample"],
            links=[]
        )
        
        self.assertEqual(node.node_id, "node_123")
        self.assertEqual(node.name, "Test Node")
        self.assertEqual(node.content, "This is test content")
        self.assertEqual(node.node_type, NodeType.NOTE)
        self.assertEqual(node.user_id, self.user_id)
        self.assertEqual(node.tenant_id, self.tenant_id)
        self.assertEqual(node.tags, ["test", "sample"])
        self.assertEqual(node.links, [])
        
    def test_create_node(self):
        """Test creating a node through the service."""
        # Set up parameters
        name = "Test Node"
        content = "This is test content"
        node_type = NodeType.NOTE
        tags = ["test", "sample"]
        
        # Call the service method
        result = self.obsidian_service.create_node(
            self.user_id,
            self.tenant_id,
            name,
            content,
            node_type,
            tags
        )
        
        # Verify repository was called
        self.mock_repo.save.assert_called_once()
        
        # Get the node that was saved
        saved_node = self.mock_repo.save.call_args[0][0]
        
        # Verify node properties
        self.assertIsNotNone(saved_node.node_id)
        self.assertEqual(saved_node.name, name)
        self.assertEqual(saved_node.content, content)
        self.assertEqual(saved_node.node_type, node_type)
        self.assertEqual(saved_node.user_id, self.user_id)
        self.assertEqual(saved_node.tenant_id, self.tenant_id)
        self.assertEqual(saved_node.tags, tags)
        
    def test_get_node(self):
        """Test getting a node."""
        # Create a sample node
        node_id = "node_test_1"
        mock_node = self._create_sample_node(node_id)
        
        # Set up the mock to return the sample node
        self.mock_repo.find_by_id.return_value = mock_node
        
        # Call the service method
        result = self.obsidian_service.get_node(node_id, self.user_id, self.tenant_id)
        
        # Verify results
        self.assertEqual(result.node_id, node_id)
        self.assertEqual(result.user_id, self.user_id)
        self.assertEqual(result.tenant_id, self.tenant_id)
        
        # Verify repository was called
        self.mock_repo.find_by_id.assert_called_once_with(node_id, self.user_id, self.tenant_id)
        
    def test_update_node(self):
        """Test updating a node."""
        # Create a sample node
        node_id = "node_test_1"
        mock_node = self._create_sample_node(node_id)
        
        # Set up the mock to return the sample node
        self.mock_repo.find_by_id.return_value = mock_node
        
        # Set up parameters
        new_name = "Updated Node"
        new_content = "This is updated content"
        new_tags = ["updated", "test"]
        
        # Call the service method
        result = self.obsidian_service.update_node(
            node_id,
            self.user_id,
            self.tenant_id,
            name=new_name,
            content=new_content,
            tags=new_tags
        )
        
        # Verify repository was called twice (once to find, once to save)
        self.assertEqual(self.mock_repo.find_by_id.call_count, 1)
        self.assertEqual(self.mock_repo.save.call_count, 1)
        
        # Get the node that was saved
        updated_node = self.mock_repo.save.call_args[0][0]
        
        # Verify node properties
        self.assertEqual(updated_node.node_id, node_id)
        self.assertEqual(updated_node.name, new_name)
        self.assertEqual(updated_node.content, new_content)
        self.assertEqual(updated_node.tags, new_tags)
        
    def test_delete_node(self):
        """Test deleting a node."""
        # Create a sample node
        node_id = "node_test_1"
        
        # Call the service method
        result = self.obsidian_service.delete_node(node_id, self.user_id, self.tenant_id)
        
        # Verify repository was called
        self.mock_repo.delete.assert_called_once_with(node_id, self.user_id, self.tenant_id)
        
    def test_create_link(self):
        """Test creating a link between nodes."""
        # Create two sample nodes
        source_id = "source_node"
        target_id = "target_node"
        source_node = self._create_sample_node(source_id)
        target_node = self._create_sample_node(target_id)
        
        # Set up the mock to return the source node
        self.mock_repo.find_by_id.return_value = source_node
        
        # Call the service method
        result = self.obsidian_service.create_link(
            source_id,
            target_id,
            self.user_id,
            self.tenant_id
        )
        
        # Verify repository was called twice (once to find, once to save)
        self.assertEqual(self.mock_repo.find_by_id.call_count, 1)
        self.assertEqual(self.mock_repo.save.call_count, 1)
        
        # Get the node that was saved
        updated_node = self.mock_repo.save.call_args[0][0]
        
        # Verify link was added
        self.assertEqual(len(updated_node.links), 1)
        self.assertEqual(updated_node.links[0], target_id)
        
    def test_find_nodes_by_tag(self):
        """Test finding nodes by tag."""
        # Set up tag to search for
        tag = "test_tag"
        
        # Create sample nodes
        nodes = [
            self._create_sample_node("node1", tags=[tag, "other"]),
            self._create_sample_node("node2", tags=[tag]),
            self._create_sample_node("node3", tags=["other"])
        ]
        
        # Set up the mock to return filtered nodes
        self.mock_repo.find_by_tag.return_value = [nodes[0], nodes[1]]
        
        # Call the service method
        result = self.obsidian_service.find_nodes_by_tag(
            tag,
            self.user_id,
            self.tenant_id
        )
        
        # Verify results
        self.assertEqual(len(result), 2)
        self.assertIn("node1", [node.node_id for node in result])
        self.assertIn("node2", [node.node_id for node in result])
        self.assertNotIn("node3", [node.node_id for node in result])
        
        # Verify repository was called
        self.mock_repo.find_by_tag.assert_called_once_with(tag, self.user_id, self.tenant_id)
        
    def _create_sample_node(self, node_id, tags=None):
        """Create a sample obsidian node for testing."""
        if tags is None:
            tags = ["test"]
            
        return ObsidianNode(
            node_id=node_id,
            name="Test Node",
            content="This is test content",
            node_type=NodeType.NOTE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            tags=tags,
            links=[]
        )


if __name__ == '__main__':
    unittest.main() 