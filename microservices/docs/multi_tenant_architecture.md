# Multi-tenant Architecture in MACH Microservices

## Overview
This document outlines the multi-tenant architecture across our microservices, reflecting recent optimizations and service-specific implementations.

## Current Architecture

### Marketing Base (Multi-tenant)
The only service maintaining full multi-tenant capabilities due to its specific requirements.

#### Implementation Details
- **Database Isolation**: Schema-based tenant isolation
```python
# Example of tenant-aware database connection
PostgresDatabase(
    connection_string=config.marketing_db_uri,
    database_name=config.marketing_db_name,
    tenant_aware=True
)
```

- **Multiple Database Types**:
  - Marketing DB (tenant-aware)
  - CRM DB (tenant-aware)
  - Product DB (tenant-aware)
  - User DB (not tenant-aware)

- **Cross-Database Operations**: Maintains tenant context across different database operations
- **Data Types**: Handles persistent data requiring strict tenant isolation
  - Marketing campaigns
  - Customer data
  - Product catalogs
  - Analytics data

### Communication Base (Session-Based)
Optimized to use session-based isolation instead of tenant context.

#### Implementation Details
- **Session Management**:
```python
class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.memory_store = {}  # Stores ConversationSummaryMemory instances

    async def get_or_create_session(self, session_id: str, user_id: str, bot_type: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "user_id": user_id,
                "bot_type": bot_type,
                "last_active": time.time()
            }
```

- **Key Features**:
  - Session-based conversation state
  - Bot-specific memory management
  - Automatic session cleanup
  - No tenant context switching

### Analysis Base (Job-Based)
Moved from schema-based isolation to job-based isolation for improved performance.

#### Implementation Details
- **Job-Based Processing**:
  - Each analysis job runs independently
  - Results stored at job level
  - No tenant context switching
  - Simplified database architecture

- **Data Flow**:
  - Input data → Job Processing → Results Storage
  - No tenant-specific schemas or configurations needed

### Generative Base (Batch-Based)
Optimized for batch processing without tenant context.

#### Implementation Details
- **Batch Processing**:
  - Template-based generation
  - Batch-level configurations
  - No tenant context switching
  - Efficient state tracking

- **Key Features**:
  - Template processing without tenant context
  - Batch-level configuration management
  - Simplified state tracking
  - Improved performance through reduced context switching

## Benefits of Current Architecture

### 1. Performance Improvements
- Eliminated unnecessary tenant context switching
- Reduced database schema switching overhead
- More efficient resource utilization
- Streamlined batch processing

### 2. Simplified Implementation
- Clearer separation of concerns
- Service-specific isolation strategies
- Reduced complexity in most services
- More maintainable codebase

### 3. Resource Optimization
- Optimized database connections
- Reduced memory overhead
- Better connection pool management
- Simplified state management

### 4. Enhanced Maintainability
- Clear data isolation boundaries
- Simplified debugging
- Easier monitoring
- Reduced complexity

## Isolation Strategies

### Database Isolation
| Service | Strategy | Reason |
|---------|----------|---------|
| Marketing Base | Schema-based | Multiple tenant-specific databases |
| Communication Base | Session-based | Conversational state isolation |
| Analysis Base | Job-based | Independent analysis tasks |
| Generative Base | Batch-based | Template-based generation |

### State Management
| Service | State Level | Implementation |
|---------|------------|----------------|
| Marketing Base | Tenant | Tenant context and schemas |
| Communication Base | Session | Session manager and memory store |
| Analysis Base | Job | Job-specific state tracking |
| Generative Base | Batch | Batch-level configuration |

## Configuration Management

### Per-Service Configuration Approach
| Service | Configuration Level | Details |
|---------|-------------------|----------|
| Marketing Base | Tenant-specific | Separate configurations per tenant |
| Communication Base | Session-specific | Bot and conversation settings |
| Analysis Base | Job-specific | Analysis parameters and settings |
| Generative Base | Batch-specific | Template and generation settings |

## Best Practices

### When to Use Tenant Context
- Multiple databases requiring isolation
- Cross-database operations
- Persistent data storage
- Tenant-specific configurations

### When to Avoid Tenant Context
- Session-based operations
- Independent job processing
- Batch processing
- Stateless operations

## Migration Guidelines

### Moving Away from Tenant Context
1. Identify isolation requirements
2. Choose appropriate isolation strategy
3. Update database access patterns
4. Remove tenant middleware
5. Simplify configuration management

### Maintaining Tenant Context
1. Ensure proper schema isolation
2. Implement robust tenant identification
3. Maintain cross-database consistency
4. Handle tenant-specific configurations

## Monitoring and Maintenance

### Key Metrics to Monitor
- Database connection usage
- Session/Job/Batch completion rates
- Resource utilization
- Error rates per isolation strategy

### Maintenance Tasks
- Regular session cleanup
- Job state management
- Batch processing optimization
- Database performance monitoring

## Future Considerations

### Potential Improvements
- Enhanced session management
- Optimized batch processing
- Improved job scheduling
- Better resource allocation

### Scaling Strategies
- Horizontal scaling of stateless services
- Session affinity for Communication Base
- Job distribution for Analysis Base
- Batch distribution for Generative Base 