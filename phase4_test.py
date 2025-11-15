#!/usr/bin/env python3
"""
Phase 4 MVP Features Testing Script
Tests the 5 core Phase 4 services: Context Management, Cost Optimizer, Learning Service, Workspace Service, Analytics Service
"""

import requests
import json
import time
from datetime import datetime

class Phase4Tester:
    def __init__(self, base_url="https://catalyst-viz.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def test_endpoint(self, name, method, endpoint, data=None, params=None, expected_status=200, timeout=15):
        """Test a single endpoint"""
        url = f"{self.base_url}/api/{endpoint}"
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, timeout=timeout)
            elif method == 'POST':
                if data is not None:
                    # For POST with JSON body
                    headers = {'Content-Type': 'application/json'}
                    response = requests.post(url, json=data, headers=headers, params=params, timeout=timeout)
                elif params:
                    # For POST with query params only
                    response = requests.post(url, params=params, timeout=timeout)
                else:
                    response = requests.post(url, timeout=timeout)
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                self.failed_tests.append(name)
                return False, {}
                
        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Timeout after {timeout}s")
            self.failed_tests.append(name)
            return False, {}
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append(name)
            return False, {}

    def run_phase4_tests(self):
        """Run all Phase 4 MVP tests"""
        
        print("🚀 Starting Phase 4 MVP Features Testing...")
        print("=" * 60)
        
        # Test 1: Context Management
        print("\n" + "="*20 + " CONTEXT MANAGEMENT " + "="*20)
        
        # Simple context check
        success, response = self.test_endpoint(
            "Context Check (Simple)",
            "POST",
            "context/check?model=claude-3-7-sonnet-20250219",
            data=[{"role": "user", "content": "Hello"}]
        )
        if success and response.get("success"):
            print(f"   Status: {response.get('status')}")
            print(f"   Tokens: {response.get('current_tokens')}")
        
        # Context truncation
        large_messages = [{"role": "user", "content": "A" * 1000} for _ in range(50)]
        success, response = self.test_endpoint(
            "Context Truncate",
            "POST", 
            "context/truncate?model=claude-3-7-sonnet-20250219&strategy=sliding_window",
            data=large_messages
        )
        if success and response.get("success"):
            print(f"   Truncated: {len(response.get('messages', []))} messages")
        
        # Test 2: Cost Optimizer
        print("\n" + "="*20 + " COST OPTIMIZER " + "="*20)
        
        # Model selection
        success, response = self.test_endpoint(
            "Cost Optimizer (Model Selection)",
            "POST",
            "optimizer/select-model",
            params={
                "task_description": "Simple documentation fix", 
                "complexity": 0.3,
                "current_model": "claude-3-7-sonnet-20250219"
            }
        )
        if success and response.get("success"):
            print(f"   Recommended: {response.get('recommended_model')}")
        
        # Cache stats
        success, response = self.test_endpoint(
            "Cost Optimizer (Cache Stats)",
            "GET",
            "optimizer/cache-stats"
        )
        if success and response.get("success"):
            print(f"   Cache size: {response.get('cache_size')}")
        
        # Test 3: Learning Service
        print("\n" + "="*20 + " LEARNING SERVICE " + "="*20)
        
        # Learn from project (Mixed params and body)
        success, response = self.test_endpoint(
            "Learning Service (Learn)",
            "POST",
            "learning/learn",
            data={
                "tech_stack": ["React", "FastAPI"],
                "metrics": {"completion_time_seconds": 1800, "cost_usd": 2.5}
            },
            params={
                "project_id": f"test_project_{int(time.time())}",
                "task_description": "Build authentication system",
                "success": True
            }
        )
        if success and response.get("success"):
            print(f"   Patterns extracted: {response.get('patterns_extracted')}")
        
        # Find similar projects (Note: This endpoint has design issues with List parameters)
        success, response = self.test_endpoint(
            "Learning Service (Similar)",
            "POST",
            "learning/similar",
            params={
                "task_description": "authentication", 
                "limit": 3
            }
        )
        if success and response.get("success"):
            print(f"   Similar projects: {len(response.get('similar_projects', []))}")
        
        # Predict success (Mixed params and body)
        success, response = self.test_endpoint(
            "Learning Service (Predict)",
            "POST",
            "learning/predict",
            data=["React", "FastAPI"],
            params={
                "task_description": "login system"
            }
        )
        if success and response.get("success"):
            print(f"   Success probability: {response.get('probability'):.2f}")
        
        # Learning stats
        success, response = self.test_endpoint(
            "Learning Service (Stats)",
            "GET",
            "learning/stats"
        )
        if success and response.get("success"):
            print(f"   Patterns in memory: {response.get('patterns_in_memory')}")
        
        # Test 4: Workspace Service
        print("\n" + "="*20 + " WORKSPACE SERVICE " + "="*20)
        
        # Create workspace
        workspace_name = f"Test Workspace {datetime.now().strftime('%H%M%S')}"
        success, response = self.test_endpoint(
            "Workspace Service (Create)",
            "POST",
            "workspaces",
            params={
                "name": workspace_name,
                "owner_id": f"user_{int(time.time())}",
                "owner_email": "test@example.com"
            }
        )
        workspace_id = None
        if success and response.get("success"):
            workspace_id = response.get("workspace_id")
            print(f"   Workspace ID: {workspace_id}")
        
        # Get workspace (if created)
        if workspace_id:
            success, response = self.test_endpoint(
                "Workspace Service (Get)",
                "GET",
                f"workspaces/{workspace_id}"
            )
            if success and response.get("success"):
                workspace = response.get("workspace", {})
                print(f"   Members: {len(workspace.get('members', []))}")
        
        # List user workspaces
        success, response = self.test_endpoint(
            "Workspace Service (List)",
            "GET",
            f"workspaces/user/user_{int(time.time())}"
        )
        if success and response.get("success"):
            print(f"   User workspaces: {len(response.get('workspaces', []))}")
        
        # Test 5: Analytics Service
        print("\n" + "="*20 + " ANALYTICS SERVICE " + "="*20)
        
        # Track metrics (Note: This endpoint has design issues with Dict parameters)
        success, response = self.test_endpoint(
            "Analytics Service (Track)",
            "POST",
            "analytics/track",
            params={
                "metric_name": "task.completion_time",
                "value": 1200.0,
                "unit": "seconds"
            }
        )
        if success and response.get("success"):
            print(f"   Metric tracked successfully")
        
        # Performance dashboard
        success, response = self.test_endpoint(
            "Analytics Service (Performance)",
            "GET",
            "analytics/performance?timeframe_days=30"
        )
        if success and response.get("success"):
            task_completion = response.get("task_completion", {})
            print(f"   Avg completion: {task_completion.get('average_seconds', 0):.1f}s")
        
        # Cost dashboard
        success, response = self.test_endpoint(
            "Analytics Service (Cost)",
            "GET",
            "analytics/cost?timeframe_days=30"
        )
        if success and response.get("success"):
            print(f"   Total cost: ${response.get('total_cost', 0):.4f}")
        
        # Quality dashboard
        success, response = self.test_endpoint(
            "Analytics Service (Quality)",
            "GET",
            "analytics/quality?timeframe_days=30"
        )
        if success and response.get("success"):
            print(f"   Avg quality: {response.get('average_quality_score', 0):.1f}")
        
        # Generate insights
        success, response = self.test_endpoint(
            "Analytics Service (Insights)",
            "GET",
            f"analytics/insights/user_{int(time.time())}?timeframe_days=30"
        )
        if success and response.get("success"):
            print(f"   Insights generated: {len(response.get('insights', []))}")

    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print(f"📊 PHASE 4 MVP TEST RESULTS")
        print(f"{'='*60}")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ Failed tests:")
            for test in self.failed_tests:
                print(f"   - {test}")
        else:
            print(f"\n🎉 All Phase 4 MVP tests passed!")

def main():
    tester = Phase4Tester()
    tester.run_phase4_tests()
    tester.print_summary()
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    exit(main())