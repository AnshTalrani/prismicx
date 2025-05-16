"""
Configuration manager for the Sales Bot module.

This module provides functionality to load, validate, and access
configuration settings specific to the Sales Bot.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

import pytz
from dateutil import tz
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

# Pydantic models for configuration validation


class ChainConfig(BaseModel):
    """Chain configuration validation for Sales Bot."""
    retrieval: Dict
    prompt: Dict
    memory: Optional[Dict]


class AnalysisConfig(BaseModel):
    """Analysis configuration validation for Sales Bot."""
    nlp_features: Dict
    templates: Dict
    patterns: Dict


class SalesBotConfig(BaseModel):
    """Sales bot configuration validation."""
    bot_type: str
    model_name: str
    temperature: float
    memory_tokens: int
    system_message: str
    chain_config: ChainConfig
    analysis_config: AnalysisConfig
    # Sales-specific configs
    campaign_config: Dict


class SalesConfigManager:
    """
    Configuration manager for the Sales Bot.
    
    This class handles loading and validating configurations for the Sales Bot,
    and provides methods to access specific configuration sections.
    It supports caching to avoid repeated file operations.
    
    Attributes:
        config_path (str): Path to the sales bot configuration file
        sales_config_cache (Dict): Cached configuration
        conversation_guidance_cache (Dict): Cached conversation guidance by stage
        timing_config_cache (Dict): Cached timing configurations
    """
    
    def __init__(self):
        """
        Initialize the sales configuration manager.
        
        Sets default configuration paths and initializes caches.
        """
        self.config_path = os.environ.get(
            "SALES_BOT_CONFIG_PATH", 
            "/app/config/sales_bot_config.json"
        )
        self.sales_config_cache = None
        self.conversation_guidance_cache = {}
        self.timing_config_cache = {}
        
        logger.info("Sales Config Manager initialized", config_path=self.config_path)
    
    def load_config(self) -> Dict:
        """
        Load and validate the sales bot configuration.
        
        Returns:
            Dict: Validated configuration dictionary
        """
        if self.sales_config_cache:
            return self.sales_config_cache
        
        try:
            raw_config = self._load_config(self.config_path)
            
            # Validate with pydantic
            validated_config = SalesBotConfig(**raw_config).dict()
            
            self.sales_config_cache = validated_config
            logger.info("Sales bot configuration loaded and validated")
            return validated_config
        except Exception as e:
            logger.error("Failed to load sales bot configuration", error=str(e))
            raise
    
    def get_conversation_guidance(self, stage: str) -> Dict[str, Any]:
        """
        Get conversation guidance for a specific sales pipeline stage.
        
        Args:
            stage: The sales pipeline stage (e.g., "prospecting", "qualification")
            
        Returns:
            Dict containing conversation guidance for the specified stage
        """
        # Check cache first
        if stage in self.conversation_guidance_cache:
            return self.conversation_guidance_cache[stage]
        
        # Load full config
        config = self.load_config()
        campaign_config = config.get("campaign_config", {})
        stages_config = campaign_config.get("stages", {})
        
        # Get stage config or default
        stage_config = stages_config.get(stage, {})
        
        if not stage_config:
            logger.warning("No guidance found for sales stage", stage=stage)
            stage_config = {
                "description": "Generic sales conversation",
                "goals": ["Build rapport", "Identify needs", "Present solutions"],
                "talking_points": ["Product features", "Value proposition", "Next steps"]
            }
        
        # Cache the result
        self.conversation_guidance_cache[stage] = stage_config
        return stage_config
    
    def get_chain_config(self) -> Dict:
        """
        Get the LLM chain configuration for the sales bot.
        
        Returns:
            Dict containing chain configuration
        """
        config = self.load_config()
        return config.get("chain_config", {})
    
    def get_analysis_config(self) -> Dict:
        """
        Get the analysis configuration for the sales bot.
        
        Returns:
            Dict containing analysis configuration
        """
        config = self.load_config()
        return config.get("analysis_config", {})
    
    def get_campaign_config(self) -> Dict:
        """
        Get the sales campaign configuration.
        
        Returns:
            Dict containing sales campaign configuration
        """
        config = self.load_config()
        return config.get("campaign_config", {})
    
    def get_timing_config(self, campaign_template: Dict[str, Any], stage: str = None) -> Dict[str, Any]:
        """
        Get timing configuration for a sales campaign template, optionally for a specific stage.
        
        Args:
            campaign_template: Sales campaign template configuration
            stage: Optional stage name to get stage-specific timing
            
        Returns:
            Dict containing timing configuration
        """
        # Generate cache key
        template_id = campaign_template.get("id", "default")
        cache_key = f"{template_id}:{stage or 'global'}"
        
        # Check cache
        if cache_key in self.timing_config_cache:
            return self.timing_config_cache[cache_key]
        
        # Get global timing settings
        global_timing = campaign_template.get("timing", {})
        
        # If no stage specified, return global timing
        if not stage:
            self.timing_config_cache[cache_key] = global_timing
            return global_timing
        
        # Get stage config
        stages = campaign_template.get("stages", {})
        stage_config = stages.get(stage, {})
        
        if not stage_config:
            logger.warning(
                "Stage not found in sales campaign template", 
                stage=stage, 
                template_id=template_id
            )
            self.timing_config_cache[cache_key] = global_timing
            return global_timing
        
        # Get stage-specific timing
        stage_timing = stage_config.get("follow_up_timing", {})
        
        # Merge with global timing (stage-specific settings override global)
        result = {**global_timing}
        result.update(stage_timing)
        
        # Cache the result
        self.timing_config_cache[cache_key] = result
        return result
    
    def calculate_next_contact_time(
        self,
        timing_config: Dict[str, Any],
        current_time: datetime,
        user_data: Dict[str, Any] = None,
        engagement_metrics: Dict[str, Any] = None
    ) -> datetime:
        """
        Calculate the next time to contact a user based on sales timing rules.
        
        Args:
            timing_config: Sales timing configuration from a campaign template
            current_time: Current datetime
            user_data: User profile data
            engagement_metrics: Metrics about previous engagement
            
        Returns:
            Datetime representing the next contact time
        """
        # Start with default follow-up time
        default_hours = timing_config.get("default_follow_up_hours", 24)
        next_time = current_time + timedelta(hours=default_hours)
        
        # Apply engagement-based rules if metrics are provided
        if engagement_metrics:
            # If high engagement, follow up sooner
            if engagement_metrics.get("engagement_level") == "high":
                follow_up_hours = timing_config.get("high_engagement_follow_up_hours", 12)
                next_time = current_time + timedelta(hours=follow_up_hours)
            
            # If low engagement, follow up later
            elif engagement_metrics.get("engagement_level") == "low":
                follow_up_hours = timing_config.get("low_engagement_follow_up_hours", 48)
                next_time = current_time + timedelta(hours=follow_up_hours)
        
        # Apply user timezone and business hours rules if specified
        business_hours = timing_config.get("business_hours", None)
        if business_hours:
            # Get user timezone or default to UTC
            user_tz = "UTC"
            if user_data and "timezone" in user_data:
                user_tz = user_data["timezone"]
            
            # Adjust for business hours
            next_time = self._adjust_for_business_hours(
                next_time, 
                business_hours,
                user_tz
            )
        
        return next_time
    
    def should_escalate(
        self, 
        timing_config: Dict[str, Any],
        attempt_count: int,
        user_data: Dict[str, Any] = None,
    ) -> bool:
        """
        Determine if a sales conversation should be escalated based on timing rules.
        
        Args:
            timing_config: Sales timing configuration from a campaign template
            attempt_count: Number of sales attempts so far
            user_data: User profile data
            
        Returns:
            Boolean indicating if escalation should occur
        """
        # Get escalation threshold
        escalation_threshold = timing_config.get("escalation_threshold", 3)
        
        # Check user-specific thresholds for VIP customers
        if user_data and user_data.get("customer_tier") == "VIP":
            vip_threshold = timing_config.get("vip_escalation_threshold", 2)
            escalation_threshold = vip_threshold
        
        # Return true if attempt count exceeds threshold
        return attempt_count >= escalation_threshold
    
    def should_advance_stage(
        self,
        current_stage: str,
        all_stages: List[str],
        timing_config: Dict[str, Any],
        stage_data: Dict[str, Any],
        user_data: Dict[str, Any] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if the sales campaign should advance to the next stage.
        
        Args:
            current_stage: Current sales stage name
            all_stages: List of all sales pipeline stages in order
            timing_config: Sales timing configuration
            stage_data: Data about the current stage progression
            user_data: User profile data
            
        Returns:
            Tuple of (should_advance, next_stage)
        """
        # Find current stage index
        try:
            current_index = all_stages.index(current_stage)
        except ValueError:
            logger.warning("Invalid sales stage", stage=current_stage)
            return False, None
        
        # Check if this is already the final stage
        if current_index == len(all_stages) - 1:
            return False, None
        
        # Get advancement criteria
        time_in_stage = stage_data.get("time_in_stage", 0)  # Days in current stage
        max_time_in_stage = timing_config.get("max_days_in_stage", 14)
        
        # Check if customer has been in stage too long
        if time_in_stage >= max_time_in_stage:
            next_stage = all_stages[current_index + 1]
            return True, next_stage
        
        # Check for positive signals
        positive_signals = stage_data.get("positive_signals", 0)
        advancement_signal_threshold = timing_config.get("advancement_signal_threshold", 3)
        
        if positive_signals >= advancement_signal_threshold:
            next_stage = all_stages[current_index + 1]
            return True, next_stage
        
        # No advancement
        return False, None
    
    def is_within_frequency_limits(
        self,
        user_data: Dict[str, Any],
        contact_history: List[datetime],
        timing_config: Dict[str, Any]
    ) -> bool:
        """
        Check if contacting a user now would exceed sales frequency limits.
        
        Args:
            user_data: User profile data
            contact_history: List of previous contact timestamps
            timing_config: Sales timing configuration
            
        Returns:
            Boolean indicating if within frequency limits
        """
        # Get configured limits
        max_per_week = timing_config.get("max_contacts_per_week", 3)
        max_per_day = timing_config.get("max_contacts_per_day", 1)
        
        # Adjust for VIP customers
        if user_data and user_data.get("customer_tier") == "VIP":
            max_per_week = timing_config.get("vip_max_contacts_per_week", max_per_week)
            max_per_day = timing_config.get("vip_max_contacts_per_day", max_per_day)
        
        # Calculate current counts
        now = datetime.utcnow()
        one_day_ago = now - timedelta(days=1)
        one_week_ago = now - timedelta(days=7)
        
        contacts_today = sum(1 for t in contact_history if t >= one_day_ago)
        contacts_this_week = sum(1 for t in contact_history if t >= one_week_ago)
        
        # Check against limits
        return contacts_today < max_per_day and contacts_this_week < max_per_week
    
    #
    # Helper Methods
    #
        
    def _load_config(self, path: str) -> Dict:
        """
        Load a JSON configuration file for the sales bot.
        
        Args:
            path: Path to the sales bot configuration file
            
        Returns:
            Loaded sales bot configuration
        """
        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Sales bot configuration file not found", path=path)
            raise
        except json.JSONDecodeError:
            logger.error("Invalid JSON in sales bot configuration file", path=path)
            raise
    
    def _adjust_for_business_hours(
        self,
        target_time: datetime,
        business_hours: Dict[str, Any],
        timezone_str: str = "UTC"
    ) -> datetime:
        """
        Adjust a sales contact time to fall within business hours.
        
        Args:
            target_time: Original target time (UTC)
            business_hours: Business hours configuration for sales contacts
            timezone_str: Timezone to use for business hours
            
        Returns:
            Adjusted datetime
        """
        # Convert to target timezone
        target_tz = tz.gettz(timezone_str)
        local_time = target_time.astimezone(target_tz)
        
        # Get day of week (0 = Monday, 6 = Sunday)
        day_of_week = local_time.weekday()
        
        # Check if this is a working day
        working_days = business_hours.get("working_days", [0, 1, 2, 3, 4])  # Default Mon-Fri
        if day_of_week not in working_days:
            # Find next working day
            days_to_add = 1
            while (day_of_week + days_to_add) % 7 not in working_days:
                days_to_add += 1
            
            # Move to start of next working day
            local_time = local_time.replace(hour=9, minute=0, second=0) + timedelta(days=days_to_add)
        
        # Get business hours for this day
        start_hour = business_hours.get("start_hour", 9)
        end_hour = business_hours.get("end_hour", 17)
        
        # If too early, move to start of business hours
        if local_time.hour < start_hour:
            local_time = local_time.replace(hour=start_hour, minute=0, second=0)
        
        # If too late, move to start of next business day
        if local_time.hour >= end_hour:
            local_time = local_time.replace(hour=start_hour, minute=0, second=0) + timedelta(days=1)
            
            # Check if next day is a working day
            next_day = (day_of_week + 1) % 7
            if next_day not in working_days:
                # Find next working day
                days_to_add = 1
                while (day_of_week + days_to_add) % 7 not in working_days:
                    days_to_add += 1
                
                local_time = local_time.replace(hour=start_hour, minute=0, second=0) + timedelta(days=days_to_add)
        
        # Convert back to UTC
        return local_time.astimezone(pytz.UTC)
    
    def invalidate_cache(self, cache_type: str = "all", key_pattern: str = None):
        """
        Invalidate specific sales bot configuration caches.
        
        Args:
            cache_type: Type of cache to invalidate (all, config, guidance, timing)
            key_pattern: Optional pattern to match cache keys
        """
        if cache_type in ["all", "config"]:
            self.sales_config_cache = None
        
        if cache_type in ["all", "guidance"]:
            if key_pattern:
                keys_to_delete = [k for k in self.conversation_guidance_cache.keys() if key_pattern in k]
                for key in keys_to_delete:
                    del self.conversation_guidance_cache[key]
            else:
                self.conversation_guidance_cache.clear()
        
        if cache_type in ["all", "timing"]:
            if key_pattern:
                keys_to_delete = [k for k in self.timing_config_cache.keys() if key_pattern in k]
                for key in keys_to_delete:
                    del self.timing_config_cache[key]
            else:
                self.timing_config_cache.clear()
        
        logger.info("Sales bot cache invalidated", cache_type=cache_type, key_pattern=key_pattern) 