import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the parent directory to the path so we can import the application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.obsidian_node import ObsidianNode, NodeType, NodeRelationship
from services.obsidian_service import ObsidianService


class TestObsidian(unittest.TestCase):
    """Test cases for Obsidian functionality."""

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
            title="Test Node",
            content="This is a test node",
            node_type=NodeType.NOTE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            metadata={"source": "test"},
            tags=["test", "note"]
        )
        
        self.assertEqual(node.node_id, "node_123")
        self.assertEqual(node.title, "Test Node")
        self.assertEqual(node.content, "This is a test node")
        self.assertEqual(node.node_type, NodeType.NOTE)
        self.assertEqual(node.user_id, self.user_id)
        self.assertEqual(node.tenant_id, self.tenant_id)
        self.assertEqual(node.metadata, {"source": "test"})
        self.assertEqual(node.tags, ["test", "note"])
        
    def test_create_node(self):
        """Test creating a new node."""
        # Set up parameters
        title = "Test Node"
        content = "This is a test node"
        node_type = NodeType.NOTE
        metadata = {"source": "test"}
        tags = ["test", "note"]
        
        # Call the service method
        result = self.obsidian_service.create_node(
            self.user_id,
            self.tenant_id,
            title,
            content,
            node_type,
            metadata,
            tags
        )
        
        # Verify repository was called
        self.mock_repo.save_node.assert_called_once()
        
        # Get the node that was saved
        saved_node = self.mock_repo.save_node.call_args[0][0]
        
        # Verify node properties
        self.assertIsNotNone(saved_node.node_id)
        self.assertEqual(saved_node.title, title)
        self.assertEqual(saved_node.content, content)
        self.assertEqual(saved_node.node_type, node_type)
        self.assertEqual(saved_node.user_id, self.user_id)
        self.assertEqual(saved_node.tenant_id, self.tenant_id)
        self.assertEqual(saved_node.metadata, metadata)
        self.assertEqual(saved_node.tags, tags)
        
    def test_get_node(self):
        """Test getting a node."""
        # Create a sample node
        node_id = "node_test_1"
        mock_node = self._create_sample_node(node_id)
        
        # Set up the mock to return the sample node
        self.mock_repo.find_node_by_id.return_value = mock_node
        
        # Call the service method
        result = self.obsidian_service.get_node(node_id, self.user_id, self.tenant_id)
        
        # Verify results
        self.assertEqual(result.node_id, node_id)
        self.assertEqual(result.user_id, self.user_id)
        self.assertEqual(result.tenant_id, self.tenant_id)
        
        # Verify repository was called
        self.mock_repo.find_node_by_id.assert_called_once_with(node_id, self.user_id, self.tenant_id)
        
    def test_get_all_nodes(self):
        """Test getting all nodes for a user."""
        # Create sample nodes
        nodes = [
            self._create_sample_node("node1"),
            self._create_sample_node("node2"),
            self._create_sample_node("node3")
        ]
        
        # Set up the mock to return sample nodes
        self.mock_repo.find_nodes_by_user.return_value = nodes
        
        # Call the service method
        result = self.obsidian_service.get_all_nodes(self.user_id, self.tenant_id)
        
        # Verify results
        self.assertEqual(len(result), 3)
        self.assertIn("node1", [node.node_id for node in result])
        self.assertIn("node2", [node.node_id for node in result])
        self.assertIn("node3", [node.node_id for node in result])
        
        # Verify repository was called
        self.mock_repo.find_nodes_by_user.assert_called_once_with(self.user_id, self.tenant_id)
        
    def test_get_nodes_by_type(self):
        """Test getting nodes by type."""
        # Create sample nodes of different types
        note_nodes = [
            self._create_sample_node("node1", NodeType.NOTE),
            self._create_sample_node("node2", NodeType.NOTE)
        ]
        
        # Set up the mock to return sample nodes
        self.mock_repo.find_nodes_by_type.return_value = note_nodes
        
        # Call the service method
        result = self.obsidian_service.get_nodes_by_type(NodeType.NOTE, self.user_id, self.tenant_id)
        
        # Verify results
        self.assertEqual(len(result), 2)
        self.assertIn("node1", [node.node_id for node in result])
        self.assertIn("node2", [node.node_id for node in result])
        
        # Verify repository was called
        self.mock_repo.find_nodes_by_type.assert_called_once_with(NodeType.NOTE, self.user_id, self.tenant_id)
        
    def test_get_nodes_by_tag(self):
        """Test getting nodes by tag."""
        # Create sample nodes with different tags
        tagged_nodes = [
            self._create_sample_node("node1", tags=["important", "test"]),
            self._create_sample_node("node2", tags=["important", "note"])
        ]
        
        # Set up the mock to return sample nodes
        self.mock_repo.find_nodes_by_tag.return_value = tagged_nodes
        
        # Call the service method
        result = self.obsidian_service.get_nodes_by_tag("important", self.user_id, self.tenant_id)
        
        # Verify results
        self.assertEqual(len(result), 2)
        self.assertIn("node1", [node.node_id for node in result])
        self.assertIn("node2", [node.node_id for node in result])
        
        # Verify repository was called
        self.mock_repo.find_nodes_by_tag.assert_called_once_with("important", self.user_id, self.tenant_id)
        
    def test_update_node(self):
        """Test updating a node."""
        # Create a sample node
        node_id = "node_test_1"
        mock_node = self._create_sample_node(node_id)
        
        # Set up the mock to return the sample node
        self.mock_repo.find_node_by_id.return_value = mock_node
        
        # Set up parameters
        new_title = "Updated Node"
        new_content = "This is an updated node"
        new_metadata = {"source": "updated_test"}
        new_tags = ["updated", "important"]
        
        # Call the service method
        result = self.obsidian_service.update_node(
            node_id,
            self.user_id,
            self.tenant_id,
            title=new_title,
            content=new_content,
            metadata=new_metadata,
            tags=new_tags
        )
        
        # Verify repository was called twice (once to find, once to save)
        self.assertEqual(self.mock_repo.find_node_by_id.call_count, 1)
        self.assertEqual(self.mock_repo.save_node.call_count, 1)
        
        # Get the node that was saved
        updated_node = self.mock_repo.save_node.call_args[0][0]
        
        # Verify node properties
        self.assertEqual(updated_node.node_id, node_id)
        self.assertEqual(updated_node.title, new_title)
        self.assertEqual(updated_node.content, new_content)
        self.assertEqual(updated_node.metadata, new_metadata)
        self.assertEqual(updated_node.tags, new_tags)
        
    def test_delete_node(self):
        """Test deleting a node."""
        # Create a sample node
        node_id = "node_test_1"
        
        # Call the service method
        result = self.obsidian_service.delete_node(node_id, self.user_id, self.tenant_id)
        
        # Verify repository was called
        self.mock_repo.delete_node.assert_called_once_with(node_id, self.user_id, self.tenant_id)
        
    def test_create_relationship(self):
        """Test creating a relationship between nodes."""
        # Create sample nodes
        source_id = "source_node"
        target_id = "target_node"
        relationship_type = NodeRelationship.REFERENCES
        
        # Call the service method
        result = self.obsidian_service.create_relationship(
            self.user_id,
            self.tenant_id,
            source_id,
            target_id,
            relationship_type
        )
        
        # Verify repository was called
        self.mock_repo.save_relationship.assert_called_once()
        
        # Get the relationship that was saved
        saved_relationship = self.mock_repo.save_relationship.call_args[0][0]
        
        # Verify relationship properties
        self.assertEqual(saved_relationship["source_id"], source_id)
        self.assertEqual(saved_relationship["target_id"], target_id)
        self.assertEqual(saved_relationship["relationship_type"], relationship_type)
        self.assertEqual(saved_relationship["user_id"], self.user_id)
        self.assertEqual(saved_relationship["tenant_id"], self.tenant_id)
        
    def test_get_node_relationships(self):
        """Test getting relationships for a node."""
        # Create a sample node id
        node_id = "node_test_1"
        
        # Create sample relationships
        relationships = [
            {
                "source_id": node_id,
                "target_id": "related_node_1",
                "relationship_type": NodeRelationship.REFERENCES,
                "user_id": self.user_id,
                "tenant_id": self.tenant_id
            },
            {
                "source_id": "related_node_2",
                "target_id": node_id,
                "relationship_type": NodeRelationship.RELATED_TO,
                "user_id": self.user_id,
                "tenant_id": self.tenant_id
            }
        ]
        
        # Set up the mock to return sample relationships
        self.mock_repo.find_relationships_for_node.return_value = relationships
        
        # Call the service method
        result = self.obsidian_service.get_node_relationships(node_id, self.user_id, self.tenant_id)
        
        # Verify results
        self.assertEqual(len(result), 2)
        
        # Verify repository was called
        self.mock_repo.find_relationships_for_node.assert_called_once_with(node_id, self.user_id, self.tenant_id)
        
    def test_delete_relationship(self):
        """Test deleting a relationship."""
        # Create sample relationship parameters
        source_id = "source_node"
        target_id = "target_node"
        relationship_type = NodeRelationship.REFERENCES
        
        # Call the service method
        result = self.obsidian_service.delete_relationship(
            self.user_id,
            self.tenant_id,
            source_id,
            target_id,
            relationship_type
        )
        
        # Verify repository was called
        self.mock_repo.delete_relationship.assert_called_once_with(
            self.user_id,
            self.tenant_id,
            source_id,
            target_id,
            relationship_type
        )
        
    def _create_sample_node(self, node_id, node_type=NodeType.NOTE, tags=None):
        """Create a sample node for testing."""
        if tags is None:
            tags = ["test", "note"]
            
        return ObsidianNode(
            node_id=node_id,
            title="Test Node",
            content="This is a test node",
            node_type=node_type,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            metadata={"source": "test"},
            tags=tags
        )


if __name__ == '__main__':
    unittest.main() 