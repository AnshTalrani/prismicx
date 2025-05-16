# Retrieval-Augmented Generation (RAG) System

This directory contains the implementation of a hybrid RAG system that combines custom components with LangChain integration.

## Architecture Overview

The RAG system architecture uses a hybrid approach:

1. **Custom Components**: Core functionality implemented specifically for our communication platform
2. **LangChain Integration**: Standardized interfaces and advanced components from LangChain

```
┌─────────────────────────────────────────┐
│            RAG Coordinator              │
│                                         │
│  ┌───────────┐ ┌───────────┐ ┌────────┐ │
│  │ User      │ │ Vector    │ │Database│ │
│  │ Details   │ │ Store     │ │RAG     │ │
│  │ RAG       │ │ RAG       │ │        │ │
│  └───────────┘ └───────────┘ └────────┘ │
└───────────────────┬─────────────────────┘
                    │
        ┌───────────▼───────────┐
        │  LangChain Integration│
        │                       │
        │  ┌─────────────────┐  │
        │  │ Chains & Prompts│  │
        │  └─────────────────┘  │
        │  ┌─────────────────┐  │
        │  │Document Process.│  │
        │  └─────────────────┘  │
        │  ┌─────────────────┐  │
        │  │Memory Components│  │
        │  └─────────────────┘  │
        └───────────┬───────────┘
                    │
        ┌───────────▼───────────┐
        │    LLM Integration    │
        └───────────────────────┘
```

## Key Components

### 1. RAG Coordinator (`rag_coordinator.py`)

Central orchestration component that manages multiple retrieval sources:

- Coordinates retrieval from User Details, Vector Stores, and Databases
- Handles asynchronous parallel retrieval
- Provides unified interfaces for bot-specific retrieval strategies

### 2. Specialized RAG Services

Bot-specific retrieval services that access different data sources:

- **User Details RAG** (`user_details_rag.py`): Retrieves user-specific information from the User Details microservice
- **Vector Store RAG** (`vector_store_rag.py`): Handles semantic search through vector embeddings
- **Database RAG** (`database_rag.py`): Queries structured databases for relevant information

### 3. Query Enhancement

Components for improving query quality:

- **Query Preprocessor** (`query_preprocessor.py`): Enhances queries before retrieval
- **Topic Mapper** (`topic_mapper.py`): Maps queries to relevant topics

### 4. Document Processing

Components for document handling:

- **Document Loaders** (`document_loaders.py`): Loads documents from various sources
- **Vector Store Service** (`vector_store_service.py`): Manages vector databases

### 5. LangChain Integration (`langchain_integration.py`)

Bridge between our custom RAG system and LangChain's components:

- Creates and manages LangChain retrieval chains
- Provides conversational retrieval capabilities
- Handles document compression and reranking
- Manages memory for conversation context

## Hybrid Integration Approach

### What Our Custom Code Handles:

- Integration with our configuration system
- Bot-specific business logic
- Microservice communication
- RAG coordination and orchestration
- User context and authorization

### What LangChain Provides:

- Document schema standardization
- Retriever interfaces
- Chain composition
- Prompt templating
- Memory management
- Document compression

## Configuration

The RAG system is configured through the configuration system:

```yaml
# Example rag section in bot config
rag:
  # Sources to use
  sources: ["vector_store", "user_details", "database"]
  
  # Source-specific limits
  vector_store_limit: 5
  user_details_limit: 3
  database_limit: 2
  
  # Document processing
  chunk_size: 1000
  chunk_overlap: 200
  
  # Prompt templates
  document_prompt_template: "Use the following context: {context}\n\nQuestion: {question}\n\nAnswer:"
  
  # Advanced features
  use_document_compression: true
  compression_ratio: 0.75
```

## Usage Examples

### Basic Usage

```python
from src.langchain_components.rag.langchain_integration import LangChainRAGIntegration

# Initialize components
langchain_integration = LangChainRAGIntegration(
    rag_coordinator=rag_coordinator,
    llm_manager=llm_manager,
    config_integration=config_integration
)

# Run RAG chain
result = await langchain_integration.arun_rag_chain(
    query="What products do you recommend for me?",
    bot_type="sales",
    session_id="session123",
    user_id="user456",
    chain_type="conversational"
)

# Extract answer
answer = result["answer"]
```

### Conversation Flow Integration

```python
# In conversation flow handler
async def process_user_message(message, user_id, session_id, bot_type):
    # Get or create conversation memory
    memory = langchain_integration.get_or_create_memory(session_id)
    
    # Run RAG-enhanced response generation
    result = await langchain_integration.arun_rag_chain(
        query=message,
        bot_type=bot_type,
        session_id=session_id,
        user_id=user_id,
        chain_type="conversational",
        memory=memory
    )
    
    # Process result
    response = result["answer"]
    
    # Track sources for analytics
    sources = [doc.metadata.get("source") for doc in result.get("source_documents", [])]
    
    return response, sources
```

## Bot-Specific Customization

Each bot type has specialized retrieval behavior:

- **Sales Bot**: Prioritizes user preferences and purchase history
- **Consultancy Bot**: Focuses on business context and pain points
- **Support Bot**: Emphasizes user history and support tickets

These customizations are configured through the configuration system and implemented in the specialized RAG services.

## Testing

Run the example script to see the RAG system in action:

```bash
python -m src.langchain_components.rag.example_usage
```

## Further Development

The RAG system can be extended in several ways:

1. **Additional Data Sources**: Add new specialized RAG services
2. **Advanced Reranking**: Implement more sophisticated document ranking
3. **Streaming Responses**: Add support for streaming responses
4. **Multi-stage Retrieval**: Implement iterative retrieval strategies

## Integration with Other Components

The RAG system integrates with other microservice components:

- **Configuration System**: Uses the config inheritance for bot-specific settings
- **Adapter System**: Works with the adapter system for bot-specific behavior
- **LLM Integration**: Connects with language models through the LLM manager 