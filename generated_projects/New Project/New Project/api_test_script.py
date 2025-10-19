#!/usr/bin/env python3
"""
Todo API Testing Script

This script tests the Todo API endpoints using httpx.
It tests both valid data and error cases for each endpoint.
"""

import json
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class TestResult:
    """Class to store test results"""
    endpoint: str
    method: str
    description: str
    status_code: int
    expected_status_code: int
    success: bool
    error_message: Optional[str] = None
    response_data: Optional[Any] = None


class TodoApiTester:
    """Class to test Todo API endpoints"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.results: List[TestResult] = []
        self.test_todo_id = None
    
    def get_headers(self) -> Dict[str, str]:
        """Return headers for API requests"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def log_result(self, result: TestResult):
        """Log test result"""
        self.results.append(result)
        status = "✅ PASSED" if result.success else "❌ FAILED"
        print(f"{status} - {result.method} {result.endpoint} - {result.description}")
        if not result.success and result.error_message:
            print(f"  Error: {result.error_message}")

    async def test_get_todos(self, client: httpx.AsyncClient):
        """Test GET /api/todos endpoint"""
        endpoint = "/api/todos"
        
        # Test valid request
        response = await client.get(f"{self.base_url}{endpoint}", headers=self.get_headers())
        self.log_result(TestResult(
            endpoint=endpoint,
            method="GET",
            description="Get all todos",
            status_code=response.status_code,
            expected_status_code=200,
            success=response.status_code == 200,
            response_data=response.json() if response.status_code == 200 else None
        ))
        
        # Test with query params
        response = await client.get(
            f"{self.base_url}{endpoint}", 
            params={"completed": "false", "priority": "high"},
            headers=self.get_headers()
        )
        self.log_result(TestResult(
            endpoint=f"{endpoint}?completed=false&priority=high",
            method="GET",
            description="Get todos with filters",
            status_code=response.status_code,
            expected_status_code=200,
            success=response.status_code == 200,
            response_data=response.json() if response.status_code == 200 else None
        ))
        
        # Test unauthorized access
        response = await client.get(f"{self.base_url}{endpoint}")
        self.log_result(TestResult(
            endpoint=endpoint,
            method="GET",
            description="Get todos without authentication",
            status_code=response.status_code,
            expected_status_code=401,
            success=response.status_code == 401,
        ))

    async def test_create_todo(self, client: httpx.AsyncClient):
        """Test POST /api/todos endpoint"""
        endpoint = "/api/todos"
        
        # Test valid creation
        todo_data = {
            "title": "Test Todo",
            "description": "This is a test todo item",
            "priority": "high",
            "due_date": (datetime.now() + timedelta(days=1)).isoformat()
        }
        
        response = await client.post(
            f"{self.base_url}{endpoint}",
            headers=self.get_headers(),
            json=todo_data
        )
        
        success = response.status_code == 201
        if success and response.json().get("id"):
            self.test_todo_id = response.json().get("id")
        
        self.log_result(TestResult(
            endpoint=endpoint,
            method="POST",
            description="Create a new todo",
            status_code=response.status_code,
            expected_status_code=201,
            success=success,
            response_data=response.json() if success else None
        ))
        
        # Test invalid data
        invalid_todo = {"title": ""}
        response = await client.post(
            f"{self.base_url}{endpoint}",
            headers=self.get_headers(),
            json=invalid_todo
        )
        self.log_result(TestResult(
            endpoint=endpoint,
            method="POST",
            description="Create todo with invalid data",
            status_code=response.status_code,
            expected_status_code=400,
            success=response.status_code == 400,
        ))

    async def test_get_todo_by_id(self, client: httpx.AsyncClient):
        """Test GET /api/todos/{todo_id} endpoint"""
        if not self.test_todo_id:
            self.log_result(TestResult(
                endpoint="/api/todos/{todo_id}",
                method="GET",
                description="Get todo by ID - Skipped (No test todo created)",
                status_code=0,
                expected_status_code=200,
                success=False,
                error_message="No test todo ID available"
            ))
            return
        
        endpoint = f"/api/todos/{self.test_todo_id}"
        
        # Test valid request
        response = await client.get(f"{self.base_url}{endpoint}", headers=self.get_headers())
        self.log_result(TestResult(
            endpoint=endpoint,
            method="GET",
            description="Get todo by ID",
            status_code=response.status_code,
            expected_status_code=200,
            success=response.status_code == 200,
            response_data=response.json() if response.status_code == 200 else None
        ))
        
        # Test with non-existent ID
        fake_endpoint = f"/api/todos/nonexistentid123"
        response = await client.get(f"{self.base_url}{fake_endpoint}", headers=self.get_headers())
        self.log_result(TestResult(
            endpoint=fake_endpoint,
            method="GET",
            description="Get todo with non-existent ID",
            status_code=response.status_code,
            expected_status_code=404,
            success=response.status_code == 404,
        ))

    async def test_update_todo(self, client: httpx.AsyncClient):
        """Test PUT /api/todos/{todo_id} endpoint"""
        if not self.test_todo_id:
            self.log_result(TestResult(
                endpoint="/api/todos/{todo_id}",
                method="PUT",
                description="Update todo - Skipped (No test todo created)",
                status_code=0,
                expected_status_code=200,
                success=False,
                error_message="No test todo ID available"
            ))
            return
        
        endpoint = f"/api/todos/{self.test_todo_id}"
        
        # Test valid update
        update_data = {
            "title": "Updated Test Todo",
            "description": "This todo has been updated",
            "completed": True,
            "priority": "medium"
        }
        
        response = await client.put(
            f"{self.base_url}{endpoint}",
            headers=self.get_headers(),
            json=update_data
        )
        
        self.log_result(TestResult(
            endpoint=endpoint,
            method="PUT",
            description="Update todo",
            status_code=response.status_code,
            expected_status_code=200,
            success=response.status_code == 200,
            response_data=response.json() if response.status_code == 200 else None
        ))
        
        # Test update with invalid ID
        fake_endpoint = f"/api/todos/nonexistentid123"
        response = await client.put(
            f"{self.base_url}{fake_endpoint}",
            headers=self.get_headers(),
            json=update_data
        )
        self.log_result(TestResult(
            endpoint=fake_endpoint,
            method="PUT",
            description="Update todo with non-existent ID",
            status_code=response.status_code,
            expected_status_code=404,
            success=response.status_code == 404,
        ))

    async def test_toggle_todo_completion(self, client: httpx.AsyncClient):
        """Test PATCH /api/todos/{todo_id}/complete endpoint"""
        if not self.test_todo_id:
            self.log_result(TestResult(
                endpoint="/api/todos/{todo_id}/complete",
                method="PATCH",
                description="Toggle todo completion - Skipped (No test todo created)",
                status_code=0,
                expected_status_code=200,
                success=False,
                error_message="No test todo ID available"
            ))
            return
        
        endpoint = f"/api/todos/{self.test_todo_id}/complete"
        
        # Test toggle completion
        response = await client.patch(f"{self.base_url}{endpoint}", headers=self.get_headers())
        self.log_result(TestResult(
            endpoint=endpoint,
            method="PATCH",
            description="Toggle todo completion",
            status_code=response.status_code,
            expected_status_code=200,
            success=response.status_code == 200,
            response_data=response.json() if response.status_code == 200 else None
        ))
        
        # Test with non-existent ID
        fake_endpoint = f"/api/todos/nonexistentid123/complete"
        response = await client.patch(f"{self.base_url}{fake_endpoint}", headers=self.get_headers())
        self.log_result(TestResult(
            endpoint=fake_endpoint,
            method="PATCH",
            description="Toggle completion with non-existent ID",
            status_code=response.status_code,
            expected_status_code=404,
            success=response.status_code == 404,
        ))

    async def test_delete_todo(self, client: httpx.AsyncClient):
        """Test DELETE /api/todos/{todo_id} endpoint"""
        if not self.test_todo_id:
            self.log_result(TestResult(
                endpoint="/api/todos/{todo_id}",
                method="DELETE",
                description="Delete todo - Skipped (No test todo created)",
                status_code=0,
                expected_status_code=204,
                success=False,
                error_message="No test todo ID available"
            ))
            return
        
        endpoint = f"/api/todos/{self.test_todo_id}"
        
        # Test valid deletion
        response = await client.delete(f"{self.base_url}{endpoint}", headers=self.get_headers())
        self.log_result(TestResult(
            endpoint=endpoint,
            method="DELETE",
            description="Delete todo",
            status_code=response.status_code,
            expected_status_code=204,
            success=response.status_code == 204,
        ))
        
        # Test delete with invalid ID
        fake_endpoint = f"/api/todos/nonexistentid123"
        response = await client.delete(f"{self.base_url}{fake_endpoint}", headers=self.get_headers())
        self.log_result(TestResult(
            endpoint=fake_endpoint,
            method="DELETE",
            description="Delete todo with non-existent ID",
            status_code=response.status_code,
            expected_status_code=404,
            success=response.status_code == 404,
        ))

    def print_summary(self):
        """Print summary of test results"""
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result.success)
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 50)
        print(f"TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests / total_tests * 100):.2f}%")
        print("=" * 50)
        
        if failed_tests > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if not result.success:
                    print(f"- {result.method} {result.endpoint}: {result.description}")
                    if result.error_message:
                        print(f"  Error: {result.error_message}")
        
        # Return JSON summary
        summary_data = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "test_results": [
                {
                    "endpoint": result.endpoint,
                    "method": result.method,
                    "description": result.description,
                    "status_code": result.status_code,
                    "expected_status_code": result.expected_status_code,
                    "success": result.success,
                    "error_message": result.error_message
                }
                for result in self.results
            ]
        }
        
        with open("api_test_summary.json", "w") as f:
            json.dump(summary_data, f, indent=2)
        
        print("\nTest summary saved to api_test_summary.json")


async def run_tests():
    """Run all API tests"""
    # Configure these values for your API
    base_url = "https://api.example.com"  # Replace with your API base URL
    api_token = "your-api-token"  # Replace with your API token
    
    tester = TodoApiTester(base_url, api_token)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Starting API Tests...\n")
        
        # Test all endpoints
        await tester.test_get_todos(client)
        await tester.test_create_todo(client)
        await tester.test_get_todo_by_id(client)
        await tester.test_update_todo(client)
        await tester.test_toggle_todo_completion(client)
        await tester.test_delete_todo(client)
        
        # Print summary
        tester.print_summary()


if __name__ == "__main__":
    asyncio.run(run_tests())