import requests
import sys
import json
import time
from datetime import datetime

class CatalystAPITester:
    def __init__(self, base_url="https://dev-catalyst-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.project_id = None
        self.task_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout after {timeout}s")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_api_root(self):
        """Test API root endpoint"""
        success, response = self.run_test(
            "API Root",
            "GET",
            "",
            200
        )
        return success

    def test_create_project(self):
        """Test project creation"""
        project_data = {
            "name": f"Test Project {datetime.now().strftime('%H%M%S')}",
            "description": "Test project for API validation"
        }
        
        success, response = self.run_test(
            "Create Project",
            "POST",
            "projects",
            200,
            data=project_data
        )
        
        if success and 'id' in response:
            self.project_id = response['id']
            print(f"   Project ID: {self.project_id}")
            return True
        return False

    def test_get_projects(self):
        """Test getting all projects"""
        success, response = self.run_test(
            "Get Projects",
            "GET",
            "projects",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} projects")
            return True
        return False

    def test_get_project(self):
        """Test getting specific project"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
            
        success, response = self.run_test(
            "Get Project by ID",
            "GET",
            f"projects/{self.project_id}",
            200
        )
        
        if success and response.get('id') == self.project_id:
            print(f"   Project name: {response.get('name')}")
            return True
        return False

    def test_create_task(self):
        """Test task creation and multi-agent execution"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
            
        task_data = {
            "project_id": self.project_id,
            "prompt": "Create a simple todo list app with React frontend"
        }
        
        success, response = self.run_test(
            "Create Task",
            "POST",
            "tasks",
            200,
            data=task_data
        )
        
        if success and 'id' in response:
            self.task_id = response['id']
            print(f"   Task ID: {self.task_id}")
            print(f"   Status: {response.get('status')}")
            return True
        return False

    def test_get_tasks(self):
        """Test getting tasks"""
        success, response = self.run_test(
            "Get Tasks",
            "GET",
            f"tasks?project_id={self.project_id}",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} tasks")
            return True
        return False

    def test_get_task(self):
        """Test getting specific task"""
        if not self.task_id:
            print("❌ Skipping - No task ID available")
            return False
            
        success, response = self.run_test(
            "Get Task by ID",
            "GET",
            f"tasks/{self.task_id}",
            200
        )
        
        if success and response.get('id') == self.task_id:
            print(f"   Task status: {response.get('status')}")
            print(f"   Task cost: ${response.get('cost', 0)}")
            print(f"   Graph state: {response.get('graph_state', {})}")
            return True
        return False

    def test_wait_for_task_completion(self, max_wait=120):
        """Wait for task to complete and test agent execution"""
        if not self.task_id:
            print("❌ Skipping - No task ID available")
            return False
            
        print(f"\n⏳ Waiting for task completion (max {max_wait}s)...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            success, response = self.run_test(
                "Check Task Progress",
                "GET",
                f"tasks/{self.task_id}",
                200
            )
            
            if success:
                status = response.get('status')
                graph_state = response.get('graph_state', {})
                
                print(f"   Status: {status}")
                print(f"   Agents completed: {list(graph_state.keys())}")
                
                if status in ['completed', 'failed']:
                    print(f"✅ Task finished with status: {status}")
                    return status == 'completed'
                    
            time.sleep(5)
        
        print(f"❌ Task did not complete within {max_wait}s")
        return False

    def test_get_logs(self):
        """Test getting agent logs"""
        if not self.task_id:
            print("❌ Skipping - No task ID available")
            return False
            
        success, response = self.run_test(
            "Get Agent Logs",
            "GET",
            f"logs/{self.task_id}",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} log entries")
            if response:
                agents = set(log.get('agent_name') for log in response)
                print(f"   Agents logged: {list(agents)}")
            return True
        return False

    def test_get_deployment(self):
        """Test getting deployment info"""
        if not self.task_id:
            print("❌ Skipping - No task ID available")
            return False
            
        success, response = self.run_test(
            "Get Deployment",
            "GET",
            f"deployments/{self.task_id}",
            200
        )
        
        if success:
            print(f"   Deployment URL: {response.get('url')}")
            print(f"   Commit SHA: {response.get('commit_sha')}")
            print(f"   Cost: ${response.get('cost', 0)}")
            return True
        return False

    def test_explorer_scan(self):
        """Test Explorer agent scanning"""
        scan_data = {
            "system_name": "SailPoint IdentityIQ",
            "repo_url": "https://github.com/sailpoint/identityiq",
            "jira_project": "SAIL"
        }
        
        success, response = self.run_test(
            "Explorer Scan",
            "POST",
            "explorer/scan",
            200,
            data=scan_data
        )
        
        if success:
            print(f"   System: {response.get('system_name')}")
            print(f"   Brief: {response.get('brief', '')[:100]}...")
            print(f"   Risks: {len(response.get('risks', []))} identified")
            print(f"   Proposals: {len(response.get('proposals', []))} suggested")
            return True
        return False

    def test_get_explorer_scans(self):
        """Test getting explorer scans"""
        success, response = self.run_test(
            "Get Explorer Scans",
            "GET",
            "explorer/scans",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} scans")
            return True
        return False

def main():
    print("🚀 Starting Catalyst API Testing...")
    print("=" * 60)
    
    tester = CatalystAPITester()
    
    # Test sequence
    tests = [
        ("API Root", tester.test_api_root),
        ("Create Project", tester.test_create_project),
        ("Get Projects", tester.test_get_projects),
        ("Get Project", tester.test_get_project),
        ("Create Task", tester.test_create_task),
        ("Get Tasks", tester.test_get_tasks),
        ("Get Task", tester.test_get_task),
        ("Wait for Task Completion", tester.test_wait_for_task_completion),
        ("Get Agent Logs", tester.test_get_logs),
        ("Get Deployment", tester.test_get_deployment),
        ("Explorer Scan", tester.test_explorer_scan),
        ("Get Explorer Scans", tester.test_get_explorer_scans),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    # Print final results
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())