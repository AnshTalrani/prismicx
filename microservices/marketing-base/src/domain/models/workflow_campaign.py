"""
Workflow Campaign Model for orchestrating multi-stage marketing campaigns.

This module defines the WorkflowCampaign class which represents a complete
multi-stage marketing campaign with workflow rules, analytics tracking,
and execution logic.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
import uuid

from .campaign_stage import CampaignStage


class WorkflowType(str, Enum):
    """Enum representing different types of campaign workflows."""
    SEQUENTIAL = "sequential"  # Stages executed in sequence
    PARALLEL = "parallel"  # Stages executed in parallel
    CONDITIONAL = "conditional"  # Stages executed based on conditions
    CUSTOM = "custom"  # Custom workflow logic


class AnalyticsConfig:
    """Configuration for campaign analytics tracking."""
    track_opens: bool = True
    track_clicks: bool = True
    track_conversions: bool = False
    conversion_event: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    custom_tracking_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analytics configuration to a dictionary."""
        return {
            "track_opens": self.track_opens,
            "track_clicks": self.track_clicks,
            "track_conversions": self.track_conversions,
            "conversion_event": self.conversion_event,
            "utm_source": self.utm_source,
            "utm_medium": self.utm_medium,
            "utm_campaign": self.utm_campaign,
            "custom_tracking_params": self.custom_tracking_params
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalyticsConfig':
        """Create an AnalyticsConfig instance from a dictionary."""
        config = cls()
        config.track_opens = data.get("track_opens", True)
        config.track_clicks = data.get("track_clicks", True)
        config.track_conversions = data.get("track_conversions", False)
        config.conversion_event = data.get("conversion_event")
        config.utm_source = data.get("utm_source")
        config.utm_medium = data.get("utm_medium")
        config.utm_campaign = data.get("utm_campaign")
        config.custom_tracking_params = data.get("custom_tracking_params", {})
        return config


@dataclass
class SegmentConfig:
    """Configuration for recipient segmentation."""
    name: str
    description: Optional[str] = None
    filter_criteria: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert segment configuration to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "filter_criteria": self.filter_criteria
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SegmentConfig':
        """Create a SegmentConfig instance from a dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description"),
            filter_criteria=data.get("filter_criteria", {})
        )


@dataclass
class WorkflowCampaign:
    """
    Represents a multi-stage marketing campaign with workflow rules.
    
    This class connects campaign information with stages and execution logic,
    enabling complex multi-step communications across different channels.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    
    # Campaign configuration
    stages: List[CampaignStage] = field(default_factory=list)
    workflow_type: WorkflowType = WorkflowType.SEQUENTIAL
    workflow_config: Dict[str, Any] = field(default_factory=dict)
    
    # Campaign metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    status: str = "draft"
    
    # Tracking and segmentation
    analytics_config: AnalyticsConfig = field(default_factory=AnalyticsConfig)
    segment_configs: List[SegmentConfig] = field(default_factory=list)
    
    # Additional data
    product_data: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    
    def add_stage(self, stage: CampaignStage) -> None:
        """
        Add a stage to the campaign workflow.
        
        Args:
            stage: The campaign stage to add
        """
        # Set the sequence order if not already set
        if stage.sequence_order == 0:
            stage.sequence_order = len(self.stages) + 1
        
        # Check for duplicate sequence numbers
        existing_sequences = [s.sequence_order for s in self.stages]
        if stage.sequence_order in existing_sequences:
            # Find the next available sequence number
            max_sequence = max(existing_sequences) if existing_sequences else 0
            stage.sequence_order = max_sequence + 1
        
        self.stages.append(stage)
        self.stages.sort(key=lambda s: s.sequence_order)
        self.updated_at = datetime.utcnow()
    
    def remove_stage(self, stage_id: str) -> bool:
        """
        Remove a stage from the campaign workflow.
        
        Args:
            stage_id: The ID of the stage to remove
            
        Returns:
            True if the stage was removed, False if not found
        """
        initial_count = len(self.stages)
        self.stages = [s for s in self.stages if s.id != stage_id]
        
        # Update sequence orders to be consecutive
        for i, stage in enumerate(self.stages):
            stage.sequence_order = i + 1
        
        self.updated_at = datetime.utcnow()
        return len(self.stages) < initial_count
    
    def get_stage_by_id(self, stage_id: str) -> Optional[CampaignStage]:
        """
        Get a stage by its ID.
        
        Args:
            stage_id: The ID of the stage to retrieve
            
        Returns:
            The stage if found, None otherwise
        """
        for stage in self.stages:
            if stage.id == stage_id:
                return stage
        return None
    
    def get_next_stage(self, current_stage_id: str) -> Optional[CampaignStage]:
        """
        Get the next stage in the workflow after the given stage.
        
        Args:
            current_stage_id: The ID of the current stage
            
        Returns:
            The next stage if there is one, None otherwise
        """
        current_stage = self.get_stage_by_id(current_stage_id)
        if not current_stage:
            return None
        
        # For sequential workflows, find the stage with the next sequence number
        if self.workflow_type == WorkflowType.SEQUENTIAL:
            next_stages = [s for s in self.stages 
                          if s.sequence_order > current_stage.sequence_order]
            return min(next_stages, key=lambda s: s.sequence_order) if next_stages else None
        
        # For other workflow types, consult the workflow configuration
        # This is a simplified implementation - real implementations would be more complex
        return None
    
    def add_segment(self, segment: SegmentConfig) -> None:
        """
        Add a segment configuration to the campaign.
        
        Args:
            segment: The segment configuration to add
        """
        self.segment_configs.append(segment)
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the workflow campaign to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "stages": [stage.to_dict() for stage in self.stages],
            "workflow_type": self.workflow_type.value,
            "workflow_config": self.workflow_config,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "status": self.status,
            "analytics_config": self.analytics_config.to_dict(),
            "segment_configs": [segment.to_dict() for segment in self.segment_configs],
            "product_data": self.product_data,
            "tags": self.tags,
            "custom_attributes": self.custom_attributes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowCampaign':
        """Create a WorkflowCampaign instance from a dictionary."""
        # Create the campaign without complex attributes
        campaign = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            description=data.get("description"),
            version=data.get("version", "1.0.0"),
            workflow_type=WorkflowType(data.get("workflow_type", "sequential")),
            workflow_config=data.get("workflow_config", {}),
            created_by=data.get("created_by"),
            status=data.get("status", "draft"),
            product_data=data.get("product_data", {}),
            tags=data.get("tags", []),
            custom_attributes=data.get("custom_attributes", {})
        )
        
        # Convert timestamps
        if "created_at" in data:
            campaign.created_at = datetime.fromisoformat(data["created_at"])
        
        if "updated_at" in data:
            campaign.updated_at = datetime.fromisoformat(data["updated_at"])
        
        # Parse analytics config
        if "analytics_config" in data:
            campaign.analytics_config = AnalyticsConfig.from_dict(data["analytics_config"])
        
        # Parse segments
        if "segment_configs" in data:
            campaign.segment_configs = [
                SegmentConfig.from_dict(segment_data)
                for segment_data in data["segment_configs"]
            ]
        
        # Parse stages
        if "stages" in data:
            campaign.stages = [
                CampaignStage.from_dict(stage_data)
                for stage_data in data["stages"]
            ]
            # Sort stages by sequence order
            campaign.stages.sort(key=lambda stage: stage.sequence_order)
        
        return campaign 