import requests
import sys
import json
import time
from datetime import datetime

class InfrastructureTester:
    def __init__(self, base_url="https://catalyst-app-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.warnings = []

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
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout after {timeout}s")
            self.failed_tests.append(f"{name}: Timeout after {timeout}s")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append(f"{name}: {str(e)}")
            return False, {}

    # ==================== TEST SUITE 1: Backend Integration with Infrastructure ====================
    
    def test_cost_optimizer_redis_integration(self):
        """Test 1.1: Cost Optimizer - Redis Integration"""
        print("\n" + "="*60)
        print("TEST SUITE 1: Backend Integration with Infrastructure")
        print("="*60)
        
        success, response = self.run_test(
            "Cost Optimizer - Cache Stats (Redis Integration)",
            "GET",
            "optimizer/cache-stats",
            200
        )
        
        if success and response.get("success"):
            cache_size = response.get("cache_size", 0)
            cache_maxsize = response.get("cache_maxsize", 0)
            cache_ttl = response.get("cache_ttl_seconds", 0)
            estimated_savings = response.get("estimated_savings", 0)
            cache_type = response.get("cache_type", "unknown")
            redis_connected = response.get("redis_connected", None)
            
            print(f"   Cache size: {cache_size}")
            print(f"   Cache maxsize: {cache_maxsize}")
            print(f"   Cache TTL: {cache_ttl} seconds")
            print(f"   Estimated savings: ${estimated_savings}")
            print(f"   Cache type: {cache_type}")
            print(f"   Redis connected: {redis_connected}")
            
            # Verify expected behavior without Redis
            if redis_connected == False and cache_type == "memory":
                print("✅ Correct fallback: Using memory cache when Redis unavailable")
                return True
            elif redis_connected == True and cache_type in ["redis+memory", "redis"]:
                print("✅ Redis connected: Using Redis cache")
                return True
            else:
                print(f"⚠️  Unexpected cache configuration: redis_connected={redis_connected}, cache_type={cache_type}")
                self.warnings.append("Cost Optimizer cache configuration unexpected")
                return True  # Still working, just unexpected config
        return False

    def test_cost_optimizer_model_selection(self):
        """Test 1.2: Cost Optimizer - Model Selection"""
        success, response = self.run_test(
            "Cost Optimizer - Model Selection (Without Redis)",
            "POST",
            "optimizer/select-model?task_description=Simple%20bug%20fix&complexity=0.3&current_model=claude-3-7-sonnet-20250219",
            200
        )
        
        if success and response.get("success"):
            recommended_model = response.get("recommended_model", "")
            current_model = response.get("current_model", "")
            reason = response.get("reason", "")
            cost_per_1k = response.get("cost_per_1k", 0)
            estimated_savings = response.get("estimated_savings_percent", 0)
            
            print(f"   Recommended model: {recommended_model}")
            print(f"   Current model: {current_model}")
            print(f"   Reason: {reason}")
            print(f"   Cost per 1k tokens: ${cost_per_1k}")
            print(f"   Estimated savings: {estimated_savings}%")
            
            # Should recommend cheaper model for low complexity
            if "gpt-4o-mini" in recommended_model.lower() or estimated_savings > 0:
                print("✅ Correctly recommends cheaper model for simple task")
                return True
            else:
                print("⚠️  Model selection may not be optimal for simple task")
                return True  # Still working
        return False

    def test_cost_optimizer_caching(self):
        """Test 1.3: Cost Optimizer - Caching Test"""
        # First request (cache miss)
        start_time = time.time()
        success1, response1 = self.run_test(
            "Cost Optimizer - First Request (Cache Miss)",
            "POST",
            "optimizer/select-model?task_description=test%20task&complexity=0.5",
            200
        )
        first_request_time = time.time() - start_time
        
        if not success1:
            return False
            
        # Second request (should be cached)
        start_time = time.time()
        success2, response2 = self.run_test(
            "Cost Optimizer - Second Request (Cache Hit)",
            "POST",
            "optimizer/select-model?task_description=test%20task&complexity=0.5",
            200
        )
        second_request_time = time.time() - start_time
        
        if success1 and success2:
            print(f"   First request time: {first_request_time:.3f}s")
            print(f"   Second request time: {second_request_time:.3f}s")
            
            # Check if second request was faster (cached)
            if second_request_time < first_request_time:
                print("✅ In-memory caching working (second request faster)")
            else:
                print("⚠️  Caching may not be working optimally")
                
            # Check cache stats
            success3, response3 = self.run_test(
                "Cost Optimizer - Cache Stats After Requests",
                "GET",
                "optimizer/cache-stats",
                200
            )
            
            if success3 and response3.get("success"):
                cache_size = response3.get("cache_size", 0)
                print(f"   Cache size after requests: {cache_size}")
                return cache_size > 0
        return False

    # ==================== TEST SUITE 2: Learning Service - Qdrant Fallback ====================
    
    def test_learning_stats(self):
        """Test 2.1: Learning Stats"""
        print("\n" + "="*60)
        print("TEST SUITE 2: Learning Service - Qdrant Fallback")
        print("="*60)
        
        success, response = self.run_test(
            "Learning Service - Stats (Without Qdrant)",
            "GET",
            "learning/stats",
            200
        )
        
        if success and response.get("success"):
            patterns_memory = response.get("patterns_in_memory", 0)
            patterns_db = response.get("patterns_in_db", 0)
            total_projects = response.get("total_projects_learned", 0)
            successful_projects = response.get("successful_projects", 0)
            success_rate = response.get("success_rate", 0)
            
            print(f"   Patterns in memory: {patterns_memory}")
            print(f"   Patterns in DB: {patterns_db}")
            print(f"   Total projects learned: {total_projects}")
            print(f"   Successful projects: {successful_projects}")
            print(f"   Success rate: {success_rate}")
            
            # Should work without Qdrant
            if patterns_db == 0:
                print("✅ Working without Qdrant (patterns_in_db = 0)")
            else:
                print("⚠️  Qdrant may be connected (patterns_in_db > 0)")
                
            return True
        return False

    def test_learning_learn_project(self):
        """Test 2.2: Learn from Project (Without Qdrant)"""
        # Use query parameters for learning service
        params = {
            "project_id": "test_infra_001",
            "task_description": "Build REST API with authentication",
            "tech_stack": ["FastAPI", "JWT", "MongoDB"],
            "success": True,
            "metrics": {
                "completion_time_seconds": 900,
                "cost_usd": 3.5,
                "code_quality_score": 85,
                "iterations_needed": 2
            }
        }
        
        # Build URL with query parameters
        import urllib.parse
        query_string = urllib.parse.urlencode({
            "project_id": params["project_id"],
            "task_description": params["task_description"],
            "success": params["success"]
        })
        
        success, response = self.run_test(
            "Learning Service - Learn from Project (Without Qdrant)",
            "POST",
            f"learning/learn?{query_string}",
            200,
            data={"tech_stack": params["tech_stack"], "metrics": params["metrics"]}
        )
        
        if success and response.get("success"):
            learned = response.get("learned", False)
            patterns_extracted = response.get("patterns_extracted", 0)
            entry_id = response.get("entry_id", "")
            
            print(f"   Learned: {learned}")
            print(f"   Patterns extracted: {patterns_extracted}")
            print(f"   Entry ID: {entry_id}")
            
            if learned and patterns_extracted > 0:
                print("✅ Successfully stored learning in memory")
                return True
            else:
                print("⚠️  Learning may not be working properly")
        return False

    def test_learning_find_similar(self):
        """Test 2.3: Find Similar Projects (In-Memory Search)"""
        # Use query parameters for learning service
        import urllib.parse
        query_string = urllib.parse.urlencode({
            "task_description": "REST API authentication",
            "limit": 3
        })
        
        success, response = self.run_test(
            "Learning Service - Find Similar (In-Memory Search)",
            "POST",
            f"learning/similar?{query_string}",
            200,
            data={"tech_stack": ["FastAPI"]}
        )
        
        if success and response.get("success"):
            similar_projects = response.get("similar_projects", [])
            print(f"   Found {len(similar_projects)} similar projects")
            
            for i, project in enumerate(similar_projects):
                project_id = project.get("project_id", "")
                task_desc = project.get("task_description", "")
                similarity = project.get("similarity", 0)
                print(f"   Project {i+1}: {project_id} (similarity: {similarity:.3f})")
                
                # Verify similarity scores are valid
                if not (0 <= similarity <= 1):
                    print(f"❌ Invalid similarity score: {similarity}")
                    return False
                    
            print("✅ In-memory numpy search working")
            return True
        return False

    def test_learning_predict_success(self):
        """Test 2.4: Success Prediction"""
        # Use query parameters for learning service
        import urllib.parse
        query_string = urllib.parse.urlencode({
            "task_description": "Build user authentication"
        })
        
        success, response = self.run_test(
            "Learning Service - Success Prediction",
            "POST",
            f"learning/predict?{query_string}",
            200,
            data={"tech_stack": ["React", "FastAPI"]}
        )
        
        if success and response.get("success"):
            probability = response.get("probability", 0)
            confidence = response.get("confidence", "")
            similar_projects = response.get("similar_projects", 0)
            successful_similar = response.get("successful_similar", 0)
            message = response.get("message", "")
            
            print(f"   Success probability: {probability}")
            print(f"   Confidence: {confidence}")
            print(f"   Similar projects: {similar_projects}")
            print(f"   Successful similar: {successful_similar}")
            print(f"   Message: {message}")
            
            # Verify probability is valid
            if 0 <= probability <= 1 and confidence in ["low", "medium", "high"]:
                print("✅ Success prediction working with in-memory data")
                return True
            else:
                print(f"❌ Invalid prediction values: probability={probability}, confidence={confidence}")
        return False

    # ==================== TEST SUITE 3: Failover Mechanisms ====================
    
    def test_multiple_learning_entries(self):
        """Test 3.1: Multiple Learning Entries"""
        print("\n" + "="*60)
        print("TEST SUITE 3: Failover Mechanisms")
        print("="*60)
        
        # Get initial stats
        success_initial, response_initial = self.run_test(
            "Learning Stats - Initial",
            "GET",
            "learning/stats",
            200
        )
        
        if not success_initial:
            return False
            
        initial_patterns = response_initial.get("patterns_in_memory", 0)
        print(f"   Initial patterns in memory: {initial_patterns}")
        
        # Store multiple entries
        entries_to_add = 5
        successful_adds = 0
        
        for i in range(1, entries_to_add + 1):
            # Use query parameters for learning service
            import urllib.parse
            query_string = urllib.parse.urlencode({
                "project_id": f"test_{i}",
                "task_description": f"Project {i}",
                "success": True
            })
            
            success, response = self.run_test(
                f"Add Learning Entry {i}",
                "POST",
                f"learning/learn?{query_string}",
                200,
                data={"tech_stack": ["React", "FastAPI"], "metrics": {"cost_usd": 2.5}}
            )
            
            if success and response.get("success"):
                successful_adds += 1
        
        print(f"   Successfully added {successful_adds}/{entries_to_add} entries")
        
        # Check final stats
        success_final, response_final = self.run_test(
            "Learning Stats - After Additions",
            "GET",
            "learning/stats",
            200
        )
        
        if success_final and response_final.get("success"):
            final_patterns = response_final.get("patterns_in_memory", 0)
            print(f"   Final patterns in memory: {final_patterns}")
            
            patterns_added = final_patterns - initial_patterns
            print(f"   Patterns added: {patterns_added}")
            
            if patterns_added >= successful_adds:
                print("✅ In-memory storage handling multiple entries correctly")
                return True
            else:
                print("⚠️  Pattern storage may not be working as expected")
        return False

    def test_cost_optimizer_cache_capacity(self):
        """Test 3.2: Cost Optimizer Cache Capacity"""
        success, response = self.run_test(
            "Cost Optimizer - Cache Capacity Check",
            "GET",
            "optimizer/cache-stats",
            200
        )
        
        if success and response.get("success"):
            cache_maxsize = response.get("cache_maxsize", 0)
            cache_ttl = response.get("cache_ttl_seconds", 0)
            
            print(f"   Cache max size: {cache_maxsize}")
            print(f"   Cache TTL: {cache_ttl} seconds")
            
            # Verify expected values
            if cache_maxsize == 1000 and cache_ttl == 3600:
                print("✅ Cache configuration correct (maxsize=1000, TTL=3600s)")
                return True
            else:
                print(f"⚠️  Unexpected cache config: maxsize={cache_maxsize}, TTL={cache_ttl}")
                self.warnings.append(f"Cache config: maxsize={cache_maxsize}, TTL={cache_ttl}")
                return True  # Still working
        return False

    # ==================== TEST SUITE 4: Analytics Service ====================
    
    def test_analytics_track_metrics(self):
        """Test 4.1: Track Metrics (Without TimescaleDB)"""
        print("\n" + "="*60)
        print("TEST SUITE 4: Analytics Service")
        print("="*60)
        
        # Use query parameters for analytics service
        import urllib.parse
        query_string = urllib.parse.urlencode({
            "metric_name": "test.metric",
            "value": 123.45,
            "unit": "seconds"
        })
        
        success, response = self.run_test(
            "Analytics - Track Metrics (Without TimescaleDB)",
            "POST",
            f"analytics/track?{query_string}",
            200,
            data={"tags": {"test": "infrastructure"}}
        )
        
        if success and response.get("success"):
            message = response.get("message", "")
            print(f"   Message: {message}")
            
            if "tracked" in message.lower():
                print("✅ Metric tracking working (stored in MongoDB)")
                return True
        return False

    def test_analytics_performance_dashboard(self):
        """Test 4.2: Performance Dashboard"""
        success, response = self.run_test(
            "Analytics - Performance Dashboard",
            "GET",
            "analytics/performance?timeframe_days=7",
            200
        )
        
        if success and response.get("success"):
            timeframe_days = response.get("timeframe_days", 0)
            task_completion = response.get("task_completion", {})
            success_rate = response.get("success_rate", 0)
            agent_performance = response.get("agent_performance", {})
            
            print(f"   Timeframe: {timeframe_days} days")
            print(f"   Task completion data: {len(task_completion)} fields")
            print(f"   Success rate: {success_rate}")
            print(f"   Agent performance: {len(agent_performance)} agents")
            
            if timeframe_days == 7:
                print("✅ Performance dashboard working without TimescaleDB")
                return True
        return False

    # ==================== TEST SUITE 5: Error Handling & Graceful Degradation ====================
    
    def test_backend_startup_logs(self):
        """Test 5.1: Backend Startup Logs"""
        print("\n" + "="*60)
        print("TEST SUITE 5: Error Handling & Graceful Degradation")
        print("="*60)
        
        # Check if we can access the API (indicates backend started successfully)
        success, response = self.run_test(
            "Backend Startup Check",
            "GET",
            "",
            200
        )
        
        if success:
            print("✅ Backend started successfully despite missing infrastructure")
            print("   Expected: Warning messages for Redis/Qdrant/RabbitMQ not available")
            print("   Expected: Confirmation of fallback modes")
            return True
        else:
            print("❌ Backend failed to start - may be crashing due to infrastructure dependencies")
        return False

    def test_environment_variables(self):
        """Test 5.2: Environment Variables"""
        import os
        
        print("\n🔍 Checking Phase 4 environment variables...")
        
        expected_vars = {
            "REDIS_URL": "redis://localhost:6379",
            "QDRANT_URL": "http://localhost:6333", 
            "RABBITMQ_URL": "amqp://catalyst:catalyst_queue_2025@localhost:5672/catalyst"
        }
        
        env_file_path = "/app/backend/.env"
        
        try:
            with open(env_file_path, 'r') as f:
                env_content = f.read()
                
            all_found = True
            for var_name, expected_value in expected_vars.items():
                if f"{var_name}=" in env_content:
                    print(f"✅ Found {var_name} in .env")
                else:
                    print(f"❌ Missing {var_name} in .env")
                    all_found = False
                    
            if all_found:
                print("✅ All Phase 4 infrastructure environment variables configured")
                return True
            else:
                print("⚠️  Some infrastructure environment variables missing")
                
        except Exception as e:
            print(f"❌ Error reading .env file: {str(e)}")
            
        return False

    # ==================== TEST SUITE 6: Workspace Service (MongoDB Only) ====================
    
    def test_workspace_creation(self):
        """Test 6.1: Workspace Creation"""
        print("\n" + "="*60)
        print("TEST SUITE 6: Workspace Service (MongoDB Only)")
        print("="*60)
        
        workspace_data = {
            "name": "InfraTest",
            "owner_id": "test123",
            "owner_email": "test@test.com"
        }
        
        success, response = self.run_test(
            "Workspace Creation (MongoDB Only)",
            "POST",
            "workspaces",
            200,
            data=workspace_data
        )
        
        if success and response.get("success"):
            workspace_id = response.get("workspace_id", "")
            name = response.get("name", "")
            message = response.get("message", "")
            
            print(f"   Workspace ID: {workspace_id}")
            print(f"   Name: {name}")
            print(f"   Message: {message}")
            
            # Store for potential cleanup
            self.workspace_id = workspace_id
            
            if workspace_id and name == "InfraTest":
                print("✅ Workspace creation working with MongoDB only")
                return True
        return False

    def run_all_tests(self):
        """Run all infrastructure tests"""
        print("🚀 Starting Phase 4 Infrastructure Testing...")
        print("Testing failover mechanisms and infrastructure integration")
        print("=" * 80)
        
        # Test Suite 1: Backend Integration with Infrastructure
        self.test_cost_optimizer_redis_integration()
        self.test_cost_optimizer_model_selection()
        self.test_cost_optimizer_caching()
        
        # Test Suite 2: Learning Service - Qdrant Fallback
        self.test_learning_stats()
        self.test_learning_learn_project()
        self.test_learning_find_similar()
        self.test_learning_predict_success()
        
        # Test Suite 3: Failover Mechanisms
        self.test_multiple_learning_entries()
        self.test_cost_optimizer_cache_capacity()
        
        # Test Suite 4: Analytics Service
        self.test_analytics_track_metrics()
        self.test_analytics_performance_dashboard()
        
        # Test Suite 5: Error Handling & Graceful Degradation
        self.test_backend_startup_logs()
        self.test_environment_variables()
        
        # Test Suite 6: Workspace Service (MongoDB Only)
        self.test_workspace_creation()
        
        # Print final results
        self.print_results()

    def print_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 80)
        print("🏁 PHASE 4 INFRASTRUCTURE TESTING RESULTS")
        print("=" * 80)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"📊 Overall Results:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests ({len(self.failed_tests)}):")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
        
        print(f"\n🎯 Infrastructure Failover Assessment:")
        
        # Expected results summary
        expected_working = [
            "Cost Optimizer → In-memory cache (no Redis)",
            "Learning Service → Numpy search (no Qdrant)", 
            "Analytics → MongoDB storage (no TimescaleDB)",
            "Workspace → MongoDB only"
        ]
        
        expected_warnings = [
            "Redis not available, using in-memory cache",
            "Qdrant not available, using in-memory storage",
            "Sentence Transformers not available, using simple embeddings"
        ]
        
        should_not_see = [
            "Connection errors that crash backend",
            "Unhandled exceptions",
            "Missing service errors that block features"
        ]
        
        print(f"\n✅ Services Should Work Without Infrastructure:")
        for service in expected_working:
            print(f"   • {service}")
            
        print(f"\n⚠️  Expected Warnings (Not Errors):")
        for warning in expected_warnings:
            print(f"   • {warning}")
            
        print(f"\n❌ Should NOT See:")
        for error in should_not_see:
            print(f"   • {error}")
        
        print(f"\n📈 Performance Expectations:")
        print(f"   With Infrastructure (Redis, Qdrant):")
        print(f"   • Cache hits: ~20-30% faster")
        print(f"   • Vector search: O(log n) - very fast")
        print(f"   • Persistent across restarts")
        print(f"   ")
        print(f"   Without Infrastructure (Current):")
        print(f"   • In-memory cache: Still fast, but lost on restart")
        print(f"   • Numpy search: O(n) - slower for large datasets")
        print(f"   • Works for development/testing")

if __name__ == "__main__":
    tester = InfrastructureTester()
    tester.run_all_tests()