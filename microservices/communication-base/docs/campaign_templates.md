# Campaign Templates

## Overview

Campaign templates define the structure, content, and behavior of automated sales and communication campaigns. They provide a standardized framework for creating consistent, personalized customer interactions across different stages of the customer journey. These templates are used by the agent microservice to create batch requests that are processed by the communication-base microservice.

## Template Usage with Agent Batch Requests

When the agent microservice creates a batch request, it includes a complete campaign template in the following format:

```json
{
  "_id": "batch_request_id",
  "name": "Q4 Enterprise Software Campaign",
  "servicetype": "communication",
  "status": "new",
  "created_by": "agent",
  "created_at": "2023-10-15T08:00:00Z",
  "template": {
    "template_type": "campaign",
    "global_settings": { ... },
    "stages": [ ... ]
  },
  "recipients": [
    {"id": "user1", "contact_info": {...}},
    {"id": "user2", "contact_info": {...}}
  ],
  "scheduled_at": "2023-10-15T09:00:00Z"
}
```

The `template` field contains the complete campaign template that defines the structure and behavior of the campaign. The communication-base microservice extracts and processes this template to create a campaign.

## Template Structure

Each template has the following high-level structure:

```json
{
  "template_type": "campaign",
  "global_settings": { ... },
  "stages": [ ... ]
}
```

### Global Settings

The `global_settings` section defines parameters that apply to the entire campaign:

- `follow_up_days`: Default number of days to wait before following up
- `reminder_count`: Number of reminders to send before escalation
- `escalation_threshold`: Confidence threshold for automatic escalation

#### Timing Settings

The `timing_settings` section within `global_settings` provides comprehensive control over when communications occur:

```json
"timing_settings": {
  "timezone": "UTC",
  "business_hours": {
    "start_hour": 9,
    "end_hour": 17,
    "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
  },
  "optimal_send_times": ["10:00", "14:00", "16:00"],
  "global_cooldown_hours": 24,
  "response_wait_time_hours": 48,
  "follow_up_strategy": {
    "default_max_attempts": 3,
    "default_interval_hours": 48,
    "escalation_timing": {
      "manager_escalation_after_attempts": 3,
      "manager_response_time_hours": 24
    },
    "reschedule_policy": {
      "after_no_response_days": 14,
      "max_reschedule_attempts": 2
    }
  }
}
```

- **Timezone Configuration**: All timing is based on the specified timezone
- **Business Hours**: Defines when communications can be sent
- **Optimal Send Times**: Preferred times of day to send communications
- **Global Cooldown**: Minimum time between communications to avoid overwhelming recipients
- **Response Wait Time**: How long to wait for a response before follow-up
- **Follow-up Strategy**:
  - `default_max_attempts`: Maximum number of follow-up attempts
  - `default_interval_hours`: Default time between follow-ups
  - `escalation_timing`: When and how to escalate to management
  - `reschedule_policy`: How to handle campaigns that need rescheduling after no response

#### Personalization

The `personalization` section defines rules for customizing campaigns:

```json
"personalization": {
  "fields": ["user_name", "past_purchases", "loyalty_tier"],
  "rules": [
    {
      "condition": "loyalty_tier == 'gold'",
      "modifications": {
        "headline_prefix": "Exclusive: "
      }
    }
  ]
}
```

### Campaign Stages

The `stages` array contains configurations for each stage of the customer journey:

1. **Awareness**: Initial introduction and value proposition
2. **Interest**: Highlighting benefits and use cases
3. **Consideration**: Providing detailed information and comparisons
4. **Decision**: Offering incentives and finalizing the sale

Each stage includes:

- `stage`: The stage identifier
- `content_structure`: Templates for message content
- `variables`: Dynamic content options
- `completion_criteria`: Metrics that indicate stage completion
- `follow_up_timing`: Detailed timing configuration for follow-ups
- `conversation_guidance`: Instructions for the AI agent

#### Follow-up Timing Configuration

Each stage has a detailed `follow_up_timing` configuration that controls when and how follow-ups occur:

```json
"follow_up_timing": {
  "initial_delay_hours": 24,
  "max_follow_ups": 3,
  "follow_up_interval_hours": 48,
  "session_timeout_minutes": 30,
  "escalation_after_attempts": 2,
  "time_in_stage_before_next_stage_days": 7,
  "best_days": ["Tuesday", "Wednesday"],
  "message_spacing_minutes": 5,
  "time_of_day_preferences": ["morning", "early_afternoon"],
  "follow_up_message_templates": {
    "first_follow_up": "Just checking in regarding our previous message about {{product_name}}.",
    "second_follow_up": "I wanted to make sure you received our information about how {{product_name}} can help with {{benefit}}."
  },
  "engagement_based_timing": {
    "email_open_follow_up_hours": 4,
    "link_click_follow_up_hours": 2
  }
}
```

Key components include:
- **Basic Timing**:
  - `initial_delay_hours`: Time to wait before first follow-up
  - `max_follow_ups`: Maximum number of follow-up attempts for this stage
  - `follow_up_interval_hours`: Time between follow-ups
  - `session_timeout_minutes`: How long to keep a conversation session open

- **Progression Control**:
  - `escalation_after_attempts`: When to escalate if no response
  - `time_in_stage_before_next_stage_days`: Maximum time to spend in this stage

- **Optimization Parameters**:
  - `best_days`: Preferred days of the week for communications
  - `message_spacing_minutes`: Minimum time between messages in a session
  - `time_of_day_preferences`: Preferred times of day (morning, afternoon, etc.)

- **Content Templates**:
  - `follow_up_message_templates`: Pre-defined templates for follow-up messages

- **Behavioral Triggers**:
  - `engagement_based_timing`: Timing adjustments based on user engagement

#### Decision Stage Special Timing

The decision stage includes additional urgency-based timing:

```json
"urgency_escalation": {
  "final_offer_delay_days": 2,
  "discount_expiration_days": 5,
  "reminder_schedule_hours": [24, 48, 72],
  "final_day_reminder_times": ["9:00", "13:00", "16:00"]
}
```

This creates a sense of urgency with expiring offers and strategically timed reminders.

## ConfigManager Processing

The communication-base microservice's `ConfigManager` plays a critical role in processing campaign templates:

1. **Template Extraction from Batch Requests**: 
   - The `CampaignPoller` extracts the template from the batch request
   - Passes it to the `ConfigManager` for processing

2. **Conversion to Campaign Format**:
   - The template stages are converted to a format suitable for campaign processing
   - Stage-specific guidance is preserved for use by the Sales Bot

3. **Timing Rule Extraction**:
   - Parses the global and stage-specific timing configurations
   - Creates a timing strategy for each campaign based on its current stage
   - Schedules follow-ups according to the defined parameters

4. **Stage-Based Processing**:
   - Retrieves the current stage configuration for a campaign
   - Applies the appropriate timing rules for that stage
   - Tracks time spent in each stage for progression decisions

## Template to Campaign Processing Flow

1. **Agent creates batch request** containing the campaign template
2. **CampaignPoller** discovers the batch request and extracts the template
3. **ConfigManager** processes the template to extract:
   - Stage definitions
   - Timing rules
   - Conversation guidance
4. **Campaign** is created with stages derived from the template
5. **WorkerService** processes conversations according to the template stages
6. **SalesBot** uses the conversation guidance from the template

## Best Practices for Template Design

1. **Define Clear Stages**: Each stage should have distinct goals and progression criteria
2. **Provide Comprehensive Guidance**: Include detailed conversation guidance for the sales bot
3. **Set Realistic Timing Rules**: Configure follow-up timing that respects user preferences
4. **Test Templates Thoroughly**: Verify that templates produce the expected conversation flow

## Monitoring Template Effectiveness

Monitor the effectiveness of templates by tracking:
- Stage progression rates
- Conversation completion rates
- Response rates at each stage
- Time spent in each stage
- Conversion rates from initial stage to final stage 