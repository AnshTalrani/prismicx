import uuid
import logging
import requests
from typing import List, Dict, Any, Optional
from models.user_insight import UserInsight, Topic, Subtopic
from repositories.user_insight_repo import UserInsightRepository
from repositories.extension_repo import UserExtensionRepository
from services.config_service import ConfigService

logger = logging.getLogger(__name__)


class InsightService:
    """Service for managing User Insights with business logic."""
    
    def __init__(self, insight_repo: UserInsightRepository, extension_repo: UserExtensionRepository, config_service: ConfigService = None):
        """Initialize with repositories and config service."""
        self.insight_repo = insight_repo
        self.extension_repo = extension_repo
        self.config_service = config_service or ConfigService()
    
    def get_user_insight(self, user_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user's complete insight data.
        Returns None if not found.
        """
        insight = self.insight_repo.find_by_id(user_id, tenant_id)
        if not insight:
            logger.warning(f"No insight found for user {user_id}")
            return None
        
        result = insight.to_dict()
        
        # Enrich with extensions
        extensions = self.extension_repo.find_by_user_id(user_id, tenant_id)
        if extensions:
            result['extensions'] = [ext.to_dict() for ext in extensions]
        
        return result
    
    def get_user_topic(self, user_id: str, tenant_id: str, topic_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific topic for a user.
        Returns None if either the user or topic is not found.
        
        Args:
            user_id: The ID of the user
            tenant_id: The tenant ID
            topic_id: The ID of the topic to retrieve
            
        Returns:
            The topic data as a dictionary, or None if not found
        """
        insight = self.insight_repo.find_by_id(user_id, tenant_id)
        if not insight:
            logger.warning(f"No insight found for user {user_id}")
            return None
        
        topic = insight.get_topic(topic_id)
        if not topic:
            logger.warning(f"No topic found with ID {topic_id} for user {user_id}")
            return None
        
        return topic.to_dict()
    
    def create_user_insight(self, user_id: str, tenant_id: str) -> Dict[str, Any]:
        """
        Create a new UserInsight for a user.
        
        Only creates insights for users who meet eligibility criteria
        (e.g., paid subscription or other conditions defined by business rules).
        Uses the configured structure from templates.
        """
        # Check if user is eligible for insight creation
        if not self._check_user_eligibility(user_id, tenant_id):
            logger.warning(f"User {user_id} not eligible for insight creation")
            return {"error": "User not eligible for insight creation", "user_id": user_id}
        
        # If user already has an insight, return it
        existing_insight = self.insight_repo.find_by_id(user_id, tenant_id)
        if existing_insight:
            logger.info(f"User {user_id} already has insight record")
            return existing_insight.to_dict()
        
        # Create new insight with structure from configuration
        insight = UserInsight(user_id, tenant_id)
        
        # Apply default metadata from config
        structure_config = self.config_service.get_insight_structure()
        if structure_config and 'default_metadata' in structure_config:
            insight.metadata = structure_config['default_metadata'].copy()
            logger.info(f"Applied default metadata from template for user {user_id}")
        
        # Add default topics from config
        default_topics = self.config_service.get_default_topics()
        for topic_data in default_topics:
            # Create each topic with its subtopics
            topic_id = topic_data.get('topic_id', str(uuid.uuid4()))
            topic = Topic(
                topic_id=topic_id,
                name=topic_data.get('name', 'Unnamed Topic'),
                description=topic_data.get('description', '')
            )
            
            # Add subtopics if provided
            if 'subtopics' in topic_data and isinstance(topic_data['subtopics'], list):
                for subtopic_data in topic_data['subtopics']:
                    subtopic_id = subtopic_data.get('subtopic_id', str(uuid.uuid4()))
                    subtopic = Subtopic(
                        subtopic_id=subtopic_id,
                        name=subtopic_data.get('name', 'Unnamed Subtopic'),
                        content=subtopic_data.get('content', {})
                    )
                    topic.add_subtopic(subtopic)
            
            insight.add_topic(topic)
            logger.info(f"Added default topic {topic.name} for user {user_id}")
        
        # Save the insight
        self.insight_repo.save(insight)
        logger.info(f"Created new insight for user {user_id} with configured structure")
        
        return insight.to_dict()
    
    def _check_user_eligibility(self, user_id: str, tenant_id: str) -> bool:
        """
        Check if a user is eligible for insight creation based on business rules.
        
        This could check for subscription status, payment status, or any other
        criteria that determines whether a user should have access to insights.
        
        Returns:
            bool: True if user is eligible, False otherwise
        """
        try:
            # Example: Check with subscription service
            # This would be replaced with actual integration with your subscription service
            subscription_service_url = self._get_subscription_service_url()
            if subscription_service_url:
                response = requests.get(
                    f"{subscription_service_url}/api/v1/users/{user_id}/subscription/status",
                    headers={"X-Tenant-ID": tenant_id},
                    timeout=5
                )
                
                if response.status_code == 200:
                    subscription_data = response.json()
                    return subscription_data.get("is_active", False)
            
            # Fallback or alternative checks
            # Example: Check user permissions in a user service
            # More conditional checks can be added here based on business requirements
            
            # For development/testing - set default based on environment variable
            import os
            if os.getenv("DEVELOPMENT_MODE", "false").lower() == "true":
                logger.info(f"Development mode enabled, all users eligible")
                return True
                
            # Default to False in production if integration fails
            logger.warning(f"Could not determine eligibility for user {user_id}, defaulting to not eligible")
            return False
            
        except Exception as e:
            logger.error(f"Error checking user eligibility: {e}")
            # In case of integration errors, you could decide to:
            # 1. Default to False (restrictive)
            # 2. Default to True (permissive)
            # 3. Use a cached result
            # Choosing the restrictive approach here
            return False
    
    def _get_subscription_service_url(self) -> Optional[str]:
        """Get the URL for the subscription service from environment variables."""
        import os
        return os.getenv("SUBSCRIPTION_SERVICE_URL")
    
    def add_topic(self, user_id: str, tenant_id: str, topic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new topic to a user's insights."""
        insight = self.insight_repo.find_by_id(user_id, tenant_id)
        if not insight:
            insight = UserInsight(user_id, tenant_id)
        
        # Check if topic already exists with same name
        existing_topic = insight.get_topic_by_name(topic_data.get('name', ''))
        if existing_topic:
            logger.warning(f"Topic with name '{topic_data.get('name')}' already exists for user {user_id}")
            return existing_topic.to_dict()
        
        # Create new topic
        topic_id = topic_data.get('topic_id', str(uuid.uuid4()))
        topic = Topic(
            topic_id=topic_id,
            name=topic_data.get('name', 'Unnamed Topic'),
            description=topic_data.get('description', '')
        )
        
        # Add subtopics if provided
        if 'subtopics' in topic_data and isinstance(topic_data['subtopics'], list):
            for subtopic_data in topic_data['subtopics']:
                subtopic_id = subtopic_data.get('subtopic_id', str(uuid.uuid4()))
                subtopic = Subtopic(
                    subtopic_id=subtopic_id,
                    name=subtopic_data.get('name', 'Unnamed Subtopic'),
                    content=subtopic_data.get('content', {})
                )
                topic.add_subtopic(subtopic)
        
        insight.add_topic(topic)
        self.insight_repo.save(insight)
        logger.info(f"Added topic {topic_id} to user {user_id}")
        
        return topic.to_dict()
    
    def update_topic(self, user_id: str, tenant_id: str, topic_id: str, topic_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing topic."""
        insight = self.insight_repo.find_by_id(user_id, tenant_id)
        if not insight:
            logger.warning(f"No insight found for user {user_id}")
            return None
        
        topic = insight.get_topic(topic_id)
        if not topic:
            logger.warning(f"No topic found with ID {topic_id} for user {user_id}")
            return None
        
        # Update topic properties
        if 'name' in topic_data:
            topic.name = topic_data['name']
        
        if 'description' in topic_data:
            topic.description = topic_data['description']
        
        # Save changes
        self.insight_repo.save(insight)
        logger.info(f"Updated topic {topic_id} for user {user_id}")
        
        return topic.to_dict()
    
    def add_subtopic(self, user_id: str, tenant_id: str, topic_id: str, subtopic_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add a new subtopic to a topic."""
        insight = self.insight_repo.find_by_id(user_id, tenant_id)
        if not insight:
            logger.warning(f"No insight found for user {user_id}")
            return None
        
        topic = insight.get_topic(topic_id)
        if not topic:
            logger.warning(f"No topic found with ID {topic_id} for user {user_id}")
            return None
        
        # Create new subtopic
        subtopic_id = subtopic_data.get('subtopic_id', str(uuid.uuid4()))
        subtopic = Subtopic(
            subtopic_id=subtopic_id,
            name=subtopic_data.get('name', 'Unnamed Subtopic'),
            content=subtopic_data.get('content', {})
        )
        
        topic.add_subtopic(subtopic)
        self.insight_repo.save(insight)
        logger.info(f"Added subtopic {subtopic_id} to topic {topic_id} for user {user_id}")
        
        return subtopic.to_dict()
    
    def update_subtopic(self, user_id: str, tenant_id: str, topic_id: str, subtopic_id: str, subtopic_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing subtopic."""
        insight = self.insight_repo.find_by_id(user_id, tenant_id)
        if not insight:
            logger.warning(f"No insight found for user {user_id}")
            return None
        
        topic = insight.get_topic(topic_id)
        if not topic:
            logger.warning(f"No topic found with ID {topic_id} for user {user_id}")
            return None
        
        subtopic = topic.get_subtopic(subtopic_id)
        if not subtopic:
            logger.warning(f"No subtopic found with ID {subtopic_id} in topic {topic_id}")
            return None
        
        # Update subtopic properties
        if 'name' in subtopic_data:
            subtopic.name = subtopic_data['name']
        
        if 'content' in subtopic_data:
            subtopic.update_content(subtopic_data['content'])
        
        # Save changes
        self.insight_repo.save(insight)
        logger.info(f"Updated subtopic {subtopic_id} in topic {topic_id} for user {user_id}")
        
        return subtopic.to_dict()
    
    def remove_topic(self, user_id: str, tenant_id: str, topic_id: str) -> bool:
        """Remove a topic from a user's insights."""
        insight = self.insight_repo.find_by_id(user_id, tenant_id)
        if not insight:
            logger.warning(f"No insight found for user {user_id}")
            return False
        
        topic = insight.get_topic(topic_id)
        if not topic:
            logger.warning(f"No topic found with ID {topic_id} for user {user_id}")
            return False
        
        insight.remove_topic(topic_id)
        self.insight_repo.save(insight)
        logger.info(f"Removed topic {topic_id} from user {user_id}")
        
        return True
    
    def remove_subtopic(self, user_id: str, tenant_id: str, topic_id: str, subtopic_id: str) -> bool:
        """Remove a subtopic from a topic."""
        insight = self.insight_repo.find_by_id(user_id, tenant_id)
        if not insight:
            logger.warning(f"No insight found for user {user_id}")
            return False
        
        topic = insight.get_topic(topic_id)
        if not topic:
            logger.warning(f"No topic found with ID {topic_id} for user {user_id}")
            return False
        
        subtopic = topic.get_subtopic(subtopic_id)
        if not subtopic:
            logger.warning(f"No subtopic found with ID {subtopic_id} in topic {topic_id}")
            return False
        
        topic.remove_subtopic(subtopic_id)
        self.insight_repo.save(insight)
        logger.info(f"Removed subtopic {subtopic_id} from topic {topic_id} for user {user_id}")
        
        return True
    
    def find_users_by_topic(self, topic_name: str, filter_criteria: Dict[str, Any], page: int, page_size: int, tenant_id: str) -> List[Dict[str, Any]]:
        """Find all users that have a specific topic, with their associated data."""
        users_data = self.insight_repo.find_users_by_topic(
            topic_name=topic_name,
            filter_criteria=filter_criteria,
            page=page,
            page_size=page_size,
            tenant_id=tenant_id
        )
        
        # Enrich with relevant associated data
        for user_data in users_data:
            user_id = user_data.get('user_id')
            if user_id:
                extensions = self.extension_repo.find_by_user_id(user_id, tenant_id)
                if extensions:
                    user_data['extensions'] = [ext.to_dict() for ext in extensions]
        
        return users_data
    
    def summarize_topic(self, topic_name: str, tenant_id: str) -> Dict[str, Any]:
        """Generate a summary of a specific topic across all users."""
        all_topic_data = self.insight_repo.get_topic_across_users(topic_name, tenant_id)
        
        # Generate statistical summary
        user_count = len(all_topic_data)
        
        subtopic_counts = {}
        for user_data in all_topic_data:
            topic = user_data.get('topic', [{}])[0] if user_data.get('topic') else {}
            for subtopic in topic.get('subtopics', []):
                subtopic_name = subtopic.get('name', '')
                if subtopic_name:
                    subtopic_counts[subtopic_name] = subtopic_counts.get(subtopic_name, 0) + 1
        
        # Sort subtopics by frequency
        subtopic_frequency = [
            {"name": name, "count": count, "percentage": (count / user_count) * 100}
            for name, count in sorted(subtopic_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        summary = {
            'topic_name': topic_name,
            'user_count': user_count,
            'subtopic_frequency': subtopic_frequency,
            'most_common_subtopics': subtopic_frequency[:5] if subtopic_frequency else []
        }
        
        return summary
    
    def generate_insight_snapshot(self, user_id: str, tenant_id: str) -> Dict[str, Any]:
        """Create a condensed view of user insights for quick decision making."""
        insight = self.insight_repo.find_by_id(user_id, tenant_id)
        if not insight:
            logger.warning(f"No insight found for user {user_id}")
            return {"user_id": user_id, "error": "No insight found"}
        
        # Transform to decision-oriented format
        snapshot = {
            'user_id': user_id,
            'tenant_id': tenant_id,
            'topic_count': len(insight.topics),
            'primary_interests': self._extract_primary_interests(insight),
            'topic_summary': [
                {
                    'name': topic.name,
                    'subtopic_count': len(topic.subtopics),
                    'key_subtopics': [s.name for s in topic.subtopics[:3]]
                }
                for topic in insight.topics[:5]  # Limit to top 5 topics
            ]
        }
        
        # Add extension summaries
        extensions = self.extension_repo.find_by_user_id(user_id, tenant_id)
        if extensions:
            snapshot['extension_summary'] = []
            for ext in extensions:
                extension_summary = {
                    'type': ext.extension_type,
                    'metric_count': len(ext.metrics)
                }
                
                if ext.practicality:
                    extension_summary['practicality_score'] = ext.practicality.score
                    extension_summary['factor_count'] = len(ext.practicality.factors)
                
                snapshot['extension_summary'].append(extension_summary)
        
        return snapshot
    
    def _extract_primary_interests(self, insight: UserInsight) -> List[str]:
        """Extract the primary interests from a user insight."""
        # For this example, we'll just return the top 3 topic names
        # In a real implementation, this could use more sophisticated logic
        return [topic.name for topic in insight.topics[:3]]
    
    def process_batch_operations(self, operations: List[Dict[str, Any]], tenant_id: str) -> Dict[str, Any]:
        """Process multiple insight operations in a single request."""
        results = {
            'success': [],
            'failures': []
        }
        
        for operation in operations:
            try:
                op_type = operation.get('type')
                user_id = operation.get('user_id')
                
                if not op_type or not user_id:
                    results['failures'].append({
                        'operation': operation,
                        'error': 'Missing required fields: type and user_id'
                    })
                    continue
                
                # Handle different operation types
                if op_type == 'add_topic':
                    topic_data = operation.get('topic_data', {})
                    result = self.add_topic(user_id, tenant_id, topic_data)
                    results['success'].append({
                        'operation': op_type,
                        'user_id': user_id,
                        'result': result
                    })
                
                elif op_type == 'add_subtopic':
                    topic_id = operation.get('topic_id')
                    subtopic_data = operation.get('subtopic_data', {})
                    
                    if not topic_id:
                        results['failures'].append({
                            'operation': operation,
                            'error': 'Missing required field: topic_id'
                        })
                        continue
                    
                    result = self.add_subtopic(user_id, tenant_id, topic_id, subtopic_data)
                    results['success'].append({
                        'operation': op_type,
                        'user_id': user_id,
                        'result': result
                    })
                
                elif op_type == 'update_topic':
                    topic_id = operation.get('topic_id')
                    topic_data = operation.get('topic_data', {})
                    
                    if not topic_id:
                        results['failures'].append({
                            'operation': operation,
                            'error': 'Missing required field: topic_id'
                        })
                        continue
                    
                    result = self.update_topic(user_id, tenant_id, topic_id, topic_data)
                    results['success'].append({
                        'operation': op_type,
                        'user_id': user_id,
                        'result': result
                    })
                
                elif op_type == 'update_subtopic':
                    topic_id = operation.get('topic_id')
                    subtopic_id = operation.get('subtopic_id')
                    subtopic_data = operation.get('subtopic_data', {})
                    
                    if not topic_id or not subtopic_id:
                        results['failures'].append({
                            'operation': operation,
                            'error': 'Missing required fields: topic_id and subtopic_id'
                        })
                        continue
                    
                    result = self.update_subtopic(user_id, tenant_id, topic_id, subtopic_id, subtopic_data)
                    results['success'].append({
                        'operation': op_type,
                        'user_id': user_id,
                        'result': result
                    })
                
                elif op_type == 'remove_topic':
                    topic_id = operation.get('topic_id')
                    
                    if not topic_id:
                        results['failures'].append({
                            'operation': operation,
                            'error': 'Missing required field: topic_id'
                        })
                        continue
                    
                    result = self.remove_topic(user_id, tenant_id, topic_id)
                    results['success'].append({
                        'operation': op_type,
                        'user_id': user_id,
                        'result': result
                    })
                
                elif op_type == 'remove_subtopic':
                    topic_id = operation.get('topic_id')
                    subtopic_id = operation.get('subtopic_id')
                    
                    if not topic_id or not subtopic_id:
                        results['failures'].append({
                            'operation': operation,
                            'error': 'Missing required fields: topic_id and subtopic_id'
                        })
                        continue
                    
                    result = self.remove_subtopic(user_id, tenant_id, topic_id, subtopic_id)
                    results['success'].append({
                        'operation': op_type,
                        'user_id': user_id,
                        'result': result
                    })
                
                else:
                    results['failures'].append({
                        'operation': operation,
                        'error': f'Unknown operation type: {op_type}'
                    })
            
            except Exception as e:
                logger.error(f"Error processing batch operation: {e}")
                results['failures'].append({
                    'operation': operation,
                    'error': str(e)
                })
        
        return results 