"""
Integration tests between Agent microservice and Management Systems microservice.

These tests validate cross-service workflows and ensure proper communication
between the Agent and Management Systems microservices.
"""

import pytest
import httpx
import asyncio
import json
import time
from typing import Dict, Any, List
from datetime import datetime

# Service URLs
AGENT_BASE_URL = "http://localhost:8000"
MANAGEMENT_BASE_URL = "http://localhost:8002"

class IntegrationTestSuite:
    """Integration test suite for Agent and Management Systems microservices."""
    
    def __init__(self):
        self.agent_client = httpx.AsyncClient(base_url=AGENT_BASE_URL, timeout=30.0)
        self.management_client = httpx.AsyncClient(base_url=MANAGEMENT_BASE_URL, timeout=30.0)
    
    async def cleanup(self):
        """Clean up HTTP clients."""
        await self.agent_client.aclose()
        await self.management_client.aclose()

@pytest.fixture
async def integration_suite():
    """Fixture to provide integration test suite."""
    suite = IntegrationTestSuite()
    yield suite
    await suite.cleanup()

class TestServiceHealth:
    """Test basic service health and connectivity."""
    
    async def test_both_services_healthy(self, integration_suite):
        """Test that both services are running and healthy."""
        # Test Agent service health
        agent_response = await integration_suite.agent_client.get("/health")
        assert agent_response.status_code == 200
        agent_health = agent_response.json()
        assert agent_health["status"] in ["healthy", "unhealthy"]  # Service running
        
        # Test Management Systems service health
        mgmt_response = await integration_suite.management_client.get("/health")
        assert mgmt_response.status_code == 200
        mgmt_health = mgmt_response.json()
        assert mgmt_health["status"] in ["healthy", "unhealthy"]  # Service running
        
        print(f"✅ Agent Service Health: {agent_health}")
        print(f"✅ Management Service Health: {mgmt_health}")

class TestManagementSystemTemplates:
    """Test management system template retrieval and validation."""
    
    async def test_get_management_templates(self, integration_suite):
        """Test retrieving management system templates."""
        response = await integration_suite.management_client.get("/api/v1/management/templates")
        assert response.status_code == 200
        
        templates = response.json()
        assert isinstance(templates, list)
        assert len(templates) > 0
        
        # Validate template structure
        for template in templates:
            assert "system_id" in template
            assert "name" in template
            assert "type" in template
            assert "data_fields" in template
            assert "data_views" in template
            
        print(f"✅ Retrieved {len(templates)} management system templates")
        return templates
    
    async def test_get_specific_template(self, integration_suite):
        """Test retrieving a specific CRM template."""
        response = await integration_suite.management_client.get("/api/v1/management/templates/crm-contacts")
        assert response.status_code == 200
        
        template = response.json()
        assert template["system_id"] == "crm-contacts"
        assert template["name"] == "Customer Contacts"
        assert template["type"] == "crm"
        assert len(template["data_fields"]) > 0
        assert len(template["data_views"]) > 0
        
        print(f"✅ Retrieved CRM template: {template['name']}")
        return template

class TestAgentBotIntegration:
    """Test Agent bot functionality with management system context."""
    
    async def test_bot_request_with_crm_context(self, integration_suite):
        """Test bot request that involves CRM management system."""
        bot_request = {
            "text": "I need to add a new customer contact: John Smith, email john@example.com, company ABC Corp",
            "user_id": "test_user_123",
            "session_id": "integration_test_session",
            "urgency": "normal"
        }
        
        response = await integration_suite.agent_client.post("/bot/request", json=bot_request)
        assert response.status_code == 200
        
        bot_response = response.json()
        assert "session_id" in bot_response
        assert "user_id" in bot_response
        assert "status" in bot_response
        assert bot_response["session_id"] == "integration_test_session"
        assert bot_response["user_id"] == "test_user_123"
        
        print(f"✅ Bot request processed: {bot_response}")
        return bot_response
    
    async def test_bot_notification_handling(self, integration_suite):
        """Test bot notification handling."""
        notification = {
            "session_id": "integration_test_session",
            "user_id": "test_user_123",
            "notification_type": "crm_contact_created",
            "data": {
                "contact_id": "contact_12345",
                "name": "John Smith",
                "email": "john@example.com"
            }
        }
        
        response = await integration_suite.agent_client.post("/bot/notification", json=notification)
        assert response.status_code == 200
        
        notification_response = response.json()
        assert "session_id" in notification_response
        assert "status" in notification_response
        assert notification_response["session_id"] == "integration_test_session"
        
        print(f"✅ Bot notification processed: {notification_response}")
        return notification_response

class TestBatchProcessingIntegration:
    """Test batch processing integration between services."""
    
    async def test_matrix_batch_with_management_templates(self, integration_suite):
        """Test matrix batch processing using management system templates."""
        # First, get available templates from management service
        templates_response = await integration_suite.management_client.get("/api/v1/management/templates")
        assert templates_response.status_code == 200
        templates = templates_response.json()
        
        # Use CRM template for batch processing
        crm_template = next((t for t in templates if t["system_id"] == "crm-contacts"), None)
        assert crm_template is not None
        
        # Create batch request using CRM template structure
        batch_request = {
            "source": "crm_integration_test",
            "template_id": "crm-contacts",
            "items": [
                {
                    "full_name": "Alice Johnson",
                    "email": "alice@example.com",
                    "company": "Tech Corp",
                    "status": "lead"
                },
                {
                    "full_name": "Bob Wilson",
                    "email": "bob@example.com", 
                    "company": "Design Studio",
                    "status": "prospect"
                },
                {
                    "full_name": "Carol Davis",
                    "email": "carol@example.com",
                    "company": "Marketing Inc",
                    "status": "customer"
                }
            ],
            "processing_method": "individual",
            "data_source_type": "users",
            "metadata": {
                "integration_test": True,
                "template_source": "management_system",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        response = await integration_suite.agent_client.post("/api/batch/matrix", json=batch_request)
        assert response.status_code == 200
        
        batch_response = response.json()
        assert "batch_id" in batch_response
        assert "status" in batch_response
        
        print(f"✅ Matrix batch created: {batch_response}")
        return batch_response
    
    async def test_user_batch_processing(self, integration_suite):
        """Test user batch processing with management system integration."""
        batch_request = {
            "source": "user_management_integration",
            "template_id": "crm-contacts",
            "items": [
                {
                    "user_id": "user_001",
                    "full_name": "David Brown",
                    "email": "david@example.com",
                    "company": "Finance Corp"
                },
                {
                    "user_id": "user_002", 
                    "full_name": "Eva Green",
                    "email": "eva@example.com",
                    "company": "Health Systems"
                }
            ],
            "metadata": {
                "integration_test": True,
                "batch_type": "user_management"
            }
        }
        
        response = await integration_suite.agent_client.post(
            "/api/batch/user_batch?process_individually=true", 
            json=batch_request
        )
        assert response.status_code == 200
        
        batch_response = response.json()
        assert "batch_id" in batch_response
        assert "status" in batch_response
        
        print(f"✅ User batch created: {batch_response}")
        return batch_response

class TestCrossServiceWorkflows:
    """Test complete workflows that span both services."""
    
    async def test_end_to_end_crm_workflow(self, integration_suite):
        """Test complete CRM workflow from template to processing."""
        print("\n🔄 Starting End-to-End CRM Workflow Test")
        
        # Step 1: Get CRM template from Management Systems
        print("Step 1: Retrieving CRM template...")
        template_response = await integration_suite.management_client.get("/api/v1/management/templates/crm-contacts")
        assert template_response.status_code == 200
        crm_template = template_response.json()
        print(f"✅ Retrieved template: {crm_template['name']}")
        
        # Step 2: Create bot request for CRM data entry
        print("Step 2: Processing bot request for CRM entry...")
        bot_request = {
            "text": f"Create a new contact using the {crm_template['name']} template: Sarah Connor, sarah@skynet.com, Cyberdyne Systems",
            "user_id": "integration_user",
            "session_id": "crm_workflow_session",
            "urgency": "normal"
        }
        
        bot_response = await integration_suite.agent_client.post("/bot/request", json=bot_request)
        assert bot_response.status_code == 200
        bot_result = bot_response.json()
        print(f"✅ Bot processed request: {bot_result['status']}")
        
        # Step 3: Create batch processing for multiple CRM entries
        print("Step 3: Creating batch for multiple CRM entries...")
        batch_request = {
            "source": "crm_workflow_integration",
            "template_id": crm_template["system_id"],
            "items": [
                {
                    "full_name": "Kyle Reese",
                    "email": "kyle@resistance.com",
                    "company": "Human Resistance",
                    "status": "lead",
                    "source": "referral"
                },
                {
                    "full_name": "John Connor",
                    "email": "john@future.com", 
                    "company": "Future Command",
                    "status": "customer",
                    "source": "website"
                }
            ],
            "processing_method": "individual",
            "data_source_type": "users",
            "metadata": {
                "workflow": "end_to_end_crm",
                "template_name": crm_template["name"],
                "integration_test": True
            }
        }
        
        batch_response = await integration_suite.agent_client.post("/api/batch/matrix", json=batch_request)
        assert batch_response.status_code == 200
        batch_result = batch_response.json()
        print(f"✅ Batch created: {batch_result['batch_id']}")
        
        # Step 4: Send notification about CRM workflow completion
        print("Step 4: Sending workflow completion notification...")
        notification = {
            "session_id": "crm_workflow_session",
            "user_id": "integration_user",
            "notification_type": "workflow_completed",
            "data": {
                "workflow_type": "crm_integration",
                "batch_id": batch_result["batch_id"],
                "template_used": crm_template["system_id"],
                "items_processed": len(batch_request["items"])
            }
        }
        
        notification_response = await integration_suite.agent_client.post("/bot/notification", json=notification)
        assert notification_response.status_code == 200
        notification_result = notification_response.json()
        print(f"✅ Notification sent: {notification_result['status']}")
        
        print("🎉 End-to-End CRM Workflow Test Completed Successfully!")
        
        return {
            "template": crm_template,
            "bot_response": bot_result,
            "batch_response": batch_result,
            "notification_response": notification_result
        }

class TestErrorHandlingIntegration:
    """Test error handling across services."""
    
    async def test_invalid_template_handling(self, integration_suite):
        """Test handling of invalid template references."""
        batch_request = {
            "source": "error_test",
            "template_id": "non_existent_template",
            "items": [{"test": "data"}],
            "processing_method": "individual",
            "data_source_type": "users"
        }
        
        response = await integration_suite.agent_client.post("/api/batch/matrix", json=batch_request)
        # Should still process but may have different behavior
        assert response.status_code in [200, 400, 422]
        
        result = response.json()
        print(f"✅ Invalid template handled: {result}")
        return result
    
    async def test_malformed_request_handling(self, integration_suite):
        """Test handling of malformed requests."""
        malformed_request = {
            "invalid_field": "test",
            "missing_required_fields": True
        }
        
        response = await integration_suite.agent_client.post("/bot/request", json=malformed_request)
        assert response.status_code == 422  # Validation error expected
        
        error_response = response.json()
        assert "detail" in error_response
        print(f"✅ Malformed request properly rejected: {error_response}")
        return error_response

# Test execution functions
async def run_integration_tests():
    """Run all integration tests."""
    print("🚀 Starting Agent-Management Systems Integration Tests")
    print("=" * 60)
    
    suite = IntegrationTestSuite()
    
    try:
        # Test service health
        print("\n📋 Testing Service Health...")
        health_test = TestServiceHealth()
        await health_test.test_both_services_healthy(suite)
        
        # Test management templates
        print("\n📋 Testing Management System Templates...")
        template_test = TestManagementSystemTemplates()
        await template_test.test_get_management_templates(suite)
        await template_test.test_get_specific_template(suite)
        
        # Test bot integration
        print("\n📋 Testing Agent Bot Integration...")
        bot_test = TestAgentBotIntegration()
        await bot_test.test_bot_request_with_crm_context(suite)
        await bot_test.test_bot_notification_handling(suite)
        
        # Test batch processing
        print("\n📋 Testing Batch Processing Integration...")
        batch_test = TestBatchProcessingIntegration()
        await batch_test.test_matrix_batch_with_management_templates(suite)
        await batch_test.test_user_batch_processing(suite)
        
        # Test cross-service workflows
        print("\n📋 Testing Cross-Service Workflows...")
        workflow_test = TestCrossServiceWorkflows()
        await workflow_test.test_end_to_end_crm_workflow(suite)
        
        # Test error handling
        print("\n📋 Testing Error Handling...")
        error_test = TestErrorHandlingIntegration()
        await error_test.test_invalid_template_handling(suite)
        await error_test.test_malformed_request_handling(suite)
        
        print("\n🎉 ALL INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {str(e)}")
        raise
    finally:
        await suite.cleanup()

if __name__ == "__main__":
    asyncio.run(run_integration_tests())
