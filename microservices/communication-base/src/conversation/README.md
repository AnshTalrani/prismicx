# Conversation Flow Management System

This module provides a comprehensive conversation flow management system for AI-powered chatbots, enabling structured, stateful conversations with dynamic transitions and context tracking.

## Overview

The conversation flow management system orchestrates the entire lifecycle of a conversation, from initial greeting to closing, managing:

- State transitions and business logic
- Conversation context and persistence
- Integration with language models and adapters
- Middleware processing of messages and responses
- Human-like response characteristics

The system is designed to support multiple bot types (Sales, Consultancy, Support) with domain-specific conversation flows while sharing common infrastructure.

## Architecture

The system follows a modular architecture with these key components:

### Core Components

1. **Conversation Manager (`manager.py`)**: 
   - Central orchestration layer
   - Initializes and coordinates all other components
   - Processes incoming messages and generates responses
   - Tracks active conversations

2. **State Machine (`state/state_machine.py`)**: 
   - Manages conversation state transitions
   - Executes state-specific logic
   - Loads state definitions from configuration

3. **Context Store (`context/context_store.py`)**: 
   - Maintains conversation context
   - Handles persistence and retrieval
   - Manages message history and entity tracking

4. **Transition Engine (`transitions/engine.py`)**: 
   - Evaluates transition conditions
   - Determines state transitions based on message content and context
   - Provides extensible condition types

5. **Middleware Pipeline (`middleware/pipeline.py`)**: 
   - Applies pre and post-processors to messages and responses
   - Handles intent detection, entity extraction, sentiment analysis, etc.
   - Enables bot-specific processing

### Data Models

1. **Context Models (`context/models.py`)**: 
   - Defines structured data types for conversation context
   - Provides serialization/deserialization
   - Ensures consistency across the system

### Conversation States

1. **State Definitions (`states/`)**: 
   - Bot-specific state definitions
   - Common state definitions shared across bot types
   - State handler implementations

## Key Features

### State-based Conversation Flow

The system uses a state machine to manage conversations, with each state representing a specific phase of the conversation. States define:

- Required entities to be gathered
- Possible transitions to other states
- Adapters to be activated
- Default responses
- RAG integration settings

### Dynamic Transitions

Transitions between states occur based on evaluating conditions such as:

- Intent matching
- Keyword presence
- Entity detection
- State duration
- Message count
- Context values

### Middleware Processing

The middleware pipeline enables extending the system with:

- Intent detection
- Entity extraction
- Sentiment analysis
- Message summarization
- Response formatting
- Response enhancement for human-like interaction

### Context Management

The context store maintains conversation state and history:

- Messages and their metadata
- Extracted entities
- User information
- Detected intents
- Analytics and tracking

### Human-like Response Generation

The system supports realistic conversation by:

- Adding typing indicators and delays
- Personalizing responses based on user information
- Including contextual awareness
- Enhancing responses based on sentiment and conversation history

## Usage

### Basic Usage

```python
# Initialize the conversation manager
conversation_manager = ConversationManager()

# Process a message
response = await conversation_manager.process_message(
    message="Hello, I need help with your product",
    session_id="user123-session456",
    user_id="user123",
    bot_type="support",
    platform="web"
)

# Response contains text and metadata
print(response["text"])
```

### Custom State Handlers

You can extend the system with custom state handlers:

```python
# Define a custom state handler
async def custom_greeting_handler(state_name, message, context, **kwargs):
    # Custom logic here
    return {
        "response": "Custom greeting response",
        "context_updates": {"some_key": "some_value"},
        "adapters": ["custom_adapter"],
        "use_rag": True
    }

# Register the custom handler
from src.conversation.states import STATE_HANDLERS
STATE_HANDLERS["support"]["greeting"] = custom_greeting_handler
```

### Custom Middleware

You can add custom middleware processors:

```python
# Define a custom pre-processor
async def custom_processor(message, context, bot_type):
    # Process message
    return processed_message, context_updates

# Register the processor
middleware_pipeline = conversation_manager.middleware_pipeline
middleware_pipeline.register_pre_processor(custom_processor, bot_types=["sales"])
```

## Integration Points

The conversation system integrates with:

1. **LLM Manager**: For language model generation
2. **Adapter Manager**: For context-specific model adaptation
3. **RAG Integration**: For knowledge retrieval during conversations
4. **Configuration Integration**: For loading settings and state definitions

## Future Enhancements

- Multi-modal conversation support (images, voice, etc.)
- A/B testing of conversation flows
- Learning-based transition optimization
- Advanced analytics and conversation insights
- Enhanced summarization for long conversations 