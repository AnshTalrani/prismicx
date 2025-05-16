import os
import json
import logging
import copy
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigService:
    """
    Service for managing configuration templates for user insights and extensions.
    
    This service loads structure templates from JSON files and provides methods
    to access and validate against these templates.
    """
    
    def __init__(self, config_path: str = None, insight_repo=None, extension_repo=None):
        """
        Initialize the config service with a path to config files.
        
        Args:
            config_path: Path to the directory containing template JSON files.
                         Defaults to the CONFIG_PATH environment variable or 'config/templates'.
            insight_repo: Optional repository for user insights (required for automatic migrations)
            extension_repo: Optional repository for extensions (required for automatic migrations)
        """
        self.config_path = config_path or os.environ.get('CONFIG_PATH', 'config/templates')
        self.insight_structure = None
        self.extension_types = {}
        self.default_topics = None
        self.last_reload = None
        self.previous_insight_structure = None  # Store previous structure for migration comparison
        self.previous_extension_types = {}      # Store previous extension types for migration comparison
        self.insight_repo = insight_repo
        self.extension_repo = extension_repo
        self.reload_configs()
    
    def reload_configs(self, auto_migrate: bool = True) -> Dict[str, Any]:
        """
        Reload all configuration files from disk and trigger migrations if changes are detected.
        
        This method is called on initialization and can be called again
        to refresh configurations without restarting the service.
        
        Args:
            auto_migrate: Whether to automatically migrate existing data when templates change.
                          Default is True (making migrations mandatory).
                          
        Returns:
            A summary of reload and migration results
        """
        reload_results = {
            "status": "started",
            "templates_reloaded": [],
            "errors": [],
            "migration_summary": None
        }
        
        try:
            # Store previous configurations for migration comparison
            self.previous_insight_structure = copy.deepcopy(self.insight_structure) if self.insight_structure else None
            self.previous_extension_types = copy.deepcopy(self.extension_types) if self.extension_types else {}
            
            # Ensure the templates directory exists
            os.makedirs(self.config_path, exist_ok=True)
            os.makedirs(os.path.join(self.config_path, 'extension_types'), exist_ok=True)
            
            # Load user insight structure
            insight_path = os.path.join(self.config_path, 'user_insight_structure.json')
            if os.path.exists(insight_path):
                with open(insight_path, 'r') as f:
                    self.insight_structure = json.load(f)
                    logger.info(f"Loaded user insight structure from {insight_path}")
                    reload_results["templates_reloaded"].append("user_insight_structure")
            else:
                logger.warning(f"User insight structure file not found at {insight_path}")
                # Create with defaults if missing
                self._create_default_insight_structure(insight_path)
                reload_results["templates_reloaded"].append("user_insight_structure (default)")
            
            # Load extension types
            ext_dir = os.path.join(self.config_path, 'extension_types')
            if os.path.exists(ext_dir):
                for filename in os.listdir(ext_dir):
                    if filename.endswith('.json'):
                        with open(os.path.join(ext_dir, filename), 'r') as f:
                            ext_config = json.load(f)
                            ext_type = ext_config.get('extension_type')
                            if ext_type:
                                self.extension_types[ext_type] = ext_config
                                logger.info(f"Loaded extension type configuration for {ext_type}")
                                reload_results["templates_reloaded"].append(f"extension_type:{ext_type}")
                            else:
                                logger.warning(f"Extension type not specified in {filename}")
                                reload_results["errors"].append(f"Extension type not specified in {filename}")
            
            # If no extension types were found, create a default one
            if not self.extension_types:
                self._create_default_extension_type()
                reload_results["templates_reloaded"].append("extension_type:content_recommender (default)")
            
            # Load default topics
            topics_path = os.path.join(self.config_path, 'default_topics.json')
            if os.path.exists(topics_path):
                with open(topics_path, 'r') as f:
                    self.default_topics = json.load(f)
                    logger.info(f"Loaded default topics from {topics_path}")
                    reload_results["templates_reloaded"].append("default_topics")
            else:
                logger.warning(f"Default topics file not found at {topics_path}")
                # Create with defaults if missing
                self._create_default_topics(topics_path)
                reload_results["templates_reloaded"].append("default_topics (default)")
            
            self.last_reload = datetime.now()
            logger.info(f"Configuration reloaded successfully at {self.last_reload}")
            reload_results["status"] = "completed"
            
            # Automatically trigger migrations if changes are detected (mandatory)
            if auto_migrate and (self.insight_repo or self.extension_repo):
                # Check if migrations are needed
                has_insight_changes = self._has_insight_structure_changes()
                has_extension_changes = self._has_extension_type_changes()
                
                if has_insight_changes or has_extension_changes:
                    logger.info("Template changes detected. Triggering mandatory migration...")
                    
                    migration_results = {}
                    
                    # Migrate insights if repo is available and changes detected
                    if self.insight_repo and has_insight_changes:
                        insight_migration = self.migrate_existing_insights(self.insight_repo)
                        migration_results["insights"] = insight_migration
                    
                    # Migrate extensions if repo is available and changes detected
                    if self.extension_repo and has_extension_changes:
                        extension_migration = self.migrate_extensions(self.extension_repo)
                        migration_results["extensions"] = extension_migration
                    
                    reload_results["migration_summary"] = migration_results
                else:
                    logger.info("No template changes detected. Migration not needed.")
                    reload_results["migration_summary"] = {"status": "skipped", "reason": "No changes detected"}
            elif auto_migrate:
                logger.warning("Repositories not provided. Cannot perform automatic migrations.")
                reload_results["migration_summary"] = {"status": "skipped", "reason": "Repositories not available"}
            
            return reload_results
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            reload_results["status"] = "error"
            reload_results["errors"].append(str(e))
            return reload_results
    
    def _has_insight_structure_changes(self) -> bool:
        """
        Check if there are changes between previous and current insight structure.
        
        Returns:
            True if changes are detected, False otherwise
        """
        if not self.previous_insight_structure or not self.insight_structure:
            # First load or missing data
            return False
            
        # Compare insight structure
        if self.previous_insight_structure != self.insight_structure:
            return True
            
        # Compare default topics
        if self.default_topics and self.default_topics != self.get_default_topics():
            return True
            
        return False
    
    def _has_extension_type_changes(self) -> bool:
        """
        Check if there are changes between previous and current extension types.
        
        Returns:
            True if changes are detected, False otherwise
        """
        if not self.previous_extension_types or not self.extension_types:
            # First load or missing data
            return False
            
        # Check if any extension types have been added or removed
        if set(self.previous_extension_types.keys()) != set(self.extension_types.keys()):
            return True
            
        # Check if any extension types have changed
        for ext_type, config in self.extension_types.items():
            if ext_type in self.previous_extension_types:
                if self.previous_extension_types[ext_type] != config:
                    return True
                    
        return False
    
    def migrate_existing_insights(self, insight_repo) -> Dict[str, Any]:
        """
        Migrate all existing user insights across all tenants to match the new structure.
        
        This function:
        1. Detects changes between previous and current structure templates
        2. Applies those changes to all existing user insights
        3. Updates default topics if needed
        4. Saves the updated insights back to the database
        
        Args:
            insight_repo: The repository for user insights
            
        Returns:
            A summary of the migration results
        """
        if not self.previous_insight_structure:
            return {"status": "skipped", "reason": "No previous structure available for comparison"}
        
        try:
            # Get migration operations
            migration_ops = self._get_structure_migrations()
            if not migration_ops:
                return {"status": "skipped", "reason": "No structure changes detected"}
            
            # Get all tenants from the repository
            tenants = insight_repo.get_all_tenants()
            
            total_insights = 0
            updated_insights = 0
            failed_updates = 0
            
            # Process each tenant
            tenant_summaries = []
            for tenant_id in tenants:
                tenant_result = {
                    "tenant_id": tenant_id,
                    "total_insights": 0,
                    "updated_insights": 0,
                    "failed_updates": 0
                }
                
                # Get all insights for this tenant
                insights = insight_repo.find_all_for_tenant(tenant_id)
                tenant_result["total_insights"] = len(insights)
                total_insights += len(insights)
                
                # Apply migrations to each insight
                for insight in insights:
                    try:
                        # Apply structure changes
                        self._apply_structure_migrations(insight, migration_ops)
                        
                        # Apply topic updates if needed
                        if "add_default_topics" in migration_ops:
                            self._apply_topic_migrations(insight, migration_ops["add_default_topics"])
                        
                        # Save the updated insight
                        insight_repo.save(insight)
                        updated_insights += 1
                        tenant_result["updated_insights"] += 1
                    except Exception as e:
                        logger.error(f"Failed to migrate insight for user {insight.user_id}: {e}")
                        failed_updates += 1
                        tenant_result["failed_updates"] += 1
                
                tenant_summaries.append(tenant_result)
            
            # Prepare and return summary
            return {
                "status": "completed",
                "total_insights": total_insights,
                "updated_insights": updated_insights,
                "failed_updates": failed_updates,
                "tenant_summaries": tenant_summaries,
                "migration_operations": migration_ops
            }
            
        except Exception as e:
            logger.error(f"Error during insight migration: {e}")
            return {"status": "error", "error": str(e)}
    
    def _get_structure_migrations(self) -> Dict[str, Any]:
        """
        Determine what migrations need to be performed by comparing previous and current structures.
        
        Returns:
            A dictionary of migration operations
        """
        migrations = {}
        
        # Skip if no previous structure
        if not self.previous_insight_structure or not self.insight_structure:
            return migrations
        
        # Check for metadata changes
        if self.previous_insight_structure.get('default_metadata') != self.insight_structure.get('default_metadata'):
            migrations["metadata"] = {
                "old": self.previous_insight_structure.get('default_metadata', {}),
                "new": self.insight_structure.get('default_metadata', {})
            }
        
        # Check for topic changes
        if self.default_topics:
            # Determine if we have new default topics that should be added
            migrations["add_default_topics"] = self.default_topics
        
        # Check for schema changes - primarily for validation
        old_schema = self.previous_insight_structure.get('schema', {})
        new_schema = self.insight_structure.get('schema', {})
        if old_schema != new_schema:
            migrations["schema"] = {
                "old": old_schema,
                "new": new_schema
            }
        
        return migrations
    
    def _apply_structure_migrations(self, insight, migration_ops: Dict[str, Any]) -> None:
        """
        Apply the structure migrations to a single user insight.
        
        Args:
            insight: The user insight object
            migration_ops: The migration operations to apply
        """
        # Apply metadata changes
        if "metadata" in migration_ops:
            new_metadata = migration_ops["metadata"]["new"]
            
            # Update existing metadata with new fields
            for key, value in new_metadata.items():
                if key not in insight.metadata:
                    insight.metadata[key] = value
            
            # Remove fields that are no longer in the schema
            allowed_properties = self.insight_structure.get('schema', {}).get('metadata', {}).get('allowed_properties', [])
            if allowed_properties:
                # Only keep allowed properties and preserve user-specific data
                for key in list(insight.metadata.keys()):
                    if key not in allowed_properties and key not in new_metadata:
                        del insight.metadata[key]
        
        # Update the insight's updated_at timestamp
        insight.updated_at = datetime.now()
    
    def _apply_topic_migrations(self, insight, default_topics: List[Dict[str, Any]]) -> None:
        """
        Apply topic migrations to a user insight.
        
        Args:
            insight: The user insight object
            default_topics: The default topics to potentially add
        """
        from models.user_insight import Topic, Subtopic
        import uuid
        
        # Get existing topic names
        existing_topic_names = set(topic.name for topic in insight.topics)
        
        # Add any missing default topics
        for topic_data in default_topics:
            topic_name = topic_data.get('name')
            
            # Skip if this topic already exists
            if topic_name in existing_topic_names:
                continue
            
            # Create new topic
            topic_id = topic_data.get('topic_id', str(uuid.uuid4()))
            topic = Topic(
                topic_id=topic_id,
                name=topic_name,
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
            
            # Add the topic to the insight
            insight.add_topic(topic)
            logger.info(f"Added default topic {topic_name} to existing insight for user {insight.user_id}")
    
    def migrate_extensions(self, extension_repo) -> Dict[str, Any]:
        """
        Migrate all existing extensions across all tenants to match the new structure.
        
        Args:
            extension_repo: The repository for extensions
            
        Returns:
            A summary of the migration results
        """
        if not self.previous_extension_types:
            return {"status": "skipped", "reason": "No previous extension types available for comparison"}
        
        try:
            # Track stats
            total_extensions = 0
            updated_extensions = 0
            failed_updates = 0
            
            # Get all extensions for all extension types that have changed
            changed_types = []
            for ext_type, config in self.extension_types.items():
                if ext_type not in self.previous_extension_types or self.previous_extension_types[ext_type] != config:
                    changed_types.append(ext_type)
            
            if not changed_types:
                return {"status": "skipped", "reason": "No extension type changes detected"}
            
            # Process each extension type
            type_summaries = []
            for ext_type in changed_types:
                type_result = {
                    "extension_type": ext_type,
                    "total_extensions": 0,
                    "updated_extensions": 0,
                    "failed_updates": 0
                }
                
                # Get all extensions of this type
                extensions = extension_repo.find_by_type(ext_type)
                type_result["total_extensions"] = len(extensions)
                total_extensions += len(extensions)
                
                # Apply migrations to each extension
                for extension in extensions:
                    try:
                        # Apply the default values for new fields
                        self._apply_extension_migrations(extension, ext_type)
                        
                        # Save the updated extension
                        extension_repo.update(extension)
                        updated_extensions += 1
                        type_result["updated_extensions"] += 1
                    except Exception as e:
                        logger.error(f"Failed to migrate extension {extension.id}: {e}")
                        failed_updates += 1
                        type_result["failed_updates"] += 1
                
                type_summaries.append(type_result)
            
            # Prepare and return summary
            return {
                "status": "completed",
                "total_extensions": total_extensions,
                "updated_extensions": updated_extensions,
                "failed_updates": failed_updates,
                "type_summaries": type_summaries,
                "changed_types": changed_types
            }
            
        except Exception as e:
            logger.error(f"Error during extension migration: {e}")
            return {"status": "error", "error": str(e)}
    
    def _apply_extension_migrations(self, extension, ext_type: str) -> None:
        """
        Apply the extension migrations to a single extension.
        
        Args:
            extension: The extension object
            ext_type: The extension type
        """
        # Get the current extension type configuration
        config = self.extension_types.get(ext_type)
        if not config or 'defaults' not in config:
            return
        
        defaults = config['defaults']
        
        # Apply default values for fields that don't exist
        for key, value in defaults.items():
            if key not in ['metadata', 'id', 'user_id', 'tenant_id', 'extension_type'] and not hasattr(extension, key):
                setattr(extension, key, value)
        
        # Apply metadata defaults
        if 'metadata' in defaults and hasattr(extension, 'metadata'):
            for key, value in defaults['metadata'].items():
                if key not in extension.metadata:
                    extension.metadata[key] = value
        
        # Update the extension's updated_at timestamp
        if hasattr(extension, 'updated_at'):
            extension.updated_at = datetime.now()

    def _create_default_insight_structure(self, file_path: str) -> None:
        """Create a default user insight structure file if it doesn't exist."""
        default_structure = {
            "version": "1.0",
            "schema": {
                "topics": {
                    "required": ["topic_id", "name"],
                    "properties": {
                        "topic_id": "string",
                        "name": "string",
                        "description": "string",
                        "subtopics": "array"
                    }
                },
                "subtopics": {
                    "required": ["subtopic_id", "name"],
                    "properties": {
                        "subtopic_id": "string",
                        "name": "string",
                        "content": "object"
                    }
                },
                "metadata": {
                    "allowed_properties": ["primary_interests", "learning_style", "preferred_content_formats"]
                }
            },
            "default_metadata": {
                "learning_style": "unspecified",
                "preferred_content_formats": ["text"]
            }
        }
        
        try:
            with open(file_path, 'w') as f:
                json.dump(default_structure, f, indent=2)
            self.insight_structure = default_structure
            logger.info(f"Created default user insight structure at {file_path}")
        except Exception as e:
            logger.error(f"Error creating default insight structure: {e}")
    
    def _create_default_extension_type(self) -> None:
        """Create a default extension type file if none exist."""
        ext_dir = os.path.join(self.config_path, 'extension_types')
        file_path = os.path.join(ext_dir, 'content_recommender.json')
        
        default_ext = {
            "extension_type": "content_recommender",
            "schema": {
                "required": ["name", "enabled"],
                "metadata": {
                    "required": ["version", "configuration"],
                    "configuration": {
                        "required": ["refresh_frequency", "max_recommendations"]
                    }
                },
                "metrics": {
                    "properties": ["usage_count", "feedback_score", "last_used_at"]
                },
                "practicality": {
                    "factors": ["relevance", "utility", "ease_of_use"]
                }
            },
            "defaults": {
                "priority": 1,
                "enabled": True,
                "metadata": {
                    "version": "1.0",
                    "configuration": {
                        "refresh_frequency": "weekly",
                        "max_recommendations": 5
                    }
                }
            }
        }
        
        try:
            with open(file_path, 'w') as f:
                json.dump(default_ext, f, indent=2)
            self.extension_types["content_recommender"] = default_ext
            logger.info(f"Created default extension type at {file_path}")
        except Exception as e:
            logger.error(f"Error creating default extension type: {e}")
    
    def _create_default_topics(self, file_path: str) -> None:
        """Create a default topics file if it doesn't exist."""
        default_topics = [
            {
                "name": "Getting Started",
                "description": "Initial topics to help new users get started",
                "subtopics": [
                    {
                        "name": "System Introduction",
                        "content": {
                            "expertise_level": "beginner",
                            "key_points": ["Overview of system features", "How to navigate interfaces"]
                        }
                    }
                ]
            }
        ]
        
        try:
            with open(file_path, 'w') as f:
                json.dump(default_topics, f, indent=2)
            self.default_topics = default_topics
            logger.info(f"Created default topics at {file_path}")
        except Exception as e:
            logger.error(f"Error creating default topics: {e}")
    
    def get_insight_structure(self) -> Dict[str, Any]:
        """
        Get the user insight structure configuration.
        
        Returns:
            The configuration dictionary for user insight structure.
        """
        return self.insight_structure
    
    def get_extension_type_config(self, extension_type: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific extension type.
        
        Args:
            extension_type: The type of extension to get configuration for.
            
        Returns:
            The configuration dictionary for the specified extension type,
            or None if the type is not found.
        """
        return self.extension_types.get(extension_type)
    
    def get_all_extension_types(self) -> List[str]:
        """
        Get a list of all available extension types.
        
        Returns:
            A list of all configured extension type names.
        """
        return list(self.extension_types.keys())
    
    def get_default_topics(self) -> List[Dict[str, Any]]:
        """
        Get the default topics for new users.
        
        Returns:
            A list of default topic dictionaries, or an empty list if none are configured.
        """
        return self.default_topics if self.default_topics else []
    
    def validate_insight_structure(self, insight: Dict[str, Any]) -> bool:
        """
        Validate a user insight against the defined structure.
        
        Args:
            insight: The user insight dictionary to validate.
            
        Returns:
            True if the insight conforms to the structure, False otherwise.
        """
        # Basic validation - would be expanded in a real implementation
        if not self.insight_structure:
            return True  # No structure to validate against
        
        try:
            # Check if required top-level fields exist
            if "user_id" not in insight or "tenant_id" not in insight:
                logger.warning("Insight missing required fields: user_id or tenant_id")
                return False
            
            # For now, just do some basic validation - would be more extensive in production
            return True
        except Exception as e:
            logger.error(f"Error validating insight structure: {e}")
            return False
    
    def validate_extension(self, extension_type: str, extension: Dict[str, Any]) -> bool:
        """
        Validate an extension against its type-specific schema.
        
        Args:
            extension_type: The type of extension being validated.
            extension: The extension dictionary to validate.
            
        Returns:
            True if the extension conforms to its type schema, False otherwise.
        """
        # Get extension type configuration
        ext_config = self.get_extension_type_config(extension_type)
        if not ext_config or 'schema' not in ext_config:
            # Can't validate without a schema
            return True
        
        try:
            schema = ext_config['schema']
            
            # Check required fields
            if 'required' in schema:
                for field in schema['required']:
                    if field not in extension:
                        logger.warning(f"Extension missing required field: {field}")
                        return False
            
            # For now, just do basic validation - would be more extensive in production
            return True
        except Exception as e:
            logger.error(f"Error validating extension: {e}")
            return False 