"""Purpose entity representing the purpose of a request."""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class Purpose:
    """Purpose entity representing the purpose of a request."""
    
    id: str
    name: str
    description: str
    keywords: List[str] = field(default_factory=list)
    template_ids: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    priority: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert purpose to dictionary.
        
        Returns:
            Dictionary representation of purpose
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "keywords": self.keywords,
            "template_ids": self.template_ids,
            "attributes": self.attributes,
            "is_active": self.is_active,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Purpose':
        """
        Create purpose from dictionary.
        
        Args:
            data: Dictionary with purpose data
            
        Returns:
            Purpose instance
        """
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            keywords=data.get("keywords", []),
            template_ids=data.get("template_ids", []),
            attributes=data.get("attributes", {}),
            is_active=data.get("is_active", True),
            priority=data.get("priority", 0)
        )
    
    def add_keyword(self, keyword: str, importance: float = 1.0) -> None:
        """
        Add a keyword with optional importance.
        
        Args:
            keyword: Keyword to add
            importance: Importance value (default: 1.0)
        """
        if importance != 1.0:
            self.keywords.append(f"{keyword}:{importance}")
        else:
            self.keywords.append(keyword)
    
    def add_template_id(self, template_id: str) -> None:
        """
        Add a template ID to the purpose.
        
        Args:
            template_id: Template ID to add
        """
        if template_id not in self.template_ids:
            self.template_ids.append(template_id)
    
    def remove_template_id(self, template_id: str) -> bool:
        """
        Remove a template ID from the purpose.
        
        Args:
            template_id: Template ID to remove
            
        Returns:
            True if removed, False if not found
        """
        if template_id in self.template_ids:
            self.template_ids.remove(template_id)
            return True
        return False 