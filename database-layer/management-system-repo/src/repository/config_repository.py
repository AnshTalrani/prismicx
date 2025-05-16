"""
Configuration Database Repository for managing tenant configurations in MongoDB.
"""

import logging
import motor.motor_asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pydantic import ValidationError

from ..models.config_models import TenantConfig, ConfigSchema, UserPreference, FeatureFrequencyGroup

logger = logging.getLogger(__name__)

class ConfigRepository:
    """Repository for managing tenant configurations."""
    
    def __init__(
        self,
        db_host: str,
        db_port: int,
        db_user: str,
        db_password: str,
        db_name: str
    ):
        """Initialize the config repository."""
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.client = None
        self.db = None
        
    async def initialize(self):
        """Initialize database connection."""
        connection_string = f"mongodb://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}"
        self.client = motor.motor_asyncio.AsyncIOMotorClient(connection_string)
        self.db = self.client[self.db_name]
        
        # Create indexes for better query performance
        await self._create_indexes()
        
        logger.info(f"Connected to MongoDB config database at {self.db_host}:{self.db_port}")
        
    async def _create_indexes(self):
        """Create database indexes for optimal query performance."""
        # Create compound index on tenant_id and config_key for tenant_configs collection
        await self.db.tenant_configs.create_index([("tenant_id", 1), ("config_key", 1)], unique=True)
        
        # Create index on config_key for faster prefix queries
        await self.db.tenant_configs.create_index("config_key")
        
        # Create index on key for config schemas
        await self.db.config_schemas.create_index("key", unique=True)
        
        # Create compound index for user preferences
        await self.db.user_preferences.create_index([("user_id", 1), ("feature_type", 1)], unique=True)
        
        # Create compound index for feature frequency groups
        await self.db.feature_frequency_groups.create_index(
            [("feature_type", 1), ("frequency", 1), ("time_key", 1)], 
            unique=True
        )
        
    async def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")
            
    async def get_config(self, tenant_id: str, config_key: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific tenant."""
        try:
            result = await self.db.tenant_configs.find_one(
                {"tenant_id": tenant_id, "config_key": config_key}
            )
            return result
        except Exception as e:
            logger.error(f"Error retrieving config for tenant {tenant_id}, key {config_key}: {str(e)}")
            return None
            
    async def get_config_for_all_tenants(self, config_key: str) -> Dict[str, Any]:
        """
        Get configuration for all tenants at once.
        
        This optimized method returns a mapping of tenant_id -> config_value
        for all tenants that have the requested configuration key.
        """
        try:
            result = {}
            cursor = self.db.tenant_configs.find({"config_key": config_key})
            
            async for document in cursor:
                tenant_id = document.get("tenant_id")
                if tenant_id:
                    result[tenant_id] = document.get("config_value")
                    
            return result
        except Exception as e:
            logger.error(f"Error retrieving config for all tenants, key {config_key}: {str(e)}")
            return {}
            
    async def set_config(
        self, 
        tenant_id: str, 
        config_key: str, 
        config_value: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Set or update configuration for a specific tenant."""
        try:
            # Check if configuration exists
            existing = await self.get_config(tenant_id, config_key)
            
            # Prepare metadata
            if metadata is None:
                metadata = {}
                
            now = datetime.utcnow()
            
            if existing:
                # Update existing config
                update_data = {
                    "config_value": config_value,
                    "updated_at": now
                }
                
                if metadata:
                    update_data["metadata"] = {**existing.get("metadata", {}), **metadata}
                    
                if updated_by:
                    update_data["updated_by"] = updated_by
                
                result = await self.db.tenant_configs.update_one(
                    {"tenant_id": tenant_id, "config_key": config_key},
                    {"$set": update_data}
                )
                
                if result.modified_count == 0:
                    logger.warning(f"Failed to update config for tenant {tenant_id}, key {config_key}")
                    return None
                    
                return await self.get_config(tenant_id, config_key)
            else:
                # Create new config
                doc = {
                    "tenant_id": tenant_id,
                    "config_key": config_key,
                    "config_value": config_value,
                    "metadata": metadata,
                    "created_at": now,
                    "updated_at": now
                }
                
                if created_by:
                    doc["created_by"] = created_by
                    
                if updated_by:
                    doc["updated_by"] = updated_by
                
                result = await self.db.tenant_configs.insert_one(doc)
                
                if not result.inserted_id:
                    logger.warning(f"Failed to create config for tenant {tenant_id}, key {config_key}")
                    return None
                    
                return await self.get_config(tenant_id, config_key)
        except Exception as e:
            logger.error(f"Error setting config for tenant {tenant_id}, key {config_key}: {str(e)}")
            return None
    
    async def delete_config(self, tenant_id: str, config_key: str) -> bool:
        """Delete configuration for a specific tenant."""
        try:
            result = await self.db.tenant_configs.delete_one(
                {"tenant_id": tenant_id, "config_key": config_key}
            )
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting config for tenant {tenant_id}, key {config_key}: {str(e)}")
            return False
    
    async def get_configs_by_prefix(
        self, 
        tenant_id: str, 
        prefix: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all configurations for a tenant that match a key prefix."""
        try:
            cursor = self.db.tenant_configs.find({
                "tenant_id": tenant_id,
                "config_key": {"$regex": f"^{prefix}"}
            }).limit(limit)
            
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error retrieving configs with prefix for tenant {tenant_id}: {str(e)}")
            return []
    
    async def get_all_tenant_configs(self, tenant_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all configurations for a specific tenant."""
        try:
            cursor = self.db.tenant_configs.find({"tenant_id": tenant_id}).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error retrieving all configs for tenant {tenant_id}: {str(e)}")
            return []
    
    # Schema management methods
    
    async def get_config_schema(self, key: str) -> Optional[Dict[str, Any]]:
        """Get configuration schema for a specific key."""
        try:
            return await self.db.config_schemas.find_one({"key": key})
        except Exception as e:
            logger.error(f"Error retrieving config schema for key {key}: {str(e)}")
            return None
    
    async def set_config_schema(
        self,
        key: str,
        schema: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        required: bool = False,
        default_value: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Set or update configuration schema."""
        try:
            # Check if schema exists
            existing = await self.get_config_schema(key)
            
            if metadata is None:
                metadata = {}
            
            if existing:
                # Update existing schema
                update_data = {
                    "schema": schema,
                    "required": required,
                }
                
                if metadata:
                    update_data["metadata"] = {**existing.get("metadata", {}), **metadata}
                    
                if default_value is not None:
                    update_data["default_value"] = default_value
                
                result = await self.db.config_schemas.update_one(
                    {"key": key},
                    {"$set": update_data}
                )
                
                if result.modified_count == 0:
                    logger.warning(f"Failed to update config schema for key {key}")
                    return None
                    
                return await self.get_config_schema(key)
            else:
                # Create new schema
                doc = {
                    "key": key,
                    "schema": schema,
                    "metadata": metadata,
                    "required": required,
                }
                
                if default_value is not None:
                    doc["default_value"] = default_value
                
                result = await self.db.config_schemas.insert_one(doc)
                
                if not result.inserted_id:
                    logger.warning(f"Failed to create config schema for key {key}")
                    return None
                    
                return await self.get_config_schema(key)
        except Exception as e:
            logger.error(f"Error setting config schema for key {key}: {str(e)}")
            return None
    
    async def delete_config_schema(self, key: str) -> bool:
        """Delete configuration schema."""
        try:
            result = await self.db.config_schemas.delete_one({"key": key})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting config schema for key {key}: {str(e)}")
            return False
    
    async def get_all_config_schemas(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all configuration schemas."""
        try:
            cursor = self.db.config_schemas.find().limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error retrieving all config schemas: {str(e)}")
            return []
    
    # User preference methods
    
    async def get_user_preference(self, user_id: str, feature_type: str) -> Optional[Dict[str, Any]]:
        """Get user preference for a specific feature type."""
        try:
            return await self.db.user_preferences.find_one({
                "user_id": user_id,
                "feature_type": feature_type
            })
        except Exception as e:
            logger.error(f"Error retrieving user preference for user {user_id}, feature {feature_type}: {str(e)}")
            return None
    
    async def set_user_preference(
        self,
        user_id: str,
        feature_type: str,
        preferences: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Set or update user preference."""
        try:
            # Check if preference exists
            existing = await self.get_user_preference(user_id, feature_type)
            
            now = datetime.utcnow()
            
            if existing:
                # Update existing preference
                result = await self.db.user_preferences.update_one(
                    {"user_id": user_id, "feature_type": feature_type},
                    {"$set": {"preferences": preferences, "updated_at": now}}
                )
                
                if result.modified_count == 0:
                    logger.warning(f"Failed to update preference for user {user_id}, feature {feature_type}")
                    return None
                    
                return await self.get_user_preference(user_id, feature_type)
            else:
                # Create new preference
                doc = {
                    "user_id": user_id,
                    "feature_type": feature_type,
                    "preferences": preferences,
                    "created_at": now,
                    "updated_at": now
                }
                
                result = await self.db.user_preferences.insert_one(doc)
                
                if not result.inserted_id:
                    logger.warning(f"Failed to create preference for user {user_id}, feature {feature_type}")
                    return None
                    
                return await self.get_user_preference(user_id, feature_type)
        except Exception as e:
            logger.error(f"Error setting user preference for user {user_id}, feature {feature_type}: {str(e)}")
            return None
    
    async def delete_user_preference(self, user_id: str, feature_type: str) -> bool:
        """Delete user preference."""
        try:
            result = await self.db.user_preferences.delete_one({
                "user_id": user_id,
                "feature_type": feature_type
            })
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting user preference for user {user_id}, feature {feature_type}: {str(e)}")
            return False
    
    async def get_all_user_preferences(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all preferences for a specific user."""
        try:
            cursor = self.db.user_preferences.find({"user_id": user_id}).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error retrieving all preferences for user {user_id}: {str(e)}")
            return []
    
    # Feature frequency group methods for batch processing
    
    async def get_feature_types(self) -> List[str]:
        """Get all available feature types."""
        try:
            pipeline = [
                {"$match": {"config_key": {"$regex": "^features/"}}},
                {"$project": {"feature_type": {"$arrayElemAt": [{"$split": ["$config_key", "/"]}, 1]}}},
                {"$group": {"_id": "$feature_type"}},
                {"$project": {"_id": 0, "feature_type": "$_id"}}
            ]
            
            cursor = self.db.tenant_configs.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            return [result["feature_type"] for result in results]
        except Exception as e:
            logger.error(f"Error retrieving feature types: {str(e)}")
            return []
    
    async def get_frequency_groups(self, feature_type: str) -> Dict[str, List[str]]:
        """Get frequency groups for a specific feature type."""
        try:
            cursor = self.db.feature_frequency_groups.find({"feature_type": feature_type})
            results = await cursor.to_list(length=None)
            
            # Organize by frequency
            frequency_groups = {}
            for result in results:
                frequency = result.get("frequency")
                if frequency not in frequency_groups:
                    frequency_groups[frequency] = []
                
                frequency_groups[frequency].append(result.get("time_key"))
            
            return frequency_groups
        except Exception as e:
            logger.error(f"Error retrieving frequency groups for feature {feature_type}: {str(e)}")
            return {}
    
    async def get_frequency_group_tenants(
        self,
        feature_type: str,
        frequency: str,
        time_key: str
    ) -> List[str]:
        """Get tenants in a specific frequency group."""
        try:
            result = await self.db.feature_frequency_groups.find_one({
                "feature_type": feature_type,
                "frequency": frequency,
                "time_key": time_key
            })
            
            if result:
                return result.get("tenant_ids", [])
            else:
                return []
        except Exception as e:
            logger.error(f"Error retrieving tenants for frequency group {feature_type}/{frequency}/{time_key}: {str(e)}")
            return []
    
    async def set_frequency_group(
        self,
        feature_type: str,
        frequency: str,
        time_key: str,
        tenant_ids: List[str]
    ) -> bool:
        """Set or update a frequency group."""
        try:
            # Check if group exists
            existing = await self.db.feature_frequency_groups.find_one({
                "feature_type": feature_type,
                "frequency": frequency,
                "time_key": time_key
            })
            
            if existing:
                # Update existing group
                result = await self.db.feature_frequency_groups.update_one(
                    {
                        "feature_type": feature_type,
                        "frequency": frequency,
                        "time_key": time_key
                    },
                    {"$set": {"tenant_ids": tenant_ids}}
                )
                
                return result.modified_count > 0
            else:
                # Create new group
                doc = {
                    "feature_type": feature_type,
                    "frequency": frequency,
                    "time_key": time_key,
                    "tenant_ids": tenant_ids
                }
                
                result = await self.db.feature_frequency_groups.insert_one(doc)
                
                return result.inserted_id is not None
        except Exception as e:
            logger.error(f"Error setting frequency group {feature_type}/{frequency}/{time_key}: {str(e)}")
            return False
    
    async def add_tenant_to_frequency_group(
        self,
        feature_type: str,
        frequency: str,
        time_key: str,
        tenant_id: str
    ) -> bool:
        """Add a tenant to a frequency group."""
        try:
            result = await self.db.feature_frequency_groups.update_one(
                {
                    "feature_type": feature_type,
                    "frequency": frequency,
                    "time_key": time_key
                },
                {"$addToSet": {"tenant_ids": tenant_id}},
                upsert=True
            )
            
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            logger.error(f"Error adding tenant {tenant_id} to frequency group {feature_type}/{frequency}/{time_key}: {str(e)}")
            return False
    
    async def remove_tenant_from_frequency_group(
        self,
        feature_type: str,
        frequency: str,
        time_key: str,
        tenant_id: str
    ) -> bool:
        """Remove a tenant from a frequency group."""
        try:
            result = await self.db.feature_frequency_groups.update_one(
                {
                    "feature_type": feature_type,
                    "frequency": frequency,
                    "time_key": time_key
                },
                {"$pull": {"tenant_ids": tenant_id}}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error removing tenant {tenant_id} from frequency group {feature_type}/{frequency}/{time_key}: {str(e)}")
            return False
    
    async def delete_frequency_group(
        self,
        feature_type: str,
        frequency: str,
        time_key: str
    ) -> bool:
        """Delete a frequency group."""
        try:
            result = await self.db.feature_frequency_groups.delete_one({
                "feature_type": feature_type,
                "frequency": frequency,
                "time_key": time_key
            })
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting frequency group {feature_type}/{frequency}/{time_key}: {str(e)}")
            return False 