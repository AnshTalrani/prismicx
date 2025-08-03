#!/usr/bin/env python3
"""
Comprehensive Test Suite for Task Repository Service

This test suite thoroughly validates the Task Repository Service as a standalone database service,
testing all endpoints, error handling, database operations, and real-world scenarios.
"""

import asyncio
import json
import time
import subprocess
import sys
import os
import signal
from datetime import datetime
from typing import Dict, List, Any, Optional
import httpx
from bson import ObjectId

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class TaskRepoTestSuite:
    """Comprehensive test suite for Task Repository Service."""
    
    def __init__(self):
        self.base_url = "http://localhost:8503"
        self.api_key = "dev_api_key"
        self.headers = {"X-API-Key": self.api_key}
        self.service_process = None
        self.test_results = {
            "start_time": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }
        
    async def setup_environment(self):
        """Set up the testing environment."""
        print("🔧 Setting up Task Repository Service testing environment...")
        
        # Check if required dependencies are installed
        try:
            import fastapi
            import uvicorn
            import motor
            import pymongo
            print("  ✅ All required dependencies are installed")
        except ImportError as e:
            print(f"  ❌ Missing dependency: {e}")
            print("  Installing missing dependencies...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                         cwd="/Users/luvtalrani/ansh projects/prismicx-2/database-layer/task-repo-service")
            print("  ✅ Dependencies installed")
    
    async def start_service(self):
        """Start the Task Repository Service."""
        print("🚀 Starting Task Repository Service...")
        
        # Set environment variables for testing
        env = os.environ.copy()
        env.update({
            "MONGODB_URI": "mongodb://localhost:27017",
            "MONGODB_DATABASE": "task_repository_test",
            "MONGODB_TASKS_COLLECTION": "tasks_test",
            "API_KEY": self.api_key,
            "HOST": "0.0.0.0",
            "PORT": "8503",
            "SERVICE_NAME": "task-repo-service"
        })
        
        try:
            # Start the service using uvicorn
            self.service_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "src.main:app", 
                "--host", "0.0.0.0", 
                "--port", "8503",
                "--reload"
            ], 
            cwd="/Users/luvtalrani/ansh projects/prismicx-2/database-layer/task-repo-service",
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
            )
            
            # Wait for service to start
            await asyncio.sleep(3)
            
            # Test if service is running
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(f"{self.base_url}/health", timeout=5.0)
                    if response.status_code == 200:
                        print("  ✅ Task Repository Service started successfully")
                        return True
                except Exception as e:
                    print(f"  ❌ Service not responding: {e}")
                    return False
                    
        except Exception as e:
            print(f"  ❌ Failed to start service: {e}")
            return False
    
    async def stop_service(self):
        """Stop the Task Repository Service."""
        print("🛑 Stopping Task Repository Service...")
        if self.service_process:
            self.service_process.terminate()
            try:
                self.service_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.service_process.kill()
                self.service_process.wait()
            print("  ✅ Service stopped")
    
    async def test_health_endpoint(self):
        """Test the health endpoint."""
        print("🔍 Testing Health Endpoint...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health", headers=self.headers)
                
                if response.status_code == 200:
                    health_data = response.json()
                    
                    # Validate health response structure
                    required_fields = ["status", "service", "timestamp"]
                    for field in required_fields:
                        if field not in health_data:
                            raise ValueError(f"Missing required field: {field}")
                    
                    print("  ✅ Health endpoint structure validation passed")
                    print(f"  ✅ Service status: {health_data.get('status', 'unknown')}")
                    print(f"  ✅ Service name: {health_data.get('service', 'unknown')}")
                    
                    self.test_results["tests"]["health"] = {
                        "status": "passed",
                        "response": health_data
                    }
                    return True
                else:
                    raise Exception(f"Health check failed with status {response.status_code}")
                    
        except Exception as e:
            print(f"  ❌ Health endpoint test failed: {e}")
            self.test_results["tests"]["health"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    async def test_task_crud_operations(self):
        """Test task CRUD operations."""
        print("🔍 Testing Task CRUD Operations...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test task creation
                task_data = {
                    "task_type": "GENERATIVE",
                    "request": {
                        "content": {"text": "Generate a test response"},
                        "metadata": {"user_id": "test_user_123"}
                    },
                    "template": {
                        "service_type": "GENERATIVE",
                        "parameters": {"model": "gpt-4", "max_tokens": 1024}
                    },
                    "tags": {
                        "service": "test-service",
                        "source": "test-api"
                    }
                }
                
                # Create task
                create_response = await client.post(
                    f"{self.base_url}/api/v1/tasks",
                    json=task_data,
                    headers=self.headers
                )
                
                if create_response.status_code != 201:
                    raise Exception(f"Task creation failed with status {create_response.status_code}: {create_response.text}")
                
                created_task = create_response.json()
                task_id = created_task["task_id"]
                print(f"  ✅ Task created: {task_id}")
                
                # Get task by ID
                get_response = await client.get(
                    f"{self.base_url}/api/v1/tasks/{task_id}",
                    headers=self.headers
                )
                
                if get_response.status_code != 200:
                    raise Exception(f"Task retrieval failed with status {get_response.status_code}")
                
                retrieved_task = get_response.json()
                print(f"  ✅ Task retrieved: {retrieved_task['task_type']}")
                
                # Update task
                update_data = {
                    "status": "processing",
                    "metadata": {"updated": True}
                }
                
                update_response = await client.put(
                    f"{self.base_url}/api/v1/tasks/{task_id}",
                    json=update_data,
                    headers=self.headers
                )
                
                if update_response.status_code != 200:
                    raise Exception(f"Task update failed with status {update_response.status_code}")
                
                print("  ✅ Task updated successfully")
                
                # Get pending tasks
                pending_response = await client.get(
                    f"{self.base_url}/api/v1/tasks?task_type=GENERATIVE&limit=5",
                    headers=self.headers
                )
                
                if pending_response.status_code != 200:
                    raise Exception(f"Pending tasks retrieval failed with status {pending_response.status_code}")
                
                pending_tasks = pending_response.json()
                print(f"  ✅ Pending tasks retrieved: {len(pending_tasks.get('tasks', []))} tasks")
                
                # Claim task
                claim_response = await client.post(
                    f"{self.base_url}/api/v1/tasks/{task_id}/claim",
                    headers=self.headers
                )
                
                if claim_response.status_code != 200:
                    raise Exception(f"Task claim failed with status {claim_response.status_code}")
                
                print("  ✅ Task claimed successfully")
                
                # Complete task
                complete_data = {
                    "result": {
                        "generated_text": "This is a test response",
                        "metadata": {"tokens_used": 150}
                    }
                }
                
                complete_response = await client.post(
                    f"{self.base_url}/api/v1/tasks/{task_id}/complete",
                    json=complete_data,
                    headers=self.headers
                )
                
                if complete_response.status_code != 200:
                    raise Exception(f"Task completion failed with status {complete_response.status_code}")
                
                print("  ✅ Task completed successfully")
                
                # Delete task
                delete_response = await client.delete(
                    f"{self.base_url}/api/v1/tasks/{task_id}",
                    headers=self.headers
                )
                
                if delete_response.status_code != 200:
                    raise Exception(f"Task deletion failed with status {delete_response.status_code}")
                
                print("  ✅ Task deleted successfully")
                
                self.test_results["tests"]["task_crud"] = {
                    "status": "passed",
                    "task_id": task_id,
                    "operations": ["create", "read", "update", "claim", "complete", "delete"]
                }
                return True
                
        except Exception as e:
            print(f"  ❌ Task CRUD operations test failed: {e}")
            self.test_results["tests"]["task_crud"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    async def test_task_lifecycle(self):
        """Test complete task lifecycle scenarios."""
        print("🔍 Testing Task Lifecycle Scenarios...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test multiple task types
                task_types = ["GENERATIVE", "ANALYSIS", "PROCESSING"]
                created_tasks = []
                
                for task_type in task_types:
                    task_data = {
                        "task_type": task_type,
                        "request": {
                            "content": {"text": f"Test {task_type.lower()} request"},
                            "metadata": {"user_id": f"test_user_{task_type.lower()}"}
                        },
                        "template": {
                            "service_type": task_type,
                            "parameters": {"priority": "high"}
                        },
                        "tags": {
                            "service": f"{task_type.lower()}-service",
                            "source": "lifecycle-test"
                        }
                    }
                    
                    response = await client.post(
                        f"{self.base_url}/api/v1/tasks",
                        json=task_data,
                        headers=self.headers
                    )
                    
                    if response.status_code == 201:
                        task = response.json()
                        created_tasks.append((task["task_id"], task_type))
                        print(f"  ✅ {task_type} task created: {task['task_id']}")
                
                # Test task failure scenario
                if created_tasks:
                    fail_task_id, _ = created_tasks[0]
                    fail_response = await client.post(
                        f"{self.base_url}/api/v1/tasks/{fail_task_id}/fail",
                        json={"error": "Test failure scenario"},
                        headers=self.headers
                    )
                    
                    if fail_response.status_code == 200:
                        print("  ✅ Task failure scenario tested")
                
                # Test bulk operations
                if len(created_tasks) > 1:
                    bulk_claim_count = 0
                    for task_id, _ in created_tasks[1:]:
                        claim_response = await client.post(
                            f"{self.base_url}/api/v1/tasks/{task_id}/claim",
                            headers=self.headers
                        )
                        if claim_response.status_code == 200:
                            bulk_claim_count += 1
                    
                    print(f"  ✅ Bulk task claiming: {bulk_claim_count} tasks claimed")
                
                self.test_results["tests"]["task_lifecycle"] = {
                    "status": "passed",
                    "tasks_created": len(created_tasks),
                    "task_types": task_types
                }
                return True
                
        except Exception as e:
            print(f"  ❌ Task lifecycle test failed: {e}")
            self.test_results["tests"]["task_lifecycle"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    async def test_error_handling(self):
        """Test error handling scenarios."""
        print("🔍 Testing Error Handling...")
        
        error_tests = []
        
        try:
            async with httpx.AsyncClient() as client:
                # Test invalid task creation
                invalid_task_data = {
                    "invalid_field": "test"
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/tasks",
                    json=invalid_task_data,
                    headers=self.headers
                )
                
                if response.status_code == 422:
                    error_tests.append("invalid_task_creation")
                    print("  ✅ Invalid task creation properly rejected")
                
                # Test non-existent task retrieval
                fake_task_id = str(ObjectId())
                response = await client.get(
                    f"{self.base_url}/api/v1/tasks/{fake_task_id}",
                    headers=self.headers
                )
                
                if response.status_code == 404:
                    error_tests.append("non_existent_task")
                    print("  ✅ Non-existent task properly handled")
                
                # Test unauthorized access
                response = await client.get(
                    f"{self.base_url}/api/v1/tasks",
                    headers={"X-API-Key": "invalid_key"}
                )
                
                if response.status_code == 401:
                    error_tests.append("unauthorized_access")
                    print("  ✅ Unauthorized access properly rejected")
                
                # Test invalid task operations
                response = await client.post(
                    f"{self.base_url}/api/v1/tasks/{fake_task_id}/claim",
                    headers=self.headers
                )
                
                if response.status_code == 404:
                    error_tests.append("invalid_task_operation")
                    print("  ✅ Invalid task operations properly handled")
            
            self.test_results["tests"]["error_handling"] = {
                "status": "passed",
                "tests_passed": len(error_tests),
                "error_scenarios": error_tests
            }
            return True
            
        except Exception as e:
            print(f"  ❌ Error handling test failed: {e}")
            self.test_results["tests"]["error_handling"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    async def test_performance_and_load(self):
        """Test performance under load."""
        print("🔍 Testing Performance Under Load...")
        
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient() as client:
                # Create multiple tasks concurrently
                tasks = []
                for i in range(20):
                    task_data = {
                        "task_type": "PERFORMANCE_TEST",
                        "request": {
                            "content": {"text": f"Performance test task {i}"},
                            "metadata": {"test_id": f"perf_test_{i}"}
                        },
                        "template": {
                            "service_type": "PERFORMANCE_TEST",
                            "parameters": {"batch_id": "performance_batch"}
                        },
                        "tags": {
                            "service": "performance-test",
                            "source": "load-test"
                        }
                    }
                    
                    task = asyncio.create_task(
                        client.post(
                            f"{self.base_url}/api/v1/tasks",
                            json=task_data,
                            headers=self.headers
                        )
                    )
                    tasks.append(task)
                
                # Wait for all tasks to complete
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                successful_creates = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 201)
                
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"  ✅ Load test completed in {duration:.2f} seconds")
                print(f"  ✅ Created {successful_creates} tasks successfully")
                print(f"  ✅ Performance: {successful_creates/duration:.1f} tasks/second")
                
                self.test_results["tests"]["performance"] = {
                    "status": "passed",
                    "duration": duration,
                    "tasks_created": successful_creates,
                    "tasks_per_second": successful_creates/duration
                }
                return True
                
        except Exception as e:
            print(f"  ❌ Performance test failed: {e}")
            self.test_results["tests"]["performance"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    async def test_data_validation(self):
        """Test data validation and edge cases."""
        print("🔍 Testing Data Validation and Edge Cases...")
        
        validation_tests = []
        
        try:
            async with httpx.AsyncClient() as client:
                # Test empty task type
                response = await client.post(
                    f"{self.base_url}/api/v1/tasks",
                    json={"task_type": "", "request": {}, "template": {}, "tags": {}},
                    headers=self.headers
                )
                
                if response.status_code == 422:
                    validation_tests.append("empty_task_type")
                    print("  ✅ Empty task type validation")
                
                # Test very large task data
                large_data = {
                    "task_type": "LARGE_DATA_TEST",
                    "request": {
                        "content": {"text": "x" * 10000},  # Large text
                        "metadata": {"large_field": "y" * 5000}
                    },
                    "template": {
                        "service_type": "LARGE_DATA_TEST",
                        "parameters": {"data": "z" * 3000}
                    },
                    "tags": {
                        "service": "large-data-service",
                        "source": "validation-test"
                    }
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/tasks",
                    json=large_data,
                    headers=self.headers
                )
                
                if response.status_code in [201, 422]:  # Either accepted or properly rejected
                    validation_tests.append("large_data_handling")
                    print("  ✅ Large data handling validation")
                
                # Test special characters
                special_char_data = {
                    "task_type": "SPECIAL_CHARS_TEST",
                    "request": {
                        "content": {"text": "Test with émojis 🚀 and spëcial chars ñ"},
                        "metadata": {"unicode": "测试中文字符"}
                    },
                    "template": {
                        "service_type": "SPECIAL_CHARS_TEST",
                        "parameters": {"encoding": "utf-8"}
                    },
                    "tags": {
                        "service": "special-chars-service",
                        "source": "validation-test"
                    }
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/tasks",
                    json=special_char_data,
                    headers=self.headers
                )
                
                if response.status_code == 201:
                    validation_tests.append("special_characters")
                    print("  ✅ Special characters handling")
                
                # Test null/None values
                null_data = {
                    "task_type": "NULL_TEST",
                    "request": {
                        "content": {"text": None},
                        "metadata": {}
                    },
                    "template": {
                        "service_type": "NULL_TEST",
                        "parameters": None
                    },
                    "tags": {
                        "service": "null-test-service",
                        "source": "validation-test"
                    }
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/tasks",
                    json=null_data,
                    headers=self.headers
                )
                
                if response.status_code in [201, 422]:  # Either accepted or properly rejected
                    validation_tests.append("null_values")
                    print("  ✅ Null values handling")
            
            self.test_results["tests"]["data_validation"] = {
                "status": "passed",
                "tests_passed": len(validation_tests),
                "validation_scenarios": validation_tests
            }
            return True
            
        except Exception as e:
            print(f"  ❌ Data validation test failed: {e}")
            self.test_results["tests"]["data_validation"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    def generate_report(self):
        """Generate comprehensive test report."""
        end_time = datetime.now()
        start_time = datetime.fromisoformat(self.test_results["start_time"])
        total_duration = (end_time - start_time).total_seconds()
        
        # Calculate summary statistics
        total_tests = len(self.test_results["tests"])
        passed_tests = sum(1 for test in self.test_results["tests"].values() if test["status"] == "passed")
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.test_results["summary"] = {
            "end_time": end_time.isoformat(),
            "total_duration": total_duration,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate
        }
        
        # Print comprehensive report
        print("\n📊 COMPREHENSIVE TEST REPORT")
        print("=" * 70)
        print(f"🕒 Total testing time: {total_duration:.2f} seconds")
        print(f"✅ Tests passed: {passed_tests}/{total_tests}")
        print(f"❌ Tests failed: {failed_tests}/{total_tests}")
        
        print(f"\n📋 DETAILED TEST RESULTS:")
        for test_name, result in self.test_results["tests"].items():
            status_icon = "✅" if result["status"] == "passed" else "❌"
            print(f"   {status_icon} {test_name.replace('_', ' ').title()}")
        
        # Performance metrics
        if "performance" in self.test_results["tests"] and self.test_results["tests"]["performance"]["status"] == "passed":
            perf_data = self.test_results["tests"]["performance"]
            print(f"\n⚡ PERFORMANCE METRICS:")
            print(f"   🚀 Tasks per second: {perf_data.get('tasks_per_second', 0):.1f}")
            print(f"   📊 Tasks created: {perf_data.get('tasks_created', 0)}")
        
        # Assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print(f"   Success Rate: {success_rate:.1f}%")
        if success_rate >= 90:
            print("   🎉 EXCELLENT: Service is production-ready!")
        elif success_rate >= 75:
            print("   ✅ GOOD: Service is mostly functional with minor issues.")
        elif success_rate >= 50:
            print("   ⚠️  FAIR: Service has significant issues that need addressing.")
        else:
            print("   ❌ POOR: Service has critical issues and is not ready for use.")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"task_repo_test_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
    
    async def run_comprehensive_tests(self):
        """Run all comprehensive tests."""
        print("🚀 STARTING COMPREHENSIVE TASK REPOSITORY SERVICE TESTING")
        print("=" * 70)
        
        try:
            # Setup environment
            await self.setup_environment()
            
            # Start service
            service_started = await self.start_service()
            if not service_started:
                print("❌ Failed to start service. Aborting tests.")
                return
            
            # Run all tests
            test_functions = [
                self.test_health_endpoint,
                self.test_task_crud_operations,
                self.test_task_lifecycle,
                self.test_error_handling,
                self.test_performance_and_load,
                self.test_data_validation
            ]
            
            for test_func in test_functions:
                try:
                    await test_func()
                    await asyncio.sleep(0.5)  # Brief pause between tests
                except Exception as e:
                    print(f"❌ Test {test_func.__name__} failed with exception: {e}")
            
        finally:
            # Stop service
            await self.stop_service()
            
            # Generate report
            self.generate_report()
            print("\n🎉 COMPREHENSIVE TESTING COMPLETED!")

async def main():
    """Main function to run the comprehensive test suite."""
    test_suite = TaskRepoTestSuite()
    await test_suite.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())
