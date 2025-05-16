# Communication Base Microservice Architecture

## Overview

The communication-base microservice is a flexible, scalable system for managing various types of communication campaigns and interactive conversations. It serves as the foundation for customer support bots, sales bots, and consultancy bots within the Prismicx platform.

## Architecture and Components

The system follows the MACH architecture (Microservices, API-first, Cloud-native, Headless) and consists of several key components:

### Core Components

1. **Repository Layer**
   - MongoDB Repository for persistent storage
   - Collections for campaigns, templates, interactions, and users
   - Asynchronous data access patterns

2. **Processing Layer**
   - Component Registry for managing processing components
   - Pipeline architecture for flexible processing flows
   - Base Component pattern for consistent component interfaces

3. **Service Layer**
   - Worker Service for processing campaigns
   - Campaign Poller for retrieving campaigns from the database
   - Session management for maintaining conversation state

4. **API Layer**
   - RESTful endpoints for campaign and template management
   - Health and metrics endpoints
   - Webhook handlers for external integrations

5. **Bot Integration**
   - Specialized bot types (sales, support, consultancy)
   - LangChain integration for conversational AI
   - Configurable conversation flows

## How Campaigns and Conversations Work

### Campaign Processing

1. **Campaign Creation**
   - Campaigns are created through the API or directly in the database
   - Each campaign includes metadata, configuration, and targeting information
   - Campaigns are initially set with "pending" status

2. **Campaign Processing**
   - The Worker Service continuously polls for pending campaigns
   - It claims campaigns by setting their status to "processing"
   - It selects the appropriate component based on campaign type
   - Components execute the campaign logic (sending emails, initiating conversations)

3. **Interactions Tracking**
   - All communications are recorded as interactions
   - Interactions include metadata, content, and recipient information
   - Responses and engagement metrics are tracked

### Conversation Handling

1. **Conversation Initiation**
   - Conversations can be initiated via campaigns or user messages
   - A session is created to maintain conversation state
   - The appropriate bot type is selected based on configuration

2. **Message Processing**
   - User messages are analyzed for intent, sentiment, and context
   - The bot's response is guided by configuration and templates
   - Conversation history is maintained in memory

3. **Conversation Stages**
   - Sales conversations follow defined stages (awareness, interest, consideration, decision)
   - Each stage has specific templates and strategies
   - The bot adapts its approach based on the current stage

## Collection Structures

### 1. Campaigns Collection

**Example:**
```json
{
  "campaign_id": "sales_q4_promo",
  "name": "Q4 Software Upgrade Promotion",
  "status": "pending",
  "type": "sales",
  "config": {
    "target_segment": "enterprise_annual",
    "offer_code": "UPGRADE23",
    "discount_percentage": 15,
    "priority": "high"
  },
  "created_at": "2023-11-01T10:00:00Z"
}
```

### 2. Templates Collection

**Example:**
```json
{
  "template_id": "financial_advice_initial",
  "name": "Financial Advisory Introduction",
  "content": "Hello {{user.first_name}}, I'm your financial consultant bot. Based on your {{user.account_type}} status, I'd recommend exploring our {{recommendation}} options. Would you like more information?",
  "variables": ["user.first_name", "user.account_type", "recommendation"],
  "category": "consultancy",
  "created_at": "2023-06-15T14:30:00Z"
}
```

### 3. Interactions Collection

**Example:**
```json
{
  "interaction_id": "int_78920",
  "campaign_id": "sales_q4_promo",
  "user_id": "user_5432",
  "template_id": "product_demo_offer",
  "channel": "email",
  "content_sent": "Hi John, interested in seeing how our new Enterprise Suite could save your team 20 hours per week? Book a demo with code UPGRADE23 for a 15% discount.",
  "status": "delivered",
  "response": {
    "action": "link_click",
    "timestamp": "2023-11-05T14:23:17Z",
    "details": "clicked_demo_booking"
  },
  "metrics": {
    "open_time": "2023-11-05T14:22:05Z",
    "time_to_response": 72
  },
  "created_at": "2023-11-05T09:30:00Z"
}
```

### 4. Users Collection

**Example:**
```json
{
  "user_id": "user_5432",
  "first_name": "John",
  "last_name": "Smith",
  "email": "j.smith@corpexample.com",
  "company": "Corp Solutions Inc.",
  "role": "IT Director",
  "preferences": {
    "communication_channels": ["email", "phone"],
    "contact_frequency": "monthly",
    "demo_availability": ["Tuesday", "Thursday"]
  },
  "history": {
    "current_plan": "business_50",
    "contract_renewal": "2024-03-15",
    "previous_purchases": [
      {"product": "basic_crm", "date": "2022-04-10"},
      {"product": "team_collab", "date": "2023-01-22"}
    ],
    "sales_interactions": 12
  },
  "created_at": "2022-04-01T09:15:00Z"
}
```

## Configuration Management

The system uses a comprehensive configuration management approach:

1. **Bot Configuration**
   - Each bot type (sales, support, consultancy) has specific configuration
   - Configuration includes LLM settings, memory parameters, and conversation strategies
   - Configuration is validated via Pydantic models

2. **Campaign Configuration**
   - Campaigns have type-specific configuration
   - Sales campaigns include stage definitions and processing settings
   - Configuration guides the conversation flow

3. **Templates**
   - Message templates for different channels
   - Conversation templates for different stages
   - Analysis templates for processing user messages

## End-to-End Workflow Examples

### Example 1: Sales Campaign Workflow

1. **Campaign Creation**
   ```json
   {
     "name": "Q4 Enterprise Software Sales",
     "type": "sales_conversation",
     "config": {
       "bot_type": "sales",
       "initial_message": "Hi {{user.first_name}}, I noticed you've been using our basic plan. Would you be interested in learning about the enterprise features that could help your team scale?",
       "conversation_goals": ["identify_needs", "present_solution", "handle_objections", "close_sale"],
       "product_context": {
         "product_name": "Enterprise Suite",
         "key_features": ["unlimited users", "advanced analytics", "dedicated support"],
         "pricing": "$499/month"
       }
     },
     "recipients": ["user_123", "user_456"]
   }
   ```

2. **Initial Contact**
   - System sends the initial message to recipients
   - Creates a session for each potential conversation
   - Records interactions in the database

3. **User Response**
   - User replies to the message
   - System analyzes the response for intent and sentiment
   - Bot determines the appropriate next step based on campaign configuration

4. **Ongoing Conversation**
   - Bot uses the session to maintain context
   - Responses are guided by the sales stage and campaign goals
   - Each message and response is tracked as an interaction

5. **Conversion or Close**
   - Conversation concludes with a sale or follow-up action
   - Campaign is marked as completed
   - Results are recorded for analysis

### Example 2: Customer Support Workflow

1. **User Initiates Support Request**
   - User sends a support message
   - System creates a new session
   - Support bot is activated

2. **Issue Classification**
   - Bot analyzes the message to classify the issue
   - Retrieves relevant knowledge base articles
   - Determines if it can handle the issue or should escalate

3. **Resolution Attempt**
   - Bot provides guidance based on the issue type
   - Walks the user through troubleshooting steps
   - Records all interactions

4. **Follow-up**
   - After resolution, system sends a satisfaction survey
   - Tracks the feedback as part of the interaction history
   - Uses the feedback to improve future support

## Architectural Benefits

1. **Separation of Concerns**
   - Clean separation between request objects (campaigns) and supporting data
   - Each component has a single responsibility
   - Processing logic is isolated from storage concerns

2. **Scalability**
   - Stateless workers can be scaled horizontally
   - Database-driven coordination prevents duplicate processing
   - Asynchronous processing for better throughput

3. **Flexibility**
   - Component-based design allows easy extension
   - Campaign types can be added without changing core architecture
   - Template-driven approach for consistent yet customizable communications

4. **Reliability**
   - Robust error handling and retry mechanisms
   - Comprehensive logging and metrics
   - Clear state transitions for campaigns and interactions

This architecture enables sophisticated communication workflows while maintaining clean separation between different aspects of the system, making it maintainable, extensible, and powerful. 