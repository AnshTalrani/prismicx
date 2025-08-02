"""File-based implementation of the purpose repository that uses purpose_mapping.json."""
import os
import json
import logging
from typing import List, Optional, Dict, Any

from src.application.interfaces.repository.purpose_repository import IPurposeRepository
from src.domain.entities.purpose import Purpose

class FilePurposeRepository(IPurposeRepository):
    """
    File-based purpose repository that loads purposes directly from purpose_mapping.json.
    
    This implementation provides a consistent way to access purpose data while allowing
    manual updates to the purpose_mapping.json file.
    """
    
    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize FilePurposeRepository.
        
        Args:
            file_path: Path to purpose mapping JSON file (optional)
        """
        self.logger = logging.getLogger(__name__)
        self.file_path = file_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config",
            "purpose_mapping.json"
        )
        self.purposes: Dict[str, Purpose] = {}
        self._load_purposes()
        
    def _load_purposes(self) -> None:
        """Load purposes from purpose_mapping.json."""
        if not os.path.exists(self.file_path):
            self.logger.warning(f"Purpose mapping file not found: {self.file_path}")
            return
        
        try:
            with open(self.file_path, 'r') as f:
                purpose_data = json.load(f)
                
            # Handle both dictionary and array formats
            if isinstance(purpose_data, dict):
                # Dictionary format (original format)
                for purpose_id, mapping in purpose_data.items():
                    # Create Purpose object with data from mapping
                    purpose = Purpose(
                        id=mapping.get("id", purpose_id),
                        name=purpose_id,  # Use purpose_id as name if not provided
                        description=mapping.get("description", f"Purpose for {purpose_id}"),
                        keywords=mapping.get("keywords", []),
                        template_ids=[mapping.get("template_id")] if mapping.get("template_id") else [],
                        attributes=mapping,  # Store entire mapping as attributes
                        is_active=True
                    )
                    self.purposes[purpose_id] = purpose
            elif isinstance(purpose_data, list):
                # Array format (used in tests)
                for purpose_item in purpose_data:
                    purpose_id = purpose_item.get("id")
                    if purpose_id:
                        purpose = Purpose(
                            id=purpose_id,
                            name=purpose_item.get("name", purpose_id),
                            description=purpose_item.get("description", f"Purpose for {purpose_id}"),
                            keywords=purpose_item.get("keywords", []),
                            template_ids=purpose_item.get("template_ids", []),
                            attributes=purpose_item,  # Store entire item as attributes
                            is_active=purpose_item.get("is_active", True)
                        )
                        self.purposes[purpose_id] = purpose
                    else:
                        self.logger.warning(f"Skipping purpose without ID: {purpose_item}")
            else:
                self.logger.error(f"Invalid purpose data format in {self.file_path}")
                
            self.logger.info(f"Loaded {len(self.purposes)} purposes from {self.file_path}")
        except Exception as e:
            self.logger.error(f"Error loading purposes: {str(e)}")
    
    def _reload_purposes(self) -> None:
        """Reload purposes from file to get latest changes."""
        self.purposes.clear()
        self._load_purposes()
    
    async def get_purpose(self, purpose_id: str) -> Optional[Purpose]:
        """
        Get purpose by ID.
        
        Args:
            purpose_id: Purpose ID
            
        Returns:
            Purpose if found, None otherwise
        """
        # Reload to ensure we have the latest changes
        self._reload_purposes()
        return self.purposes.get(purpose_id)
    
    async def list_purposes(self) -> List[Purpose]:
        """
        List all purposes.
        
        Returns:
            List of all purposes
        """
        # Reload to ensure we have the latest changes
        self._reload_purposes()
        return list(self.purposes.values())
    
    async def add_purpose(self, purpose: Purpose) -> bool:
        """
        Add a new purpose.
        
        Note: This method is not implemented as purposes should be manually added to the JSON file.
        
        Args:
            purpose: Purpose to add
            
        Returns:
            Always False
        """
        self.logger.warning("add_purpose not implemented for FilePurposeRepository - update the JSON file manually")
        return False
    
    async def update_purpose(self, purpose: Purpose) -> bool:
        """
        Update an existing purpose.
        
        Note: This method is not implemented as purposes should be manually updated in the JSON file.
        
        Args:
            purpose: Purpose with updated data
            
        Returns:
            Always False
        """
        self.logger.warning("update_purpose not implemented for FilePurposeRepository - update the JSON file manually")
        return False
    
    async def delete_purpose(self, purpose_id: str) -> bool:
        """
        Delete a purpose.
        
        Note: This method is not implemented as purposes should be manually deleted from the JSON file.
        
        Args:
            purpose_id: ID of purpose to delete
            
        Returns:
            Always False
        """
        self.logger.warning("delete_purpose not implemented for FilePurposeRepository - update the JSON file manually")
        return False
    
    async def get_purpose_by_name(self, name: str) -> Optional[Purpose]:
        """
        Get purpose by name.
        
        Args:
            name: Purpose name
            
        Returns:
            Purpose if found, None otherwise
        """
        # Reload to ensure we have the latest changes
        self._reload_purposes()
        
        # Search by name in all purposes
        for purpose in self.purposes.values():
            if purpose.name == name:
                return purpose
                
        return None 