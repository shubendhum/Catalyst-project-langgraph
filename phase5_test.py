import requests
import json
from datetime import datetime

class Phase5Tester:
    def __init__(self, base_url="https://agentflow-21.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

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
                self.failed_tests.append(name)
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return False, {}

        except requests.exceptions.Timeout:
            self.failed_tests.append(name)
            print(f"❌ Failed - Request timeout after {timeout}s")
            return False, {}
        except Exception as e:
            self.failed_tests.append(name)
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

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
                
                # Check for both supervisor and agent logs
                has_supervisor_logs = any("backend" in log.get("source", "") for log in logs)
                has_agent_logs = any(log.get("source", "") == "agent" for log in logs)
                
                print(f"   Has supervisor logs: {has_supervisor_logs}")
                print(f"   Has agent logs: {has_agent_logs}")
                
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
            "optimizer/select-model?task_description=simple%20documentation%20fix",
            200
        )
        
        if success and response.get("success"):
            recommended = response.get("recommended_model", "")
            savings = response.get("estimated_savings_percent", 0)
            print(f"   Recommended model: {recommended}")
            print(f"   Estimated savings: {savings:.1f}%")
            return True
        return False

def main():
    print("🚀 Starting Phase 5 Optimization Testing...")
    print("=" * 60)
    
    tester = Phase5Tester()
    
    # Phase 5 test sequence
    tests = [
        ("Backend Logs (5 minutes)", tester.test_backend_logs_5_minutes),
        ("Backend Logs (1 minute)", tester.test_backend_logs_1_minute),
        ("Backend Logs (15 minutes)", tester.test_backend_logs_15_minutes),
        ("Global Cost Statistics", tester.test_cost_stats_global),
        ("Chat Config (Existing)", tester.test_existing_chat_config),
        ("List Conversations (Existing)", tester.test_existing_conversations_list),
        ("Optimizer Select Model (Existing)", tester.test_existing_optimizer_select_model),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            tester.failed_tests.append(test_name)
    
    # Print final results
    print(f"\n{'='*60}")
    print(f"📊 PHASE 5 TEST RESULTS")
    print(f"{'='*60}")
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.failed_tests:
        print(f"\n❌ Failed tests:")
        for test in tester.failed_tests:
            print(f"   - {test}")
    else:
        print(f"\n✅ All tests passed!")
    
    return tester.tests_passed == tester.tests_run

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
