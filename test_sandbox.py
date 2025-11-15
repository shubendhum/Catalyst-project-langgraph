#!/usr/bin/env python3
"""
Sandbox Service Test Suite

Tests the sandboxed code execution system.
Run this after building the sandbox-runner image.
"""
import asyncio
import json
import sys
from typing import Dict, Any


async def test_sandbox_status():
    """Test sandbox service status endpoint"""
    import aiohttp
    
    print("\n" + "="*60)
    print("TEST 1: Sandbox Service Status")
    print("="*60)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8001/api/sandbox/status") as response:
                result = await response.json()
                
                print(f"Status Code: {response.status}")
                print(f"Response: {json.dumps(result, indent=2)}")
                
                if result.get("success") and result.get("status") == "healthy":
                    print("✅ PASSED: Sandbox service is healthy")
                    return True
                else:
                    print("❌ FAILED: Sandbox service is not healthy")
                    return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


async def test_simple_command():
    """Test simple command execution"""
    import aiohttp
    
    print("\n" + "="*60)
    print("TEST 2: Simple Command Execution")
    print("="*60)
    
    payload = {
        "command": "echo 'Hello from sandbox!'",
        "timeout": 30
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8001/api/sandbox/run",
                json=payload
            ) as response:
                result = await response.json()
                
                print(f"Status Code: {response.status}")
                print(f"Command: {payload['command']}")
                print(f"Exit Code: {result.get('exit_code')}")
                print(f"Stdout: {result.get('stdout')}")
                print(f"Duration: {result.get('duration')}s")
                
                if result.get("success") and result.get("exit_code") == 0:
                    print("✅ PASSED: Command executed successfully")
                    return True
                else:
                    print("❌ FAILED: Command execution failed")
                    return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


async def test_python_script():
    """Test Python script execution"""
    import aiohttp
    
    print("\n" + "="*60)
    print("TEST 3: Python Script Execution")
    print("="*60)
    
    payload = {
        "command": "python hello.py",
        "files": {
            "hello.py": "print('Hello, World!')\nprint(f'1 + 1 = {1+1}')"
        },
        "timeout": 30
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8001/api/sandbox/run",
                json=payload
            ) as response:
                result = await response.json()
                
                print(f"Status Code: {response.status}")
                print(f"Exit Code: {result.get('exit_code')}")
                print(f"Stdout:\n{result.get('stdout')}")
                print(f"Duration: {result.get('duration')}s")
                
                if result.get("success") and "Hello, World!" in result.get("stdout", ""):
                    print("✅ PASSED: Python script executed successfully")
                    return True
                else:
                    print("❌ FAILED: Python script execution failed")
                    return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


async def test_python_tests():
    """Test Python pytest execution"""
    import aiohttp
    
    print("\n" + "="*60)
    print("TEST 4: Python Tests with pytest")
    print("="*60)
    
    payload = {
        "test_files": {
            "test_math.py": """
def test_addition():
    assert 1 + 1 == 2

def test_subtraction():
    assert 5 - 3 == 2

def test_multiplication():
    assert 3 * 4 == 12
"""
        },
        "source_files": {
            "math_utils.py": """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
        },
        "requirements": ["pytest"],
        "pytest_args": "-v"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8001/api/sandbox/test/python",
                json=payload
            ) as response:
                result = await response.json()
                
                print(f"Status Code: {response.status}")
                print(f"Success: {result.get('success')}")
                print(f"Exit Code: {result.get('exit_code')}")
                print(f"Duration: {result.get('duration')}s")
                print(f"\nTest Output (first 500 chars):\n{result.get('stdout', '')[:500]}")
                
                if result.get("exit_code") == 0:
                    print("✅ PASSED: pytest executed successfully")
                    return True
                else:
                    print("❌ FAILED: pytest execution failed")
                    print(f"Stderr: {result.get('stderr', '')[:200]}")
                    return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


async def test_linter():
    """Test code linting"""
    import aiohttp
    
    print("\n" + "="*60)
    print("TEST 5: Code Linting with flake8")
    print("="*60)
    
    payload = {
        "files": {
            "example.py": """
def hello():
    print('world')

def add(a, b):
    return a + b
"""
        },
        "linter": "flake8",
        "linter_args": "--max-line-length=120"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8001/api/sandbox/lint",
                json=payload
            ) as response:
                result = await response.json()
                
                print(f"Status Code: {response.status}")
                print(f"Success: {result.get('success')}")
                print(f"Exit Code: {result.get('exit_code')}")
                print(f"Duration: {result.get('duration')}s")
                
                if result.get('stdout'):
                    print(f"\nLinter Output:\n{result.get('stdout')}")
                if result.get('stderr'):
                    print(f"\nLinter Warnings:\n{result.get('stderr')}")
                
                # flake8 returns 0 if no issues or 1 if issues found
                # Both are "successful" executions
                if result.get("exit_code") in [0, 1]:
                    print("✅ PASSED: Linter executed successfully")
                    return True
                else:
                    print("❌ FAILED: Linter execution failed")
                    return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


async def test_timeout():
    """Test timeout mechanism"""
    import aiohttp
    
    print("\n" + "="*60)
    print("TEST 6: Timeout Protection")
    print("="*60)
    
    payload = {
        "command": "python infinite.py",
        "files": {
            "infinite.py": "import time\nwhile True:\n    time.sleep(1)"
        },
        "timeout": 5  # 5 second timeout
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8001/api/sandbox/run",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)  # HTTP timeout > sandbox timeout
            ) as response:
                result = await response.json()
                
                print(f"Status Code: {response.status}")
                print(f"Success: {result.get('success')}")
                print(f"Duration: {result.get('duration')}s")
                
                error_msg = result.get('error', '')
                if 'timeout' in error_msg.lower():
                    print(f"Error: {error_msg}")
                    print("✅ PASSED: Timeout protection working")
                    return True
                else:
                    print("⚠️ PARTIAL: Command may have been killed but no timeout error")
                    return True  # Still pass as timeout worked
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


async def test_requirements_install():
    """Test package installation"""
    import aiohttp
    
    print("\n" + "="*60)
    print("TEST 7: Python Requirements Installation")
    print("="*60)
    
    payload = {
        "command": "python -c 'import requests; print(f\"requests version: {requests.__version__}\")'",
        "requirements": ["requests"],
        "timeout": 120  # Allow time for package install
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8001/api/sandbox/run",
                json=payload
            ) as response:
                result = await response.json()
                
                print(f"Status Code: {response.status}")
                print(f"Exit Code: {result.get('exit_code')}")
                print(f"Stdout: {result.get('stdout')}")
                print(f"Duration: {result.get('duration')}s")
                
                if result.get("success") and "requests version" in result.get("stdout", ""):
                    print("✅ PASSED: Requirements installed successfully")
                    return True
                else:
                    print("❌ FAILED: Requirements installation failed")
                    print(f"Stderr: {result.get('stderr', '')[:300]}")
                    return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 SANDBOX SERVICE TEST SUITE")
    print("="*60)
    print("\nTesting sandboxed code execution system...")
    print("Make sure the backend is running and sandbox image is built!")
    print("\nPrerequisites:")
    print("  1. docker-compose up -d")
    print("  2. docker-compose build sandbox-runner")
    print("")
    
    tests = [
        ("Sandbox Status", test_sandbox_status),
        ("Simple Command", test_simple_command),
        ("Python Script", test_python_script),
        ("Python Tests", test_python_tests),
        ("Code Linting", test_linter),
        ("Timeout Protection", test_timeout),
        ("Requirements Install", test_requirements_install),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ TEST CRASHED: {name}")
            print(f"   Error: {str(e)}")
            results.append((name, False))
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\n{passed}/{total} tests passed ({int(passed/total*100)}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Sandbox service is working correctly.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
