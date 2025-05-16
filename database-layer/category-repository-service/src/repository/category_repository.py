"""
Category Repository Implementation for MongoDB.

This module provides the CategoryRepository class for managing categories, factors,
campaigns, batch as objects, and entity assignments in MongoDB.
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

from ..models.category import (
    Category, CategoryCreate, Factor, FactorCreate, 
    Campaign, CampaignCreate, BatchAsObject, BatchAsObjectCreate,
    EntityAssignment, EntityAssignmentCreate, Metrics
)

logger = logging.getLogger(__name__)


class CategoryRepository:
    """
    Repository for managing categories, factors, campaigns, batch as objects, and assignments.
    
    This class provides methods for CRUD operations and advanced queries on all category-related
    entities. It ensures proper data integrity and provides caching for frequently accessed data.
    """
    
    def __init__(self, 
                 mongodb_uri: str,
                 database_name: str = "category_repository",
                 categories_collection: str = "categories",
                 factors_collection: str = "factors",
                 campaigns_collection: str = "campaigns",
                 batch_as_objects_collection: str = "batch_as_objects",
                 entity_assignments_collection: str = "entity_assignments"):
        """
        Initialize the category repository.
        
        Args:
            mongodb_uri: MongoDB connection URI
            database_name: Database name
            categories_collection: Categories collection name
            factors_collection: Factors collection name
            campaigns_collection: Campaigns collection name
            batch_as_objects_collection: Batch as objects collection name
            entity_assignments_collection: Entity assignments collection name
        """
        self.mongodb_uri = mongodb_uri
        self.database_name = database_name
        self.categories_collection_name = categories_collection
        self.factors_collection_name = factors_collection
        self.campaigns_collection_name = campaigns_collection
        self.batch_as_objects_collection_name = batch_as_objects_collection
        self.entity_assignments_collection_name = entity_assignments_collection
        
        # Initialize client to None - will connect on first use
        self.client = None
        self.db = None
        self.categories_collection = None
        self.factors_collection = None
        self.campaigns_collection = None
        self.batch_as_objects_collection = None
        self.entity_assignments_collection = None
        
        # In-memory cache
        self.cache = {
            "categories": {},
            "factors": {},
            "campaigns": {},
            "batch_as_objects": {},
            "entity_assignments": {}
        }
        
        logger.info(f"Initialized CategoryRepository with database {database_name}")
        
    async def connect(self) -> bool:
        """
        Connect to the MongoDB database.
        
        Returns:
            True if connection successful, False otherwise
        """
        if self.client is not None:
            return True  # Already connected
            
        try:
            self.client = AsyncIOMotorClient(self.mongodb_uri)
            self.db = self.client[self.database_name]
            self.categories_collection = self.db[self.categories_collection_name]
            self.factors_collection = self.db[self.factors_collection_name]
            self.campaigns_collection = self.db[self.campaigns_collection_name]
            self.batch_as_objects_collection = self.db[self.batch_as_objects_collection_name]
            self.entity_assignments_collection = self.db[self.entity_assignments_collection_name]
            
            # Create indexes
            await self._create_indexes()
            
            # Test connection
            await self.db.command("ping")
            
            logger.info(f"Connected to MongoDB {self.database_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            return False
    
    async def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.categories_collection = None
            self.factors_collection = None
            self.campaigns_collection = None
            self.batch_as_objects_collection = None
            self.entity_assignments_collection = None
            logger.info("Closed MongoDB connection")
    
    async def ensure_connected(self):
        """Ensure the repository is connected to MongoDB."""
        if self.client is None:
            await self.connect()
            
    async def _create_indexes(self):
        """Create database indexes for optimized queries."""
        # Categories indexes
        await self.categories_collection.create_index("category_id", unique=True)
        await self.categories_collection.create_index("type")
        
        # Factors indexes
        await self.factors_collection.create_index("factor_id", unique=True)
        await self.factors_collection.create_index("category_id")
        
        # Campaigns indexes
        await self.campaigns_collection.create_index("campaign_id", unique=True)
        await self.campaigns_collection.create_index("category_id")
        
        # Batch as objects indexes
        await self.batch_as_objects_collection.create_index("bao_id", unique=True)
        await self.batch_as_objects_collection.create_index("category_id")
        
        # Entity assignments indexes
        await self.entity_assignments_collection.create_index([
            ("entity_type", 1), 
            ("entity_id", 1),
            ("category_type", 1),
            ("item_id", 1)
        ], unique=True)
        await self.entity_assignments_collection.create_index([
            ("entity_type", 1),
            ("entity_id", 1)
        ])
        await self.entity_assignments_collection.create_index([
            ("category_type", 1),
            ("item_id", 1)
        ])
        
    # ========================
    # Category CRUD Operations
    # ========================
    
    async def create_category(self, category: CategoryCreate) -> Optional[str]:
        """
        Create a new category.
        
        Args:
            category: Category data
            
        Returns:
            Category ID if successful, None otherwise
        """
        await self.ensure_connected()
        
        try:
            # Generate ID if not provided
            category_id = category.category_id or f"cat_{uuid.uuid4().hex}"
            
            now = datetime.utcnow()
            
            # Create category document
            category_doc = {
                "category_id": category_id,
                "name": category.name,
                "description": category.description,
                "type": category.type,
                "metadata": category.metadata,
                "created_at": now,
                "updated_at": now
            }
            
            # Insert into database
            await self.categories_collection.insert_one(category_doc)
            
            # Update cache
            self.cache["categories"][category_id] = category_doc
            
            logger.info(f"Created category with ID {category_id}")
            return category_id
            
        except Exception as e:
            logger.error(f"Error creating category: {str(e)}")
            return None
    
    async def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a category by ID.
        
        Args:
            category_id: Category ID
            
        Returns:
            Category document if found, None otherwise
        """
        # Check cache first
        if category_id in self.cache["categories"]:
            return self.cache["categories"][category_id]
            
        await self.ensure_connected()
        
        try:
            # Find category in database
            category = await self.categories_collection.find_one({"category_id": category_id})
            
            if category:
                # Remove MongoDB ID
                if "_id" in category:
                    del category["_id"]
                    
                # Update cache
                self.cache["categories"][category_id] = category
                
                return category
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving category {category_id}: {str(e)}")
            return None
    
    async def update_category(self, category_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update a category.
        
        Args:
            category_id: Category ID
            update_data: Data to update
            
        Returns:
            True if successful, False otherwise
        """
        await self.ensure_connected()
        
        try:
            # Add updated_at timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            # Update in database
            result = await self.categories_collection.update_one(
                {"category_id": category_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                logger.warning(f"Category {category_id} not found for update")
                return False
                
            # Update cache if exists
            if category_id in self.cache["categories"]:
                self.cache["categories"][category_id].update(update_data)
                
            logger.info(f"Updated category {category_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating category {category_id}: {str(e)}")
            return False
    
    async def delete_category(self, category_id: str, cascade: bool = False) -> bool:
        """
        Delete a category.
        
        Args:
            category_id: Category ID
            cascade: If True, also delete all associated factors, campaigns, batch as objects
            
        Returns:
            True if successful, False otherwise
        """
        await self.ensure_connected()
        
        try:
            # Delete from database
            result = await self.categories_collection.delete_one({"category_id": category_id})
            
            if result.deleted_count == 0:
                logger.warning(f"Category {category_id} not found for deletion")
                return False
                
            # Remove from cache
            if category_id in self.cache["categories"]:
                del self.cache["categories"][category_id]
                
            # Cascade delete if requested
            if cascade:
                # Delete all factors in this category
                await self.factors_collection.delete_many({"category_id": category_id})
                
                # Delete all campaigns in this category
                await self.campaigns_collection.delete_many({"category_id": category_id})
                
                # Delete all batch as objects in this category
                await self.batch_as_objects_collection.delete_many({"category_id": category_id})
                
                # Clear related cache entries
                for factor_id, factor in list(self.cache["factors"].items()):
                    if factor.get("category_id") == category_id:
                        del self.cache["factors"][factor_id]
                        
                for campaign_id, campaign in list(self.cache["campaigns"].items()):
                    if campaign.get("category_id") == category_id:
                        del self.cache["campaigns"][campaign_id]
                        
                for bao_id, bao in list(self.cache["batch_as_objects"].items()):
                    if bao.get("category_id") == category_id:
                        del self.cache["batch_as_objects"][bao_id]
                
                logger.info(f"Cascade deleted all items in category {category_id}")
            
            logger.info(f"Deleted category {category_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting category {category_id}: {str(e)}")
            return False
    
    async def get_categories_by_type(self, category_type: str, 
                                    skip: int = 0, 
                                    limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get categories by type.
        
        Args:
            category_type: Category type
            skip: Number of categories to skip
            limit: Maximum number of categories to return
            
        Returns:
            List of category documents
        """
        await self.ensure_connected()
        
        try:
            # Find categories in database
            cursor = self.categories_collection.find(
                {"type": category_type}
            ).skip(skip).limit(limit)
            
            categories = []
            async for category in cursor:
                # Remove MongoDB ID
                if "_id" in category:
                    del category["_id"]
                    
                categories.append(category)
                
                # Update cache
                self.cache["categories"][category["category_id"]] = category
                
            return categories
            
        except Exception as e:
            logger.error(f"Error retrieving categories by type {category_type}: {str(e)}")
            return []

    # ========================
    # Factor CRUD Operations
    # ========================

    async def create_factor(self, factor: FactorCreate) -> Optional[str]:
        """
        Create a new factor.
        
        Args:
            factor: Factor data
            
        Returns:
            Factor ID if successful, None otherwise
        """
        await self.ensure_connected()
        
        try:
            # Generate ID if not provided
            factor_id = factor.factor_id or f"fac_{uuid.uuid4().hex}"
            
            now = datetime.utcnow()
            
            # Create factor document
            factor_doc = {
                "factor_id": factor_id,
                "name": factor.name,
                "category_id": factor.category_id,
                "definition": factor.definition,
                "purpose": factor.purpose,
                "metadata": factor.metadata,
                "metrics": factor.metrics.dict() if factor.metrics else {},
                "created_at": now,
                "updated_at": now
            }
            
            # Insert into database
            await self.factors_collection.insert_one(factor_doc)
            
            # Update cache
            self.cache["factors"][factor_id] = factor_doc
            
            logger.info(f"Created factor with ID {factor_id}")
            return factor_id
            
        except Exception as e:
            logger.error(f"Error creating factor: {str(e)}")
            return None

    async def get_factor(self, factor_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a factor by ID.
        
        Args:
            factor_id: Factor ID
            
        Returns:
            Factor document if found, None otherwise
        """
        # Check cache first
        if factor_id in self.cache["factors"]:
            return self.cache["factors"][factor_id]
            
        await self.ensure_connected()
        
        try:
            # Find factor in database
            factor = await self.factors_collection.find_one({"factor_id": factor_id})
            
            if factor:
                # Remove MongoDB ID
                if "_id" in factor:
                    del factor["_id"]
                    
                # Update cache
                self.cache["factors"][factor_id] = factor
                
                return factor
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving factor {factor_id}: {str(e)}")
            return None

    async def update_factor(self, factor_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update a factor.
        
        Args:
            factor_id: Factor ID
            update_data: Data to update
            
        Returns:
            True if successful, False otherwise
        """
        await self.ensure_connected()
        
        try:
            # Add updated_at timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            # Update in database
            result = await self.factors_collection.update_one(
                {"factor_id": factor_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                logger.warning(f"Factor {factor_id} not found for update")
                return False
                
            # Update cache if exists
            if factor_id in self.cache["factors"]:
                self.cache["factors"][factor_id].update(update_data)
                
            logger.info(f"Updated factor {factor_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating factor {factor_id}: {str(e)}")
            return False

    async def delete_factor(self, factor_id: str) -> bool:
        """
        Delete a factor.
        
        Args:
            factor_id: Factor ID
            
        Returns:
            True if successful, False otherwise
        """
        await self.ensure_connected()
        
        try:
            # Delete from database
            result = await self.factors_collection.delete_one({"factor_id": factor_id})
            
            if result.deleted_count == 0:
                logger.warning(f"Factor {factor_id} not found for deletion")
                return False
                
            # Remove from cache
            if factor_id in self.cache["factors"]:
                del self.cache["factors"][factor_id]
                
            # Also delete any entity assignments
            await self.entity_assignments_collection.delete_many({
                "category_type": "factor",
                "item_id": factor_id
            })
            
            # Clean up related cache entries
            for key in list(self.cache["entity_assignments"].keys()):
                if ":" in key:
                    _, item_type, item_id = key.split(":")
                    if item_type == "factor" and item_id == factor_id:
                        del self.cache["entity_assignments"][key]
            
            logger.info(f"Deleted factor {factor_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting factor {factor_id}: {str(e)}")
            return False

    async def get_factors_by_category(self, category_id: str, 
                                     skip: int = 0, 
                                     limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get factors by category.
        
        Args:
            category_id: Category ID
            skip: Number of factors to skip
            limit: Maximum number of factors to return
            
        Returns:
            List of factor documents
        """
        await self.ensure_connected()
        
        try:
            # Find factors in database
            cursor = self.factors_collection.find(
                {"category_id": category_id}
            ).skip(skip).limit(limit)
            
            factors = []
            async for factor in cursor:
                # Remove MongoDB ID
                if "_id" in factor:
                    del factor["_id"]
                    
                factors.append(factor)
                
                # Update cache
                self.cache["factors"][factor["factor_id"]] = factor
                
            return factors
            
        except Exception as e:
            logger.error(f"Error retrieving factors by category {category_id}: {str(e)}")
            return []

    async def update_factor_metrics(self, factor_id: str, metrics: Metrics) -> bool:
        """
        Update factor metrics.
        
        Args:
            factor_id: Factor ID
            metrics: Metrics data
            
        Returns:
            True if successful, False otherwise
        """
        await self.ensure_connected()
        
        try:
            now = datetime.utcnow()
            
            # Convert metrics to dict
            metrics_dict = metrics.dict()
            
            # Update in database
            result = await self.factors_collection.update_one(
                {"factor_id": factor_id},
                {
                    "$set": {
                        "metrics": metrics_dict,
                        "updated_at": now
                    }
                }
            )
            
            if result.matched_count == 0:
                logger.warning(f"Factor {factor_id} not found for metrics update")
                return False
                
            # Update cache if exists
            if factor_id in self.cache["factors"]:
                self.cache["factors"][factor_id]["metrics"] = metrics_dict
                self.cache["factors"][factor_id]["updated_at"] = now
                
            logger.info(f"Updated metrics for factor {factor_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating metrics for factor {factor_id}: {str(e)}")
            return False

    # ========================
    # Campaign CRUD Operations
    # ========================
    
    async def create_campaign(self, campaign: CampaignCreate) -> Optional[str]:
        """
        Create a new campaign.
        
        Args:
            campaign: Campaign data
            
        Returns:
            Campaign ID if successful, None otherwise
        """
        await self.ensure_connected()
        
        try:
            # Generate ID if not provided
            campaign_id = campaign.campaign_id or f"camp_{uuid.uuid4().hex}"
            
            now = datetime.utcnow()
            
            # Create campaign document
            campaign_doc = {
                "campaign_id": campaign_id,
                "name": campaign.name,
                "category_id": campaign.category_id,
                "structure": campaign.structure,
                "purpose": campaign.purpose,
                "metadata": campaign.metadata,
                "metrics": campaign.metrics.dict() if campaign.metrics else {},
                "created_at": now,
                "updated_at": now
            }
            
            # Insert into database
            await self.campaigns_collection.insert_one(campaign_doc)
            
            # Update cache
            self.cache["campaigns"][campaign_id] = campaign_doc
            
            logger.info(f"Created campaign with ID {campaign_id}")
            return campaign_id
            
        except Exception as e:
            logger.error(f"Error creating campaign: {str(e)}")
            return None
    
    async def get_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a campaign by ID.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Campaign document if found, None otherwise
        """
        # Check cache first
        if campaign_id in self.cache["campaigns"]:
            return self.cache["campaigns"][campaign_id]
            
        await self.ensure_connected()
        
        try:
            # Find campaign in database
            campaign = await self.campaigns_collection.find_one({"campaign_id": campaign_id})
            
            if campaign:
                # Remove MongoDB ID
                if "_id" in campaign:
                    del campaign["_id"]
                    
                # Update cache
                self.cache["campaigns"][campaign_id] = campaign
                
                return campaign
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving campaign {campaign_id}: {str(e)}")
            return None
    
    async def update_campaign(self, campaign_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update a campaign.
        
        Args:
            campaign_id: Campaign ID
            update_data: Data to update
            
        Returns:
            True if successful, False otherwise
        """
        await self.ensure_connected()
        
        try:
            # Add updated_at timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            # Update in database
            result = await self.campaigns_collection.update_one(
                {"campaign_id": campaign_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                logger.warning(f"Campaign {campaign_id} not found for update")
                return False
                
            # Update cache if exists
            if campaign_id in self.cache["campaigns"]:
                self.cache["campaigns"][campaign_id].update(update_data)
                
            logger.info(f"Updated campaign {campaign_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating campaign {campaign_id}: {str(e)}")
            return False
    
    async def delete_campaign(self, campaign_id: str) -> bool:
        """
        Delete a campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            True if successful, False otherwise
        """
        await self.ensure_connected()
        
        try:
            # Delete from database
            result = await self.campaigns_collection.delete_one({"campaign_id": campaign_id})
            
            if result.deleted_count == 0:
                logger.warning(f"Campaign {campaign_id} not found for deletion")
                return False
                
            # Remove from cache
            if campaign_id in self.cache["campaigns"]:
                del self.cache["campaigns"][campaign_id]
                
            # Also delete any entity assignments
            await self.entity_assignments_collection.delete_many({
                "category_type": "campaign",
                "item_id": campaign_id
            })
            
            # Clean up related cache entries
            for key in list(self.cache["entity_assignments"].keys()):
                if ":" in key:
                    _, item_type, item_id = key.split(":")
                    if item_type == "campaign" and item_id == campaign_id:
                        del self.cache["entity_assignments"][key]
            
            logger.info(f"Deleted campaign {campaign_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting campaign {campaign_id}: {str(e)}")
            return False
    
    async def get_campaigns_by_category(self, category_id: str, 
                                       skip: int = 0, 
                                       limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get campaigns by category.
        
        Args:
            category_id: Category ID
            skip: Number of campaigns to skip
            limit: Maximum number of campaigns to return
            
        Returns:
            List of campaign documents
        """
        await self.ensure_connected()
        
        try:
            # Find campaigns in database
            cursor = self.campaigns_collection.find(
                {"category_id": category_id}
            ).skip(skip).limit(limit)
            
            campaigns = []
            async for campaign in cursor:
                # Remove MongoDB ID
                if "_id" in campaign:
                    del campaign["_id"]
                    
                campaigns.append(campaign)
                
                # Update cache
                self.cache["campaigns"][campaign["campaign_id"]] = campaign
                
            return campaigns
            
        except Exception as e:
            logger.error(f"Error retrieving campaigns by category {category_id}: {str(e)}")
            return []
    
    async def update_campaign_metrics(self, campaign_id: str, metrics: Metrics) -> bool:
        """
        Update campaign metrics.
        
        Args:
            campaign_id: Campaign ID
            metrics: Metrics data
            
        Returns:
            True if successful, False otherwise
        """
        await self.ensure_connected()
        
        try:
            now = datetime.utcnow()
            
            # Convert metrics to dict
            metrics_dict = metrics.dict()
            
            # Update in database
            result = await self.campaigns_collection.update_one(
                {"campaign_id": campaign_id},
                {
                    "$set": {
                        "metrics": metrics_dict,
                        "updated_at": now
                    }
                }
            )
            
            if result.matched_count == 0:
                logger.warning(f"Campaign {campaign_id} not found for metrics update")
                return False
                
            # Update cache if exists
            if campaign_id in self.cache["campaigns"]:
                self.cache["campaigns"][campaign_id]["metrics"] = metrics_dict
                self.cache["campaigns"][campaign_id]["updated_at"] = now
                
            logger.info(f"Updated metrics for campaign {campaign_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating metrics for campaign {campaign_id}: {str(e)}")
            return False

    # ========================
    # Entity Assignment Operations
    # ========================
    
    async def create_entity_assignment(self, assignment: EntityAssignmentCreate) -> Optional[str]:
        """
        Create a new entity assignment.
        
        Args:
            assignment: Entity assignment data
            
        Returns:
            Assignment ID if successful, None otherwise
        """
        await self.ensure_connected()
        
        try:
            # Generate assignment ID
            assignment_id = f"assign_{uuid.uuid4().hex}"
            
            now = datetime.utcnow()
            
            # Create assignment document
            assignment_doc = {
                "assignment_id": assignment_id,
                "entity_type": assignment.entity_type,
                "entity_id": assignment.entity_id,
                "category_type": assignment.category_type,
                "item_id": assignment.item_id,
                "created_at": now
            }
            
            # Insert into database (use update_one with upsert to avoid duplicate assignments)
            await self.entity_assignments_collection.update_one(
                {
                    "entity_type": assignment.entity_type,
                    "entity_id": assignment.entity_id,
                    "category_type": assignment.category_type,
                    "item_id": assignment.item_id
                },
                {"$set": assignment_doc},
                upsert=True
            )
            
            # Update cache - Use a composite key for efficient lookups
            cache_key = f"{assignment.entity_type}:{assignment.entity_id}:{assignment.category_type}:{assignment.item_id}"
            self.cache["entity_assignments"][cache_key] = assignment_doc
            
            logger.info(f"Created entity assignment with ID {assignment_id}")
            return assignment_id
            
        except Exception as e:
            logger.error(f"Error creating entity assignment: {str(e)}")
            return None
    
    async def delete_entity_assignment(self, entity_type: str, entity_id: str, 
                                      category_type: str, item_id: str) -> bool:
        """
        Delete an entity assignment.
        
        Args:
            entity_type: Entity type
            entity_id: Entity ID
            category_type: Category type
            item_id: Item ID
            
        Returns:
            True if successful, False otherwise
        """
        await self.ensure_connected()
        
        try:
            # Delete from database
            result = await self.entity_assignments_collection.delete_one({
                "entity_type": entity_type,
                "entity_id": entity_id,
                "category_type": category_type,
                "item_id": item_id
            })
            
            if result.deleted_count == 0:
                logger.warning(f"Entity assignment not found for deletion")
                return False
                
            # Remove from cache
            cache_key = f"{entity_type}:{entity_id}:{category_type}:{item_id}"
            if cache_key in self.cache["entity_assignments"]:
                del self.cache["entity_assignments"][cache_key]
                
            logger.info(f"Deleted entity assignment for {entity_type}:{entity_id} -> {category_type}:{item_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting entity assignment: {str(e)}")
            return False
    
    async def get_entities_by_item(self, category_type: str, item_id: str, 
                                  entity_type: Optional[str] = None,
                                  skip: int = 0, 
                                  limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get entities assigned to a specific item.
        
        Args:
            category_type: Category type (factor, campaign)
            item_id: Item ID
            entity_type: Optional entity type filter
            skip: Number of assignments to skip
            limit: Maximum number of assignments to return
            
        Returns:
            List of entity assignments
        """
        await self.ensure_connected()
        
        try:
            # Build query
            query = {
                "category_type": category_type,
                "item_id": item_id
            }
            
            if entity_type:
                query["entity_type"] = entity_type
                
            # Find assignments in database
            cursor = self.entity_assignments_collection.find(query).skip(skip).limit(limit)
            
            assignments = []
            async for assignment in cursor:
                # Remove MongoDB ID
                if "_id" in assignment:
                    del assignment["_id"]
                    
                assignments.append(assignment)
                
                # Update cache
                cache_key = f"{assignment['entity_type']}:{assignment['entity_id']}:{assignment['category_type']}:{assignment['item_id']}"
                self.cache["entity_assignments"][cache_key] = assignment
                
            return assignments
            
        except Exception as e:
            logger.error(f"Error retrieving entities for {category_type}:{item_id}: {str(e)}")
            return []
    
    async def get_items_by_entity(self, entity_type: str, entity_id: str, 
                                 category_type: Optional[str] = None,
                                 skip: int = 0, 
                                 limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get items assigned to a specific entity.
        
        Args:
            entity_type: Entity type
            entity_id: Entity ID
            category_type: Optional category type filter
            skip: Number of assignments to skip
            limit: Maximum number of assignments to return
            
        Returns:
            List of item assignments
        """
        await self.ensure_connected()
        
        try:
            # Build query
            query = {
                "entity_type": entity_type,
                "entity_id": entity_id
            }
            
            if category_type:
                query["category_type"] = category_type
                
            # Find assignments in database
            cursor = self.entity_assignments_collection.find(query).skip(skip).limit(limit)
            
            assignments = []
            async for assignment in cursor:
                # Remove MongoDB ID
                if "_id" in assignment:
                    del assignment["_id"]
                    
                assignments.append(assignment)
                
                # Update cache
                cache_key = f"{assignment['entity_type']}:{assignment['entity_id']}:{assignment['category_type']}:{assignment['item_id']}"
                self.cache["entity_assignments"][cache_key] = assignment
                
            return assignments
            
        except Exception as e:
            logger.error(f"Error retrieving items for {entity_type}:{entity_id}: {str(e)}")
            return []
            
    async def check_entity_assignment(self, entity_type: str, entity_id: str, 
                                     category_type: str, item_id: str) -> bool:
        """
        Check if an entity is assigned to an item.
        
        Args:
            entity_type: Entity type
            entity_id: Entity ID
            category_type: Category type
            item_id: Item ID
            
        Returns:
            True if assigned, False otherwise
        """
        await self.ensure_connected()
        
        try:
            # Check cache first
            cache_key = f"{entity_type}:{entity_id}:{category_type}:{item_id}"
            if cache_key in self.cache["entity_assignments"]:
                return True
                
            # Check database
            assignment = await self.entity_assignments_collection.find_one({
                "entity_type": entity_type,
                "entity_id": entity_id,
                "category_type": category_type,
                "item_id": item_id
            })
            
            if assignment:
                # Update cache
                if "_id" in assignment:
                    del assignment["_id"]
                self.cache["entity_assignments"][cache_key] = assignment
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking entity assignment: {str(e)}")
            return False
            
    async def get_item_details_by_entity(self, entity_type: str, entity_id: str, 
                                        category_type: str) -> List[Dict[str, Any]]:
        """
        Get detailed item information for items assigned to an entity.
        
        Args:
            entity_type: Entity type
            entity_id: Entity ID
            category_type: Category type
            
        Returns:
            List of item details
        """
        await self.ensure_connected()
        
        try:
            # Get assignments
            assignments = await self.get_items_by_entity(entity_type, entity_id, category_type)
            
            if not assignments:
                return []
                
            # Get item details based on category type
            items = []
            
            for assignment in assignments:
                item_id = assignment["item_id"]
                item = None
                
                if category_type == "factor":
                    item = await self.get_factor(item_id)
                elif category_type == "campaign":
                    item = await self.get_campaign(item_id)
                elif category_type == "batch_as_object":
                    item = await self.get_batch_as_object(item_id)
                    
                if item:
                    items.append(item)
                    
            return items
            
        except Exception as e:
            logger.error(f"Error retrieving item details for {entity_type}:{entity_id}: {str(e)}")
            return []

    # ========================
    # BatchAsObject CRUD Operations
    # ========================
    
    async def create_batch_as_object(self, batch_as_object: BatchAsObjectCreate) -> Optional[str]:
        """
        Create a new batch as object.
        
        Args:
            batch_as_object: Batch as object data
            
        Returns:
            Batch as object ID if successful, None otherwise
        """
        await self.ensure_connected()
        
        try:
            # Generate ID if not provided
            bao_id = batch_as_object.bao_id or f"bao_{uuid.uuid4().hex}"
            
            now = datetime.utcnow()
            
            # Create batch as object document
            bao_doc = {
                "bao_id": bao_id,
                "name": batch_as_object.name,
                "category_id": batch_as_object.category_id,
                "json_data": batch_as_object.json_data,
                "metadata": batch_as_object.metadata,
                "metrics": batch_as_object.metrics.dict() if batch_as_object.metrics else {},
                "created_at": now,
                "updated_at": now
            }
            
            # Insert into database
            await self.batch_as_objects_collection.insert_one(bao_doc)
            
            # Update cache
            self.cache["batch_as_objects"][bao_id] = bao_doc
            
            logger.info(f"Created batch as object with ID {bao_id}")
            return bao_id
            
        except Exception as e:
            logger.error(f"Error creating batch as object: {str(e)}")
            return None
    
    async def get_batch_as_object(self, bao_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a batch as object by ID.
        
        Args:
            bao_id: Batch as object ID
            
        Returns:
            Batch as object document if found, None otherwise
        """
        # Check cache first
        if bao_id in self.cache["batch_as_objects"]:
            return self.cache["batch_as_objects"][bao_id]
            
        await self.ensure_connected()
        
        try:
            # Find batch as object in database
            batch_as_object = await self.batch_as_objects_collection.find_one({"bao_id": bao_id})
            
            if batch_as_object:
                # Remove MongoDB ID
                if "_id" in batch_as_object:
                    del batch_as_object["_id"]
                    
                # Update cache
                self.cache["batch_as_objects"][bao_id] = batch_as_object
                
                return batch_as_object
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving batch as object {bao_id}: {str(e)}")
            return None
    
    async def update_batch_as_object(self, bao_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update a batch as object.
        
        Args:
            bao_id: Batch as object ID
            update_data: Data to update
            
        Returns:
            True if successful, False otherwise
        """
        await self.ensure_connected()
        
        try:
            # Add updated_at timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            # Update in database
            result = await self.batch_as_objects_collection.update_one(
                {"bao_id": bao_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                logger.warning(f"Batch as object {bao_id} not found for update")
                return False
                
            # Update cache if exists
            if bao_id in self.cache["batch_as_objects"]:
                self.cache["batch_as_objects"][bao_id].update(update_data)
                
            logger.info(f"Updated batch as object {bao_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating batch as object {bao_id}: {str(e)}")
            return False
    
    async def delete_batch_as_object(self, bao_id: str) -> bool:
        """
        Delete a batch as object.
        
        Args:
            bao_id: Batch as object ID
            
        Returns:
            True if successful, False otherwise
        """
        await self.ensure_connected()
        
        try:
            # Delete from database
            result = await self.batch_as_objects_collection.delete_one({"bao_id": bao_id})
            
            if result.deleted_count == 0:
                logger.warning(f"Batch as object {bao_id} not found for deletion")
                return False
                
            # Remove from cache
            if bao_id in self.cache["batch_as_objects"]:
                del self.cache["batch_as_objects"][bao_id]
                
            # Also delete any entity assignments
            await self.entity_assignments_collection.delete_many({
                "category_type": "batch_as_object",
                "item_id": bao_id
            })
            
            # Clean up related cache entries
            for key in list(self.cache["entity_assignments"].keys()):
                if ":" in key:
                    _, item_type, item_id = key.split(":")
                    if item_type == "batch_as_object" and item_id == bao_id:
                        del self.cache["entity_assignments"][key]
            
            logger.info(f"Deleted batch as object {bao_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting batch as object {bao_id}: {str(e)}")
            return False
    
    async def get_batch_as_objects_by_category(self, category_id: str, 
                                             skip: int = 0, 
                                             limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get batch as objects by category.
        
        Args:
            category_id: Category ID
            skip: Number of batch as objects to skip
            limit: Maximum number of batch as objects to return
            
        Returns:
            List of batch as object documents
        """
        await self.ensure_connected()
        
        try:
            # Find batch as objects in database
            cursor = self.batch_as_objects_collection.find(
                {"category_id": category_id}
            ).skip(skip).limit(limit)
            
            batch_as_objects = []
            async for batch_as_object in cursor:
                # Remove MongoDB ID
                if "_id" in batch_as_object:
                    del batch_as_object["_id"]
                    
                batch_as_objects.append(batch_as_object)
                
                # Update cache
                self.cache["batch_as_objects"][batch_as_object["bao_id"]] = batch_as_object
                
            return batch_as_objects
            
        except Exception as e:
            logger.error(f"Error retrieving batch as objects by category {category_id}: {str(e)}")
            return []
    
    async def update_batch_as_object_metrics(self, bao_id: str, metrics: Metrics) -> bool:
        """
        Update batch as object metrics.
        
        Args:
            bao_id: Batch as object ID
            metrics: Metrics data
            
        Returns:
            True if successful, False otherwise
        """
        await self.ensure_connected()
        
        try:
            now = datetime.utcnow()
            
            # Convert metrics to dict
            metrics_dict = metrics.dict()
            
            # Update in database
            result = await self.batch_as_objects_collection.update_one(
                {"bao_id": bao_id},
                {
                    "$set": {
                        "metrics": metrics_dict,
                        "updated_at": now
                    }
                }
            )
            
            if result.matched_count == 0:
                logger.warning(f"Batch as object {bao_id} not found for metrics update")
                return False
                
            # Update cache if exists
            if bao_id in self.cache["batch_as_objects"]:
                self.cache["batch_as_objects"][bao_id]["metrics"] = metrics_dict
                self.cache["batch_as_objects"][bao_id]["updated_at"] = now
                
            logger.info(f"Updated metrics for batch as object {bao_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating metrics for batch as object {bao_id}: {str(e)}")
            return False