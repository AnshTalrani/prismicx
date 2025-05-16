from datetime import datetime
from typing import Dict, Any, List, Optional


class Factor:
    """
    Represents a factor in an extension.
    
    Attributes:
        factor_id (str): Unique identifier for the factor
        name (str): Name of the factor
        value (Any): Value of the factor
        weight (float): Weight of the factor in calculations
        description (str): Description of the factor
    """
    
    def __init__(self, factor_id: str, name: str, value: Any, weight: float = 1.0, description: str = ""):
        self.factor_id = factor_id
        self.name = name
        self.value = value
        self.weight = weight
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the factor to a dictionary."""
        return {
            "factor_id": self.factor_id,
            "name": self.name,
            "value": self.value,
            "weight": self.weight,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Factor':
        """Create a Factor instance from a dictionary."""
        return cls(
            factor_id=data["factor_id"],
            name=data["name"],
            value=data["value"],
            weight=data.get("weight", 1.0),
            description=data.get("description", "")
        )


class Practicality:
    """
    Represents the practicality metrics of an extension.
    
    Attributes:
        practicality_id (str): Unique identifier for the practicality
        score (float): Overall practicality score
        factors (List[Factor]): List of factors influencing practicality
        description (str): Description of the practicality
    """
    
    def __init__(self, practicality_id: str, score: float = 0.0, description: str = ""):
        self.practicality_id = practicality_id
        self.score = score
        self.factors: List[Factor] = []
        self.description = description
    
    def add_factor(self, factor: Factor) -> None:
        """Add a factor to the practicality."""
        self.factors.append(factor)
        self._recalculate_score()
    
    def remove_factor(self, factor_id: str) -> None:
        """Remove a factor by its ID."""
        self.factors = [f for f in self.factors if f.factor_id != factor_id]
        self._recalculate_score()
    
    def _recalculate_score(self) -> None:
        """Recalculate the practicality score based on factors."""
        if not self.factors:
            self.score = 0.0
            return
        
        weighted_sum = sum(f.value * f.weight for f in self.factors if isinstance(f.value, (int, float)))
        total_weight = sum(f.weight for f in self.factors if isinstance(f.value, (int, float)))
        
        if total_weight > 0:
            self.score = weighted_sum / total_weight
        else:
            self.score = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the practicality to a dictionary."""
        return {
            "practicality_id": self.practicality_id,
            "score": self.score,
            "factors": [f.to_dict() for f in self.factors],
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Practicality':
        """Create a Practicality instance from a dictionary."""
        practicality = cls(
            practicality_id=data["practicality_id"],
            score=data.get("score", 0.0),
            description=data.get("description", "")
        )
        if "factors" in data:
            practicality.factors = [Factor.from_dict(f) for f in data["factors"]]
        return practicality


class UserExtension:
    """
    Extension model for tenant-specific user data.
    
    Attributes:
        extension_id (str): Unique identifier for the extension
        user_id (str): Identifier for the user
        tenant_id (str): Identifier for the tenant
        extension_type (str): Type of extension (e.g., social_media, etsy)
        metrics (Dict[str, Any]): Metrics associated with the extension
        practicality (Practicality): Practicality metrics
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
    """
    
    def __init__(self, extension_id: str, user_id: str, tenant_id: str, extension_type: str):
        self.extension_id = extension_id
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.extension_type = extension_type
        self.metrics: Dict[str, Any] = {}
        self.practicality: Optional[Practicality] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def set_practicality(self, practicality: Practicality) -> None:
        """Set the practicality of the extension."""
        self.practicality = practicality
        self.updated_at = datetime.now()
    
    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update the metrics of the extension."""
        self.metrics.update(metrics)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the extension to a dictionary."""
        result = {
            "extension_id": self.extension_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "extension_type": self.extension_type,
            "metrics": self.metrics,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
        
        if self.practicality:
            result["practicality"] = self.practicality.to_dict()
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserExtension':
        """Create a UserExtension instance from a dictionary."""
        extension = cls(
            extension_id=data["extension_id"],
            user_id=data["user_id"],
            tenant_id=data["tenant_id"],
            extension_type=data["extension_type"]
        )
        
        if "metrics" in data:
            extension.metrics = data["metrics"]
        
        if "practicality" in data:
            extension.practicality = Practicality.from_dict(data["practicality"])
        
        if "created_at" in data and isinstance(data["created_at"], str):
            extension.created_at = datetime.fromisoformat(data["created_at"])
        
        if "updated_at" in data and isinstance(data["updated_at"], str):
            extension.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return extension 