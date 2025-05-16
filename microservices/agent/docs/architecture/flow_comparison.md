# Processing Flow Comparison: Individual vs. Batch

This document compares individual request processing and batch processing flows in the Agent microservice, highlighting the key differences and similarities between these two approaches.

## Visual Comparison

### Individual Request Processing Flow

```
┌────────┐    ┌─────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│ Client │───►│ Controller  │───►│ RequestService   │───►│TemplateRepository   │
└────────┘    └─────────────┘    └──────────────────┘    └─────────────────────┘
                                     │         ▲  
                                     ▼         │  
                    ┌───────────────────────────────┐    ┌─────────────────────┐         
                    │      ContextManager           │◄───┤   DefaultNLPService │
                    └───────────────┬───────────────┘    └─────────────────────┘
                                    │                          
                                    ▼                          
                        ┌───────────────────────────────┐          
                        │     MongoDB Repository        │          
                        └───────────────┬───────────────┘          
                                        │   
                                        │                
                                        ▼                 
                                  /─────────────\
                                 (    Workers    )
                                  \─────────────/         
                                        │
                                        ▼ 
                        ┌───────────────────────────────┐          
                        │    External Service           │          
                        └───────────────┬───────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │      Response to Client       │
                        │   (with context & results)    │
                        └───────────────────────────────┘
```

### Batch Processing Flow

```
┌────────┐    ┌─────────────┐    ┌──────────────────┐    
│ Client │───►│ Controller  │───►│  BatchProcessor  │    
└────────┘    └─────────────┘    └───────┬──────────┘    
                                          │             
                                          │ Immediate Response: Batch Accepted         
                                          ▼             
                         ┌────────────────────────────────┐          
                         │         ContextManager         │          
                         └────────────────┬───────────────┘          
                                          │                          
                                          ▼                          
                       ┌─────────────────────────────────────┐          
                       │ For Each Item in Batch              │          
                       │ ┌───────────────────────────────┐   │          
                       │ │   TemplateRepository          │   │
                       │ │   (with purpose_id mapping)   │   │
                       │ └───────────────────────────────┘   │
                       │              │                      │
                       │              ▼                      │
                       │ ┌───────────────────────────────┐   │
                       │ │   Create Service Context      │   │
                       │ └───────────────┬───────────────┘   │
                       │              │                      │
                       │              ▼                      │
                       │ ┌───────────────────────────────┐   │
                       │ │   MongoDB Repository          │   │
                       │ └───────────────────────────────┘   │
                       └─────────────────────────────────────┘
                                          │
                                          │ Workers poll for contexts                 
                                          ▼                          
                                     /─────────\
                                    (  Workers  )
                                     \─────────/
                                          │
                                          ▼
                         ┌────────────────────────────────┐
                         │ Optional: Notify Completion    │
                         └────────────────────────────────┘
                                          
┌────────┐    ┌─────────────┐    ┌──────────────────┐    
│ Client │───►│ Controller  │───►│  BatchRepository │ ◄── Separate Request for Status/Results
└────────┘    └─────────────┘    └───────┬──────────┘    
                                          │             
                                          ▼            
                         ┌────────────────────────────────┐          
                         │  Results to Client with        │          
                         │  Complete Context Information  │          
                         └────────────────────────────────┘          
```

## Key Differences

### 1. Request Processing Model

**Individual Request Processing**:
- Synchronous processing
- Client waits for complete result
- Direct response containing processing output and context
- NLP service used for purpose detection via keyword matching
- Single template and context per request

**Batch Processing**:
- Asynchronous processing
- Immediate acknowledgment response (202 Accepted)
- Client must make separate requests to check status/results
- Items supply their own purpose_ids or template_ids
- Multiple items processed using the same or different templates
- Shared batch context plus individual item contexts

### 2. Context Management

**Individual Request Processing**:
- Context created at start of processing
- Purpose ID determined by NLP service using keyword matching
- Template selected based on purpose ID
- Context updated throughout processing
- Results and tags added to context by service client
- Final context returned with response

**Batch Processing**:
- Batch-level context created at initialization
- Per-item contexts created during processing
- Item-level contexts inherit from batch context
- Purpose IDs or template IDs provided with batch items
- Results and tags added to individual item contexts
- All contexts preserved with results in storage

### 3. Template Selection

**Individual Request Processing**:
- If template_id is provided, use directly
- Otherwise, DefaultNLPService detects purpose_id via keyword matching
- Template retrieved by purpose_id from repository

**Batch Processing**:
- Batch items specify template_id directly, or
- Batch items provide purpose_id
- Template retrieved by either id from repository
- No NLP service involvement required for batch items

### 4. Resource Utilization

**Individual Request Processing**:
- Resources allocated for duration of single request
- Client connection remains open until processing completes
- Resource constraints can limit concurrent requests
- Better for low-latency, immediate response needs

**Batch Processing**:
- Resources distributed across time
- Better throughput for large volumes
- No long-held client connections
- Can implement throttling and prioritization
- Better for high-volume, non-interactive processes

### 5. Data Flow & Storage

**Individual Request Processing**:
- Context managed in memory during request
- No persistent storage of contexts or results (unless explicitly requested)
- Direct flow from request to response
- Simpler error propagation

**Batch Processing**:
- Requires persistent storage for batch metadata, contexts, and results
- Results and contexts retrievable long after processing
- Partial success handling (some items may succeed while others fail)
- Comprehensive status tracking and context preservation

## Example Use Cases

### Individual Processing Ideal For:

1. Interactive user interfaces requiring immediate feedback
2. Simple one-off operations with text that needs purpose detection
3. Low-latency requirements
4. Operations needing contextual information
5. Debug and development scenarios

### Batch Processing Ideal For:

1. Bulk operations with known purpose IDs (e.g., multiple social media posts)
2. Resource-intensive tasks that can be distributed
3. Operations that can tolerate higher latency
4. Background processing with complex context management
5. Scheduled or triggered workflows

## Context Management Benefits

Both processing models benefit from comprehensive context management:

1. **Traceability**: Track information across the entire processing flow
2. **Enrichment**: Build context incrementally throughout processing
3. **Tag Support**: Attach metadata tags for filtering and categorization
4. **Error Context**: Preserve context even when errors occur
5. **Analytics**: Use context data for performance and usage analysis

## Implementation Notes

When implementing features, consider:

1. **Purpose Detection**: 
   - Individual requests use DefaultNLPService for purpose detection when template ID isn't provided
   - Batch items should provide purpose_id or template_id directly
   - Keep keyword dictionaries updated for accurate purpose detection

2. **Context Management**:
   - Create contexts at the start of processing
   - Update contexts at key processing stages
   - Store relevant data, results, and tags in contexts
   - Return or store full contexts with results

3. **Template Selection**:
   - Use purpose_id → template mapping for flexibility
   - Allow direct template_id specification for performance
   - Ensure template repository can retrieve by either ID type

4. **Choose Appropriate Model**: Select individual or batch processing based on:
   - Volume of items to process
   - Latency requirements
   - Whether purpose detection is needed
   - Resource constraints

5. **Error Handling**:
   - Capture errors in context
   - Provide contextual information with error responses

## Conclusion

The Agent microservice supports both individual and batch processing flows, with appropriate context management and purpose detection strategies for each approach. Individual processing leverages the DefaultNLPService for purpose detection via keyword matching, while batch processing expects purpose IDs or template IDs to be provided with each item. Both approaches maintain context throughout processing, ensuring that results, tags, and other contextual information are properly captured and returned to clients. 