"""
Campaign Configuration Model for parsing marketing campaign config files.

This module defines the CampaignConfig class which handles the parsing and validation
of campaign configuration files, such as campaign_marketing.json.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Union

from .campaign_stage import CampaignStage, ChannelType, TriggerType


class ABTestingVariant(str, Enum):
    """Enum representing different A/B testing variants."""
    A = "A"
    B = "B"
    CONTROL = "CONTROL"


@dataclass
class ABTestingConfig:
    """Configuration for A/B testing in a campaign."""
    enabled: bool = False
    test_type: str = "subject"  # subject, content, sender, etc.
    variants: Dict[str, Any] = field(default_factory=dict)
    distribution: Dict[str, float] = field(default_factory=dict)
    success_metric: str = "open_rate"  # open_rate, click_rate, conversion_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the AB testing config to a dictionary."""
        return {
            "enabled": self.enabled,
            "test_type": self.test_type,
            "variants": self.variants,
            "distribution": self.distribution,
            "success_metric": self.success_metric
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ABTestingConfig':
        """Create an ABTestingConfig instance from a dictionary."""
        return cls(
            enabled=data.get("enabled", False),
            test_type=data.get("test_type", "subject"),
            variants=data.get("variants", {}),
            distribution=data.get("distribution", {}),
            success_metric=data.get("success_metric", "open_rate")
        )


@dataclass
class AnalyticsConfig:
    """Configuration for campaign analytics tracking."""
    track_opens: bool = True
    track_clicks: bool = True
    track_conversions: bool = False
    utm_parameters: Dict[str, str] = field(default_factory=dict)
    conversion_goals: List[str] = field(default_factory=list)
    custom_tracking: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the analytics config to a dictionary."""
        return {
            "track_opens": self.track_opens,
            "track_clicks": self.track_clicks,
            "track_conversions": self.track_conversions,
            "utm_parameters": self.utm_parameters,
            "conversion_goals": self.conversion_goals,
            "custom_tracking": self.custom_tracking
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalyticsConfig':
        """Create an AnalyticsConfig instance from a dictionary."""
        return cls(
            track_opens=data.get("track_opens", True),
            track_clicks=data.get("track_clicks", True),
            track_conversions=data.get("track_conversions", False),
            utm_parameters=data.get("utm_parameters", {}),
            conversion_goals=data.get("conversion_goals", []),
            custom_tracking=data.get("custom_tracking", {})
        )


@dataclass
class WorkflowConfig:
    """Configuration for campaign workflow and automation rules."""
    auto_continue: bool = True  # Continue to next stage automatically
    max_retries: int = 3  # Max retries for failed deliveries
    retry_interval_minutes: int = 60  # Wait time between retries
    stop_conditions: Dict[str, Any] = field(default_factory=dict)
    skip_weekend: bool = False  # Skip sending on weekends
    working_hours_only: bool = False  # Send only during working hours
    working_hours: Dict[str, Any] = field(default_factory=lambda: {
        "start": "09:00",
        "end": "17:00",
        "timezone": "UTC"
    })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the workflow config to a dictionary."""
        return {
            "auto_continue": self.auto_continue,
            "max_retries": self.max_retries,
            "retry_interval_minutes": self.retry_interval_minutes,
            "stop_conditions": self.stop_conditions,
            "skip_weekend": self.skip_weekend,
            "working_hours_only": self.working_hours_only,
            "working_hours": self.working_hours
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowConfig':
        """Create a WorkflowConfig instance from a dictionary."""
        return cls(
            auto_continue=data.get("auto_continue", True),
            max_retries=data.get("max_retries", 3),
            retry_interval_minutes=data.get("retry_interval_minutes", 60),
            stop_conditions=data.get("stop_conditions", {}),
            skip_weekend=data.get("skip_weekend", False),
            working_hours_only=data.get("working_hours_only", False),
            working_hours=data.get("working_hours", {
                "start": "09:00",
                "end": "17:00",
                "timezone": "UTC"
            })
        )


@dataclass
class CampaignConfig:
    """
    Represents the complete configuration for a multi-stage marketing campaign.
    
    This class parses and validates campaign configuration files (like campaign_marketing.json),
    ensuring all necessary parameters are present and correctly formatted.
    It provides structured access to all campaign settings including stages, workflow rules,
    A/B testing configurations, and analytics tracking.
    """
    name: str
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    segment_id: Optional[str] = None
    
    # Campaign stages configuration
    stages: List[CampaignStage] = field(default_factory=list)
    
    # Campaign workflow configuration
    workflow_config: WorkflowConfig = field(default_factory=WorkflowConfig)
    
    # A/B testing configuration
    ab_testing_config: ABTestingConfig = field(default_factory=ABTestingConfig)
    
    # Analytics tracking configuration
    analytics_config: AnalyticsConfig = field(default_factory=AnalyticsConfig)
    
    # Product data for templates
    product_data: Dict[str, Any] = field(default_factory=dict)
    
    # Custom attributes
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the campaign configuration to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "segment_id": self.segment_id,
            "stages": [stage.to_dict() for stage in self.stages],
            "workflow_config": self.workflow_config.to_dict(),
            "ab_testing_config": self.ab_testing_config.to_dict(),
            "analytics_config": self.analytics_config.to_dict(),
            "product_data": self.product_data,
            "custom_attributes": self.custom_attributes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CampaignConfig':
        """Create a CampaignConfig instance from a dictionary."""
        # Parse stages
        stages = []
        for stage_data in data.get("stages", []):
            stages.append(CampaignStage.from_dict(stage_data))
            
        # Sort stages by sequence_order
        stages.sort(key=lambda stage: stage.sequence_order)
        
        # Parse configs
        workflow_config = WorkflowConfig.from_dict(data.get("workflow_config", {}))
        ab_testing_config = ABTestingConfig.from_dict(data.get("ab_testing_config", {}))
        analytics_config = AnalyticsConfig.from_dict(data.get("analytics_config", {}))
        
        return cls(
            name=data["name"],
            description=data.get("description"),
            tags=data.get("tags", []),
            segment_id=data.get("segment_id"),
            stages=stages,
            workflow_config=workflow_config,
            ab_testing_config=ab_testing_config,
            analytics_config=analytics_config,
            product_data=data.get("product_data", {}),
            custom_attributes=data.get("custom_attributes", {})
        )
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'CampaignConfig':
        """
        Load a campaign configuration from a JSON file.
        
        Args:
            file_path: Path to the JSON configuration file
            
        Returns:
            CampaignConfig instance
        """
        import json
        
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        return cls.from_dict(data)
    
    def validate(self) -> List[str]:
        """
        Validate the campaign configuration.
        
        Returns:
            List of validation error messages, empty if valid
        """
        errors = []
        
        # Basic validation
        if not self.name:
            errors.append("Campaign name is required")
            
        if not self.stages:
            errors.append("At least one campaign stage is required")
            
        # Validate stages
        for i, stage in enumerate(self.stages):
            if not stage.name:
                errors.append(f"Stage {i+1} name is required")
                
            if stage.channel_type == ChannelType.EMAIL and not stage.template_id:
                errors.append(f"Stage '{stage.name}' requires a template_id for EMAIL channel")
                
        return errors 