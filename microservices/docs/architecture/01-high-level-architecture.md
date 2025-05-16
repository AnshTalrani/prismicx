# High-Level Architecture Diagram

## Overview

This document provides a high-level architecture view of our microservices ecosystem, showing how the different services interact within the MACH architecture framework.

## MACH Architecture Principles

Our architecture follows MACH principles:
- **M**icroservices-based: Independent services with focused responsibilities
- **A**PI-first: All services expose and consume standardized APIs
- **C**loud-native: Designed for containerized deployment and scalability
- **H**eadless: Clear separation between frontend and backend concerns

## System Architecture Diagram

```mermaid
graph TD
    subgraph Clients
        web[Web Application]
        mobile[Mobile Application]
        ext[External Systems]
    end

    subgraph API Gateway
        gateway[API Gateway / BFF]
    end

    subgraph Microservices
        subgraph Content Generation
            generative[Generative Base Service]
            templates[Template Service]
        end
        
        subgraph User Management
            user[User Service]
            auth[Authentication Service]
        end
        
        subgraph Content Management
            content[Content Service]
            media[Media Service]
        end
        
        subgraph Analytics
            analytics[Analytics Service]
            insights[Insights Service]
        end
    end

    subgraph Data Layer
        subgraph Databases
            mongodb[(MongoDB)]
            redis[(Redis Cache)]
        end
        
        subgraph Message Brokers
            queue[Message Queue]
        end
    end

    %% Client connections
    web --> gateway
    mobile --> gateway
    ext --> gateway
    
    %% Gateway to services
    gateway --> generative
    gateway --> templates
    gateway --> user
    gateway --> auth
    gateway --> content
    gateway --> media
    gateway --> analytics
    gateway --> insights
    
    %% Service interconnections
    generative --> templates
    insights --> analytics
    content --> media
    
    %% Services to data layer
    generative --> mongodb
    generative --> redis
    generative --> queue
    templates --> mongodb
    user --> mongodb
    auth --> redis
    auth --> mongodb
    content --> mongodb
    media --> mongodb
    analytics --> mongodb
    analytics --> queue
    insights --> mongodb
    insights --> queue
```

## Service Responsibilities

| Service | Primary Responsibility | Key Features |
|---------|------------------------|--------------|
| Generative Base | Process context-based content generation | Component-based pipeline, template processing |
| Template Service | Manage and serve content templates | Template versioning, validation, rendering |
| User Service | Manage user profiles and preferences | User CRUD, preferences, profiles |
| Authentication Service | Handle user authentication and authorization | OAuth, JWT, role-based access |
| Content Service | Manage structured content | Content CRUD, workflows, versioning |
| Media Service | Store and process media assets | Image/video processing, CDN integration |
| Analytics Service | Collect and process analytics data | Event tracking, aggregation, reporting |
| Insights Service | Generate insights from analytics data | ML-based insights, recommendations |

## Communication Patterns

Our microservices employ several communication patterns:

1. **Synchronous REST API Calls**: For immediate request-response needs
2. **Asynchronous Messaging**: For event-driven communication via message queues
3. **Database Integration**: For data-level integration when necessary

## Infrastructure Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| API Gateway | Route and transform API requests | API Gateway (e.g., Kong, AWS API Gateway) |
| MongoDB | Primary data storage | MongoDB Atlas |
| Redis | Caching and temporary storage | Redis |
| Message Queue | Asynchronous communication | RabbitMQ / Kafka |
| Container Orchestration | Manage service instances | Kubernetes |
| Observability | Monitoring and tracing | Prometheus, Jaeger, ELK |

## Deployment View

```mermaid
graph TD
    subgraph "Production Environment"
        subgraph "Kubernetes Cluster"
            subgraph "Namespace: API"
                api_gateway[API Gateway]
            end
            
            subgraph "Namespace: Services"
                generative_prod[Generative Service]
                templates_prod[Template Service]
                user_prod[User Service]
                %% Other services
            end
            
            subgraph "Namespace: Data"
                mongodb_prod[(MongoDB)]
                redis_prod[(Redis)]
                mq_prod[Message Queue]
            end
        end
    end
    
    subgraph "Staging Environment"
        %% Similar structure to production
        staging[Staging Components]
    end
    
    subgraph "Development Environment"
        %% Local development environment
        dev[Development Components]
    end
    
    %% Deployment flow
    dev -->|Promotion| staging
    staging -->|Promotion| generative_prod
    staging -->|Promotion| templates_prod
    staging -->|Promotion| user_prod
```

## Next Steps

For more detailed architecture information, refer to:
- [Component Architecture](02-component-architecture.md)
- [Data Flow Diagram](03-data-flow-diagram.md)
- [Database Schema Documentation](09-database-schema.md) 