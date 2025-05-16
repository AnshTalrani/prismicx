"""
Client implementation for the Category Repository service.
"""
import os
import json
import logging
import aiohttp
from typing import Dict, List, Any, Optional

from src.application.interfaces.repository.category_repository import ICategoryRepository

logger = logging.getLogger(__name__)

class CategoryRepositoryClient(ICategoryRepository):
    """
    Client implementation for interacting with the Category Repository service.
    
    Features:
    - HTTP API client for the category microservice
    - Caching for frequently accessed categories
    - Fallback mechanisms for service unavailability
    - Error handling and retries
    - Support for preference-based batch processing
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the CategoryRepositoryClient.
        
        Args:
            base_url: Base URL for the category repository service
            api_key: API key for authentication
        """
        self.base_url = base_url or os.environ.get('CATEGORY_REPOSITORY_URL', 'http://category-repository-service:8080/api/v1')
        self.api_key = api_key or os.environ.get('CATEGORY_REPOSITORY_API_KEY', '')
        self.logger = logging.getLogger(__name__)
        self.category_cache = {}
        self.cache_ttl = 300  # Cache TTL in seconds
        
        self.logger.info(f"Initialized CategoryRepositoryClient with base URL: {self.base_url}")
    
    async def get_categories_by_type(self, category_type: str) -> List[Dict[str, Any]]:
        """
        Get all categories of a specific type.
        
        Args:
            category_type: Type of categories to retrieve
            
        Returns:
            List of category objects
        """
        cache_key = f"categories_by_type_{category_type}"
        if cache_key in self.category_cache:
            return self.category_cache[cache_key]
        
        try:
            url = f"{self.base_url}/categories"
            params = {"type": category_type}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=self._get_headers()) as response:
                    if response.status == 200:
                        categories = await response.json()
                        self.category_cache[cache_key] = categories
                        return categories
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Failed to get categories by type {category_type}: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            self.logger.error(f"Error fetching categories by type {category_type}: {str(e)}")
            return await self._fallback_get_categories_by_type(category_type)
    
    async def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific category by ID.
        
        Args:
            category_id: ID of the category to retrieve
            
        Returns:
            Category object if found, None otherwise
        """
        cache_key = f"category_{category_id}"
        if cache_key in self.category_cache:
            return self.category_cache[cache_key]
        
        try:
            url = f"{self.base_url}/categories/{category_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status == 200:
                        category = await response.json()
                        self.category_cache[cache_key] = category
                        return category
                    elif response.status == 404:
                        self.logger.warning(f"Category {category_id} not found")
                        return None
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Failed to get category {category_id}: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Error fetching category {category_id}: {str(e)}")
            return await self._fallback_get_category(category_id)
    
    async def get_category_members(self, category_id: str) -> List[Dict[str, Any]]:
        """
        Get members of a specific category.
        
        Args:
            category_id: ID of the category
            
        Returns:
            List of member objects
        """
        cache_key = f"category_members_{category_id}"
        if cache_key in self.category_cache:
            return self.category_cache[cache_key]
        
        try:
            url = f"{self.base_url}/assignments/category/factors/{category_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status == 200:
                        members = await response.json()
                        self.category_cache[cache_key] = members
                        return members
                    elif response.status == 404:
                        self.logger.warning(f"Category {category_id} not found or has no members")
                        return []
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Failed to get members for category {category_id}: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            self.logger.error(f"Error fetching members for category {category_id}: {str(e)}")
            return await self._fallback_get_category_members(category_id)
    
    async def get_items(self, category: str, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """
        Get items from a category based on filters.
        
        Args:
            category: Category name or ID
            filters: Filter criteria
            limit: Maximum number of items to return
            
        Returns:
            List of items matching the criteria
        """
        filter_str = json.dumps(filters, sort_keys=True)
        cache_key = f"items_{category}_{filter_str}_{limit}"
        if cache_key in self.category_cache:
            return self.category_cache[cache_key]
        
        try:
            url = f"{self.base_url}/factors"
            params = {"category_id": category, "limit": limit, **filters}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=self._get_headers()) as response:
                    if response.status == 200:
                        items = await response.json()
                        self.category_cache[cache_key] = items
                        return items
                    elif response.status == 404:
                        self.logger.warning(f"Category {category} not found or has no items")
                        return []
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Failed to get items for category {category}: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            self.logger.error(f"Error fetching items for category {category}: {str(e)}")
            return await self._fallback_get_items(category, filters, limit)
    
    async def get_batch_data(self, category: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get batch data for a category.
        
        Args:
            category: Category name or ID
            filters: Filter criteria
            
        Returns:
            Batch data object
        """
        filter_str = json.dumps(filters, sort_keys=True)
        cache_key = f"batch_data_{category}_{filter_str}"
        if cache_key in self.category_cache:
            return self.category_cache[cache_key]
        
        try:
            url = f"{self.base_url}/batch_as_objects"
            params = {"category_id": category}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=filters, params=params, headers=self._get_headers()) as response:
                    if response.status == 200:
                        batch_data = await response.json()
                        self.category_cache[cache_key] = batch_data
                        return batch_data
                    elif response.status == 404:
                        self.logger.warning(f"Category {category} not found")
                        return {}
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Failed to get batch data for category {category}: {response.status} - {error_text}")
                        return {}
                        
        except Exception as e:
            self.logger.error(f"Error fetching batch data for category {category}: {str(e)}")
            return await self._fallback_get_batch_data(category, filters)
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for API requests.
        
        Returns:
            Headers dictionary
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
            
        return headers
    
    def invalidate_cache(self, category_id: Optional[str] = None) -> None:
        """
        Invalidate cache entries.
        
        Args:
            category_id: Optional specific category ID to invalidate
        """
        if category_id:
            # Invalidate specific category entries
            keys_to_delete = [k for k in self.category_cache.keys() if category_id in k]
            for key in keys_to_delete:
                del self.category_cache[key]
            self.logger.debug(f"Invalidated cache for category {category_id}")
        else:
            # Invalidate all cache
            self.category_cache.clear()
            self.logger.debug("Invalidated entire category cache")
    
    # Fallback methods for when the service is unavailable
    
    async def _fallback_get_categories_by_type(self, category_type: str) -> List[Dict[str, Any]]:
        """
        Fallback method to get categories by type when service is unavailable.
        
        Args:
            category_type: Type of categories to retrieve
            
        Returns:
            List of fallback category objects (empty list if no fallback)
        """
        self.logger.info(f"Using fallback for get_categories_by_type({category_type})")
        return []
    
    async def _fallback_get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """
        Fallback method to get a category when service is unavailable.
        
        Args:
            category_id: ID of the category to retrieve
            
        Returns:
            Fallback category object (None if no fallback)
        """
        self.logger.info(f"Using fallback for get_category({category_id})")
        return None
    
    async def _fallback_get_category_members(self, category_id: str) -> List[Dict[str, Any]]:
        """
        Fallback method to get category members when service is unavailable.
        
        Args:
            category_id: ID of the category
            
        Returns:
            List of fallback member objects (empty list if no fallback)
        """
        self.logger.info(f"Using fallback for get_category_members({category_id})")
        return []
    
    async def _fallback_get_items(self, category: str, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """
        Fallback method to get items when service is unavailable.
        
        Args:
            category: Category name or ID
            filters: Filter criteria
            limit: Maximum number of items to return
            
        Returns:
            List of fallback items (empty list if no fallback)
        """
        self.logger.info(f"Using fallback for get_items({category})")
        return []
    
    async def _fallback_get_batch_data(self, category: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback method to get batch data when service is unavailable.
        
        Args:
            category: Category name or ID
            filters: Filter criteria
            
        Returns:
            Fallback batch data object (empty dict if no fallback)
        """
        self.logger.info(f"Using fallback for get_batch_data({category})")
        return {}

    async def get_items_with_preferences(self, category: str, user_preferences: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get items from a category based on user preferences.
        
        This method enhances the regular get_items method by applying user preferences
        to filter and customize the items retrieved.
        
        Args:
            category: Category name or ID
            user_preferences: User preferences dictionary
            limit: Maximum number of items to return
            
        Returns:
            List of items matching the preferences
        """
        try:
            # Extract preference-based filters
            filters = self._extract_filters_from_preferences(user_preferences)
            
            # Call standard get_items with preference-based filters
            items = await self.get_items(category, filters, limit)
            
            # Apply any additional preference-based processing
            if items and user_preferences:
                items = self._apply_preference_processing(items, user_preferences)
                
            return items
            
        except Exception as e:
            self.logger.error(f"Error fetching items with preferences for {category}: {str(e)}")
            return []
    
    def _extract_filters_from_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract filters from user preferences.
        
        Args:
            preferences: User preferences dictionary
            
        Returns:
            Filters dictionary
        """
        filters = {}
        
        # Only process valid preferences
        if not preferences or not isinstance(preferences, dict):
            return filters
            
        # Extract filters based on preference structure
        template_overrides = preferences.get("template_overrides", {})
        
        # Map preference keys to filter parameters
        preference_filter_mapping = {
            "categories": "category_ids",
            "tags": "tags",
            "focus_areas": "focus",
            "date_range": "time_period",
            "sources": "sources"
        }
        
        # Apply mappings
        for pref_key, filter_key in preference_filter_mapping.items():
            if pref_key in template_overrides and template_overrides[pref_key]:
                filters[filter_key] = template_overrides[pref_key]
                
        # Add any custom parameters directly
        if "custom_filters" in template_overrides:
            custom_filters = template_overrides.get("custom_filters", {})
            filters.update(custom_filters)
                
        return filters
    
    def _apply_preference_processing(self, items: List[Dict[str, Any]], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply preference-based processing to items.
        
        Args:
            items: List of items to process
            preferences: User preferences dictionary
            
        Returns:
            Processed items
        """
        # Return original items if no preferences
        if not preferences or not isinstance(preferences, dict):
            return items
            
        # Get template overrides
        template_overrides = preferences.get("template_overrides", {})
        
        # Apply sorting based on preferences
        sort_by = template_overrides.get("sort_by")
        if sort_by and items:
            try:
                # Sort items based on the specified field
                reverse = template_overrides.get("sort_order", "desc").lower() == "desc"
                items = sorted(items, key=lambda x: x.get(sort_by, 0), reverse=reverse)
            except Exception as e:
                self.logger.warning(f"Error sorting items by {sort_by}: {str(e)}")
        
        # Apply limit based on preferences
        limit = template_overrides.get("item_limit")
        if limit and isinstance(limit, int) and limit > 0:
            items = items[:limit]
            
        return items
     
    async def get_preference_compatible_categories(self, feature_type: str) -> List[Dict[str, Any]]:
        """
        Get categories that are compatible with a specific preference feature type.
        
        Args:
            feature_type: Feature type identifier
            
        Returns:
            List of compatible categories
        """
        cache_key = f"preference_compatible_categories_{feature_type}"
        if cache_key in self.category_cache:
            return self.category_cache[cache_key]
            
        try:
            url = f"{self.base_url}/preferences/compatible-categories"
            params = {"feature_type": feature_type}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=self._get_headers()) as response:
                    if response.status == 200:
                        categories = await response.json()
                        self.category_cache[cache_key] = categories
                        return categories
                    elif response.status == 404:
                        # Feature type not found or no compatible categories
                        self.logger.warning(f"No compatible categories found for feature type {feature_type}")
                        return []
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Failed to get compatible categories for {feature_type}: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            self.logger.error(f"Error fetching compatible categories for {feature_type}: {str(e)}")
            return []
    
    async def get_batch_data_with_preferences(self, category: str, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get batch data for a category with user preferences applied.
        
        Args:
            category: Category name or ID
            user_preferences: User preferences dictionary
            
        Returns:
            Batch data object with preferences applied
        """
        try:
            # Extract filters from preferences
            filters = self._extract_filters_from_preferences(user_preferences)
            
            # Get batch data with these filters
            batch_data = await self.get_batch_data(category, filters)
            
            # Add preference metadata
            if batch_data and "metadata" not in batch_data:
                batch_data["metadata"] = {}
                
            if batch_data and "metadata" in batch_data:
                batch_data["metadata"]["preferences_applied"] = True
                batch_data["metadata"]["preference_feature_type"] = user_preferences.get("feature_type", "unknown")
                
            return batch_data
            
        except Exception as e:
            self.logger.error(f"Error fetching batch data with preferences for {category}: {str(e)}")
            return {} 