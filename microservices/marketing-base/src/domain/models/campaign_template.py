"""
Campaign Template Model for managing communication templates.

This module defines the CampaignTemplate class which represents templates
used for communication across different channels (email, SMS, push notifications)
in marketing campaign workflows.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
import uuid


class TemplateType(str, Enum):
    """Enum representing the types of templates."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"
    CUSTOM = "custom"


class TemplateFormat(str, Enum):
    """Enum representing the formats of templates."""
    HTML = "html"
    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"
    HANDLEBARS = "handlebars"
    JINJA2 = "jinja2"


@dataclass
class VariableDefinition:
    """Defines a variable that can be used in a template."""
    name: str
    description: str
    required: bool = False
    default_value: Optional[str] = None
    example_value: Optional[str] = None
    validation_regex: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert variable definition to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "example_value": self.example_value,
            "validation_regex": self.validation_regex
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VariableDefinition':
        """Create a VariableDefinition instance from a dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            required=data.get("required", False),
            default_value=data.get("default_value"),
            example_value=data.get("example_value"),
            validation_regex=data.get("validation_regex")
        )


@dataclass
class TemplateContent:
    """Content for a specific template format."""
    format: TemplateFormat
    content: str
    content_url: Optional[str] = None
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template content to a dictionary."""
        return {
            "format": self.format.value,
            "content": self.content,
            "content_url": self.content_url,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateContent':
        """Create a TemplateContent instance from a dictionary."""
        return cls(
            format=TemplateFormat(data["format"]),
            content=data["content"],
            content_url=data.get("content_url"),
            version=data.get("version", 1)
        )


@dataclass
class CampaignTemplate:
    """
    Represents a template used for communication in marketing campaigns.
    
    Templates can be used across different communication channels and
    provide a way to structure messages with variable content.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    type: TemplateType
    
    # Template contents for different formats
    contents: List[TemplateContent] = field(default_factory=list)
    
    # Template variables
    variables: List[VariableDefinition] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    version: int = 1
    is_active: bool = True
    
    # Channel-specific properties
    subject: Optional[str] = None  # For email templates
    sender_name: Optional[str] = None  # For email/SMS templates
    reply_to: Optional[str] = None  # For email templates
    
    # Additional data
    tags: List[str] = field(default_factory=list)
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    
    def get_content(self, format_type: TemplateFormat) -> Optional[TemplateContent]:
        """
        Get template content for a specific format.
        
        Args:
            format_type: The format to retrieve
            
        Returns:
            The template content or None if not found
        """
        for content in self.contents:
            if content.format == format_type:
                return content
        return None
    
    def add_content(self, content: TemplateContent) -> None:
        """
        Add or update template content for a specific format.
        
        Args:
            content: The template content to add
        """
        # Remove any existing content with the same format
        self.contents = [c for c in self.contents if c.format != content.format]
        
        # Add the new content
        self.contents.append(content)
        self.updated_at = datetime.utcnow()
    
    def add_variable(self, variable: VariableDefinition) -> None:
        """
        Add or update a variable definition.
        
        Args:
            variable: The variable definition to add
        """
        # Remove any existing variable with the same name
        self.variables = [v for v in self.variables if v.name != variable.name]
        
        # Add the new variable
        self.variables.append(variable)
        self.updated_at = datetime.utcnow()
    
    def increment_version(self) -> None:
        """Increment the template version."""
        self.version += 1
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the campaign template to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "contents": [content.to_dict() for content in self.contents],
            "variables": [variable.to_dict() for variable in self.variables],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "version": self.version,
            "is_active": self.is_active,
            "subject": self.subject,
            "sender_name": self.sender_name,
            "reply_to": self.reply_to,
            "tags": self.tags,
            "custom_attributes": self.custom_attributes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CampaignTemplate':
        """Create a CampaignTemplate instance from a dictionary."""
        # Create the template without complex attributes
        template = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            description=data.get("description"),
            type=TemplateType(data["type"]),
            created_by=data.get("created_by"),
            updated_by=data.get("updated_by"),
            version=data.get("version", 1),
            is_active=data.get("is_active", True),
            subject=data.get("subject"),
            sender_name=data.get("sender_name"),
            reply_to=data.get("reply_to"),
            tags=data.get("tags", []),
            custom_attributes=data.get("custom_attributes", {})
        )
        
        # Convert timestamps
        if "created_at" in data:
            template.created_at = datetime.fromisoformat(data["created_at"])
        
        if "updated_at" in data:
            template.updated_at = datetime.fromisoformat(data["updated_at"])
        
        # Parse template contents
        if "contents" in data:
            template.contents = [
                TemplateContent.from_dict(content_data)
                for content_data in data["contents"]
            ]
        
        # Parse variable definitions
        if "variables" in data:
            template.variables = [
                VariableDefinition.from_dict(variable_data)
                for variable_data in data["variables"]
            ]
        
        return template 