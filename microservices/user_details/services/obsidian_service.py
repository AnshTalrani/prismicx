import uuid
import logging
from typing import List, Dict, Any, Optional
import math
import random
from models.user_insight import UserInsight, Topic, Subtopic
from models.obsidian_node import ObsidianGraph, Node, Edge, NodeType
from repositories.user_insight_repo import UserInsightRepository

logger = logging.getLogger(__name__)


class ObsidianService:
    """Service for generating Obsidian visualizations from user insights."""
    
    def __init__(self, insight_repo: UserInsightRepository):
        """Initialize with repository."""
        self.insight_repo = insight_repo
    
    def generate_graph(self, user_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Generate a node-based graph representation of user insights.
        Returns None if user insights not found.
        """
        insight = self.insight_repo.find_by_id(user_id, tenant_id)
        if not insight:
            logger.warning(f"No insight found for user {user_id}")
            return None
        
        # Create graph
        graph = ObsidianGraph(user_id, tenant_id)
        
        # Create nodes for topics with circular layout
        self._add_topics_to_graph(graph, insight)
        
        return graph.to_dict()
    
    def _add_topics_to_graph(self, graph: ObsidianGraph, insight: UserInsight) -> None:
        """Add topics to the graph with a circular layout."""
        topics = insight.topics
        topic_count = len(topics)
        
        if topic_count == 0:
            return
        
        # Center node for user
        user_node = Node(
            node_id=f"user_{insight.user_id}",
            label=f"User {insight.user_id}",
            node_type=NodeType.TOPIC,
            size=2.0,
            color="#FF5722",
            position=(0, 0)
        )
        graph.add_node(user_node)
        
        # Place topics in a circle around the user node
        radius = 400  # Adjust as needed
        for i, topic in enumerate(topics):
            angle = (2 * math.pi * i) / topic_count
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            
            topic_node = Node(
                node_id=topic.topic_id,
                label=topic.name,
                node_type=NodeType.TOPIC,
                data={"description": topic.description},
                position=(x, y),
                size=1.5,
                color="#1E88E5"
            )
            graph.add_node(topic_node)
            
            # Add edge from user to topic
            edge_id = f"e_{user_node.node_id}_{topic_node.node_id}"
            edge = Edge(
                edge_id=edge_id,
                source_id=user_node.node_id,
                target_id=topic_node.node_id
            )
            graph.add_edge(edge)
            
            # Add subtopics for this topic
            self._add_subtopics_to_graph(graph, topic, (x, y))
    
    def _add_subtopics_to_graph(self, graph: ObsidianGraph, topic: Topic, topic_position: tuple) -> None:
        """Add subtopics to the graph around the topic node."""
        subtopics = topic.subtopics
        subtopic_count = len(subtopics)
        
        if subtopic_count == 0:
            return
        
        # Place subtopics in a smaller circle around the topic
        radius = 200  # Smaller radius for subtopics
        for i, subtopic in enumerate(subtopics):
            angle = (2 * math.pi * i) / subtopic_count
            # Add some randomness to make it look more natural
            jitter = random.uniform(0.8, 1.2)
            x = topic_position[0] + (radius * jitter * math.cos(angle))
            y = topic_position[1] + (radius * jitter * math.sin(angle))
            
            subtopic_node = Node(
                node_id=subtopic.subtopic_id,
                label=subtopic.name,
                node_type=NodeType.SUBTOPIC,
                data={"content": subtopic.content},
                position=(x, y),
                size=1.0,
                color="#4CAF50"
            )
            graph.add_node(subtopic_node)
            
            # Add edge from topic to subtopic
            edge_id = f"e_{topic.topic_id}_{subtopic.subtopic_id}"
            edge = Edge(
                edge_id=edge_id,
                source_id=topic.topic_id,
                target_id=subtopic.subtopic_id
            )
            graph.add_edge(edge)
    
    def get_node_details(self, user_id: str, tenant_id: str, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific node.
        Returns None if the node is not found.
        """
        insight = self.insight_repo.find_by_id(user_id, tenant_id)
        if not insight:
            logger.warning(f"No insight found for user {user_id}")
            return None
        
        # Check if node is the user node
        if node_id == f"user_{insight.user_id}":
            return {
                "node_id": node_id,
                "type": "user",
                "user_id": insight.user_id,
                "tenant_id": tenant_id,
                "topic_count": len(insight.topics),
                "metadata": insight.metadata
            }
        
        # Check if node is a topic
        for topic in insight.topics:
            if topic.topic_id == node_id:
                return {
                    "node_id": node_id,
                    "type": "topic",
                    "name": topic.name,
                    "description": topic.description,
                    "subtopic_count": len(topic.subtopics),
                    "created_at": topic.created_at.isoformat(),
                    "updated_at": topic.updated_at.isoformat()
                }
            
            # Check if node is a subtopic
            for subtopic in topic.subtopics:
                if subtopic.subtopic_id == node_id:
                    return {
                        "node_id": node_id,
                        "type": "subtopic",
                        "name": subtopic.name,
                        "parent_topic": {
                            "topic_id": topic.topic_id,
                            "name": topic.name
                        },
                        "content": subtopic.content,
                        "created_at": subtopic.created_at.isoformat(),
                        "updated_at": subtopic.updated_at.isoformat()
                    }
        
        logger.warning(f"Node {node_id} not found for user {user_id}")
        return None
    
    def force_directed_layout(self, graph: ObsidianGraph) -> ObsidianGraph:
        """
        Apply a simple force-directed layout algorithm to the graph.
        This is a basic implementation for demonstration purposes.
        """
        # Constants
        REPULSION = 10000  # Repulsion force between nodes
        ATTRACTION = 0.05  # Attraction force for edges
        ITERATIONS = 50    # Number of iterations
        
        nodes = graph.nodes
        edges = graph.edges
        
        for _ in range(ITERATIONS):
            # Calculate repulsion forces between nodes
            for i, node1 in enumerate(nodes):
                force_x, force_y = 0, 0
                
                # Repulsion from other nodes
                for j, node2 in enumerate(nodes):
                    if i == j:
                        continue
                    
                    dx = node1.position[0] - node2.position[0]
                    dy = node1.position[1] - node2.position[1]
                    
                    # Avoid division by zero
                    distance = math.sqrt(dx * dx + dy * dy) or 0.1
                    
                    # Repulsion force (inverse square law)
                    force = REPULSION / (distance * distance)
                    
                    force_x += (dx / distance) * force
                    force_y += (dy / distance) * force
                
                # Apply forces to update position
                node1.position = (
                    node1.position[0] + force_x,
                    node1.position[1] + force_y
                )
            
            # Calculate attraction forces for edges
            for edge in edges:
                source_node = graph.get_node(edge.source_id)
                target_node = graph.get_node(edge.target_id)
                
                if source_node and target_node:
                    dx = target_node.position[0] - source_node.position[0]
                    dy = target_node.position[1] - source_node.position[1]
                    
                    distance = math.sqrt(dx * dx + dy * dy) or 0.1
                    
                    # Attraction force (linear)
                    force_x = dx * ATTRACTION
                    force_y = dy * ATTRACTION
                    
                    # Apply forces (move both nodes toward each other)
                    source_node.position = (
                        source_node.position[0] + force_x,
                        source_node.position[1] + force_y
                    )
                    
                    target_node.position = (
                        target_node.position[0] - force_x,
                        target_node.position[1] - force_y
                    )
        
        return graph 