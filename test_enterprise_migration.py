#!/usr/bin/env python3
"""
Enterprise Migration Verification Test Suite
Tests that enterprise features are properly disabled in K8s environment
"""

import sys
from backend_test import CatalystAPITester

def main():
    print("=" * 80)
    print("ENTERPRISE MIGRATION VERIFICATION TEST SUITE")
    print("=" * 80)
    print()
    print("Testing that enterprise migration hasn't broken K8s environment...")
    print()
    
    tester = CatalystAPITester()
    
    # Critical Tests for Enterprise Migration
    tests = [
        ("1. Environment Detection", tester.test_environment_detection),
        ("2. Backend Health", tester.test_backend_health),
        ("3. Chat Functionality (No Postgres/RabbitMQ)", tester.test_chat_no_postgres_errors),
        ("4. Cost Stats API", tester.test_cost_stats_api),
        ("5. Model Selection API", tester.test_model_selection_api),
        ("6. Git Repos (Should Be Disabled)", tester.test_git_repos_disabled),
        ("7. Preview Deployments (Should Be Disabled)", tester.test_preview_disabled),
        ("8. Backend Startup Logs", tester.test_backend_startup_logs),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 80}")
        print(f"Running: {test_name}")
        print('=' * 80)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Print Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 80)
    
    # Exit with appropriate code
    if passed == total:
        print("\n🎉 All enterprise migration tests passed!")
        print("✅ K8s environment is working correctly")
        print("✅ Enterprise features are properly disabled")
        print("✅ Existing functionality is intact")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("Please review the failures above")
        sys.exit(1)

if __name__ == "__main__":
    main()
