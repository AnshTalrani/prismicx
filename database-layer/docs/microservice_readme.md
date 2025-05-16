# PostgreSQL Multi-Tenant Database Implementation Guide

> **IMPORTANT UPDATE**: This guide provides information about PostgreSQL multi-tenant implementation. For a comprehensive reference of all database services, their APIs, and usage details, please refer to the new [Database Services Reference](database-services-reference.md) document.

This guide outlines how to implement microservices that work with our PostgreSQL multi-tenant database architecture. Use this as your reference when creating or modifying microservices in the system.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Database Setup](#database-setup)
- [Microservice Implementation](#microservice-implementation)
- [Tenant Context Management](#tenant-context-management)
- [Docker Implementation](#docker-implementation)
- [Code Examples](#code-examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Architecture Overview

Our system uses PostgreSQL for all database needs:

- **PostgreSQL for Tenant Registry**: Used by the Tenant Management Service for tenant information
- **PostgreSQL for User Data**: Used by the User Data Service for structured user information
- **PostgreSQL for Microservices**: Each microservice can use PostgreSQL with schema-based multi-tenant isolation

The PostgreSQL instances are configured as:
- **Per-Service Databases**: Each microservice has its own database (e.g., `tenant_db`, `user_db`, `crm_db`, `product_db`)
- **Tenant Isolation**: Tenant data is isolated in separate schemas within service databases
- **Central User Management**: A system-wide `user_db` manages authentication, authorization, and user data

### Data Isolation Models

1. **System-wide data** (single database, single schema):
   - `tenant_db`: Central tenant registry and configuration
   - `user_db`: Central identity, authentication, and user management
   - Located in the default public schema
   - Shared across all services

2. **Multi-tenant data** (shared database, separate schema per tenant):
   - `crm_db`, `product_db`, etc.
   - Each tenant gets a dedicated schema: `tenant_<tenant_id>`
   - Complete logical isolation between tenants

## Database Setup

### Initialize Databases

1. Create and initialize each service database using the provided scripts:

```bash
# Initialize tenant registry database
psql -U postgres -f database-layer/init-scripts/postgres/01-init-tenant-db.sql

# Initialize user database (system-wide)
psql -U postgres -f database-layer/init-scripts/postgres/01-init-system-db.sql

# Initialize CRM database (multi-tenant)
psql -U postgres -f microservices/crm-service/init-scripts/01-init-crm-db.sql

# Initialize product database (multi-tenant)
psql -U postgres -f microservices/product-service/init-scripts/01-init-product-db.sql
```

### Database Users and Permissions

The initialization scripts create the following database roles:

- `tenant_service`: For PostgreSQL tenant registry access
- `user_service`: For PostgreSQL user database
- `crm_admin`, `crm_readonly`: For CRM database 
- `product_admin`, `product_readonly`: For product database

Create service-specific users with appropriate permissions:

```sql
-- Example for creating a product service user
CREATE USER product_service WITH PASSWORD 'your_secure_password';
GRANT product_readonly TO product_service;
```

## Microservice Implementation

### Database Configuration

Each microservice should include database configuration similar to this:

```yaml
# Example database.yml for a PostgreSQL service
database:
  host: ${DB_HOST:localhost}
  port: ${DB_PORT:5432}
  name: ${DB_NAME:service_db}  # e.g., product_db, crm_db
  username: ${DB_USERNAME:service_user}
  password: ${DB_PASSWORD:password}
  min_pool_size: ${DB_MIN_POOL_SIZE:5}
  max_pool_size: ${DB_MAX_POOL_SIZE:20}
  # For tenant-specific services only:
  tenant_aware: ${DB_TENANT_AWARE:true}
  # For central services:
  tenant_aware: false
  
# For accessing tenant information
tenant_management:
  url: ${TENANT_MGMT_URL:http://tenant-mgmt-service:8501}
  timeout_ms: 5000
```

### Dependencies

Include the following dependencies in your service:

```xml
<!-- Example Maven dependencies -->
<dependencies>
    <!-- PostgreSQL Driver -->
    <dependency>
        <groupId>org.postgresql</groupId>
        <artifactId>postgresql</artifactId>
        <version>42.6.0</version>
    </dependency>
    
    <!-- Connection Pooling -->
    <dependency>
        <groupId>com.zaxxer</groupId>
        <artifactId>HikariCP</artifactId>
        <version>5.0.1</version>
    </dependency>
    
    <!-- Add ORM or JDBC libraries as needed -->
</dependencies>
```

## Tenant Context Management

### Tenant Identification

Identify tenants using one of these methods:

1. **Header-based**: Extract from HTTP headers
   ```
   X-Tenant-ID: tenant_test001
   ```

2. **Subdomain-based**: Parse from the request domain
   ```
   tenant-name.example.com → tenant_tenant_name
   ```

3. **Path-based**: Extract from URL path
   ```
   /api/tenants/{tenant-id}/resources
   ```

### Implementing Tenant Context

Create a tenant context manager:

```java
public class TenantContext {
    private static final ThreadLocal<String> CURRENT_TENANT = new ThreadLocal<>();
    
    public static void setCurrentTenant(String tenant) {
        CURRENT_TENANT.set(tenant);
    }
    
    public static String getCurrentTenant() {
        return CURRENT_TENANT.get();
    }
    
    public static void clear() {
        CURRENT_TENANT.remove();
    }
}
```

### Request Interceptor

Implement a request interceptor to set the tenant context:

```java
@Component
public class TenantRequestInterceptor implements HandlerInterceptor {
    
    @Autowired
    private TenantClient tenantClient; // Client to call tenant management service
    
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        // Extract tenant identifier (header, domain, etc.)
        String tenantId = request.getHeader("X-Tenant-ID");
        
        if (tenantId != null) {
            // Look up tenant information from the tenant management service
            TenantInfo tenantInfo = tenantClient.getTenantInfo(tenantId);
            if (tenantInfo != null) {
                TenantContext.setCurrentTenant(tenantInfo.getSchemaName());
                return true;
            }
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            return false;
        }
        
        return true; // Non-tenant endpoints can proceed
    }
    
    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, 
                               Object handler, Exception ex) {
        // Clear context after request completes
        TenantContext.clear();
    }
}
```

## Docker Implementation

All services in the database layer are containerized using Docker. Here's how to set up your microservice to interact with the database layer:

### Connecting to the Tenant Management Service

```yaml
# Example docker-compose.yml entry for a microservice
services:
  my-microservice:
    build: .
    environment:
      - TENANT_MGMT_URL=http://tenant-mgmt-service:8501
      # Other environment variables
    networks:
      - service-network
      - tenant-network  # Connect to tenant management network
    depends_on:
      - tenant-mgmt-service  # Optional, if direct dependency needed
```

### Network Configuration

Your microservice should connect to the appropriate networks:

```yaml
networks:
  service-network:  # Your microservice's network
    driver: bridge
  tenant-network:  # External network from database layer
    external: true
    name: database-layer_tenant-db-net  # Adjust name as needed
```

### Sample Environment Variables

Configure your microservice with these environment variables:

```
# Tenant Management Service
TENANT_MGMT_URL=http://tenant-mgmt-service:8501

# User Data Service
USER_DATA_URL=http://user-data-service:8502

# PostgreSQL Connection (if using direct connection)
DB_HOST=postgres-system
DB_PORT=5432
DB_USER=service_user
DB_PASSWORD=password
DB_NAME=service_db
```

## Code Examples

### Tenant-Aware DataSource Configuration

```java
@Configuration
public class DataSourceConfig {

    @Bean
    @Primary
    public DataSource dataSource(
            @Value("${database.host}") String host,
            @Value("${database.port}") int port, 
            @Value("${database.name}") String dbName,
            @Value("${database.username}") String username,
            @Value("${database.password}") String password,
            @Value("${database.tenant_aware:false}") boolean tenantAware) {
        
        if (tenantAware) {
            return new TenantAwareDataSource(host, port, dbName, username, password);
        } else {
            return createSingleDataSource(host, port, dbName, username, password);
        }
    }
    
    private DataSource createSingleDataSource(String host, int port, String dbName, 
                                            String username, String password) {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(String.format("jdbc:postgresql://%s:%d/%s", host, port, dbName));
        config.setUsername(username);
        config.setPassword(password);
        return new HikariDataSource(config);
    }
}
```

### Tenant-Aware DataSource Implementation

```java
public class TenantAwareDataSource implements DataSource {
    private final Map<String, DataSource> tenantDataSources = new ConcurrentHashMap<>();
    private final String host;
    private final int port;
    private final String dbName;
    private final String username;
    private final String password;
    
    public TenantAwareDataSource(String host, int port, String dbName, String username, String password) {
        this.host = host;
        this.port = port;
        this.dbName = dbName;
        this.username = username;
        this.password = password;
    }
    
    @Override
    public Connection getConnection() throws SQLException {
        String tenantId = TenantContext.getCurrentTenant();
        if (tenantId == null) {
            throw new SQLException("No tenant specified");
        }
        
        DataSource dataSource = tenantDataSources.computeIfAbsent(tenantId, 
            key -> createDataSourceForTenant(key));
        
        Connection connection = dataSource.getConnection();
        connection.createStatement().execute("SET search_path TO " + tenantId);
        return connection;
    }
    
    private DataSource createDataSourceForTenant(String tenantId) {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(String.format("jdbc:postgresql://%s:%d/%s", host, port, dbName));
        config.setUsername(username);
        config.setPassword(password);
        config.setConnectionInitSql("SET search_path TO " + tenantId);
        return new HikariDataSource(config);
    }
    
    @Override
    public Connection getConnection(String username, String password) throws SQLException {
        // Implementation with custom credentials
    }
    
    // Other required methods...
}
```

### Interacting with the Tenant Management Service

```java
@Service
public class TenantClient {
    
    private final WebClient webClient;
    
    public TenantClient(@Value("${tenant_management.url}") String baseUrl) {
        this.webClient = WebClient.builder()
            .baseUrl(baseUrl)
            .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
            .build();
    }
    
    public TenantInfo getTenantInfo(String tenantId) {
        return webClient.get()
            .uri("/api/v1/tenants/{tenantId}", tenantId)
            .retrieve()
            .bodyToMono(TenantInfo.class)
            .block();
    }
    
    public Map<String, Object> getTenantConnection(String tenantId) {
        return webClient.get()
            .uri("/api/v1/tenant-connection")
            .header("X-Tenant-ID", tenantId)
            .retrieve()
            .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
            .block();
    }
}
```

## Best Practices

1. **Use the Common Client Library**: Leverage the common database client from `database-layer/common/database_client` for standard access patterns.

2. **Cache Tenant Information**: Cache tenant information to reduce calls to the tenant management service.

3. **Connection Pooling**: Implement connection pooling per tenant.

4. **Transactional Boundaries**: Keep transactions within tenant contexts.

5. **Security Enforcement**: Always enforce tenant isolation at all layers.

6. **Error Handling**: Implement robust error handling for tenant context issues.

7. **Testing**: Test with multiple tenant configurations to ensure isolation.

## Troubleshooting

### Common Issues and Solutions

1. **Missing Tenant Context**:
   - Ensure tenant headers are properly set
   - Verify interceptors are correctly registered
   - Check that tenant context is propagated in async operations

2. **Connection Issues**:
   - Verify network connectivity between services
   - Check that correct database credentials are being used
   - Ensure schema exists for the tenant

3. **Performance Problems**:
   - Monitor connection pool usage
   - Check for queries missing tenant context
   - Analyze slow queries with tenant context

### Logging Recommendations

Configure detailed logging for tenant-related operations:

```
# Logback example configuration
<logger name="com.prismicx.tenant" level="DEBUG"/>
<logger name="com.prismicx.database" level="DEBUG"/>
<logger name="org.postgresql" level="INFO"/>
```

### Support Resources

For issues with the database layer:
- Contact the platform team
- Check the internal knowledge base
- Review logs for both tenant-mgmt-service and the service experiencing issues
  - [Product Database](../../microservices/product-service/init-scripts/01-init-product-db.sql) 