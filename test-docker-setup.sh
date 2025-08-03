#!/bin/bash

# PrismicX Docker Setup Test Script
# Tests all 4 microservices in Docker containers

set -e

echo "🚀 TESTING PRISMICX DOCKER SETUP"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if service is healthy
check_service_health() {
    local service_name=$1
    local port=$2
    local endpoint=${3:-health}
    local max_attempts=30
    local attempt=1

    echo -e "${BLUE}🔍 Checking $service_name health...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$port/$endpoint" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is healthy!${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}⏳ Attempt $attempt/$max_attempts - waiting for $service_name...${NC}"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $service_name failed to become healthy${NC}"
    return 1
}

# Function to test API endpoint
test_api_endpoint() {
    local service_name=$1
    local port=$2
    local endpoint=$3
    local expected_status=${4:-200}
    
    echo -e "${BLUE}🧪 Testing $service_name API: $endpoint${NC}"
    
    response=$(curl -s -w "%{http_code}" -o /tmp/response.json "http://localhost:$port/$endpoint" || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✅ $service_name API test passed ($response)${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name API test failed (got $response, expected $expected_status)${NC}"
        return 1
    fi
}

# Start the services
echo -e "${BLUE}🐳 Starting Docker services...${NC}"
docker-compose -f docker-compose.demo.yml up -d --build

# Wait a bit for services to initialize
echo -e "${YELLOW}⏳ Waiting for services to initialize...${NC}"
sleep 10

# Check infrastructure services first
echo -e "\n${BLUE}📊 INFRASTRUCTURE SERVICES${NC}"
echo "================================="

# Check MongoDB
if docker-compose -f docker-compose.demo.yml ps mongodb-system | grep -q "Up"; then
    echo -e "${GREEN}✅ MongoDB is running${NC}"
else
    echo -e "${RED}❌ MongoDB is not running${NC}"
fi

# Check Redis
if docker-compose -f docker-compose.demo.yml ps redis-cache | grep -q "Up"; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${RED}❌ Redis is not running${NC}"
fi

# Test microservices
echo -e "\n${BLUE}🔬 MICROSERVICES HEALTH CHECKS${NC}"
echo "================================="

# Test Task Repository Service
if check_service_health "Task Repository Service" 8503; then
    test_api_endpoint "Task Repository Service" 8503 "health"
    test_api_endpoint "Task Repository Service" 8503 ""
fi

# Test Management Systems
if check_service_health "Management Systems" 8002; then
    test_api_endpoint "Management Systems" 8002 "health"
    test_api_endpoint "Management Systems" 8002 ""
fi

# Test Communication Base
if check_service_health "Communication Base" 8003; then
    test_api_endpoint "Communication Base" 8003 "health"
    test_api_endpoint "Communication Base" 8003 ""
fi

# Test Agent Service
if check_service_health "Agent Service" 8000; then
    test_api_endpoint "Agent Service" 8000 "health"
    test_api_endpoint "Agent Service" 8000 ""
fi

# Test integration scenarios
echo -e "\n${BLUE}🔗 INTEGRATION TESTS${NC}"
echo "================================="

# Test Task Repository Service task creation
echo -e "${BLUE}🧪 Testing task creation...${NC}"
task_response=$(curl -s -X POST "http://localhost:8503/api/v1/tasks" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: dev_api_key" \
    -d '{
        "task_type": "INTEGRATION_TEST",
        "request": {
            "content": {"text": "Integration test task"},
            "metadata": {"test": "docker_integration"}
        },
        "template": {
            "service_type": "INTEGRATION_TEST",
            "parameters": {"test": true}
        },
        "tags": {
            "service": "integration-test",
            "source": "docker-test"
        }
    }' || echo "failed")

if echo "$task_response" | grep -q "task_id"; then
    echo -e "${GREEN}✅ Task creation integration test passed${NC}"
else
    echo -e "${RED}❌ Task creation integration test failed${NC}"
fi

# Test Management Systems template retrieval
echo -e "${BLUE}🧪 Testing management templates...${NC}"
templates_response=$(curl -s "http://localhost:8002/api/v1/management/templates" || echo "failed")

if echo "$templates_response" | grep -q "templates"; then
    echo -e "${GREEN}✅ Management templates integration test passed${NC}"
else
    echo -e "${RED}❌ Management templates integration test failed${NC}"
fi

# Test Communication Base campaign creation
echo -e "${BLUE}🧪 Testing campaign creation...${NC}"
campaign_response=$(curl -s -X POST "http://localhost:8003/api/v1/campaigns" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Docker Integration Test Campaign",
        "message": "Testing campaign creation in Docker",
        "recipients": ["test@example.com"],
        "campaign_type": "integration_test"
    }' || echo "failed")

if echo "$campaign_response" | grep -q "campaign_id"; then
    echo -e "${GREEN}✅ Campaign creation integration test passed${NC}"
else
    echo -e "${RED}❌ Campaign creation integration test failed${NC}"
fi

# Show service logs for debugging
echo -e "\n${BLUE}📋 SERVICE STATUS SUMMARY${NC}"
echo "================================="
docker-compose -f docker-compose.demo.yml ps

# Show service URLs
echo -e "\n${BLUE}🌐 SERVICE URLS${NC}"
echo "================================="
echo -e "${GREEN}Task Repository Service:${NC} http://localhost:8503"
echo -e "${GREEN}Management Systems:${NC}      http://localhost:8002"
echo -e "${GREEN}Communication Base:${NC}      http://localhost:8003"
echo -e "${GREEN}Agent Service:${NC}           http://localhost:8000"
echo -e "${GREEN}MongoDB:${NC}                 localhost:27017"
echo -e "${GREEN}Redis:${NC}                   localhost:6379"

echo -e "\n${BLUE}📚 SWAGGER DOCUMENTATION${NC}"
echo "================================="
echo -e "${GREEN}Task Repository Service:${NC} http://localhost:8503/docs"
echo -e "${GREEN}Management Systems:${NC}      http://localhost:8002/docs"
echo -e "${GREEN}Communication Base:${NC}      http://localhost:8003/docs"
echo -e "${GREEN}Agent Service:${NC}           http://localhost:8000/docs"

echo -e "\n${GREEN}🎉 Docker setup test completed!${NC}"
echo -e "${YELLOW}💡 Use 'docker-compose -f docker-compose.demo.yml logs [service-name]' to view logs${NC}"
echo -e "${YELLOW}💡 Use 'docker-compose -f docker-compose.demo.yml down' to stop all services${NC}"
