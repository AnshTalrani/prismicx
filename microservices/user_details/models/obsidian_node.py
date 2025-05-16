from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


class NodeType(Enum):
    """Enum representing the type of node in the visualization."""
    TOPIC = "topic"
    SUBTOPIC = "subtopic"


class Node:
    """
    Represents a node in the Obsidian visualization.
    
    Attributes:
        node_id (str): Unique identifier for the node
        label (str): Display label for the node
        node_type (NodeType): Type of the node (topic or subtopic)
        data (Dict[str, Any]): Associated data for the node
        position (Tuple[float, float]): X,Y coordinates for visualization
        size (float): Size of the node in the visualization
        color (str): Color of the node
    """
    
    def __init__(
        self, 
        node_id: str, 
        label: str, 
        node_type: NodeType,
        data: Dict[str, Any] = None,
        position: Tuple[float, float] = (0, 0),
        size: float = 1.0,
        color: str = "#1E88E5"
    ):
        self.node_id = node_id
        self.label = label
        self.node_type = node_type
        self.data = data or {}
        self.position = position
        self.size = size
        self.color = color
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the node to a dictionary."""
        return {
            "id": self.node_id,  # Using 'id' for frontend compatibility
            "label": self.label,
            "type": self.node_type.value,
            "data": self.data,
            "position": {
                "x": self.position[0],
                "y": self.position[1]
            },
            "size": self.size,
            "color": self.color
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """Create a Node instance from a dictionary."""
        position = (
            data.get("position", {}).get("x", 0),
            data.get("position", {}).get("y", 0)
        )
        
        return cls(
            node_id=data.get("id"),
            label=data.get("label", ""),
            node_type=NodeType(data.get("type", "topic")),
            data=data.get("data", {}),
            position=position,
            size=data.get("size", 1.0),
            color=data.get("color", "#1E88E5")
        )


class Edge:
    """
    Represents an edge (connection) between nodes in the Obsidian visualization.
    
    Attributes:
        edge_id (str): Unique identifier for the edge
        source_id (str): ID of the source node
        target_id (str): ID of the target node
        label (str): Optional label for the edge
        weight (float): Weight/strength of the connection
        color (str): Color of the edge
    """
    
    def __init__(
        self, 
        edge_id: str, 
        source_id: str, 
        target_id: str,
        label: str = "",
        weight: float = 1.0,
        color: str = "#757575"
    ):
        self.edge_id = edge_id
        self.source_id = source_id
        self.target_id = target_id
        self.label = label
        self.weight = weight
        self.color = color
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the edge to a dictionary."""
        return {
            "id": self.edge_id,  # Using 'id' for frontend compatibility
            "source": self.source_id,
            "target": self.target_id,
            "label": self.label,
            "weight": self.weight,
            "color": self.color
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Edge':
        """Create an Edge instance from a dictionary."""
        return cls(
            edge_id=data.get("id"),
            source_id=data.get("source"),
            target_id=data.get("target"),
            label=data.get("label", ""),
            weight=data.get("weight", 1.0),
            color=data.get("color", "#757575")
        )


class ObsidianGraph:
    """
    Represents the complete graph for Obsidian visualization.
    
    Attributes:
        user_id (str): ID of the user the graph belongs to
        tenant_id (str): ID of the tenant
        nodes (List[Node]): List of nodes in the graph
        edges (List[Edge]): List of edges in the graph
        metadata (Dict[str, Any]): Additional metadata for the graph
    """
    
    def __init__(self, user_id: str, tenant_id: str):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.nodes: List[Node] = []
        self.edges: List[Edge] = []
        self.metadata: Dict[str, Any] = {}
    
    def add_node(self, node: Node) -> None:
        """Add a node to the graph."""
        self.nodes.append(node)
    
    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by its ID."""
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the graph to a dictionary."""
        return {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ObsidianGraph':
        """Create an ObsidianGraph instance from a dictionary."""
        graph = cls(
            user_id=data["user_id"],
            tenant_id=data["tenant_id"]
        )
        
        if "nodes" in data:
            graph.nodes = [Node.from_dict(node_data) for node_data in data["nodes"]]
        
        if "edges" in data:
            graph.edges = [Edge.from_dict(edge_data) for edge_data in data["edges"]]
        
        if "metadata" in data:
            graph.metadata = data["metadata"]
        
        return graph 