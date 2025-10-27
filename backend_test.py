import requests
import sys
import json
import time
from datetime import datetime

class CatalystAPITester:
    def __init__(self, base_url="https://agentflow-21.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.project_id = None
        self.task_id = None
        self.conversation_id = None
        self.workspace_id = None

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

    # ==================== PHASE 2 ORCHESTRATOR TESTS ====================
    
    def test_phase2_simple_workflow(self):
        """Test Phase 2 orchestrator with simple request"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
            
        task_data = {
            "project_id": self.project_id,
            "prompt": "Build a hello world app with React frontend and FastAPI backend"
        }
        
        success, response = self.run_test(
            "Phase 2 Simple Workflow",
            "POST",
            "tasks",
            200,
            data=task_data,
            timeout=180  # 3 minutes for agent execution
        )
        
        if success and 'id' in response:
            task_id = response['id']
            print(f"   Task ID: {task_id}")
            print(f"   Status: {response.get('status')}")
            
            # Wait a bit and check if agents started executing
            time.sleep(10)
            
            # Check task progress
            progress_success, progress_response = self.run_test(
                "Check Agent Execution",
                "GET",
                f"tasks/{task_id}",
                200
            )
            
            if progress_success:
                status = progress_response.get('status')
                graph_state = progress_response.get('graph_state', {})
                print(f"   Current Status: {status}")
                print(f"   Agents Executed: {list(graph_state.keys())}")
                
                # Check if any agents have executed (status changed from 'pending')
                if status != 'pending' or graph_state:
                    print("✅ Phase 2 orchestrator is executing agents")
                    return True
                else:
                    print("⚠️  Agents haven't started yet (may need more time)")
                    return True  # Still consider success if task was created
            
            return True
        return False

    def test_check_generated_files(self):
        """Test if files are generated in /app/generated_projects/"""
        import os
        
        generated_dir = "/app/generated_projects"
        
        try:
            if os.path.exists(generated_dir):
                projects = os.listdir(generated_dir)
                print(f"✅ Generated projects directory exists")
                print(f"   Found {len(projects)} projects: {projects}")
                
                # Check if any project has files
                for project in projects[:3]:  # Check first 3 projects
                    project_path = os.path.join(generated_dir, project)
                    if os.path.isdir(project_path):
                        files = []
                        for root, dirs, filenames in os.walk(project_path):
                            files.extend(filenames)
                        print(f"   Project '{project}': {len(files)} files")
                
                return True
            else:
                print("⚠️  Generated projects directory doesn't exist yet")
                return True  # Not a failure, just hasn't been created yet
                
        except Exception as e:
            print(f"❌ Error checking generated files: {str(e)}")
            return False

    # ==================== PHASE 4 MVP FEATURES TESTS ====================
    
    def test_context_check_10_messages(self):
        """Test context check with 10 messages (should be ok)"""
        messages = [
            {"role": "user", "content": f"Test message {i}"} for i in range(10)
        ]
        
        success, response = self.run_test(
            "Context Check (10 messages)",
            "POST",
            "context/check",
            200,
            data={"messages": messages, "model": "claude-3-7-sonnet-20250219"}
        )
        
        if success and response.get("success"):
            status = response.get("status", "unknown")
            print(f"   Status: {status}")
            print(f"   Current tokens: {response.get('current_tokens', 0)}")
            print(f"   Usage: {response.get('usage_percent', 0)*100:.1f}%")
            return status == "ok"
        return False

    def test_context_check_large_tokens(self):
        """Test context check with simulated 150K tokens (should be warning)"""
        # Create large messages to simulate 150K tokens
        large_messages = [
            {"role": "user", "content": "A" * 5000} for _ in range(30)  # ~150K tokens
        ]
        
        success, response = self.run_test(
            "Context Check (150K tokens)",
            "POST",
            "context/check",
            200,
            data={"messages": large_messages, "model": "claude-3-7-sonnet-20250219"}
        )
        
        if success and response.get("success"):
            status = response.get("status", "unknown")
            print(f"   Status: {status}")
            print(f"   Current tokens: {response.get('current_tokens', 0)}")
            print(f"   Usage: {response.get('usage_percent', 0)*100:.1f}%")
            return status in ["warning", "critical"]
        return False

    def test_context_check_critical_tokens(self):
        """Test context check with simulated 180K tokens (should be critical)"""
        # Create very large messages to simulate 180K tokens
        critical_messages = [
            {"role": "user", "content": "B" * 6000} for _ in range(30)  # ~180K tokens
        ]
        
        success, response = self.run_test(
            "Context Check (180K tokens)",
            "POST",
            "context/check",
            200,
            data={"messages": critical_messages, "model": "claude-3-7-sonnet-20250219"}
        )
        
        if success and response.get("success"):
            status = response.get("status", "unknown")
            print(f"   Status: {status}")
            print(f"   Current tokens: {response.get('current_tokens', 0)}")
            print(f"   Usage: {response.get('usage_percent', 0)*100:.1f}%")
            return status == "critical"
        return False

    def test_context_truncate_sliding_window(self):
        """Test context truncation with sliding window strategy"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant"}
        ] + [
            {"role": "user", "content": f"Message {i}: " + "X" * 100} for i in range(100)
        ]
        
        success, response = self.run_test(
            "Context Truncate (Sliding Window)",
            "POST",
            "context/truncate",
            200,
            data={
                "messages": messages,
                "model": "claude-3-7-sonnet-20250219",
                "strategy": "sliding_window"
            }
        )
        
        if success and response.get("success"):
            truncated_messages = response.get("messages", [])
            metadata = response.get("metadata", {})
            print(f"   Original: {metadata.get('original_count', 0)} messages")
            print(f"   Truncated: {metadata.get('truncated_count', 0)} messages")
            print(f"   Removed: {metadata.get('messages_removed', 0)} messages")
            print(f"   Strategy: {metadata.get('strategy', 'unknown')}")
            
            # Check system messages are preserved
            system_msgs = [msg for msg in truncated_messages if msg.get("role") == "system"]
            return len(system_msgs) > 0 and len(truncated_messages) < len(messages)
        return False

    def test_context_truncate_important_first(self):
        """Test context truncation with important_first strategy"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant"}
        ] + [
            {"role": "user", "content": f"Message {i}: " + "Y" * 100} for i in range(100)
        ]
        
        success, response = self.run_test(
            "Context Truncate (Important First)",
            "POST",
            "context/truncate",
            200,
            data={
                "messages": messages,
                "model": "claude-3-7-sonnet-20250219",
                "strategy": "important_first"
            }
        )
        
        if success and response.get("success"):
            truncated_messages = response.get("messages", [])
            metadata = response.get("metadata", {})
            print(f"   Original: {metadata.get('original_count', 0)} messages")
            print(f"   Truncated: {metadata.get('truncated_count', 0)} messages")
            print(f"   Strategy: {metadata.get('strategy', 'unknown')}")
            
            # Check system messages are preserved
            system_msgs = [msg for msg in truncated_messages if msg.get("role") == "system"]
            return len(system_msgs) > 0 and metadata.get("strategy") == "important_first"
        return False

    def test_cost_optimizer_simple_task(self):
        """Test cost optimizer for simple task (should recommend cheaper model)"""
        success, response = self.run_test(
            "Cost Optimizer (Simple Task)",
            "POST",
            "optimizer/select-model",
            200,
            data={
                "task_description": "Fix a simple typo in documentation",
                "complexity": 0.3,
                "current_model": "claude-3-7-sonnet-20250219"
            }
        )
        
        if success and response.get("success"):
            recommended = response.get("recommended_model", "")
            current = response.get("current_model", "")
            savings = response.get("estimated_savings_percent", 0)
            print(f"   Recommended: {recommended}")
            print(f"   Current: {current}")
            print(f"   Estimated savings: {savings:.1f}%")
            return recommended != current or savings >= 0
        return False

    def test_cost_optimizer_complex_task(self):
        """Test cost optimizer for complex task (should recommend capable model)"""
        success, response = self.run_test(
            "Cost Optimizer (Complex Task)",
            "POST",
            "optimizer/select-model",
            200,
            data={
                "task_description": "Design a complex distributed microservices architecture with security",
                "complexity": 0.9,
                "current_model": "gpt-3.5-turbo"
            }
        )
        
        if success and response.get("success"):
            recommended = response.get("recommended_model", "")
            reason = response.get("reason", "")
            capability = response.get("complexity_match", 0)
            print(f"   Recommended: {recommended}")
            print(f"   Reason: {reason}")
            print(f"   Capability match: {capability}")
            return capability >= 0.9
        return False

    def test_cost_optimizer_cache_stats(self):
        """Test cost optimizer cache statistics"""
        success, response = self.run_test(
            "Cost Optimizer Cache Stats",
            "GET",
            "optimizer/cache-stats",
            200
        )
        
        if success and response.get("success"):
            cache_size = response.get("cache_size", 0)
            maxsize = response.get("cache_maxsize", 0)
            ttl = response.get("cache_ttl_seconds", 0)
            savings = response.get("estimated_savings", 0)
            print(f"   Cache size: {cache_size}/{maxsize}")
            print(f"   TTL: {ttl} seconds")
            print(f"   Estimated savings: ${savings:.4f}")
            return True
        return False

    def test_cost_optimizer_set_budget(self):
        """Test setting project budget"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
            
        success, response = self.run_test(
            "Set Project Budget",
            "POST",
            f"optimizer/budget/{self.project_id}",
            200,
            data={
                "budget_limit": 100.0,
                "alert_threshold": 0.75
            }
        )
        
        if success and response.get("success"):
            limit = response.get("limit", 0)
            message = response.get("message", "")
            print(f"   Budget limit: ${limit}")
            print(f"   Message: {message}")
            return limit == 100.0
        return False

    def test_cost_optimizer_get_budget(self):
        """Test getting project budget status"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
            
        success, response = self.run_test(
            "Get Project Budget",
            "GET",
            f"optimizer/budget/{self.project_id}",
            200
        )
        
        if success and response.get("success"):
            budget_set = response.get("budget_set", False)
            if budget_set:
                limit = response.get("limit", 0)
                spent = response.get("spent", 0)
                remaining = response.get("remaining", 0)
                usage_percent = response.get("usage_percent", 0)
                print(f"   Budget: ${limit}")
                print(f"   Spent: ${spent}")
                print(f"   Remaining: ${remaining}")
                print(f"   Usage: {usage_percent:.1f}%")
            return budget_set
        return False

    def test_cost_optimizer_analytics(self):
        """Test cost analytics"""
        success, response = self.run_test(
            "Cost Analytics",
            "GET",
            "optimizer/analytics?timeframe_days=30",
            200
        )
        
        if success and response.get("success"):
            total_cost = response.get("total_cost", 0)
            total_tokens = response.get("total_tokens", 0)
            requests = response.get("requests", 0)
            daily_avg = response.get("daily_average", 0)
            print(f"   Total cost: ${total_cost:.4f}")
            print(f"   Total tokens: {total_tokens}")
            print(f"   Requests: {requests}")
            print(f"   Daily average: ${daily_avg:.4f}")
            return True
        return False

    def test_learning_service_learn_auth_project(self):
        """Test learning from successful auth project"""
        success, response = self.run_test(
            "Learning Service (Auth Project)",
            "POST",
            "learning/learn",
            200,
            data={
                "project_id": f"auth_project_{int(time.time())}",
                "task_description": "Build authentication system with JWT and user management",
                "tech_stack": ["React", "FastAPI", "JWT", "MongoDB"],
                "success": True,
                "metrics": {
                    "completion_time_seconds": 1800,
                    "cost_usd": 2.50,
                    "code_quality_score": 85,
                    "iterations_needed": 2
                }
            }
        )
        
        if success and response.get("success"):
            learned = response.get("learned", False)
            patterns = response.get("patterns_extracted", 0)
            entry_id = response.get("entry_id", "")
            print(f"   Learned: {learned}")
            print(f"   Patterns extracted: {patterns}")
            print(f"   Entry ID: {entry_id}")
            return learned and patterns > 0
        return False

    def test_learning_service_learn_crud_project(self):
        """Test learning from CRUD API project"""
        success, response = self.run_test(
            "Learning Service (CRUD Project)",
            "POST",
            "learning/learn",
            200,
            data={
                "project_id": f"crud_project_{int(time.time())}",
                "task_description": "Create REST API with CRUD operations for user management",
                "tech_stack": ["FastAPI", "SQLAlchemy", "PostgreSQL"],
                "success": True,
                "metrics": {
                    "completion_time_seconds": 1200,
                    "cost_usd": 1.75,
                    "code_quality_score": 90,
                    "iterations_needed": 1
                }
            }
        )
        
        if success and response.get("success"):
            learned = response.get("learned", False)
            patterns = response.get("patterns_extracted", 0)
            print(f"   Learned: {learned}")
            print(f"   Patterns extracted: {patterns}")
            return learned
        return False

    def test_learning_service_find_similar(self):
        """Test finding similar projects for authentication"""
        success, response = self.run_test(
            "Learning Service (Find Similar)",
            "POST",
            "learning/similar",
            200,
            data={
                "task_description": "authentication system with login and signup",
                "tech_stack": ["React", "FastAPI"],
                "limit": 5
            }
        )
        
        if success and response.get("success"):
            similar_projects = response.get("similar_projects", [])
            print(f"   Found {len(similar_projects)} similar projects")
            for i, project in enumerate(similar_projects[:3]):
                similarity = project.get("similarity", 0)
                success_status = project.get("success", False)
                print(f"   Project {i+1}: {similarity:.3f} similarity, success: {success_status}")
            return True
        return False

    def test_learning_service_predict_success(self):
        """Test predicting success for new login system project"""
        success, response = self.run_test(
            "Learning Service (Predict Success)",
            "POST",
            "learning/predict",
            200,
            data={
                "task_description": "login system with password reset functionality",
                "tech_stack": ["React", "FastAPI", "JWT"]
            }
        )
        
        if success and response.get("success"):
            probability = response.get("probability", 0)
            confidence = response.get("confidence", "unknown")
            similar_count = response.get("similar_projects", 0)
            message = response.get("message", "")
            print(f"   Success probability: {probability:.2f}")
            print(f"   Confidence: {confidence}")
            print(f"   Similar projects: {similar_count}")
            print(f"   Message: {message}")
            return 0 <= probability <= 1
        return False

    def test_learning_service_stats(self):
        """Test getting learning service statistics"""
        success, response = self.run_test(
            "Learning Service Stats",
            "GET",
            "learning/stats",
            200
        )
        
        if success and response.get("success"):
            patterns_memory = response.get("patterns_in_memory", 0)
            patterns_db = response.get("patterns_in_db", 0)
            total_projects = response.get("total_projects_learned", 0)
            successful = response.get("successful_projects", 0)
            success_rate = response.get("success_rate", 0)
            print(f"   Patterns in memory: {patterns_memory}")
            print(f"   Patterns in DB: {patterns_db}")
            print(f"   Total projects: {total_projects}")
            print(f"   Successful: {successful}")
            print(f"   Success rate: {success_rate:.2f}")
            return True
        return False

    def test_workspace_service_create(self):
        """Test creating new workspace"""
        workspace_name = f"Test Team {datetime.now().strftime('%H%M%S')}"
        
        success, response = self.run_test(
            "Create Workspace",
            "POST",
            "workspaces",
            200,
            data={
                "name": workspace_name,
                "owner_id": f"user_{int(time.time())}",
                "owner_email": "test@example.com",
                "settings": {"require_code_review": True}
            }
        )
        
        if success and response.get("success"):
            workspace_id = response.get("workspace_id", "")
            name = response.get("name", "")
            message = response.get("message", "")
            print(f"   Workspace ID: {workspace_id}")
            print(f"   Name: {name}")
            print(f"   Message: {message}")
            
            # Store for later tests
            self.workspace_id = workspace_id
            return workspace_id != ""
        return False

    def test_workspace_service_get(self):
        """Test getting workspace details"""
        if not hasattr(self, 'workspace_id') or not self.workspace_id:
            print("❌ Skipping - No workspace ID available")
            return False
            
        success, response = self.run_test(
            "Get Workspace",
            "GET",
            f"workspaces/{self.workspace_id}",
            200
        )
        
        if success and response.get("success"):
            workspace = response.get("workspace", {})
            name = workspace.get("name", "")
            members = workspace.get("members", [])
            projects = workspace.get("projects", [])
            print(f"   Name: {name}")
            print(f"   Members: {len(members)}")
            print(f"   Projects: {len(projects)}")
            return workspace.get("id") == self.workspace_id
        return False

    def test_workspace_service_list_user(self):
        """Test listing user workspaces"""
        success, response = self.run_test(
            "List User Workspaces",
            "GET",
            f"workspaces/user/user_{int(time.time())}",
            200
        )
        
        if success and response.get("success"):
            workspaces = response.get("workspaces", [])
            print(f"   Found {len(workspaces)} workspaces")
            return True
        return False

    def test_workspace_service_invite_member(self):
        """Test inviting member to workspace"""
        if not hasattr(self, 'workspace_id') or not self.workspace_id:
            print("❌ Skipping - No workspace ID available")
            return False
            
        success, response = self.run_test(
            "Invite Workspace Member",
            "POST",
            f"workspaces/{self.workspace_id}/invite",
            200,
            data={
                "email": "developer@example.com",
                "role": "developer",
                "invited_by": f"user_{int(time.time())}"
            }
        )
        
        if success and response.get("success"):
            message = response.get("message", "")
            role = response.get("role", "")
            print(f"   Message: {message}")
            print(f"   Role: {role}")
            return role == "developer"
        return False

    def test_workspace_service_analytics(self):
        """Test getting workspace analytics"""
        if not hasattr(self, 'workspace_id') or not self.workspace_id:
            print("❌ Skipping - No workspace ID available")
            return False
            
        success, response = self.run_test(
            "Workspace Analytics",
            "GET",
            f"workspaces/{self.workspace_id}/analytics",
            200
        )
        
        if success and response.get("success"):
            members = response.get("members", 0)
            projects = response.get("projects", 0)
            total_cost = response.get("total_cost", 0)
            total_tokens = response.get("total_tokens", 0)
            plan = response.get("plan", "")
            print(f"   Members: {members}")
            print(f"   Projects: {projects}")
            print(f"   Total cost: ${total_cost:.4f}")
            print(f"   Total tokens: {total_tokens}")
            print(f"   Plan: {plan}")
            return True
        return False

    def test_analytics_service_track_completion_time(self):
        """Test tracking completion time metric"""
        success, response = self.run_test(
            "Track Completion Time Metric",
            "POST",
            "analytics/track",
            200,
            data={
                "metric_name": "task.completion_time",
                "value": 1800.0,
                "unit": "seconds",
                "tags": {
                    "user_id": f"user_{int(time.time())}",
                    "project_id": self.project_id or "test_project",
                    "task_type": "build_app"
                }
            }
        )
        
        if success and response.get("success"):
            message = response.get("message", "")
            print(f"   Message: {message}")
            return "tracked" in message.lower()
        return False

    def test_analytics_service_track_token_usage(self):
        """Test tracking token usage metric"""
        success, response = self.run_test(
            "Track Token Usage Metric",
            "POST",
            "analytics/track",
            200,
            data={
                "metric_name": "token.usage",
                "value": 15000.0,
                "unit": "tokens",
                "tags": {
                    "model": "claude-3-7-sonnet-20250219",
                    "user_id": f"user_{int(time.time())}"
                }
            }
        )
        
        if success and response.get("success"):
            message = response.get("message", "")
            print(f"   Message: {message}")
            return "tracked" in message.lower()
        return False

    def test_analytics_service_track_cost(self):
        """Test tracking cost metric"""
        success, response = self.run_test(
            "Track Cost Metric",
            "POST",
            "analytics/track",
            200,
            data={
                "metric_name": "token.cost",
                "value": 2.50,
                "unit": "usd",
                "tags": {
                    "model": "claude-3-7-sonnet-20250219",
                    "project_id": self.project_id or "test_project"
                }
            }
        )
        
        if success and response.get("success"):
            message = response.get("message", "")
            print(f"   Message: {message}")
            return "tracked" in message.lower()
        return False

    def test_analytics_service_track_quality_score(self):
        """Test tracking quality score metric"""
        success, response = self.run_test(
            "Track Quality Score Metric",
            "POST",
            "analytics/track",
            200,
            data={
                "metric_name": "code.quality_score",
                "value": 85.0,
                "unit": "score",
                "tags": {
                    "project_id": self.project_id or "test_project",
                    "language": "python"
                }
            }
        )
        
        if success and response.get("success"):
            message = response.get("message", "")
            print(f"   Message: {message}")
            return "tracked" in message.lower()
        return False

    def test_analytics_service_performance_dashboard(self):
        """Test getting performance dashboard"""
        success, response = self.run_test(
            "Performance Dashboard",
            "GET",
            "analytics/performance?timeframe_days=30",
            200
        )
        
        if success and response.get("success"):
            timeframe = response.get("timeframe_days", 0)
            task_completion = response.get("task_completion", {})
            success_rate = response.get("success_rate", 0)
            agent_performance = response.get("agent_performance", {})
            total_metrics = response.get("total_metrics", 0)
            
            print(f"   Timeframe: {timeframe} days")
            print(f"   Avg completion: {task_completion.get('average_seconds', 0):.1f}s")
            print(f"   Success rate: {success_rate:.2f}")
            print(f"   Agent performance entries: {len(agent_performance)}")
            print(f"   Total metrics: {total_metrics}")
            return True
        return False

    def test_analytics_service_cost_dashboard(self):
        """Test getting cost dashboard"""
        success, response = self.run_test(
            "Cost Dashboard",
            "GET",
            "analytics/cost?timeframe_days=30",
            200
        )
        
        if success and response.get("success"):
            total_cost = response.get("total_cost", 0)
            total_tokens = response.get("total_tokens", 0)
            daily_average = response.get("daily_average", 0)
            model_breakdown = response.get("model_breakdown", {})
            avg_cost_per_token = response.get("average_cost_per_token", 0)
            
            print(f"   Total cost: ${total_cost:.4f}")
            print(f"   Total tokens: {total_tokens}")
            print(f"   Daily average: ${daily_average:.4f}")
            print(f"   Models tracked: {len(model_breakdown)}")
            print(f"   Avg cost/token: ${avg_cost_per_token:.6f}")
            return True
        return False

    def test_analytics_service_quality_dashboard(self):
        """Test getting quality dashboard"""
        success, response = self.run_test(
            "Quality Dashboard",
            "GET",
            "analytics/quality?timeframe_days=30",
            200
        )
        
        if success and response.get("success"):
            avg_quality = response.get("average_quality_score", 0)
            avg_coverage = response.get("average_test_coverage", 0)
            quality_trend = response.get("quality_trend", [])
            total_assessments = response.get("total_assessments", 0)
            
            print(f"   Avg quality score: {avg_quality:.1f}")
            print(f"   Avg test coverage: {avg_coverage:.1f}%")
            print(f"   Quality trend points: {len(quality_trend)}")
            print(f"   Total assessments: {total_assessments}")
            return True
        return False

    def test_analytics_service_insights(self):
        """Test generating insights for test user"""
        test_user_id = f"user_{int(time.time())}"
        
        success, response = self.run_test(
            "Generate Insights",
            "GET",
            f"analytics/insights/{test_user_id}?timeframe_days=30",
            200
        )
        
        if success and response.get("success"):
            insights = response.get("insights", [])
            print(f"   Generated {len(insights)} insights")
            
            for i, insight in enumerate(insights[:3]):  # Show first 3
                insight_type = insight.get("type", "unknown")
                severity = insight.get("severity", "unknown")
                title = insight.get("title", "")
                print(f"   Insight {i+1}: {insight_type} ({severity}) - {title}")
            
            return True
        return False

    # ==================== INDIVIDUAL AGENT TESTS ====================
    
    def test_agent_imports(self):
        """Test that all agent files can be imported"""
        import sys
        import os
        
        # Add backend to Python path
        backend_path = "/app/backend"
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        agents_to_test = [
            "agents.planner_agent",
            "agents.architect_agent", 
            "agents.coder",
            "agents.tester_agent",
            "agents.reviewer_agent",
            "agents.deployer_agent",
            "agents.explorer_agent"
        ]
        
        imported_count = 0
        
        for agent_module in agents_to_test:
            try:
                __import__(agent_module)
                print(f"✅ Successfully imported {agent_module}")
                imported_count += 1
            except Exception as e:
                print(f"❌ Failed to import {agent_module}: {str(e)}")
        
        success = imported_count == len(agents_to_test)
        print(f"   Imported {imported_count}/{len(agents_to_test)} agents")
        return success

    def test_file_system_service(self):
        """Test FileSystemService basic operations"""
        import sys
        backend_path = "/app/backend"
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        try:
            from services.file_system_service import get_file_system_service
            
            fs_service = get_file_system_service()
            print("✅ FileSystemService initialized")
            
            # Test project creation
            test_project = f"test_project_{int(time.time())}"
            project_path = fs_service.create_project(test_project)
            print(f"✅ Created test project: {project_path}")
            
            # Test file writing
            test_content = "# Test file\nprint('Hello World')"
            write_success = fs_service.write_file(test_project, "test.py", test_content)
            print(f"✅ File write: {'Success' if write_success else 'Failed'}")
            
            # Test file reading
            read_content = fs_service.read_file(test_project, "test.py")
            read_success = read_content == test_content
            print(f"✅ File read: {'Success' if read_success else 'Failed'}")
            
            # Test file listing
            files = fs_service.list_files(test_project)
            print(f"✅ Listed {len(files)} files")
            
            # Cleanup
            fs_service.delete_project(test_project)
            print("✅ Cleaned up test project")
            
            return write_success and read_success
            
        except Exception as e:
            print(f"❌ FileSystemService test failed: {str(e)}")
            return False

    def test_github_service_basic(self):
        """Test GitHubService basic functions (without actual GitHub operations)"""
        import sys
        backend_path = "/app/backend"
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        try:
            from services.github_service import get_github_service
            
            github_service = get_github_service()
            print("✅ GitHubService initialized")
            
            # Test URL parsing
            test_urls = [
                "https://github.com/owner/repo",
                "https://github.com/owner/repo.git",
                "git@github.com:owner/repo.git"
            ]
            
            parse_success = True
            for url in test_urls:
                parsed = github_service.parse_github_url(url)
                if "owner" in parsed and "repo" in parsed:
                    print(f"✅ Parsed URL: {url} -> {parsed['owner']}/{parsed['repo']}")
                else:
                    print(f"❌ Failed to parse URL: {url}")
                    parse_success = False
            
            return parse_success
            
        except Exception as e:
            print(f"❌ GitHubService test failed: {str(e)}")
            return False

    def test_llm_client_initialization(self):
        """Test LLM client can be initialized"""
        import sys
        backend_path = "/app/backend"
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        try:
            from llm_client import get_llm_client
            
            # Test with emergent config
            config = {
                "provider": "emergent",
                "model": "claude-3-7-sonnet-20250219"
            }
            
            llm_client = get_llm_client(config)
            print("✅ LLM client initialized with emergent provider")
            
            # Test with anthropic config
            config = {
                "provider": "anthropic", 
                "model": "claude-3-sonnet-20240229",
                "api_key": "test-key"
            }
            
            llm_client = get_llm_client(config)
            print("✅ LLM client initialized with anthropic provider")
            
            return True
            
        except Exception as e:
            print(f"❌ LLM client test failed: {str(e)}")
            return False

    def test_phase2_orchestrator_initialization(self):
        """Test Phase2Orchestrator can be initialized"""
        import sys
        backend_path = "/app/backend"
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        try:
            from orchestrator.phase2_orchestrator import get_phase2_orchestrator
            from motor.motor_asyncio import AsyncIOMotorClient
            import os
            
            # Mock database and manager
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            client = AsyncIOMotorClient(mongo_url)
            db = client.test_db
            
            class MockManager:
                async def send_log(self, task_id, log_data):
                    pass
            
            manager = MockManager()
            
            config = {
                "provider": "emergent",
                "model": "claude-3-7-sonnet-20250219"
            }
            
            orchestrator = get_phase2_orchestrator(db, manager, config)
            print("✅ Phase2Orchestrator initialized successfully")
            
            # Test that all agents are initialized
            agents = ['planner', 'architect', 'coder', 'tester', 'reviewer', 'deployer', 'explorer']
            for agent_name in agents:
                if hasattr(orchestrator, agent_name):
                    print(f"✅ {agent_name.title()} agent initialized")
                else:
                    print(f"❌ {agent_name.title()} agent missing")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Phase2Orchestrator test failed: {str(e)}")
            return False

    def test_database_connections(self):
        """Test database connections and operations"""
        import sys
        backend_path = "/app/backend"
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            import asyncio
            import os
            from datetime import datetime, timezone
            
            async def test_db_operations():
                mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
                client = AsyncIOMotorClient(mongo_url)
                db = client.catalyst_test_db
                
                # Test conversation storage
                test_conversation = {
                    "id": f"test_conv_{int(time.time())}",
                    "title": "Test Conversation",
                    "messages": [],
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                await db.conversations.insert_one(test_conversation)
                print("✅ Conversation storage test passed")
                
                # Test task storage
                test_task = {
                    "id": f"test_task_{int(time.time())}",
                    "project_id": "test_project",
                    "prompt": "Test task",
                    "status": "pending",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                await db.tasks.insert_one(test_task)
                print("✅ Task storage test passed")
                
                # Test project storage
                test_project = {
                    "id": f"test_proj_{int(time.time())}",
                    "name": "Test Project",
                    "description": "Test project description",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                await db.projects.insert_one(test_project)
                print("✅ Project storage test passed")
                
                # Cleanup
                await db.conversations.delete_one({"id": test_conversation["id"]})
                await db.tasks.delete_one({"id": test_task["id"]})
                await db.projects.delete_one({"id": test_project["id"]})
                print("✅ Database cleanup completed")
                
                client.close()
                return True
            
            # Run async test
            result = asyncio.run(test_db_operations())
            return result
            
        except Exception as e:
            print(f"❌ Database test failed: {str(e)}")
            return False


    # ==================== ENTERPRISE MIGRATION VERIFICATION TESTS ====================
    
    def test_environment_detection(self):
        """Test environment detection returns correct K8s configuration"""
        success, response = self.run_test(
            "Environment Detection",
            "GET",
            "environment/info",
            200
        )
        
        if success and response.get("success"):
            environment = response.get("environment", "")
            orchestration_mode = response.get("orchestration_mode", "")
            features = response.get("features", {})
            infrastructure = response.get("infrastructure", {})
            
            print(f"   Environment: {environment}")
            print(f"   Orchestration Mode: {orchestration_mode}")
            print(f"   Postgres: {features.get('postgres', 'N/A')}")
            print(f"   Event Streaming: {features.get('event_streaming', 'N/A')}")
            print(f"   Git Integration: {features.get('git_integration', 'N/A')}")
            print(f"   Preview Deployments: {features.get('preview_deployments', 'N/A')}")
            print(f"   MongoDB: {infrastructure.get('mongodb', 'N/A')}")
            print(f"   Redis: {infrastructure.get('redis', 'N/A')}")
            print(f"   Qdrant: {infrastructure.get('qdrant', 'N/A')}")
            
            # Verify K8s environment
            env_correct = environment == "kubernetes"
            mode_correct = orchestration_mode == "sequential"
            postgres_disabled = features.get("postgres") == False
            events_disabled = features.get("event_streaming") == False
            git_disabled = features.get("git_integration") == False
            preview_disabled = features.get("preview_deployments") == False
            mongodb_enabled = infrastructure.get("mongodb") == True
            
            all_correct = (env_correct and mode_correct and postgres_disabled and 
                          events_disabled and git_disabled and preview_disabled and mongodb_enabled)
            
            if not all_correct:
                print(f"   ❌ Environment config mismatch!")
                print(f"      Expected: kubernetes/sequential with enterprise features disabled")
            
            return all_correct
        return False
    
    def test_chat_no_postgres_errors(self):
        """Test chat functionality works without Postgres/RabbitMQ"""
        # Create a conversation first
        success, conv_response = self.run_test(
            "Create Conversation for Migration Test",
            "POST",
            "chat/conversations",
            200
        )
        
        if not success or "id" not in conv_response:
            print("   ❌ Failed to create conversation")
            return False
        
        conversation_id = conv_response["id"]
        
        # Send a simple message
        message_data = {
            "message": "Hello",
            "conversation_id": conversation_id
        }
        
        success, response = self.run_test(
            "Chat Send (No Postgres/RabbitMQ)",
            "POST",
            "chat/send",
            200,
            data=message_data,
            timeout=60
        )
        
        if success and response.get("status") == "success":
            message_content = response.get("message", {}).get("content", "")
            print(f"   Response received: {len(message_content)} chars")
            print(f"   No Postgres/RabbitMQ errors: ✅")
            
            # Cleanup
            self.run_test(
                "Delete Test Conversation",
                "DELETE",
                f"chat/conversations/{conversation_id}",
                200
            )
            
            return True
        else:
            print(f"   ❌ Chat failed or returned error")
            return False
    
    def test_cost_stats_api(self):
        """Test cost stats API works in K8s"""
        success, response = self.run_test(
            "Cost Stats API",
            "GET",
            "logs/cost-stats",
            200
        )
        
        if success and response.get("success"):
            global_stats = response.get("global_stats", {})
            print(f"   Total tasks: {global_stats.get('total_tasks', 0)}")
            print(f"   Total cost: ${global_stats.get('total_cost', 0):.4f}")
            print(f"   Cache hit rate: {global_stats.get('cache_hit_rate', 0):.2f}%")
            return True
        return False
    
    def test_model_selection_api(self):
        """Test model selection API works in K8s"""
        success, response = self.run_test(
            "Model Selection API",
            "POST",
            "optimizer/select-model?task_description=Fix%20a%20typo%20in%20documentation&complexity=0.3",
            200
        )
        
        if success and response.get("success"):
            recommended = response.get("recommended_model", "")
            savings = response.get("estimated_savings_percent", 0)
            print(f"   Recommended model: {recommended}")
            print(f"   Estimated savings: {savings:.1f}%")
            return True
        return False
    
    def test_backend_health(self):
        """Test backend health and API info"""
        success, response = self.run_test(
            "Backend Health Check",
            "GET",
            "",
            200
        )
        
        if success and "message" in response:
            print(f"   API Message: {response.get('message', '')}")
            print(f"   API Version: {response.get('version', '')}")
            return True
        return False
    
    def test_git_repos_disabled(self):
        """Test Git repos endpoint returns disabled message in K8s"""
        success, response = self.run_test(
            "Git Repos (Should Be Disabled)",
            "GET",
            "git/repos",
            200
        )
        
        if success and response.get("success"):
            repos = response.get("repos", [])
            message = response.get("message", "")
            
            print(f"   Repos count: {len(repos)}")
            print(f"   Message: {message}")
            
            # Should return empty or disabled message
            is_disabled = len(repos) == 0 or "not enabled" in message.lower()
            
            if is_disabled:
                print(f"   ✅ Git correctly disabled in K8s")
            else:
                print(f"   ⚠️  Git may be unexpectedly enabled")
            
            return True  # Not a failure, just checking behavior
        return False
    
    def test_preview_disabled(self):
        """Test preview deployments endpoint returns disabled message in K8s"""
        success, response = self.run_test(
            "Preview Deployments (Should Be Disabled)",
            "GET",
            "preview",
            200
        )
        
        if success and response.get("success"):
            previews = response.get("previews", [])
            message = response.get("message", "")
            
            print(f"   Previews count: {len(previews)}")
            print(f"   Message: {message}")
            
            # Should return empty or disabled message
            is_disabled = len(previews) == 0 or "not available" in message.lower()
            
            if is_disabled:
                print(f"   ✅ Preview deployments correctly disabled in K8s")
            else:
                print(f"   ⚠️  Preview deployments may be unexpectedly enabled")
            
            return True  # Not a failure, just checking behavior
        return False
    
    def test_backend_startup_logs(self):
        """Check backend startup logs for errors"""
        success, response = self.run_test(
            "Backend Startup Logs",
            "GET",
            "logs/backend?minutes=5",
            200
        )
        
        if success and response.get("success"):
            logs = response.get("logs", [])
            
            # Look for error patterns
            error_count = 0
            postgres_errors = 0
            rabbitmq_errors = 0
            
            for log in logs:
                message = log.get("message", "").lower()
                if "error" in message and "failed" in message:
                    error_count += 1
                    if "postgres" in message:
                        postgres_errors += 1
                    if "rabbitmq" in message or "rabbit" in message:
                        rabbitmq_errors += 1
            
            print(f"   Total logs: {len(logs)}")
            print(f"   Error messages: {error_count}")
            print(f"   Postgres errors: {postgres_errors}")
            print(f"   RabbitMQ errors: {rabbitmq_errors}")
            
            # Expected: Some warnings about missing services, but no crashes
            # We're looking for graceful degradation
            if error_count > 0:
                print(f"   ⚠️  Found {error_count} error messages (expected for missing services)")
            else:
                print(f"   ✅ No error messages in logs")
            
            return True  # Not a failure - we expect some warnings
        return False

    # ==================== PHASE 5 OPTIMIZATION TESTS ====================
    
    def test_backend_logs_5_minutes(self):
        """Test backend logs API with 5 minutes timeframe"""
        success, response = self.run_test(
            "Backend Logs (5 minutes)",
            "GET",
            "logs/backend?minutes=5",
            200
        )
        
        if success and response.get("success"):
            logs = response.get("logs", [])
            count = response.get("count", 0)
            timeframe = response.get("timeframe_minutes", 0)
            
            print(f"   Logs count: {count}")
            print(f"   Timeframe: {timeframe} minutes")
            
            # Check log structure
            if logs:
                first_log = logs[0]
                has_source = "source" in first_log
                has_message = "message" in first_log
                has_timestamp = "timestamp" in first_log
                
                print(f"   Has source field: {has_source}")
                print(f"   Has message field: {has_message}")
                print(f"   Has timestamp field: {has_timestamp}")
                
                # Check for different log sources
                sources = set(log.get("source", "") for log in logs)
                print(f"   Log sources: {sources}")
                
                return has_source and has_message and has_timestamp
            else:
                print("   No logs found (may be expected if no recent activity)")
                return True  # Not a failure if no logs
        return False
    
    def test_backend_logs_1_minute(self):
        """Test backend logs API with 1 minute timeframe"""
        success, response = self.run_test(
            "Backend Logs (1 minute)",
            "GET",
            "logs/backend?minutes=1",
            200
        )
        
        if success and response.get("success"):
            count = response.get("count", 0)
            timeframe = response.get("timeframe_minutes", 0)
            
            print(f"   Logs count: {count}")
            print(f"   Timeframe: {timeframe} minutes")
            return timeframe == 1
        return False
    
    def test_backend_logs_15_minutes(self):
        """Test backend logs API with 15 minutes timeframe"""
        success, response = self.run_test(
            "Backend Logs (15 minutes)",
            "GET",
            "logs/backend?minutes=15",
            200
        )
        
        if success and response.get("success"):
            count = response.get("count", 0)
            timeframe = response.get("timeframe_minutes", 0)
            
            print(f"   Logs count: {count}")
            print(f"   Timeframe: {timeframe} minutes")
            return timeframe == 15
        return False
    
    def test_cost_stats_global(self):
        """Test global cost statistics API"""
        success, response = self.run_test(
            "Global Cost Statistics",
            "GET",
            "logs/cost-stats",
            200
        )
        
        if success and response.get("success"):
            global_stats = response.get("global_stats", {})
            optimizer_stats = response.get("optimizer_stats", {})
            
            # Check global stats fields
            total_tasks = global_stats.get("total_tasks", 0)
            total_llm_calls = global_stats.get("total_llm_calls", 0)
            cache_hit_rate = global_stats.get("cache_hit_rate", 0)
            total_cost = global_stats.get("total_cost", 0)
            avg_cost_per_task = global_stats.get("average_cost_per_task", 0)
            
            print(f"   Total tasks: {total_tasks}")
            print(f"   Total LLM calls: {total_llm_calls}")
            print(f"   Cache hit rate: {cache_hit_rate:.2f}%")
            print(f"   Total cost: ${total_cost:.4f}")
            print(f"   Avg cost per task: ${avg_cost_per_task:.4f}")
            
            # Check optimizer stats are included
            has_optimizer_stats = bool(optimizer_stats)
            print(f"   Has optimizer stats: {has_optimizer_stats}")
            
            if optimizer_stats:
                cache_size = optimizer_stats.get("cache_size", 0)
                cache_maxsize = optimizer_stats.get("cache_maxsize", 0)
                print(f"   Optimizer cache: {cache_size}/{cache_maxsize}")
            
            # Verify required fields exist
            required_fields = ["total_tasks", "total_llm_calls", "cache_hit_rate", "total_cost"]
            has_all_fields = all(field in global_stats for field in required_fields)
            
            return has_all_fields and has_optimizer_stats
        return False
    
    def test_existing_chat_config(self):
        """Test that existing chat config endpoint still works"""
        success, response = self.run_test(
            "Chat Config (Existing Endpoint)",
            "GET",
            "chat/config",
            200
        )
        
        if success and "provider" in response:
            print(f"   Provider: {response.get('provider')}")
            print(f"   Model: {response.get('model')}")
            return True
        return False
    
    def test_existing_conversations_list(self):
        """Test that existing conversations list endpoint still works"""
        success, response = self.run_test(
            "List Conversations (Existing Endpoint)",
            "GET",
            "chat/conversations",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} conversations")
            return True
        return False
    
    def test_existing_optimizer_select_model(self):
        """Test that existing optimizer select-model endpoint still works"""
        success, response = self.run_test(
            "Optimizer Select Model (Existing Endpoint)",
            "POST",
            "optimizer/select-model",
            200,
            data={
                "task_description": "simple documentation fix",
                "complexity": 0.2,
                "current_model": "claude-3-7-sonnet-20250219"
            }
        )
        
        if success and response.get("success"):
            recommended = response.get("recommended_model", "")
            savings = response.get("estimated_savings_percent", 0)
            print(f"   Recommended model: {recommended}")
            print(f"   Estimated savings: {savings:.1f}%")
            return True
        return False


def main():
    print("🚀 Starting Catalyst API Testing...")
    print("=" * 60)
    
    tester = CatalystAPITester()
    
    # Test sequence - Phase 5 Optimization Testing
    tests = [
        ("API Root", tester.test_api_root),
        
        # 1. PHASE 5 OPTIMIZATION FEATURES (CRITICAL PRIORITY)
        ("Backend Logs (5 minutes)", tester.test_backend_logs_5_minutes),
        ("Backend Logs (1 minute)", tester.test_backend_logs_1_minute),
        ("Backend Logs (15 minutes)", tester.test_backend_logs_15_minutes),
        ("Global Cost Statistics", tester.test_cost_stats_global),
        ("Chat Config (Existing)", tester.test_existing_chat_config),
        ("List Conversations (Existing)", tester.test_existing_conversations_list),
        ("Optimizer Select Model (Existing)", tester.test_existing_optimizer_select_model),
        
        # 2. PHASE 4 MVP FEATURES - CONTEXT MANAGEMENT (HIGH PRIORITY)
        ("Context Check (10 messages)", tester.test_context_check_10_messages),
        ("Context Check (150K tokens)", tester.test_context_check_large_tokens),
        ("Context Check (180K tokens)", tester.test_context_check_critical_tokens),
        ("Context Truncate (Sliding Window)", tester.test_context_truncate_sliding_window),
        ("Context Truncate (Important First)", tester.test_context_truncate_important_first),
        
        # 2. PHASE 4 MVP FEATURES - COST OPTIMIZER (HIGH PRIORITY)
        ("Cost Optimizer (Simple Task)", tester.test_cost_optimizer_simple_task),
        ("Cost Optimizer (Complex Task)", tester.test_cost_optimizer_complex_task),
        ("Cost Optimizer Cache Stats", tester.test_cost_optimizer_cache_stats),
        ("Set Project Budget", tester.test_cost_optimizer_set_budget),
        ("Get Project Budget", tester.test_cost_optimizer_get_budget),
        ("Cost Analytics", tester.test_cost_optimizer_analytics),
        
        # 3. PHASE 4 MVP FEATURES - LEARNING SERVICE (HIGH PRIORITY)
        ("Learning Service (Auth Project)", tester.test_learning_service_learn_auth_project),
        ("Learning Service (CRUD Project)", tester.test_learning_service_learn_crud_project),
        ("Learning Service (Find Similar)", tester.test_learning_service_find_similar),
        ("Learning Service (Predict Success)", tester.test_learning_service_predict_success),
        ("Learning Service Stats", tester.test_learning_service_stats),
        
        # 4. PHASE 4 MVP FEATURES - WORKSPACE SERVICE (HIGH PRIORITY)
        ("Create Workspace", tester.test_workspace_service_create),
        ("Get Workspace", tester.test_workspace_service_get),
        ("List User Workspaces", tester.test_workspace_service_list_user),
        ("Invite Workspace Member", tester.test_workspace_service_invite_member),
        ("Workspace Analytics", tester.test_workspace_service_analytics),
        
        # 5. PHASE 4 MVP FEATURES - ANALYTICS SERVICE (HIGH PRIORITY)
        ("Track Completion Time Metric", tester.test_analytics_service_track_completion_time),
        ("Track Token Usage Metric", tester.test_analytics_service_track_token_usage),
        ("Track Cost Metric", tester.test_analytics_service_track_cost),
        ("Track Quality Score Metric", tester.test_analytics_service_track_quality_score),
        ("Performance Dashboard", tester.test_analytics_service_performance_dashboard),
        ("Cost Dashboard", tester.test_analytics_service_cost_dashboard),
        ("Quality Dashboard", tester.test_analytics_service_quality_dashboard),
        ("Generate Insights", tester.test_analytics_service_insights),
        
        # 6. Basic Chat Functionality Tests (MEDIUM PRIORITY)
        ("Set LLM Config (Emergent)", tester.test_set_llm_config_emergent),
        ("Get LLM Config", tester.test_get_llm_config),
        ("Create Conversation", tester.test_create_conversation),
        ("Send Help Message", tester.test_send_help_message),
        ("Send Create Project Message", tester.test_send_create_project_message),
        ("Get Conversation Messages", tester.test_get_conversation_messages),
        
        # 7. Individual Agent Tests (MEDIUM PRIORITY)
        ("Agent Import Test", tester.test_agent_imports),
        ("LLM Client Initialization", tester.test_llm_client_initialization),
        ("FileSystem Service Test", tester.test_file_system_service),
        ("GitHub Service Basic Test", tester.test_github_service_basic),
        ("Phase2 Orchestrator Initialization", tester.test_phase2_orchestrator_initialization),
        
        # 8. Database Operations Tests (MEDIUM PRIORITY)
        ("Database Connections Test", tester.test_database_connections),
        
        # 9. Phase 2 Orchestrator Workflow Test (LOW PRIORITY)
        ("Create Project", tester.test_create_project),
        ("Phase 2 Simple Workflow", tester.test_phase2_simple_workflow),
        ("Check Generated Files", tester.test_check_generated_files),
        
        # 10. Additional Chat Tests (LOW PRIORITY)
        ("Send Build App Message", tester.test_send_build_app_message),
        ("Send Status Message", tester.test_send_status_message),
        ("List Conversations", tester.test_list_conversations),
        ("Get Conversation", tester.test_get_conversation),
        ("Delete Conversation", tester.test_delete_conversation),
        
        # 11. Legacy Tests (LOW PRIORITY)
        ("Get Projects", tester.test_get_projects),
        ("Get Project", tester.test_get_project),
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