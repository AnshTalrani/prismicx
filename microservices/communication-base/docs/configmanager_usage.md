# ConfigManager Usage Guide

This guide explains how to use the ConfigManager in the communication-base microservice to process campaign templates from agent batch requests and implement sophisticated campaign timing logic and follow-up scheduling.

## Overview

The `ConfigManager` class provides functionality to process campaign templates that are included in batch requests from the agent microservice. It extracts timing rules, conversion guidance, and stage definitions that determine when and how follow-ups are scheduled, when to escalate conversations, and when to advance campaign stages.

## Template Processing Workflow

### 1. Template Extraction

The Campaign Poller extracts the template from an agent batch request:

```python
async def _create_campaign_from_request(self, request: Dict[str, Any]) -> Optional[str]:
    # Extract template from the batch request
    template = request.get("template", {})
    
    # Pass template to config manager for processing
    stages = self._convert_template_stages(template.get("stages", []))
    
    # Create campaign with processed template data
    # ...
```

### 2. Stage Conversion

The template stages are converted to a format suitable for campaign processing:

```python
def _convert_template_stages(self, template_stages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert template stages to campaign stages format.
    """
    campaign_stages = []
    
    for i, stage in enumerate(template_stages):
        campaign_stage = {
            "name": stage.get("stage"),
            "order": i,
            "content": stage.get("content_structure", {}),
            "variables": stage.get("variables", {}),
            "completion_criteria": stage.get("completion_criteria", {}),
            "follow_up_timing": stage.get("follow_up_timing", {}),
            "conversation_guidance": stage.get("conversation_guidance", {})
        }
        
        campaign_stages.append(campaign_stage)
    
    return campaign_stages
```

## Basic ConfigManager Usage

### Initialization

```python
from src.config.config_manager import ConfigManager

# Create a ConfigManager instance
config_manager = ConfigManager()
```

### Extracting Timing Configuration

```python
# Get global timing configuration
global_timing = config_manager.get_timing_config(campaign_template)

# Get stage-specific timing (e.g., for the "awareness" stage)
awareness_timing = config_manager.get_timing_config(campaign_template, "awareness")
```

### Calculating Next Contact Time

```python
from datetime import datetime
import pytz

# Current time
current_time = datetime.now(pytz.UTC)

# Calculate the next time to contact a user
next_contact_time = config_manager.calculate_next_contact_time(
    timing_config=awareness_timing,
    current_time=current_time,
    user_data={"segment": "enterprise"},
    engagement_metrics={
        "email_open": "2023-06-15T14:30:00Z",
        "link_click": "2023-06-15T14:35:00Z"
    }
)
```

### Determining Escalation

```python
# Check if the conversation should be escalated after 3 attempts
should_escalate = config_manager.should_escalate(
    timing_config=awareness_timing,
    attempt_count=3
)
```

### Determining Stage Advancement

```python
# Check if the campaign should advance to the next stage
should_advance = config_manager.should_advance_stage(
    timing_config=awareness_timing,
    stage_start_time=datetime(2023, 6, 1, tzinfo=pytz.UTC),
    current_time=datetime.now(pytz.UTC),
    completion_metrics={"email_opens": 120, "link_clicks": 60},
    completion_criteria={"email_opens": 100, "link_clicks": 50}
)
```

### Getting Message Templates

```python
# Get the appropriate template for the second follow-up attempt
templates = config_manager.get_message_templates(
    timing_config=awareness_timing,
    attempt_number=2
)

follow_up_template = templates.get("follow_up_template")
```

## Integration with Worker Service

The `WorkerService` uses the `ConfigManager` to process campaigns that were created from agent batch requests:

```python
# In WorkerService.process_conversation
async def process_conversation(self, conversation: Dict[str, Any]):
    # Get the campaign for this conversation
    campaign_id = conversation.get("campaign_id")
    campaign = await self.conversation_repository.get_campaign(campaign_id)
    
    # Get the campaign template (originally from agent batch request)
    template = campaign.get("template")
    
    # Get the current stage
    current_stage = conversation.get("current_stage")
    
    # Get timing config for this stage
    timing_config = self.config_manager.get_timing_config(template, current_stage)
    
    # Use timing config to determine next actions
    # ...
```

## Extracting Sales Bot Guidance

The ConfigManager also extracts conversation guidance for the Sales Bot:

```python
def get_conversation_guidance(self, template: Dict[str, Any], stage: str) -> Dict[str, Any]:
    """
    Extract conversation guidance for a specific stage.
    
    Args:
        template: Campaign template
        stage: Stage name (awareness, interest, etc.)
        
    Returns:
        Conversation guidance for the specified stage
    """
    # Find the stage in the template
    for stage_config in template.get("stages", []):
        if stage_config.get("stage") == stage:
            return stage_config.get("conversation_guidance", {})
    
    return {}
```

This guidance is used by the Sales Bot to:
- Extract specific information based on stage requirements
- Apply the appropriate response strategy for the stage
- Emphasize relevant product aspects
- Handle objections according to stage-specific guidance

## Advanced Timing Rules

### Business Hours Enforcement

The ConfigManager respects business hours defined in the timing configuration:

```json
"business_hours": {
  "start_hour": 9,
  "end_hour": 17,
  "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
}
```

If a calculated contact time falls outside business hours, it will be adjusted to the next available time within business hours.

### Optimal Send Times

You can define preferred times of day for sending messages:

```json
"optimal_send_times": ["10:00", "14:00", "16:00"]
```

The ConfigManager will adjust the contact time to one of these times whenever possible.

### Engagement-Based Timing

The system can respond dynamically to user engagement:

```json
"engagement_based_timing": {
  "email_open_follow_up_hours": 4,
  "link_click_follow_up_hours": 2,
  "feature_page_view_follow_up_hours": 24,
  "cart_abandonment_follow_up_hours": 2
}
```

When a user shows engagement (e.g., opens an email or clicks a link), the system can follow up more quickly to capitalize on the interest.

## Best Practices

1. **Provide clear conversation guidance**: Ensure each stage has comprehensive guidance for the sales bot.

2. **Define appropriate timing settings**: Configure realistic follow-up timings that respect user preferences.

3. **Implement stage-specific handling**: Different stages may require different approaches to timing and messaging.

4. **Use engagement data**: Leverage user engagement metrics to optimize contact timing.

5. **Test template processing**: Verify that your templates are correctly processed and used by the worker service.

## Monitoring

Monitor the effectiveness of your template configuration by tracking:

- Response rates relative to contact time
- Stage advancement metrics
- Escalation rates
- Follow-up effectiveness by stage and attempt number 