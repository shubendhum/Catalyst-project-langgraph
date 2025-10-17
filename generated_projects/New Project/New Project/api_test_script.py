import httpx
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys

# Configure base URL - change to your actual API server
BASE_URL = "http://localhost:8000"

class ApiTest:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url)
        self.test_results: List[Dict[str, Any]] = []
        
    def run_test(self, name: str, method: str, endpoint: str, 
                 expected_status: int, headers: Dict = None, 
                 params: Dict = None, json_data: Dict = None, 
                 path_params: Dict = None) -> Dict[str, Any]:
        """Run a test against an API endpoint and record results"""
        
        if headers is None:
            headers = {}
        
        # Replace path parameters if any
        if path_params:
            for key, value in path_params.items():
                placeholder = f"{{{key}}}"
                endpoint = endpoint.replace(placeholder, str(value))
        
        start_time = time.time()
        
        try:
            response = self.client.request(
                method=method,
                url=endpoint,
                headers=headers,
                params=params,
                json=json_data,
                timeout=10.0
            )
            
            duration = time.time() - start_time
            
            try:
                response_data = response.json() if response.content else None
            except json.JSONDecodeError:
                response_data = {"error": "Invalid JSON response", "content": response.text[:100]}
            
            result = {
                "test_name": name,
                "method": method,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "headers": dict(headers) if headers else {},
                "params": dict(params) if params else {},
                "data": json_data,
                "response": response_data,
                "duration_ms": round(duration * 1000, 2),
                "success": response.status_code == expected_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            duration = time.time() - start_time
            result = {
                "test_name": name,
                "method": method,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "error": str(e),
                "headers": dict(headers) if headers else {},
                "params": dict(params) if params else {},
                "data": json_data,
                "duration_ms": round(duration * 1000, 2),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
        
        self.test_results.append(result)
        return result
    
    def print_test_result(self, result: Dict[str, Any]) -> None:
        """Print a formatted test result"""
        status = "✅ PASS" if result.get("success") else "❌ FAIL"
        print(f"\n{status} - {result['test_name']}")
        print(f"  URL: {result['method']} {result['endpoint']}")
        
        if "error" in result:
            print(f"  ERROR: {result['error']}")
        else:
            print(f"  Status: {result.get('actual_status')} (expected: {result['expected_status']})")
            
        print(f"  Duration: {result['duration_ms']} ms")
        
        if result.get('data'):
            print(f"  Request Data: {json.dumps(result['data'], indent=2)}")
        
        if result.get('response'):
            print(f"  Response Data: {json.dumps(result['response'], indent=2)}")
    
    def print_summary(self) -> None:
        """Print test summary statistics"""
        total = len(self.test_results)
        passed = sum(1 for result in self.test_results if result.get("success"))
        failed = total - passed
        
        print("\n=== TEST SUMMARY ===")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    def get_json_summary(self) -> Dict[str, Any]:
        """Return a JSON-serializable summary of all test results"""
        total = len(self.test_results)
        passed = sum(1 for result in self.test_results if result.get("success"))
        failed = total - passed
        
        return {
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "success_rate": round((passed/total)*100, 1) if total > 0 else 0
            },
            "results": self.test_results
        }
    
    def save_results(self, filename: str) -> None:
        """Save test results to a JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.get_json_summary(), f, indent=2)
        print(f"\nResults saved to {filename}")

def main():
    print("=== API ENDPOINT TEST RUNNER ===")
    print(f"Base URL: {BASE_URL}")
    print("Running tests...\n")
    
    tester = ApiTest(BASE_URL)
    
    # Test 1: GET /api/greeting - Valid Case
    result = tester.run_test(
        name="Get default greeting",
        method="GET",
        endpoint="/api/greeting",
        expected_status=200
    )
    tester.print_test_result(result)
    
    # Test 2: GET /api/greeting/{name} - Valid Case
    result = tester.run_test(
        name="Get personalized greeting",
        method="GET",
        endpoint="/api/greeting/{name}",
        path_params={"name": "Alice"},
        expected_status=200
    )
    tester.print_test_result(result)
    
    # Test 3: GET /api/greeting/{name} - Invalid name (empty)
    result = tester.run_test(
        name="Get personalized greeting with empty name",
        method="GET",
        endpoint="/api/greeting/{name}",
        path_params={"name": ""},
        expected_status=422  # Expecting validation error
    )
    tester.print_test_result(result)
    
    # Test 4: POST /api/greeting - Valid Case
    result = tester.run_test(
        name="Save new greeting",
        method="POST",
        endpoint="/api/greeting",
        headers={"Content-Type": "application/json"},
        json_data={"name": "Bob"},
        expected_status=201
    )
    tester.print_test_result(result)
    
    # Test 5: POST /api/greeting - Invalid Case (missing name)
    result = tester.run_test(
        name="Save greeting without name",
        method="POST",
        endpoint="/api/greeting",
        headers={"Content-Type": "application/json"},
        json_data={},
        expected_status=422  # Expecting validation error
    )
    tester.print_test_result(result)
    
    # Test 6: GET /api/greetings - Get history
    result = tester.run_test(
        name="Get greetings history",
        method="GET",
        endpoint="/api/greetings",
        expected_status=200
    )
    tester.print_test_result(result)
    
    # Print summary and save results
    tester.print_summary()
    tester.save_results("api_test_results.json")
    
    # Return a JSON summary for programmatic use
    return tester.get_json_summary()

if __name__ == "__main__":
    try:
        results = main()
        # Return JSON to stdout if needed as final output
        # Uncomment the next line if you want the full JSON output at the end
        # print(json.dumps(results, indent=2))
        
        # Exit with proper status code
        sys.exit(0 if results["summary"]["failed"] == 0 else 1)
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(2)