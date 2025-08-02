"""
Category Repository interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class ICategoryRepository(ABC):
    """
    Interface for category repository operations.
    
    This interface defines the contract for interacting with category data,
    whether stored locally or in external systems.
    """
    
    @abstractmethod
    async def get_categories_by_type(self, category_type: str) -> List[Dict[str, Any]]:
        """
        Get all categories of a specific type.
        
        Args:
            category_type: Type of categories to retrieve
            
        Returns:
            List of category objects
        """
        pass
    
    @abstractmethod
    async def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific category by ID.
        
        Args:
            category_id: ID of the category to retrieve
            
        Returns:
            Category object if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_category_members(self, category_id: str) -> List[Dict[str, Any]]:
        """
        Get members of a specific category.
        
        Args:
            category_id: ID of the category
            
        Returns:
            List of member objects
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_batch_data(self, category: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get batch data for a category.
        
        Args:
            category: Category name or ID
            filters: Filter criteria
            
        Returns:
            Batch data object
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def get_preference_compatible_categories(self, feature_type: str) -> List[Dict[str, Any]]:
        """
        Get categories that are compatible with a specific preference feature type.
        
        Args:
            feature_type: Feature type identifier
            
        Returns:
            List of compatible categories
        """
        pass

    @abstractmethod
    async def get_batch_data_with_preferences(self, category: str, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get batch data for a category with user preferences applied.
        
        Args:
            category: Category name or ID
            user_preferences: User preferences dictionary
            
        Returns:
            Batch data object with preferences applied
        """
        pass 