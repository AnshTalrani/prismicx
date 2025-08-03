#!/usr/bin/env python3
"""
Comprehensive Test Suite for Communication Base Microservice

This script performs exhaustive testing of the Communication Base microservice
as a standalone service, testing all endpoints, error handling, and internal logic.
"""

import asyncio
import json
import time
import requests
import subprocess
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class CommunicationBaseTestSuite:
    """Comprehensive test suite for Communication Base microservice."""
    
    def __init__(self):
        self.base_url = "http://localhost:8003"
        self.service_process = None
        self.test_results = {}
        self.start_time = None
        
    def setup_environment(self):
        """Set up the testing environment."""
        print("🔧 Setting up Communication Base testing environment...")
        
        # Change to communication-base directory
        os.chdir("/Users/luvtalrani/ansh projects/prismicx-2/microservices/communication-base")
        
        # Check if requirements are installed
        try:
            import fastapi
            import uvicorn
            import pydantic
            import structlog
            import redis
            print("  ✅ All required dependencies are installed")
        except ImportError as e:
            print(f"  ❌ Missing dependency: {e}")
            print("  🔧 Installing missing dependencies...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            subprocess.run([sys.executable, "-m", "pip", "install", "structlog", "redis"], check=True)
    
    def start_service(self):
        """Start the Communication Base microservice."""
        print("🚀 Starting Communication Base microservice...")
        
        try:
            # Start the minimal app
            self.service_process = subprocess.Popen(
                [sys.executable, "src/minimal_app.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for service to start
            time.sleep(3)
            
            # Check if service is running
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("  ✅ Communication Base service started successfully")
                return True
            else:
                print(f"  ❌ Service health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ Failed to start service: {str(e)}")
            return False
    
    def stop_service(self):
        """Stop the Communication Base microservice."""
        if self.service_process:
            print("🛑 Stopping Communication Base microservice...")
            self.service_process.terminate()
            self.service_process.wait()
            print("  ✅ Service stopped")
    
    def test_health_endpoint(self):
        """Test the health endpoint comprehensively."""
        print("\n🔍 Testing Health Endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            # Test status code
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            # Test response structure
            health_data = response.json()
            required_fields = ["status", "timestamp", "components"]
            for field in required_fields:
                assert field in health_data, f"Missing required field: {field}"
            
            # Test components structure
            components = health_data["components"]
            expected_components = ["api", "campaigns", "conversations"]
            for component in expected_components:
                assert component in components, f"Missing component: {component}"
                assert "status" in components[component], f"Component {component} missing status"
            
            print("  ✅ Health endpoint structure validation passed")
            print(f"  ✅ Overall status: {health_data['status']}")
            print(f"  ✅ Components checked: {len(components)}")
            
            return {"status": "passed", "response": health_data}
            
        except Exception as e:
            print(f"  ❌ Health endpoint test failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        print("\n🔍 Testing Root Endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            required_fields = ["name", "version", "description"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            print("  ✅ Root endpoint validation passed")
            print(f"  ✅ Service name: {data['name']}")
            print(f"  ✅ Version: {data['version']}")
            
            return {"status": "passed", "response": data}
            
        except Exception as e:
            print(f"  ❌ Root endpoint test failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def test_campaigns_crud(self):
        """Test campaigns CRUD operations comprehensively."""
        print("\n🔍 Testing Campaigns CRUD Operations...")
        
        try:
            # Test 1: List empty campaigns
            response = requests.get(f"{self.base_url}/api/v1/campaigns", timeout=10)
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            initial_campaigns = response.json()
            assert isinstance(initial_campaigns, list), "Campaigns should be a list"
            print(f"  ✅ Initial campaigns count: {len(initial_campaigns)}")
            
            # Test 2: Create a campaign
            campaign_data = {
                "name": "Test Campaign CRUD",
                "template_type": "test_template",
                "recipients": [
                    {"id": "user1", "email": "user1@test.com", "name": "User One"},
                    {"id": "user2", "email": "user2@test.com", "name": "User Two"}
                ]
            }
            
            response = requests.post(f"{self.base_url}/api/v1/campaigns", 
                                   json=campaign_data, timeout=10)
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            created_campaign = response.json()
            required_fields = ["campaign_id", "name", "status", "created_at", "recipients_count"]
            for field in required_fields:
                assert field in created_campaign, f"Missing field in created campaign: {field}"
            
            campaign_id = created_campaign["campaign_id"]
            print(f"  ✅ Campaign created: {campaign_id}")
            print(f"  ✅ Recipients count: {created_campaign['recipients_count']}")
            
            # Test 3: Get specific campaign
            response = requests.get(f"{self.base_url}/api/v1/campaigns/{campaign_id}", timeout=10)
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            retrieved_campaign = response.json()
            assert retrieved_campaign["campaign_id"] == campaign_id, "Campaign ID mismatch"
            assert retrieved_campaign["name"] == campaign_data["name"], "Campaign name mismatch"
            print(f"  ✅ Campaign retrieved successfully: {retrieved_campaign['name']}")
            
            # Test 4: List campaigns (should now have at least one)
            response = requests.get(f"{self.base_url}/api/v1/campaigns", timeout=10)
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            final_campaigns = response.json()
            assert len(final_campaigns) >= len(initial_campaigns), "Campaign count should not decrease"
            print(f"  ✅ Final campaigns count: {len(final_campaigns)}")
            
            # Test 5: Test campaign status progression (wait for background processing)
            time.sleep(3)  # Wait for background processing
            response = requests.get(f"{self.base_url}/api/v1/campaigns/{campaign_id}", timeout=10)
            updated_campaign = response.json()
            print(f"  ✅ Campaign status after processing: {updated_campaign['status']}")
            
            return {
                "status": "passed", 
                "campaign_id": campaign_id,
                "initial_count": len(initial_campaigns),
                "final_count": len(final_campaigns)
            }
            
        except Exception as e:
            print(f"  ❌ Campaigns CRUD test failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def test_conversations_functionality(self):
        """Test conversations functionality comprehensively."""
        print("\n🔍 Testing Conversations Functionality...")
        
        try:
            # Test different bot types
            bot_types = ["support", "sales", "consultancy"]
            conversations_created = []
            
            for bot_type in bot_types:
                conversation_data = {
                    "user_id": f"test_user_{bot_type}",
                    "message": f"Hello, I need help with {bot_type} services",
                    "bot_type": bot_type
                }
                
                response = requests.post(f"{self.base_url}/api/v1/conversations",
                                       json=conversation_data, timeout=10)
                assert response.status_code == 200, f"Expected 200, got {response.status_code}"
                
                conversation_result = response.json()
                required_fields = ["response", "session_id", "bot_type", "timestamp"]
                for field in required_fields:
                    assert field in conversation_result, f"Missing field: {field}"
                
                assert conversation_result["bot_type"] == bot_type, f"Bot type mismatch: expected {bot_type}"
                conversations_created.append(conversation_result)
                
                print(f"  ✅ {bot_type.title()} bot conversation created: {conversation_result['session_id']}")
                print(f"     Response: {conversation_result['response'][:50]}...")
            
            # Test conversation retrieval
            for conversation in conversations_created:
                session_id = conversation["session_id"]
                response = requests.get(f"{self.base_url}/api/v1/conversations/{session_id}", timeout=10)
                assert response.status_code == 200, f"Expected 200, got {response.status_code}"
                
                retrieved_conversation = response.json()
                assert retrieved_conversation["session_id"] == session_id, "Session ID mismatch"
                print(f"  ✅ Conversation retrieved: {session_id}")
            
            # Test conversation with custom session ID
            custom_session_data = {
                "user_id": "custom_user",
                "message": "Testing custom session ID",
                "session_id": "custom_session_123",
                "bot_type": "support"
            }
            
            response = requests.post(f"{self.base_url}/api/v1/conversations",
                                   json=custom_session_data, timeout=10)
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            custom_result = response.json()
            assert custom_result["session_id"] == "custom_session_123", "Custom session ID not preserved"
            print(f"  ✅ Custom session ID preserved: {custom_result['session_id']}")
            
            return {
                "status": "passed",
                "conversations_created": len(conversations_created) + 1,
                "bot_types_tested": bot_types
            }
            
        except Exception as e:
            print(f"  ❌ Conversations functionality test failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def test_statistics_endpoint(self):
        """Test statistics endpoint."""
        print("\n🔍 Testing Statistics Endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/api/v1/stats", timeout=10)
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            stats = response.json()
            required_sections = ["campaigns", "conversations", "timestamp"]
            for section in required_sections:
                assert section in stats, f"Missing stats section: {section}"
            
            # Test campaigns stats structure
            campaigns_stats = stats["campaigns"]
            assert "total" in campaigns_stats, "Missing campaigns total"
            assert "by_status" in campaigns_stats, "Missing campaigns by_status"
            
            # Test conversations stats structure
            conversations_stats = stats["conversations"]
            assert "total" in conversations_stats, "Missing conversations total"
            assert "by_bot_type" in conversations_stats, "Missing conversations by_bot_type"
            
            print(f"  ✅ Total campaigns: {campaigns_stats['total']}")
            print(f"  ✅ Total conversations: {conversations_stats['total']}")
            print(f"  ✅ Stats timestamp: {stats['timestamp']}")
            
            return {"status": "passed", "stats": stats}
            
        except Exception as e:
            print(f"  ❌ Statistics endpoint test failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def test_error_handling(self):
        """Test error handling comprehensively."""
        print("\n🔍 Testing Error Handling...")
        
        try:
            error_tests = []
            
            # Test 1: Invalid campaign data
            invalid_campaign = {"invalid": "data"}
            response = requests.post(f"{self.base_url}/api/v1/campaigns", 
                                   json=invalid_campaign, timeout=10)
            assert response.status_code == 422, f"Expected 422, got {response.status_code}"
            error_tests.append("Invalid campaign data")
            
            # Test 2: Non-existent campaign retrieval
            response = requests.get(f"{self.base_url}/api/v1/campaigns/non_existent_id", timeout=10)
            assert response.status_code == 404, f"Expected 404, got {response.status_code}"
            error_tests.append("Non-existent campaign")
            
            # Test 3: Invalid conversation data
            invalid_conversation = {"message": "test"}  # Missing required fields
            response = requests.post(f"{self.base_url}/api/v1/conversations",
                                   json=invalid_conversation, timeout=10)
            assert response.status_code == 422, f"Expected 422, got {response.status_code}"
            error_tests.append("Invalid conversation data")
            
            # Test 4: Non-existent conversation retrieval
            response = requests.get(f"{self.base_url}/api/v1/conversations/non_existent_session", timeout=10)
            assert response.status_code == 404, f"Expected 404, got {response.status_code}"
            error_tests.append("Non-existent conversation")
            
            print(f"  ✅ Error handling tests passed: {len(error_tests)}")
            for test in error_tests:
                print(f"     ✅ {test}")
            
            return {"status": "passed", "tests_passed": error_tests}
            
        except Exception as e:
            print(f"  ❌ Error handling test failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def test_performance_load(self):
        """Test performance under load."""
        print("\n🔍 Testing Performance Under Load...")
        
        try:
            start_time = time.time()
            
            # Create multiple campaigns rapidly
            campaign_ids = []
            for i in range(10):
                campaign_data = {
                    "name": f"Load Test Campaign {i+1}",
                    "template_type": "load_test",
                    "recipients": [{"id": f"user{j}", "email": f"user{j}@load.test"} for j in range(5)]
                }
                
                response = requests.post(f"{self.base_url}/api/v1/campaigns",
                                       json=campaign_data, timeout=10)
                assert response.status_code == 200, f"Campaign {i+1} creation failed"
                campaign_ids.append(response.json()["campaign_id"])
            
            # Create multiple conversations rapidly
            conversation_ids = []
            for i in range(20):
                conversation_data = {
                    "user_id": f"load_user_{i}",
                    "message": f"Load test message {i+1}",
                    "bot_type": "support"
                }
                
                response = requests.post(f"{self.base_url}/api/v1/conversations",
                                       json=conversation_data, timeout=10)
                assert response.status_code == 200, f"Conversation {i+1} creation failed"
                conversation_ids.append(response.json()["session_id"])
            
            end_time = time.time()
            total_time = end_time - start_time
            total_requests = len(campaign_ids) + len(conversation_ids)
            requests_per_second = total_requests / total_time
            
            print(f"  ✅ Load test completed in {total_time:.2f} seconds")
            print(f"  ✅ Created {len(campaign_ids)} campaigns and {len(conversation_ids)} conversations")
            print(f"  ✅ Performance: {requests_per_second:.1f} requests/second")
            
            return {
                "status": "passed",
                "total_time": total_time,
                "campaigns_created": len(campaign_ids),
                "conversations_created": len(conversation_ids),
                "requests_per_second": requests_per_second
            }
            
        except Exception as e:
            print(f"  ❌ Performance load test failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def test_data_validation(self):
        """Test data validation and edge cases."""
        print("\n🔍 Testing Data Validation and Edge Cases...")
        
        try:
            validation_tests = []
            
            # Test 1: Empty recipients list
            empty_recipients_data = {
                "name": "Empty Recipients Test",
                "template_type": "test",
                "recipients": []
            }
            response = requests.post(f"{self.base_url}/api/v1/campaigns",
                                   json=empty_recipients_data, timeout=10)
            # Should still work with empty recipients
            assert response.status_code == 200, "Empty recipients should be allowed"
            validation_tests.append("Empty recipients list")
            
            # Test 2: Very long campaign name
            long_name_data = {
                "name": "A" * 1000,  # Very long name
                "template_type": "test",
                "recipients": [{"id": "user1", "email": "user1@test.com"}]
            }
            response = requests.post(f"{self.base_url}/api/v1/campaigns",
                                   json=long_name_data, timeout=10)
            assert response.status_code == 200, "Long campaign name should be handled"
            validation_tests.append("Very long campaign name")
            
            # Test 3: Special characters in message
            special_chars_data = {
                "user_id": "special_user",
                "message": "Special chars: !@#$%^&*()_+{}|:<>?[]\\;'\",./ 中文 🚀",
                "bot_type": "support"
            }
            response = requests.post(f"{self.base_url}/api/v1/conversations",
                                   json=special_chars_data, timeout=10)
            assert response.status_code == 200, "Special characters should be handled"
            validation_tests.append("Special characters in message")
            
            # Test 4: Invalid bot type (should default or handle gracefully)
            invalid_bot_data = {
                "user_id": "invalid_bot_user",
                "message": "Test with invalid bot type",
                "bot_type": "invalid_bot_type"
            }
            response = requests.post(f"{self.base_url}/api/v1/conversations",
                                   json=invalid_bot_data, timeout=10)
            assert response.status_code == 200, "Invalid bot type should be handled gracefully"
            validation_tests.append("Invalid bot type handling")
            
            print(f"  ✅ Data validation tests passed: {len(validation_tests)}")
            for test in validation_tests:
                print(f"     ✅ {test}")
            
            return {"status": "passed", "tests_passed": validation_tests}
            
        except Exception as e:
            print(f"  ❌ Data validation test failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def run_comprehensive_tests(self):
        """Run all comprehensive tests."""
        print("🚀 STARTING COMPREHENSIVE COMMUNICATION BASE TESTING")
        print("=" * 70)
        
        self.start_time = time.time()
        
        # Setup environment
        self.setup_environment()
        
        # Start service
        if not self.start_service():
            print("❌ Failed to start service. Aborting tests.")
            return
        
        try:
            # Run all tests
            self.test_results["health"] = self.test_health_endpoint()
            self.test_results["root"] = self.test_root_endpoint()
            self.test_results["campaigns_crud"] = self.test_campaigns_crud()
            self.test_results["conversations"] = self.test_conversations_functionality()
            self.test_results["statistics"] = self.test_statistics_endpoint()
            self.test_results["error_handling"] = self.test_error_handling()
            self.test_results["performance"] = self.test_performance_load()
            self.test_results["data_validation"] = self.test_data_validation()
            
        finally:
            # Always stop the service
            self.stop_service()
        
        # Generate comprehensive report
        self.generate_comprehensive_report()
    
    def generate_comprehensive_report(self):
        """Generate a comprehensive test report."""
        end_time = time.time()
        total_time = end_time - self.start_time
        
        print("\n📊 COMPREHENSIVE TEST REPORT")
        print("=" * 70)
        
        # Count passed/failed tests
        passed_tests = [name for name, result in self.test_results.items() if result.get("status") == "passed"]
        failed_tests = [name for name, result in self.test_results.items() if result.get("status") == "failed"]
        
        print(f"🕒 Total testing time: {total_time:.2f} seconds")
        print(f"✅ Tests passed: {len(passed_tests)}/{len(self.test_results)}")
        print(f"❌ Tests failed: {len(failed_tests)}/{len(self.test_results)}")
        
        # Detailed results
        print(f"\n📋 DETAILED TEST RESULTS:")
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result.get("status") == "passed" else "❌"
            print(f"   {status_icon} {test_name.replace('_', ' ').title()}")
            if result.get("status") == "failed":
                print(f"      Error: {result.get('error', 'Unknown error')}")
        
        # Performance metrics
        if "performance" in self.test_results and self.test_results["performance"].get("status") == "passed":
            perf = self.test_results["performance"]
            print(f"\n⚡ PERFORMANCE METRICS:")
            print(f"   🚀 Requests per second: {perf['requests_per_second']:.1f}")
            print(f"   📊 Campaigns created: {perf['campaigns_created']}")
            print(f"   💬 Conversations created: {perf['conversations_created']}")
        
        # Statistics summary
        if "statistics" in self.test_results and self.test_results["statistics"].get("status") == "passed":
            stats = self.test_results["statistics"]["stats"]
            print(f"\n📈 SERVICE STATISTICS:")
            print(f"   📋 Total campaigns: {stats['campaigns']['total']}")
            print(f"   💬 Total conversations: {stats['conversations']['total']}")
        
        # Overall assessment
        success_rate = len(passed_tests) / len(self.test_results) * 100
        
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("   🎉 EXCELLENT: All tests passed! Service is production-ready.")
        elif success_rate >= 80:
            print("   ✅ GOOD: Most tests passed. Minor issues to address.")
        elif success_rate >= 60:
            print("   ⚠️  FAIR: Some issues found. Needs attention before production.")
        else:
            print("   ❌ POOR: Significant issues found. Major fixes required.")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"communication_base_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_time": total_time,
                "success_rate": success_rate,
                "test_results": self.test_results,
                "summary": {
                    "tests_passed": len(passed_tests),
                    "tests_failed": len(failed_tests),
                    "total_tests": len(self.test_results)
                }
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        print("\n🎉 COMPREHENSIVE TESTING COMPLETED!")

def main():
    """Main function to run comprehensive tests."""
    test_suite = CommunicationBaseTestSuite()
    test_suite.run_comprehensive_tests()

if __name__ == "__main__":
    main()
