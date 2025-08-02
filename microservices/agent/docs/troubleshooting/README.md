# Troubleshooting Guide

## Overview

This guide provides solutions for common issues that may arise when working with the Agent microservice. It covers various aspects including setup, runtime, performance, and integration issues.

## Common Issues

### Setup Issues

#### 1. Environment Setup

**Problem**: Unable to set up the development environment
**Symptoms**:
- Dependencies installation fails
- Environment variables not loading
- Docker containers not starting

**Solutions**:
1. Verify Python version:
```bash
python --version  # Should be 3.9+
```

2. Check virtual environment:
```bash
# Create new virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

3. Verify environment variables:
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with correct values
nano .env
```

4. Check Docker setup:
```bash
# Verify Docker installation
docker --version
docker-compose --version

# Start services
docker-compose up -d
```

#### 2. Database Connection

**Problem**: Unable to connect to database
**Symptoms**:
- Connection timeout errors
- Authentication failures
- Database not found errors

**Solutions**:
1. Check database status:
```bash
docker-compose ps database
```

2. Verify connection string:
```bash
# Check environment variables
echo $DB_HOST
echo $DB_PORT
echo $DB_NAME
```

3. Test database connection:
```bash
# Connect to database
docker-compose exec database psql -U agent_user -d agent_db
```

4. Check database logs:
```bash
docker-compose logs database
```

### Runtime Issues

#### 1. Service Not Starting

**Problem**: Service fails to start
**Symptoms**:
- Service crashes on startup
- Port conflicts
- Missing dependencies

**Solutions**:
1. Check service logs:
```bash
docker-compose logs agent
```

2. Verify port availability:
```bash
# Check if port is in use
sudo lsof -i :8000
```

3. Check service status:
```bash
docker-compose ps
```

4. Restart service:
```bash
docker-compose restart agent
```

#### 2. Request Processing Failures

**Problem**: Requests fail to process
**Symptoms**:
- Request timeout errors
- Invalid template errors
- Processing errors

**Solutions**:
1. Check request logs:
```bash
# View recent logs
docker-compose logs --tail=100 agent
```

2. Verify template:
```bash
# Check template existence
curl -X GET http://localhost:8000/api/v1/templates/{template_id}
```

3. Check request status:
```bash
# Get request details
curl -X GET http://localhost:8000/api/v1/requests/{request_id}
```

4. Monitor service metrics:
```bash
# Check Prometheus metrics
curl http://localhost:8000/metrics
```

### Performance Issues

#### 1. Slow Response Times

**Problem**: High latency in request processing
**Symptoms**:
- Long request processing times
- Timeout errors
- Resource exhaustion

**Solutions**:
1. Check resource usage:
```bash
# Monitor CPU and memory
docker stats

# Check container logs
docker-compose logs agent
```

2. Optimize configuration:
```bash
# Adjust worker count
export API_WORKERS=8

# Increase timeout
export REQUEST_TIMEOUT=60
```

3. Monitor service metrics:
```bash
# Check Prometheus metrics
curl http://localhost:8000/metrics | grep duration
```

4. Scale service:
```bash
# Scale horizontally
docker-compose up -d --scale agent=3
```

#### 2. Memory Issues

**Problem**: High memory usage
**Symptoms**:
- Out of memory errors
- Container restarts
- Slow performance

**Solutions**:
1. Check memory usage:
```bash
# Monitor container memory
docker stats

# Check process memory
docker-compose exec agent ps aux
```

2. Adjust memory limits:
```bash
# Update docker-compose.yml
services:
  agent:
    deploy:
      resources:
        limits:
          memory: 4G
```

3. Optimize code:
- Review memory-intensive operations
- Implement garbage collection
- Use memory-efficient data structures

4. Monitor memory metrics:
```bash
# Check memory metrics
curl http://localhost:8000/metrics | grep memory
```

### Integration Issues

#### 1. External Service Communication

**Problem**: Failed communication with external services
**Symptoms**:
- Connection timeouts
- Authentication errors
- Invalid responses

**Solutions**:
1. Check service endpoints:
```bash
# Verify service URLs
echo $ANALYSIS_SERVICE_URL
echo $GENERATIVE_SERVICE_URL
```

2. Test connectivity:
```bash
# Test service endpoints
curl -v $ANALYSIS_SERVICE_URL/health
```

3. Check network:
```bash
# Test DNS resolution
nslookup analysis-service

# Check network connectivity
ping analysis-service
```

4. Review service logs:
```bash
# Check service logs
docker-compose logs analysis-service
```

#### 2. Authentication Issues

**Problem**: Authentication failures
**Symptoms**:
- 401 Unauthorized errors
- Token validation failures
- Session expiration

**Solutions**:
1. Verify token:
```bash
# Check token format
echo $JWT_TOKEN | jq -R 'split(".") | .[1] | @base64d | fromjson'
```

2. Check token expiration:
```bash
# Decode token
jwt decode $JWT_TOKEN
```

3. Verify authentication service:
```bash
# Check auth service health
curl http://auth-service/health
```

4. Review auth logs:
```bash
docker-compose logs auth-service
```

### Monitoring and Debugging

#### 1. Logging

**Problem**: Insufficient logging information
**Solutions**:
1. Adjust log level:
```bash
# Set debug logging
export LOG_LEVEL=DEBUG
```

2. Configure log format:
```python
# Update logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

3. Add structured logging:
```python
import structlog

logger = structlog.get_logger()

logger.info("request_processed", 
    request_id=request.id,
    duration=duration,
    status=status
)
```

#### 2. Metrics

**Problem**: Missing or incorrect metrics
**Solutions**:
1. Add custom metrics:
```python
from prometheus_client import Counter, Histogram

request_counter = Counter(
    'agent_requests_total',
    'Total number of requests processed',
    ['status']
)

request_duration = Histogram(
    'agent_request_duration_seconds',
    'Request processing duration',
    ['template_id']
)
```

2. Configure metric collection:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'agent'
    static_configs:
      - targets: ['agent:8000']
```

3. Set up alerts:
```yaml
# alerts.yml
groups:
  - name: agent
    rules:
      - alert: HighErrorRate
        expr: rate(agent_requests_total{status="error"}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
```

## Best Practices

### 1. Logging

- Use appropriate log levels
- Include context in log messages
- Implement structured logging
- Rotate logs regularly
- Monitor log volume

### 2. Monitoring

- Set up comprehensive metrics
- Configure appropriate alerts
- Monitor resource usage
- Track performance metrics
- Implement health checks

### 3. Debugging

- Use debug mode when needed
- Implement proper error handling
- Add detailed error messages
- Use logging effectively
- Monitor system resources

### 4. Performance

- Optimize database queries
- Implement caching
- Use connection pooling
- Monitor resource usage
- Scale appropriately

## Support

For issues not covered in this guide:

1. Check the documentation
2. Review GitHub issues
3. Contact the development team
4. Submit a bug report
5. Request support through the appropriate channels

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Python Logging](https://docs.python.org/3/library/logging.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/) 