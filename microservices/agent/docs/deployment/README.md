# Deployment Guide

## Overview

This guide explains how to deploy the Agent microservice in different environments (development, staging, and production). The service is containerized using Docker and can be deployed using Docker Compose or Kubernetes.

## Prerequisites

- Docker and Docker Compose
- Kubernetes cluster (for production)
- Access to container registry
- Required environment variables

## Environment Variables

Create a `.env` file with the following variables:

```env
# Application
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agent_db
DB_USER=agent_user
DB_PASSWORD=agent_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Security
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# Service Endpoints
ANALYSIS_SERVICE_URL=http://analysis-service:8000
GENERATIVE_SERVICE_URL=http://generative-service:8000
COMMUNICATION_SERVICE_URL=http://communication-service:8000

# Monitoring
PROMETHEUS_MULTIPROC_DIR=/tmp
```

## Docker Deployment

### Development Environment

1. Build the image:
```bash
docker-compose build
```

2. Start the services:
```bash
docker-compose up -d
```

3. Check logs:
```bash
docker-compose logs -f agent
```

### Production Environment

1. Build the production image:
```bash
docker build -t agent:latest -f Dockerfile.prod .
```

2. Push to registry:
```bash
docker tag agent:latest registry.example.com/agent:latest
docker push registry.example.com/agent:latest
```

3. Deploy using docker-compose:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster
- kubectl configured
- Helm installed (optional)

### Manual Deployment

1. Create namespace:
```bash
kubectl create namespace agent
```

2. Create secrets:
```bash
kubectl create secret generic agent-secrets \
  --from-file=.env \
  --namespace agent
```

3. Deploy application:
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

### Helm Deployment

1. Add Helm repository:
```bash
helm repo add agent https://helm.example.com/agent
```

2. Deploy using Helm:
```bash
helm install agent agent/agent \
  --namespace agent \
  --set environment=production \
  --set image.tag=latest
```

## Health Checks

The service provides health check endpoints:

```http
GET /health
```

Response:
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2024-03-20T12:00:00Z",
    "services": {
        "database": "healthy",
        "redis": "healthy"
    }
}
```

## Monitoring

### Prometheus Metrics

The service exposes Prometheus metrics at `/metrics`:

```http
GET /metrics
```

Key metrics:
- `http_requests_total`
- `http_request_duration_seconds`
- `active_requests`
- `template_execution_duration_seconds`

### Grafana Dashboard

A Grafana dashboard is available for monitoring:
- Request rates
- Error rates
- Response times
- Resource usage

## Scaling

### Horizontal Scaling

1. Scale using Docker Compose:
```bash
docker-compose up -d --scale agent=3
```

2. Scale using Kubernetes:
```bash
kubectl scale deployment agent --replicas=3 -n agent
```

### Vertical Scaling

Update resource limits in deployment configuration:

```yaml
resources:
  limits:
    cpu: "2"
    memory: "4Gi"
  requests:
    cpu: "1"
    memory: "2Gi"
```

## Backup and Recovery

### Database Backup

1. Create backup:
```bash
kubectl exec -it $(kubectl get pod -l app=agent -o jsonpath='{.items[0].metadata.name}') \
  -- pg_dump -U agent_user agent_db > backup.sql
```

2. Restore from backup:
```bash
kubectl exec -it $(kubectl get pod -l app=agent -o jsonpath='{.items[0].metadata.name}') \
  -- psql -U agent_user agent_db < backup.sql
```

### Configuration Backup

1. Export configuration:
```bash
kubectl get configmap agent-config -o yaml > config-backup.yaml
```

2. Restore configuration:
```bash
kubectl apply -f config-backup.yaml
```

## Security

### Network Security

1. Configure network policies:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: agent-network-policy
spec:
  podSelector:
    matchLabels:
      app: agent
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: allowed-namespace
    ports:
    - protocol: TCP
      port: 8000
```

### TLS Configuration

1. Create TLS secret:
```bash
kubectl create secret tls agent-tls \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem \
  --namespace agent
```

2. Configure ingress:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: agent-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - agent.example.com
    secretName: agent-tls
```

## Troubleshooting

### Common Issues

1. Service not starting:
```bash
kubectl describe pod -l app=agent
kubectl logs -l app=agent
```

2. Database connection issues:
```bash
kubectl exec -it $(kubectl get pod -l app=agent -o jsonpath='{.items[0].metadata.name}') \
  -- psql -U agent_user -d agent_db
```

3. Memory issues:
```bash
kubectl top pod -l app=agent
```

### Logging

1. View logs:
```bash
kubectl logs -f -l app=agent
```

2. Search logs:
```bash
kubectl logs -l app=agent | grep "ERROR"
```

## Rollback

### Docker Compose

```bash
docker-compose rollback agent
```

### Kubernetes

```bash
kubectl rollout undo deployment/agent -n agent
```

## Maintenance

### Regular Tasks

1. Update dependencies:
```bash
pip-compile requirements.in
pip-sync requirements.txt
```

2. Clean up old images:
```bash
docker system prune -a
```

3. Rotate logs:
```bash
kubectl exec -it $(kubectl get pod -l app=agent -o jsonpath='{.items[0].metadata.name}') \
  -- logrotate /etc/logrotate.d/agent
```

### Monitoring Tasks

1. Check resource usage:
```bash
kubectl top pod -l app=agent
```

2. Monitor error rates:
```bash
kubectl logs -l app=agent | grep "ERROR" | wc -l
```

3. Check service health:
```bash
curl http://localhost:8000/health
``` 