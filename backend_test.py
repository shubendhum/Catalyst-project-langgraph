import requests
import sys
import json
import time
from datetime import datetime

class CatalystAPITester:
    def __init__(self, base_url="https://agent-orchestra-11.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.project_id = None
        self.task_id = None
        self.conversation_id = None

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
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

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

    # ==================== CHAT INTERFACE TESTS ====================
    
    def test_set_llm_config_emergent(self):
        """Test setting LLM config to emergent provider"""
        config_data = {
            "provider": "emergent",
            "model": "claude-3-7-sonnet-20250219",
            "api_key": None,
            "aws_config": None
        }
        
        success, response = self.run_test(
            "Set LLM Config (Emergent)",
            "POST",
            "chat/config",
            200,
            data=config_data
        )
        
        if success and response.get("status") == "success":
            print(f"   Provider: {response.get('config', {}).get('provider')}")
            print(f"   Model: {response.get('config', {}).get('model')}")
            return True
        return False

    def test_set_llm_config_anthropic(self):
        """Test setting LLM config to anthropic provider"""
        config_data = {
            "provider": "anthropic",
            "model": "claude-3-sonnet-20240229",
            "api_key": "test-key",
            "aws_config": None
        }
        
        success, response = self.run_test(
            "Set LLM Config (Anthropic)",
            "POST",
            "chat/config",
            200,
            data=config_data
        )
        
        if success and response.get("status") == "success":
            print(f"   Provider: {response.get('config', {}).get('provider')}")
            return True
        return False

    def test_set_llm_config_bedrock(self):
        """Test setting LLM config to bedrock provider"""
        config_data = {
            "provider": "bedrock",
            "model": "anthropic.claude-3-sonnet-20240229-v1:0",
            "api_key": None,
            "aws_config": {
                "access_key_id": "test-key",
                "secret_access_key": "test-secret",
                "region": "us-east-1"
            }
        }
        
        success, response = self.run_test(
            "Set LLM Config (Bedrock)",
            "POST",
            "chat/config",
            200,
            data=config_data
        )
        
        if success and response.get("status") == "success":
            print(f"   Provider: {response.get('config', {}).get('provider')}")
            return True
        return False

    def test_get_llm_config(self):
        """Test getting current LLM config"""
        success, response = self.run_test(
            "Get LLM Config",
            "GET",
            "chat/config",
            200
        )
        
        if success and "provider" in response:
            print(f"   Provider: {response.get('provider')}")
            print(f"   Model: {response.get('model')}")
            print(f"   API Key: {response.get('api_key', 'None')}")
            return True
        return False

    def test_create_conversation(self):
        """Test creating a new conversation"""
        success, response = self.run_test(
            "Create Conversation",
            "POST",
            "chat/conversations",
            200
        )
        
        if success and "id" in response:
            self.conversation_id = response["id"]
            print(f"   Conversation ID: {self.conversation_id}")
            print(f"   Title: {response.get('title')}")
            return True
        return False

    def test_list_conversations(self):
        """Test listing all conversations"""
        success, response = self.run_test(
            "List Conversations",
            "GET",
            "chat/conversations",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} conversations")
            return True
        return False

    def test_get_conversation(self):
        """Test getting specific conversation"""
        if not self.conversation_id:
            print("❌ Skipping - No conversation ID available")
            return False
            
        success, response = self.run_test(
            "Get Conversation",
            "GET",
            f"chat/conversations/{self.conversation_id}",
            200
        )
        
        if success and response.get("id") == self.conversation_id:
            print(f"   Title: {response.get('title')}")
            print(f"   Messages: {len(response.get('messages', []))}")
            return True
        return False

    def test_send_help_message(self):
        """Test sending help message"""
        if not self.conversation_id:
            print("❌ Skipping - No conversation ID available")
            return False
            
        message_data = {
            "message": "help",
            "conversation_id": self.conversation_id
        }
        
        success, response = self.run_test(
            "Send Help Message",
            "POST",
            "chat/send",
            200,
            data=message_data,
            timeout=60
        )
        
        if success and response.get("status") == "success":
            message_content = response.get("message", {}).get("content", "")
            print(f"   Response length: {len(message_content)} chars")
            print(f"   Contains help info: {'help' in message_content.lower()}")
            return True
        return False

    def test_send_create_project_message(self):
        """Test sending create project message"""
        if not self.conversation_id:
            print("❌ Skipping - No conversation ID available")
            return False
            
        message_data = {
            "message": "create a new project called TestChatApp for testing the chat interface",
            "conversation_id": self.conversation_id
        }
        
        success, response = self.run_test(
            "Send Create Project Message",
            "POST",
            "chat/send",
            200,
            data=message_data,
            timeout=60
        )
        
        if success and response.get("status") == "success":
            message_content = response.get("message", {}).get("content", "")
            metadata = response.get("message", {}).get("metadata", {})
            print(f"   Response: {message_content[:100]}...")
            print(f"   Action: {metadata.get('action')}")
            if metadata.get("project_id"):
                print(f"   Project ID: {metadata.get('project_id')}")
            return True
        return False

    def test_send_build_app_message(self):
        """Test sending build app message"""
        if not self.conversation_id:
            print("❌ Skipping - No conversation ID available")
            return False
            
        message_data = {
            "message": "build me a simple todo list app with React frontend and FastAPI backend",
            "conversation_id": self.conversation_id
        }
        
        success, response = self.run_test(
            "Send Build App Message",
            "POST",
            "chat/send",
            200,
            data=message_data,
            timeout=60
        )
        
        if success and response.get("status") == "success":
            message_content = response.get("message", {}).get("content", "")
            metadata = response.get("message", {}).get("metadata", {})
            print(f"   Response: {message_content[:100]}...")
            print(f"   Action: {metadata.get('action')}")
            if metadata.get("task_id"):
                print(f"   Task ID: {metadata.get('task_id')}")
            return True
        return False

    def test_send_status_message(self):
        """Test sending status check message"""
        if not self.conversation_id:
            print("❌ Skipping - No conversation ID available")
            return False
            
        message_data = {
            "message": "what's the status?",
            "conversation_id": self.conversation_id
        }
        
        success, response = self.run_test(
            "Send Status Message",
            "POST",
            "chat/send",
            200,
            data=message_data,
            timeout=60
        )
        
        if success and response.get("status") == "success":
            message_content = response.get("message", {}).get("content", "")
            metadata = response.get("message", {}).get("metadata", {})
            print(f"   Response: {message_content[:100]}...")
            print(f"   Action: {metadata.get('action')}")
            return True
        return False

    def test_get_conversation_messages(self):
        """Test getting conversation messages"""
        if not self.conversation_id:
            print("❌ Skipping - No conversation ID available")
            return False
            
        success, response = self.run_test(
            "Get Conversation Messages",
            "GET",
            f"chat/conversations/{self.conversation_id}/messages",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} messages")
            for i, msg in enumerate(response[:3]):  # Show first 3 messages
                print(f"   Message {i+1}: {msg.get('role')} - {msg.get('content', '')[:50]}...")
            return True
        return False

    def test_delete_conversation(self):
        """Test deleting a conversation"""
        if not self.conversation_id:
            print("❌ Skipping - No conversation ID available")
            return False
            
        success, response = self.run_test(
            "Delete Conversation",
            "DELETE",
            f"chat/conversations/{self.conversation_id}",
            200
        )
        
        if success and response.get("status") == "success":
            print(f"   Message: {response.get('message')}")
            return True
        return False

def main():
    print("🚀 Starting Catalyst API Testing...")
    print("=" * 60)
    
    tester = CatalystAPITester()
    
    # Test sequence - focusing on chat interface as requested
    tests = [
        ("API Root", tester.test_api_root),
        
        # Chat Interface Tests (HIGH PRIORITY)
        ("Set LLM Config (Emergent)", tester.test_set_llm_config_emergent),
        ("Get LLM Config", tester.test_get_llm_config),
        ("Set LLM Config (Anthropic)", tester.test_set_llm_config_anthropic),
        ("Set LLM Config (Bedrock)", tester.test_set_llm_config_bedrock),
        ("Create Conversation", tester.test_create_conversation),
        ("List Conversations", tester.test_list_conversations),
        ("Get Conversation", tester.test_get_conversation),
        ("Send Help Message", tester.test_send_help_message),
        ("Send Create Project Message", tester.test_send_create_project_message),
        ("Send Build App Message", tester.test_send_build_app_message),
        ("Send Status Message", tester.test_send_status_message),
        ("Get Conversation Messages", tester.test_get_conversation_messages),
        ("Delete Conversation", tester.test_delete_conversation),
        
        # Original Tests (for completeness)
        ("Create Project", tester.test_create_project),
        ("Get Projects", tester.test_get_projects),
        ("Get Project", tester.test_get_project),
        ("Create Task", tester.test_create_task),
        ("Get Tasks", tester.test_get_tasks),
        ("Get Task", tester.test_get_task),
        ("Get Agent Logs", tester.test_get_logs),
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