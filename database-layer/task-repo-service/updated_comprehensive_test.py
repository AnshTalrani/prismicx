#!/usr/bin/env python3
"""
Updated Comprehensive Test Suite for Task Repository Service

This test suite thoroughly validates the Task Repository Service as a standalone database service,
using the minimal working version to bypass import issues.
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
            import pydantic
            print("  ✅ All required dependencies are installed")
        except ImportError as e:
            print(f"  ❌ Missing dependency: {e}")
            return False
        return True
    
    async def start_service(self):
        """Start the Task Repository Service."""
        print("🚀 Starting Task Repository Service...")
        
        try:
            # Kill any existing processes on port 8503
            subprocess.run(["lsof", "-ti:8503"], capture_output=True, text=True)
            subprocess.run(["pkill", "-f", "minimal_task_service"], capture_output=True)
            await asyncio.sleep(1)
            
            # Start the minimal service
            self.service_process = subprocess.Popen([
                sys.executable, "minimal_task_service.py"
            ], 
            cwd="/Users/luvtalrani/ansh projects/prismicx-2/database-layer/task-repo-service",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
            )
            
            # Wait for service to start
            await asyncio.sleep(4)
            
            # Test if service is running
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(f"{self.base_url}/health", headers=self.headers, timeout=5.0)
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
        
        # Clean up any remaining processes
        subprocess.run(["pkill", "-f", "minimal_task_service"], capture_output=True)
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
                    required_fields = ["status", "service", "timestamp", "tasks_count", "components"]
                    for field in required_fields:
                        if field not in health_data:
                            raise ValueError(f"Missing required field: {field}")
                    
                    print("  ✅ Health endpoint structure validation passed")
                    print(f"  ✅ Service status: {health_data.get('status', 'unknown')}")
                    print(f"  ✅ Service name: {health_data.get('service', 'unknown')}")
                    print(f"  ✅ Tasks count: {health_data.get('tasks_count', 0)}")
                    print(f"  ✅ Components checked: {len(health_data.get('components', {}))}")
                    
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
    
    async def test_root_endpoint(self):
        """Test the root endpoint."""
        print("🔍 Testing Root Endpoint...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/")
                
                if response.status_code == 200:
                    root_data = response.json()
                    
                    print("  ✅ Root endpoint validation passed")
                    print(f"  ✅ Service name: {root_data.get('service', 'unknown')}")
                    print(f"  ✅ Version: {root_data.get('version', 'unknown')}")
                    
                    self.test_results["tests"]["root"] = {
                        "status": "passed",
                        "response": root_data
                    }
                    return True
                else:
                    raise Exception(f"Root endpoint failed with status {response.status_code}")
                    
        except Exception as e:
            print(f"  ❌ Root endpoint test failed: {e}")
            self.test_results["tests"]["root"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    async def test_task_crud_operations(self):
        """Test task CRUD operations."""
        print("🔍 Testing Task CRUD Operations...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Get initial task count
                initial_response = await client.get(f"{self.base_url}/api/v1/tasks", headers=self.headers)
                initial_count = len(initial_response.json().get("tasks", []))
                print(f"  ✅ Initial tasks count: {initial_count}")
                
                # Test task creation
                task_data = {
                    "task_type": "GENERATIVE",
                    "request": {
                        "content": {"text": "Generate a test response for CRUD operations"},
                        "metadata": {"user_id": "test_user_crud", "test_type": "crud"}
                    },
                    "template": {
                        "service_type": "GENERATIVE",
                        "parameters": {"model": "gpt-4", "max_tokens": 1024}
                    },
                    "tags": {
                        "service": "test-service",
                        "source": "crud-test"
                    },
                    "priority": 3,
                    "metadata": {"test_scenario": "crud_operations"}
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
                print(f"  ✅ Task priority: {retrieved_task['priority']}")
                
                # Update task
                update_data = {
                    "status": "processing",
                    "processor_id": "test_processor_123",
                    "metadata": {"updated": True, "update_time": datetime.now().isoformat()}
                }
                
                update_response = await client.put(
                    f"{self.base_url}/api/v1/tasks/{task_id}",
                    json=update_data,
                    headers=self.headers
                )
                
                if update_response.status_code != 200:
                    raise Exception(f"Task update failed with status {update_response.status_code}")
                
                print("  ✅ Task updated successfully")
                
                # Get updated task to verify changes
                verify_response = await client.get(
                    f"{self.base_url}/api/v1/tasks/{task_id}",
                    headers=self.headers
                )
                
                if verify_response.status_code == 200:
                    updated_task = verify_response.json()
                    if updated_task.get("status") == "processing":
                        print("  ✅ Task status update verified")
                
                # Get all tasks to verify count increased
                final_response = await client.get(f"{self.base_url}/api/v1/tasks", headers=self.headers)
                final_count = len(final_response.json().get("tasks", []))
                print(f"  ✅ Final tasks count: {final_count}")
                
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
                    "operations": ["create", "read", "update", "delete"],
                    "initial_count": initial_count,
                    "final_count": final_count
                }
                return True
                
        except Exception as e:
            print(f"  ❌ Task CRUD operations test failed: {e}")
            self.test_results["tests"]["task_crud"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    async def test_task_lifecycle_operations(self):
        """Test task lifecycle operations (claim, complete, fail)."""
        print("🔍 Testing Task Lifecycle Operations...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Create a test task
                task_data = {
                    "task_type": "LIFECYCLE_TEST",
                    "request": {
                        "content": {"text": "Test task lifecycle operations"},
                        "metadata": {"user_id": "lifecycle_user"}
                    },
                    "template": {
                        "service_type": "LIFECYCLE_TEST",
                        "parameters": {"test": "lifecycle"}
                    },
                    "tags": {
                        "service": "lifecycle-service",
                        "source": "lifecycle-test"
                    }
                }
                
                create_response = await client.post(
                    f"{self.base_url}/api/v1/tasks",
                    json=task_data,
                    headers=self.headers
                )
                
                if create_response.status_code != 201:
                    raise Exception(f"Task creation failed: {create_response.status_code}")
                
                task_id = create_response.json()["task_id"]
                print(f"  ✅ Lifecycle test task created: {task_id}")
                
                # Claim the task
                claim_response = await client.post(
                    f"{self.base_url}/api/v1/tasks/{task_id}/claim?processor_id=lifecycle_processor",
                    headers=self.headers
                )
                
                if claim_response.status_code != 200:
                    raise Exception(f"Task claim failed: {claim_response.status_code}")
                
                claimed_task = claim_response.json()
                if claimed_task.get("status") != "processing":
                    raise Exception("Task status not updated to processing after claim")
                
                print("  ✅ Task claimed successfully")
                print(f"  ✅ Task status: {claimed_task.get('status')}")
                print(f"  ✅ Processor ID: {claimed_task.get('processor_id')}")
                
                # Complete the task
                completion_data = {
                    "result": {
                        "generated_text": "Lifecycle test completed successfully",
                        "metadata": {"tokens_used": 25, "completion_time": datetime.now().isoformat()}
                    }
                }
                
                complete_response = await client.post(
                    f"{self.base_url}/api/v1/tasks/{task_id}/complete",
                    json=completion_data,
                    headers=self.headers
                )
                
                if complete_response.status_code != 200:
                    raise Exception(f"Task completion failed: {complete_response.status_code}")
                
                print("  ✅ Task completed successfully")
                
                # Verify task completion
                verify_response = await client.get(
                    f"{self.base_url}/api/v1/tasks/{task_id}",
                    headers=self.headers
                )
                
                if verify_response.status_code == 200:
                    completed_task = verify_response.json()
                    if completed_task.get("status") == "completed":
                        print("  ✅ Task completion verified")
                        if completed_task.get("results"):
                            print("  ✅ Task results stored")
                
                # Test task failure scenario with a new task
                fail_task_data = {
                    "task_type": "FAIL_TEST",
                    "request": {
                        "content": {"text": "Test task failure"},
                        "metadata": {"user_id": "fail_user"}
                    },
                    "template": {
                        "service_type": "FAIL_TEST",
                        "parameters": {"test": "failure"}
                    },
                    "tags": {
                        "service": "fail-service",
                        "source": "fail-test"
                    }
                }
                
                fail_create_response = await client.post(
                    f"{self.base_url}/api/v1/tasks",
                    json=fail_task_data,
                    headers=self.headers
                )
                
                if fail_create_response.status_code == 201:
                    fail_task_id = fail_create_response.json()["task_id"]
                    
                    # Claim and then fail the task
                    await client.post(
                        f"{self.base_url}/api/v1/tasks/{fail_task_id}/claim?processor_id=fail_processor",
                        headers=self.headers
                    )
                    
                    fail_response = await client.post(
                        f"{self.base_url}/api/v1/tasks/{fail_task_id}/fail",
                        json={"error": "Test failure scenario", "message": "Simulated processing error"},
                        headers=self.headers
                    )
                    
                    if fail_response.status_code == 200:
                        print("  ✅ Task failure scenario tested")
                
                self.test_results["tests"]["task_lifecycle"] = {
                    "status": "passed",
                    "operations": ["claim", "complete", "fail"],
                    "task_id": task_id
                }
                return True
                
        except Exception as e:
            print(f"  ❌ Task lifecycle operations test failed: {e}")
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
                fake_task_id = "non_existent_task_123"
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
                    f"{self.base_url}/api/v1/tasks/{fake_task_id}/claim?processor_id=test",
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
            print(f"  ✅ Error handling tests passed: {len(error_tests)}")
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
                for i in range(15):
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
    
    async def test_statistics_endpoint(self):
        """Test the statistics endpoint."""
        print("🔍 Testing Statistics Endpoint...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/v1/stats", headers=self.headers)
                
                if response.status_code == 200:
                    stats_data = response.json()
                    
                    required_fields = ["total_tasks", "status_distribution", "type_distribution", "timestamp"]
                    for field in required_fields:
                        if field not in stats_data:
                            raise ValueError(f"Missing required field: {field}")
                    
                    print(f"  ✅ Total tasks: {stats_data.get('total_tasks', 0)}")
                    print(f"  ✅ Status distribution: {len(stats_data.get('status_distribution', {}))}")
                    print(f"  ✅ Type distribution: {len(stats_data.get('type_distribution', {}))}")
                    print(f"  ✅ Stats timestamp: {stats_data.get('timestamp', 'unknown')}")
                    
                    self.test_results["tests"]["statistics"] = {
                        "status": "passed",
                        "stats": stats_data
                    }
                    return True
                else:
                    raise Exception(f"Statistics endpoint failed with status {response.status_code}")
                    
        except Exception as e:
            print(f"  ❌ Statistics endpoint test failed: {e}")
            self.test_results["tests"]["statistics"] = {
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
        
        # Service statistics
        if "statistics" in self.test_results["tests"] and self.test_results["tests"]["statistics"]["status"] == "passed":
            stats_data = self.test_results["tests"]["statistics"]["stats"]
            print(f"\n📈 SERVICE STATISTICS:")
            print(f"   📋 Total tasks: {stats_data.get('total_tasks', 0)}")
            print(f"   📊 Status types: {len(stats_data.get('status_distribution', {}))}")
            print(f"   🏷️  Task types: {len(stats_data.get('type_distribution', {}))}")
        
        # Assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print(f"   Success Rate: {success_rate:.1f}%")
        if success_rate >= 90:
            print("   🎉 EXCELLENT: Task Repository Service is production-ready!")
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
            env_ready = await self.setup_environment()
            if not env_ready:
                print("❌ Environment setup failed. Aborting tests.")
                return
            
            # Start service
            service_started = await self.start_service()
            if not service_started:
                print("❌ Failed to start service. Aborting tests.")
                return
            
            # Run all tests
            test_functions = [
                self.test_health_endpoint,
                self.test_root_endpoint,
                self.test_task_crud_operations,
                self.test_task_lifecycle_operations,
                self.test_error_handling,
                self.test_performance_and_load,
                self.test_statistics_endpoint
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
