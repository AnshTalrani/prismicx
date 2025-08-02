# Automation System Architecture

The automation system follows a modular event-driven architecture that supports multi-tenant isolation. The diagram below illustrates how the components interact in the context of the Management Systems microservice.

```
┌─────────────────────────────────────────────────────────────────┐
│                 Management Systems Microservice                  │
└─────────────────────────────────────────────────────────────────┘
                        │
┌─────────────┬─────────┴───────────┬───────────────┬─────────────┐
│             │                     │               │             │
▼             ▼                     ▼               ▼             ▼
┌─────────────────┐     ┌─────────────────┐  ┌─────────────┐ ┌─────────────┐
│  API Endpoints  │     │ Event Dispatcher │  │ Management  │ │ System      │
│                 │     │                 │  │ Modules     │ │ Templates    │
└─────────────────┘     └─────────────────┘  └─────────────┘ └─────────────┘
        │                       │                  │               │
        │                       │                  ▼               │
        │                       │           ┌─────────────┐        │
        │                       │           │ CRM Module  │        │
        │                       │           └─────────────┘        │
        │                       │                  │               │
        ▼                       │                  ▼               │
┌─────────────────┐             │           ┌─────────────┐        │
│  Automation     │◄────────────┘           │ Sales Module│        │
│  Service        │                         └─────────────┘        │
└─────────────────┘                                │               │
        │                                          │               │
        ▼                                          ▼               ▼
┌─────────────────┐                        ┌─────────────────┐ ┌─────────────┐
│  Automation     │◄───────────────────────┤ Data Validation │ │ Data Models │
│  Engine         │                        │ & Processing    │ │             │
└─────────────────┘                        └─────────────────┘ └─────────────┘
        │
        ▼
┌─────────────────┐
│ MongoDB         │
│ automation_rules│
└─────────────────┘
        │
        ▼
┌───────────┬───────────┬───────────┐
│ Tenant A  │ Tenant B  │ Tenant C  │
│ Rules     │ Rules     │ Rules     │
└───────────┴───────────┴───────────┘
```

## Component Interactions in Multi-Tenant Context

### Data Flow for Event Processing

```
┌────────────┐    ┌─────────────┐    ┌────────────┐    ┌────────────┐
│            │    │             │    │            │    │            │
│ Business   │    │ Management  │    │ Event      │    │ Automation │
│ Event      │───►│ Module      │───►│ Dispatcher │───►│ Engine     │
│ (tenant X) │    │ (CRM/Sales) │    │            │    │            │
│            │    │             │    │            │    │            │
└────────────┘    └─────────────┘    └────────────┘    └────────────┘
                                                              │
┌────────────┐    ┌─────────────┐    ┌────────────┐          │
│            │    │             │    │            │          │
│ Action     │◄───┤ Conditions  │◄───┤ Rule       │◄─────────┘
│ Execution  │    │ Evaluation  │    │ Retrieval  │
│            │    │             │    │ (tenant X) │
│            │    │             │    │            │
└────────────┘    └─────────────┘    └────────────┘
```

### Rule Creation Flow

```
┌────────────┐    ┌─────────────┐    ┌────────────┐    ┌────────────┐
│            │    │             │    │            │    │            │
│ Client     │    │ API         │    │ Automation │    │ MongoDB    │
│ Request    │───►│ Controller  │───►│ Service    │───►│ Storage    │
│ (tenant X) │    │             │    │            │    │ (tenant X) │
│            │    │             │    │            │    │            │
└────────────┘    └─────────────┘    └────────────┘    └────────────┘
      │                 ▲                  │
      │                 │                  ▼
      │           ┌─────────────┐    ┌────────────┐
      │           │             │    │            │
      └──────────►│ Tenant      │◄───┤ Validation │
                  │ Middleware  │    │ Logic      │
                  │             │    │            │
                  └─────────────┘    └────────────┘
```

## Key Security and Isolation Points

1. **Tenant Middleware**: Extracts tenant ID from request headers and maintains it throughout the request lifecycle
2. **Database Queries**: Always include tenant_id in queries to ensure data isolation
3. **Event Context**: Events carry tenant context to ensure proper rule selection
4. **Rule Creation**: Automatically associates rules with the requesting tenant

This architecture ensures that even though the automation system is shared across all tenants, each tenant's data, rules, and event processing remain completely isolated. 


# Automation System

The Management Systems microservice includes a powerful event-driven automation system that enables creating custom workflows based on business events. This document explains how the automation system works, focusing on its multi-tenant capabilities.

## Architecture Overview

The automation system consists of the following components:

- **Automation Engine**: Processes events and executes actions when conditions are met
- **Event Dispatcher**: Routes events between management modules and the automation engine
- **Management Modules**: Define domain-specific triggers and condition evaluation logic
- **Automation Service**: Manages automation rules and handles tenant-specific rule storage

![Automation Architecture](architecture/automation-architecture.png)

## Tenant-Specific Triggers and Actions

### Storage Model

Tenant-specific automation rules are stored in the MongoDB database, specifically in the `automation_rules` collection within the `config` database. The system ensures complete data isolation between tenants.

#### Database Structure

```
config_db
└── automation_rules
    ├── {rule_1}  // Tenant A
    ├── {rule_2}  // Tenant A
    ├── {rule_3}  // Tenant B
    └── {rule_4}  // Tenant C
```

Each rule document includes:

```json
{
  "id": "unique-rule-id",
  "tenant_id": "tenant-identifier",
  "name": "Rule Name",
  "description": "Description of the rule",
  "module_type": "crm|sales|etc",
  "trigger_id": "event_trigger_id",
  "conditions": [
    {
      "type": "condition_type",
      "field": "optional_field_name",
      "value": "comparison_value"
    }
  ],
  "actions": [
    {
      "type": "action_type",
      "parameters": {
        "param1": "value1",
        "param2": "value2"
      }
    }
  ],
  "is_active": true,
  "created_at": "2023-06-01T12:00:00Z",
  "updated_at": "2023-06-01T12:00:00Z"
}
```

### Tenant Data Isolation

The system implements multi-tenant isolation through the following mechanisms:

1. **Tenant Context in Requests**: The `TenantMiddleware` extracts the tenant ID from the `X-Tenant-ID` header and adds it to the request context.

2. **Automatic Tenant Filtering**: When retrieving rules, the tenant ID is automatically included in database queries:

   ```python
   # When querying for rules, tenant_id is automatically added
   def get_automation_rules(self, module_type=None, trigger_id=None, is_active=None):
       query = {"tenant_id": request.state.tenant_id}
       
       # Add other filters
       if module_type:
           query["module_type"] = module_type
       # ...
       
       return list(self.db_client.config.automation_rules.find(query))
   ```

3. **Tenant Assignment on Creation**: When rules are created, they are automatically associated with the current tenant:

   ```python
   rule = {
       "id": str(uuid.uuid4()),
       "tenant_id": request.state.tenant_id,  # Assigned from request context
       "name": name,
       # Other properties...
   }
   ```

This ensures that tenants can only access, modify, and trigger their own automation rules, providing complete data isolation in a multi-tenant environment.

## Event Processing Within Tenant Context

When events occur within a tenant's system:

1. The event is published with the tenant context attached
2. The automation engine queries only rules belonging to that tenant
3. Condition evaluation and action execution happen within the tenant's context

Example flow:

```
1. Tenant ABC creates Sales Opportunity
2. Event published: {event: "opportunity_created", tenant_id: "abc", data: {...}}
3. AutomationEngine receives event
4. Queries rules: db.automation_rules.find({tenant_id: "abc", trigger_id: "opportunity_created"})
5. Evaluates conditions for matched rules
6. Executes actions for rules where conditions are met
```

## Available Triggers by Module

### CRM Module Triggers

| Trigger ID | Description | Required Data |
|------------|-------------|--------------|
| contact_created | When a new contact is created | - |
| contact_updated | When a contact is updated | contact_id |
| contact_status_changed | When a contact's status changes | contact_id, old_status, new_status |
| lead_created | When a new lead is created | lead_id |

### Sales Module Triggers

| Trigger ID | Description | Required Data |
|------------|-------------|--------------|
| opportunity_created | When a new opportunity is created | opportunity_id, opportunity_name |
| opportunity_stage_changed | When an opportunity moves to a different stage | opportunity_id, old_stage, new_stage |
| deal_closed_won | When a deal is successfully closed | opportunity_id, value |
| deal_closed_lost | When a deal is lost | opportunity_id, reason |
| high_value_opportunity | When an opportunity exceeds a value threshold | opportunity_id, value |

## Available Actions

| Action Type | Description | Parameters |
|-------------|-------------|------------|
| send_notification | Sends a notification | recipient, message |
| update_status | Updates an entity's status | entity_id, new_status |
| create_task | Creates a follow-up task | title, description, due_date, assignee |

## API Reference

### List Available Triggers

```
GET /api/v1/automation/triggers
```

Optional query parameters:
- `module_type`: Filter triggers by module type

### Create Automation Rule

```
POST /api/v1/automation/rules
```

Request body:
```json
{
  "name": "Rule Name",
  "description": "Optional description",
  "module_type": "sales",
  "trigger_id": "opportunity_created",
  "conditions": [...],
  "actions": [...],
  "is_active": true
}
```

### Get Automation Rules

```
GET /api/v1/automation/rules
```

Optional query parameters:
- `module_type`: Filter by module type
- `trigger_id`: Filter by trigger ID
- `is_active`: Filter by active status

### Toggle Rule Status

```
PUT /api/v1/automation/rules/{rule_id}/toggle?is_active=true|false
```

### Delete Rule

```
DELETE /api/v1/automation/rules/{rule_id}
```

## Example: Creating a High-Value Deal Alert

```json
// Request
POST /api/v1/automation/rules
Content-Type: application/json
X-Tenant-ID: acme-corp

{
  "name": "High Value Deal Alert",
  "description": "Notify sales manager about deals over $10,000",
  "module_type": "sales",
  "trigger_id": "high_value_opportunity",
  "conditions": [
    {
      "type": "value_threshold",
      "value": 10000
    }
  ],
  "actions": [
    {
      "type": "send_notification",
      "parameters": {
        "recipient": "sales-manager@example.com",
        "message": "New high-value opportunity: {{opportunity_name}} - ${{value}}"
      }
    }
  ]
}

// Response
{
  "id": "f7d5e791-4c3a-4b8c-8b7a-23e5b4a1c6d9",
  "name": "High Value Deal Alert",
  "tenant_id": "acme-corp",
  "description": "Notify sales manager about deals over $10,000",
  "module_type": "sales",
  "trigger_id": "high_value_opportunity",
  "conditions": [...],
  "actions": [...],
  "is_active": true,
  "created_at": "2023-06-01T12:00:00Z",
  "updated_at": "2023-06-01T12:00:00Z"
}
``` 