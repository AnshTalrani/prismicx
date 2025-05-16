"""
Campaign Stage Model for multi-stage marketing campaigns.

This module defines the CampaignStage class which represents a single stage in a multi-stage
marketing campaign, including channel configuration, timing, and content.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List
import uuid


class CommunicationChannel(str, Enum):
    """Enum representing the available communication channels for campaign stages."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class TimeUnit(str, Enum):
    """Enum representing time units for wait periods."""
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"


class DayOfWeek(int, Enum):
    """Enum representing days of the week."""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class StageType(str, Enum):
    """Enum representing the type of campaign stage."""
    STANDARD = "standard"  # Standard communication stage
    CONDITIONAL = "conditional"  # Stage with conditional execution
    WAIT = "wait"  # Wait stage with no communication
    SEGMENT_SPLIT = "segment_split"  # Split recipients into segments
    A_B_TEST = "a_b_test"  # A/B testing stage


@dataclass
class TimeWindow:
    """
    Represents a time window for sending communications.
    
    This defines when communications are allowed to be sent,
    including working hours, allowed days, and time zone information.
    """
    start_hour: int = 9  # 9 AM default start
    end_hour: int = 17  # 5 PM default end
    allowed_days: List[DayOfWeek] = field(default_factory=lambda: [
        DayOfWeek.MONDAY, 
        DayOfWeek.TUESDAY, 
        DayOfWeek.WEDNESDAY, 
        DayOfWeek.THURSDAY, 
        DayOfWeek.FRIDAY
    ])
    timezone: str = "UTC"
    
    def is_within_window(self, timestamp: datetime) -> bool:
        """
        Check if a timestamp is within the allowed sending window.
        
        Args:
            timestamp: The timestamp to check
            
        Returns:
            True if the timestamp is within the sending window, False otherwise
        """
        # Convert to the target timezone
        # Note: This is simplified; in a real implementation, you'd use a
        # library like pytz or dateutil to handle timezone conversions properly
        
        # Check if the day is allowed
        weekday = timestamp.weekday()
        if DayOfWeek(weekday) not in self.allowed_days:
            return False
        
        # Check if the hour is within range
        hour = timestamp.hour
        return self.start_hour <= hour < self.end_hour
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the time window to a dictionary."""
        return {
            "start_hour": self.start_hour,
            "end_hour": self.end_hour,
            "allowed_days": [day.value for day in self.allowed_days],
            "timezone": self.timezone
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeWindow':
        """Create a TimeWindow instance from a dictionary."""
        return cls(
            start_hour=data.get("start_hour", 9),
            end_hour=data.get("end_hour", 17),
            allowed_days=[DayOfWeek(day) for day in data.get("allowed_days", [0, 1, 2, 3, 4])],
            timezone=data.get("timezone", "UTC")
        )


@dataclass
class WaitConfig:
    """
    Configuration for wait periods between campaign stages.
    
    Defines how long to wait before executing the next stage and
    any specific timing requirements.
    """
    duration: int  # The amount of time to wait
    unit: TimeUnit  # The unit of time (minutes, hours, days, weeks)
    respect_time_window: bool = True  # Whether to respect the sending time window
    
    def to_timedelta(self) -> timedelta:
        """Convert the wait configuration to a timedelta."""
        if self.unit == TimeUnit.MINUTES:
            return timedelta(minutes=self.duration)
        elif self.unit == TimeUnit.HOURS:
            return timedelta(hours=self.duration)
        elif self.unit == TimeUnit.DAYS:
            return timedelta(days=self.duration)
        elif self.unit == TimeUnit.WEEKS:
            return timedelta(weeks=self.duration)
        else:
            raise ValueError(f"Unknown time unit: {self.unit}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the wait configuration to a dictionary."""
        return {
            "duration": self.duration,
            "unit": self.unit.value,
            "respect_time_window": self.respect_time_window
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WaitConfig':
        """Create a WaitConfig instance from a dictionary."""
        return cls(
            duration=data["duration"],
            unit=TimeUnit(data["unit"]),
            respect_time_window=data.get("respect_time_window", True)
        )


@dataclass
class ChannelConfig:
    """
    Configuration for a communication channel in a campaign stage.
    
    Contains channel-specific settings and content templates.
    """
    channel: CommunicationChannel
    template_id: Optional[str] = None
    
    # Channel-specific content and settings
    content: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the channel configuration to a dictionary."""
        return {
            "channel": self.channel.value,
            "template_id": self.template_id,
            "content": self.content,
            "settings": self.settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChannelConfig':
        """Create a ChannelConfig instance from a dictionary."""
        return cls(
            channel=CommunicationChannel(data["channel"]),
            template_id=data.get("template_id"),
            content=data.get("content", {}),
            settings=data.get("settings", {})
        )


@dataclass
class ConditionalLogic:
    """
    Conditional logic for determining if a stage should be executed.
    
    Allows for complex conditions based on recipient attributes,
    previous stage outcomes, or other campaign data.
    """
    condition_type: str  # Type of condition (e.g., "attribute", "event", "previous_stage")
    attribute: Optional[str] = None  # Attribute to check (for attribute conditions)
    operator: str = "equals"  # Comparison operator
    value: Any = None  # Value to compare against
    previous_stage_id: Optional[str] = None  # ID of previous stage (for stage conditions)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the conditional logic to a dictionary."""
        return {
            "condition_type": self.condition_type,
            "attribute": self.attribute,
            "operator": self.operator,
            "value": self.value,
            "previous_stage_id": self.previous_stage_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConditionalLogic':
        """Create a ConditionalLogic instance from a dictionary."""
        return cls(
            condition_type=data["condition_type"],
            attribute=data.get("attribute"),
            operator=data.get("operator", "equals"),
            value=data.get("value"),
            previous_stage_id=data.get("previous_stage_id")
        )


@dataclass
class CampaignStage:
    """
    Represents a stage in a multi-stage marketing campaign.
    
    Each stage defines a specific communication to be sent via
    a particular channel at a specified time.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    stage_type: StageType = StageType.STANDARD
    sequence_order: int = 0  # Order in the campaign sequence
    channel_config: Optional[ChannelConfig] = None
    wait_config: Optional[WaitConfig] = None
    time_window: TimeWindow = field(default_factory=TimeWindow)
    conditional_logic: Optional[ConditionalLogic] = None
    
    # Metadata and tracking
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    
    def get_wait_duration(self) -> Optional[timedelta]:
        """Get the wait duration before this stage as a timedelta."""
        if self.wait_config:
            return self.wait_config.to_timedelta()
        return None
    
    def calculate_send_time(self, reference_time: datetime) -> datetime:
        """
        Calculate the time when this stage should be executed.
        
        Args:
            reference_time: The reference time (usually completion of previous stage)
            
        Returns:
            The datetime when this stage should be executed
        """
        if not self.wait_config:
            return reference_time
        
        # Add the wait duration
        target_time = reference_time + self.wait_config.to_timedelta()
        
        # If we don't need to respect the time window, return immediately
        if not self.wait_config.respect_time_window:
            return target_time
        
        # Check if the target time is within the allowed window
        while not self.time_window.is_within_window(target_time):
            # If not, add a day and set the hour to the start hour
            target_time = target_time.replace(
                hour=self.time_window.start_hour, 
                minute=0, 
                second=0, 
                microsecond=0
            )
            target_time += timedelta(days=1)
        
        return target_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the campaign stage to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "stage_type": self.stage_type.value,
            "sequence_order": self.sequence_order,
            "channel_config": self.channel_config.to_dict() if self.channel_config else None,
            "wait_config": self.wait_config.to_dict() if self.wait_config else None,
            "time_window": self.time_window.to_dict(),
            "conditional_logic": self.conditional_logic.to_dict() if self.conditional_logic else None,
            "description": self.description,
            "tags": self.tags,
            "custom_attributes": self.custom_attributes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CampaignStage':
        """Create a CampaignStage instance from a dictionary."""
        # Parse nested objects
        channel_config = None
        if data.get("channel_config"):
            channel_config = ChannelConfig.from_dict(data["channel_config"])
        
        wait_config = None
        if data.get("wait_config"):
            wait_config = WaitConfig.from_dict(data["wait_config"])
        
        time_window = TimeWindow()
        if data.get("time_window"):
            time_window = TimeWindow.from_dict(data["time_window"])
        
        conditional_logic = None
        if data.get("conditional_logic"):
            conditional_logic = ConditionalLogic.from_dict(data["conditional_logic"])
        
        # Create the stage
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            stage_type=StageType(data.get("stage_type", "standard")),
            sequence_order=data.get("sequence_order", 0),
            channel_config=channel_config,
            wait_config=wait_config,
            time_window=time_window,
            conditional_logic=conditional_logic,
            description=data.get("description"),
            tags=data.get("tags", []),
            custom_attributes=data.get("custom_attributes", {})
        ) 