# Campaign Manager Configuration Guide

This document provides detailed configuration information for the Campaign Manager component in the communication-base microservice, including examples of common campaign types and their configurations.

## Environment Variables

The Campaign Manager's behavior can be customized through the following environment variables:

| Variable Name | Description | Default | Example |
|---------------|-------------|---------|---------|
| `CAMPAIGN_MAX_BATCH_SIZE` | Maximum number of conversations to process in a single batch | 100 | `CAMPAIGN_MAX_BATCH_SIZE=200` |
| `CAMPAIGN_STAGE_DELAY_FACTOR` | Multiplier applied to stage timing rules | 1.0 | `CAMPAIGN_STAGE_DELAY_FACTOR=1.5` |
| `CAMPAIGN_RETRY_DELAY_SECONDS` | Time to wait before retrying failed operations | 300 | `CAMPAIGN_RETRY_DELAY_SECONDS=600` |
| `CAMPAIGN_METRICS_TTL_SECONDS` | Time-to-live for cached campaign metrics | 600 | `CAMPAIGN_METRICS_TTL_SECONDS=900` |
| `CAMPAIGN_PROCESSING_THREADS` | Number of worker threads for campaign processing | 4 | `CAMPAIGN_PROCESSING_THREADS=8` |
| `CAMPAIGN_POLLING_INTERVAL_SECONDS` | Interval between polling for campaigns | 60 | `CAMPAIGN_POLLING_INTERVAL_SECONDS=30` |

## Campaign Templates

Campaign templates define the structure, content, and flow of a campaign. Below are examples of common campaign template configurations:

### Sales Campaign Template

```json
{
  "_id": "sales_campaign_template_001",
  "name": "B2B Lead Nurturing Campaign",
  "type": "sales",
  "description": "A multi-stage campaign for nurturing B2B leads through the sales funnel",
  "stages": {
    "awareness": {
      "name": "Product Awareness",
      "description": "Introduce the product and value proposition",
      "messages": [
        {
          "template": "Hi {{recipient.first_name}}, I wanted to reach out regarding {{company.product_name}} that helps businesses like {{recipient.company_name}} with {{company.value_proposition}}.",
          "timing": {
            "delay_hours": 0,
            "max_follow_ups": 2,
            "follow_up_delay_hours": 48
          }
        }
      ],
      "progression_rules": {
        "response_required": true,
        "min_stage_duration_hours": 24,
        "max_stage_duration_hours": 168
      }
    },
    "consideration": {
      "name": "Product Consideration",
      "description": "Provide detailed information and address specific needs",
      "messages": [
        {
          "template": "Thanks for your interest in {{company.product_name}}. Based on what you shared, I think you'd benefit from our {{recipient.recommended_feature}} capabilities. Would you like to see a quick demo?",
          "timing": {
            "delay_hours": 24,
            "max_follow_ups": 2,
            "follow_up_delay_hours": 72
          }
        }
      ],
      "progression_rules": {
        "response_required": true,
        "min_stage_duration_hours": 48,
        "max_stage_duration_hours": 336
      }
    },
    "decision": {
      "name": "Decision Stage",
      "description": "Facilitate purchasing decision",
      "messages": [
        {
          "template": "Following our discussion about {{company.product_name}}, I've prepared a custom proposal for {{recipient.company_name}}. Would you like me to walk you through the details?",
          "timing": {
            "delay_hours": 48,
            "max_follow_ups": 3,
            "follow_up_delay_hours": 96
          }
        }
      ],
      "progression_rules": {
        "response_required": true,
        "min_stage_duration_hours": 72,
        "max_stage_duration_hours": 504
      }
    }
  },
  "default_initial_stage": "awareness",
  "completion_conditions": {
    "all_stages_completed": true,
    "specific_response_received": "accept_proposal"
  },
  "metadata": {
    "created_by": "sales_team",
    "version": "1.0.2",
    "tags": ["b2b", "saas", "lead_nurturing"]
  }
}
```

### Support Campaign Template

```json
{
  "_id": "support_followup_template_001",
  "name": "Customer Support Follow-up",
  "type": "support",
  "description": "Follow up with customers after support tickets are resolved",
  "stages": {
    "initial_followup": {
      "name": "Initial Follow-up",
      "description": "Check if the customer's issue has been resolved",
      "messages": [
        {
          "template": "Hi {{recipient.first_name}}, I wanted to follow up on your recent support ticket #{{ticket.id}} regarding {{ticket.subject}}. Has the issue been resolved to your satisfaction?",
          "timing": {
            "delay_hours": 24,
            "max_follow_ups": 1,
            "follow_up_delay_hours": 48
          }
        }
      ],
      "progression_rules": {
        "response_required": true,
        "min_stage_duration_hours": 24,
        "max_stage_duration_hours": 96
      }
    },
    "feedback": {
      "name": "Feedback Collection",
      "description": "Collect feedback about the support experience",
      "messages": [
        {
          "template": "Thanks for confirming. Would you mind taking a quick moment to rate your support experience from 1-5, with 5 being excellent?",
          "timing": {
            "delay_hours": 4,
            "max_follow_ups": 1,
            "follow_up_delay_hours": 48
          }
        }
      ],
      "progression_rules": {
        "response_required": true,
        "min_stage_duration_hours": 4,
        "max_stage_duration_hours": 72
      }
    },
    "satisfaction": {
      "name": "Satisfaction Review",
      "description": "Address any remaining concerns or thank for positive feedback",
      "messages": [
        {
          "template": "Thank you for your rating of {{response.rating}}. Is there anything else we could improve about our support process?",
          "conditional_templates": [
            {
              "condition": "response.rating < 4",
              "template": "I'm sorry to hear your experience wasn't ideal. Would you be willing to share what we could have done better?"
            },
            {
              "condition": "response.rating >= 4",
              "template": "Great to hear you had a positive experience! Thank you for your feedback."
            }
          ],
          "timing": {
            "delay_hours": 4,
            "max_follow_ups": 0
          }
        }
      ],
      "progression_rules": {
        "response_required": false,
        "min_stage_duration_hours": 4,
        "max_stage_duration_hours": 48
      }
    }
  },
  "default_initial_stage": "initial_followup",
  "completion_conditions": {
    "all_stages_completed": true
  },
  "metadata": {
    "created_by": "support_team",
    "version": "1.1.0",
    "tags": ["customer_support", "feedback", "satisfaction"]
  }
}
```

## Campaign Document Example

When a new campaign is created, it references a template and specifies recipients:

```json
{
  "_id": "campaign_q3_lead_nurturing_001",
  "name": "Q3 Enterprise Lead Nurturing",
  "template_id": "sales_campaign_template_001",
  "type": "sales",
  "initial_stage": "awareness",
  "recipients": [
    "user_123456",
    "user_234567",
    "user_345678"
  ],
  "context_data": {
    "company.product_name": "CloudScale Analytics",
    "company.value_proposition": "improved data analytics performance"
  },
  "schedule": {
    "start_date": "2023-07-01T09:00:00Z",
    "end_date": "2023-09-30T23:59:59Z"
  },
  "status": "scheduled",
  "conversation_states_initialized": false,
  "metadata": {
    "owner": "sales_team_east",
    "priority": "high",
    "tags": ["enterprise", "q3_2023"]
  },
  "created_at": "2023-06-15T14:32:10Z",
  "created_by": "user_admin_001"
}
```

## Campaign Manager Configuration Examples

### Basic Configuration (docker-compose.yml)

```yaml
version: '3'

services:
  communication-base:
    image: communication-base:latest
    environment:
      # MongoDB Configuration
      MONGODB_URI: "mongodb://mongodb:27017"
      MONGODB_DATABASE: "communication_service"
      
      # Campaign Manager Configuration
      CAMPAIGN_MAX_BATCH_SIZE: 100
      CAMPAIGN_STAGE_DELAY_FACTOR: 1.0
      CAMPAIGN_RETRY_DELAY_SECONDS: 300
      CAMPAIGN_METRICS_TTL_SECONDS: 600
      CAMPAIGN_PROCESSING_THREADS: 4
      CAMPAIGN_POLLING_INTERVAL_SECONDS: 60
      
      # Logging
      LOG_LEVEL: "INFO"
      
    depends_on:
      - mongodb
    restart: unless-stopped

  mongodb:
    image: mongo:latest
    volumes:
      - mongodb_data:/data/db
    ports:
      - "27017:27017"
    restart: unless-stopped

volumes:
  mongodb_data:
```

### Production Configuration (Kubernetes ConfigMap)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: communication-base-config
  namespace: microservices
data:
  # MongoDB Configuration
  MONGODB_URI: "mongodb://mongodb-service.mongodb.svc.cluster.local:27017"
  MONGODB_DATABASE: "communication_service"
  
  # Campaign Manager Configuration
  CAMPAIGN_MAX_BATCH_SIZE: "200"
  CAMPAIGN_STAGE_DELAY_FACTOR: "1.0"
  CAMPAIGN_RETRY_DELAY_SECONDS: "300"
  CAMPAIGN_METRICS_TTL_SECONDS: "900"
  CAMPAIGN_PROCESSING_THREADS: "8"
  CAMPAIGN_POLLING_INTERVAL_SECONDS: "30"
  
  # Worker Configuration
  WORKER_THREADS: "12"
  MAX_CONCURRENT_CONVERSATIONS: "500"
  
  # Observability
  LOG_LEVEL: "INFO"
  ENABLE_METRICS: "true"
  METRICS_PORT: "9090"
```

## Stage Progression Rules

The Campaign Manager evaluates stage progression based on rules defined in the campaign template. Here's how different types of rules are configured:

### Time-Based Progression

```json
"progression_rules": {
  "response_required": false,
  "min_stage_duration_hours": 24,
  "max_stage_duration_hours": 72,
  "auto_advance_after_max_duration": true
}
```

### Response-Based Progression

```json
"progression_rules": {
  "response_required": true,
  "specific_response_required": "appointment_accepted",
  "min_stage_duration_hours": 0,
  "max_stage_duration_hours": 168,
  "max_follow_ups": 3,
  "advance_on_failure": true
}
```

### Hybrid Progression

```json
"progression_rules": {
  "response_required": true,
  "min_responses_required": 2,
  "min_stage_duration_hours": 48,
  "max_stage_duration_hours": 168,
  "advance_on_failure": false,
  "escalation_after_hours": 120,
  "escalation_action": "notify_manager"
}
```

## Monitoring Configuration

The Campaign Manager exposes metrics that can be collected by Prometheus. Example Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'communication-base'
    scrape_interval: 15s
    static_configs:
      - targets: ['communication-base:9090']
    metrics_path: '/metrics'
```

Common metrics exposed by the Campaign Manager:

```
# HELP communication_conversations_initialized Number of conversations initialized
# TYPE communication_conversations_initialized counter
communication_conversations_initialized{campaign_type="sales"} 1250

# HELP communication_stages_advanced Number of conversation stages advanced
# TYPE communication_stages_advanced counter
communication_stages_advanced{campaign_type="sales",from_stage="awareness",to_stage="consideration"} 624

# HELP communication_conversations_completed Number of conversations completed
# TYPE communication_conversations_completed counter
communication_conversations_completed{campaign_type="sales",result="success"} 315
communication_conversations_completed{campaign_type="sales",result="failed"} 42

# HELP communication_stage_duration_seconds Time spent in each stage
# TYPE communication_stage_duration_seconds histogram
communication_stage_duration_seconds{campaign_type="sales",stage="awareness",bucket="le_24h"} 112
communication_stage_duration_seconds{campaign_type="sales",stage="awareness",bucket="le_48h"} 298
communication_stage_duration_seconds{campaign_type="sales",stage="awareness",bucket="le_72h"} 425
```

## Advanced Configuration

### Custom Stage Progression Logic

To implement custom stage progression logic, extend the Campaign Manager with a specialized subclass:

```python
class CustomCampaignManager(CampaignManager):
    """
    Custom Campaign Manager with specialized progression logic.
    """
    
    async def evaluate_stage_progression(
        self, 
        conversation_id: str,
        conversation_state: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        # Get the standard evaluation result
        should_progress, next_stage, updated_state = await super().evaluate_stage_progression(
            conversation_id, conversation_state
        )
        
        # Apply custom logic
        if conversation_state.get("campaign_type") == "enterprise_sales":
            # Custom enterprise sales progression logic
            if conversation_state.get("current_stage") == "decision":
                # Check if deal size exceeds threshold
                if conversation_state.get("context", {}).get("deal_size", 0) > 100000:
                    # Require additional approval stage
                    next_stage = "executive_approval"
                    should_progress = True
        
        return should_progress, next_stage, updated_state
```

### Scaling Configuration

For high-volume campaigns, consider these additional configuration parameters:

```yaml
# High-volume campaign processing
CAMPAIGN_MAX_BATCH_SIZE: 500
CAMPAIGN_PROCESSING_THREADS: 16
WORKER_CONCURRENT_TASKS: 32
DB_CONNECTION_POOL_SIZE: 50
DB_MAX_IDLE_TIME_MS: 30000
CAMPAIGN_METRICS_SAMPLE_RATE: 0.1  # Sample only 10% of conversations for metrics
```

## Troubleshooting

### Common Configuration Issues

1. **Slow Campaign Processing**
   - Check `CAMPAIGN_MAX_BATCH_SIZE` - may be too large
   - Verify MongoDB connection pool settings
   - Consider increasing `CAMPAIGN_PROCESSING_THREADS`

2. **High Memory Usage**
   - Reduce `CAMPAIGN_MAX_BATCH_SIZE`
   - Implement pagination in repository queries
   - Check for memory leaks in custom extensions

3. **Database Contention**
   - Implement proper indexes for conversation state queries
   - Use bulk operations for updates
   - Consider sharding for very large deployments

### Logging Configuration

Adjust logging verbosity for debugging:

```yaml
LOG_LEVEL: "DEBUG"
LOG_FORMAT: "json"
INCLUDE_TRACE_ID: "true"
SENSITIVE_FIELDS: "message_content,recipient.email,recipient.phone"
```

## Related Documents

- [Campaign Processing](./campaign_processing.md)
- [Conversation Campaign Workflow](./conversation_campaign_workflow.md)
- [Campaign Manager Implementation](./campaign_manager_implementation.md)
- [Campaign Manager Class Diagram](./campaign_manager_class_diagram.md) 