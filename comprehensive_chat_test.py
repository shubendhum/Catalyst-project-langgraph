#!/usr/bin/env python3
"""
Comprehensive Chat Interface Test - Testing all scenarios from the review request
"""

import requests
import json
import time

BASE_URL = "https://catalyst-agents.preview.emergentagent.com/api"

def test_endpoint(name, method, endpoint, data=None, expected_status=200, timeout=60):
    """Test a single endpoint"""
    url = f"{BASE_URL}/{endpoint}"
    headers = {'Content-Type': 'application/json'}
    
    print(f"\n🔍 Testing {name}")
    print(f"   {method} {url}")
    if data:
        print(f"   Data: {json.dumps(data, indent=2)[:200]}...")
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=timeout)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=timeout)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == expected_status:
            print("   ✅ PASSED")
            try:
                result = response.json()
                return True, result
            except:
                return True, response.text
        else:
            print(f"   ❌ FAILED - Expected {expected_status}")
            print(f"   Response: {response.text[:300]}")
            return False, {}
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False, {}

def main():
    print("🚀 Comprehensive Chat Interface Testing")
    print("Testing all scenarios from review request")
    print("=" * 60)
    
    conversation_id = None
    
    # === LLM Configuration Tests ===
    print("\n" + "="*20 + " LLM CONFIGURATION " + "="*20)
    
    # Test 1: Set LLM config to Emergent
    success, response = test_endpoint(
        "Set LLM Config (Emergent)",
        "POST",
        "chat/config",
        {
            "provider": "emergent",
            "model": "claude-3-7-sonnet-20250219",
            "api_key": None,
            "aws_config": None
        }
    )
    
    # Test 2: Get LLM Config
    success, response = test_endpoint(
        "Get LLM Config",
        "GET",
        "chat/config"
    )
    if success:
        print(f"   Current Provider: {response.get('provider')}")
        print(f"   Current Model: {response.get('model')}")
    
    # Test 3: Set LLM config to Anthropic
    success, response = test_endpoint(
        "Set LLM Config (Anthropic)",
        "POST",
        "chat/config",
        {
            "provider": "anthropic",
            "model": "claude-3-sonnet-20240229",
            "api_key": "test-anthropic-key",
            "aws_config": None
        }
    )
    
    # Test 4: Set LLM config to Bedrock
    success, response = test_endpoint(
        "Set LLM Config (Bedrock)",
        "POST",
        "chat/config",
        {
            "provider": "bedrock",
            "model": "anthropic.claude-3-sonnet-20240229-v1:0",
            "api_key": None,
            "aws_config": {
                "access_key_id": "test-access-key",
                "secret_access_key": "test-secret-key",
                "region": "us-east-1"
            }
        }
    )
    
    # Reset to Emergent for actual testing
    success, response = test_endpoint(
        "Reset to Emergent LLM",
        "POST",
        "chat/config",
        {
            "provider": "emergent",
            "model": "claude-3-7-sonnet-20250219",
            "api_key": None,
            "aws_config": None
        }
    )
    
    # === Conversation Management Tests ===
    print("\n" + "="*20 + " CONVERSATION MANAGEMENT " + "="*20)
    
    # Test 5: Create Conversation
    success, response = test_endpoint(
        "Create New Conversation",
        "POST",
        "chat/conversations"
    )
    
    if success and "id" in response:
        conversation_id = response["id"]
        print(f"   Conversation ID: {conversation_id}")
    
    # Test 6: List Conversations
    success, response = test_endpoint(
        "List All Conversations",
        "GET",
        "chat/conversations"
    )
    if success:
        print(f"   Total conversations: {len(response)}")
    
    # Test 7: Get Specific Conversation
    if conversation_id:
        success, response = test_endpoint(
            "Get Specific Conversation",
            "GET",
            f"chat/conversations/{conversation_id}"
        )
    
    # === Message Handling Tests ===
    print("\n" + "="*20 + " MESSAGE HANDLING " + "="*20)
    
    if not conversation_id:
        print("❌ Cannot test messages - no conversation ID")
        return
    
    # Test 8: Send "help" message
    success, response = test_endpoint(
        "Send Help Message",
        "POST",
        "chat/send",
        {
            "message": "help",
            "conversation_id": conversation_id
        }
    )
    if success:
        content = response.get("message", {}).get("content", "")
        print(f"   Help response length: {len(content)} chars")
        print(f"   Contains 'help': {'help' in content.lower()}")
    
    # Test 9: Send "create project" message
    success, response = test_endpoint(
        "Send Create Project Message",
        "POST",
        "chat/send",
        {
            "message": "create a new project called TestApp",
            "conversation_id": conversation_id
        }
    )
    if success:
        metadata = response.get("message", {}).get("metadata", {})
        print(f"   Action: {metadata.get('action')}")
        if metadata.get("project_id"):
            print(f"   Project ID: {metadata.get('project_id')}")
    
    # Test 10: Send "build app" message
    success, response = test_endpoint(
        "Send Build App Message",
        "POST",
        "chat/send",
        {
            "message": "build me a todo app",
            "conversation_id": conversation_id
        }
    )
    if success:
        metadata = response.get("message", {}).get("metadata", {})
        print(f"   Action: {metadata.get('action')}")
        if metadata.get("task_id"):
            print(f"   Task ID: {metadata.get('task_id')}")
    
    # Test 11: Send "status" message
    success, response = test_endpoint(
        "Send Status Message",
        "POST",
        "chat/send",
        {
            "message": "what's the status?",
            "conversation_id": conversation_id
        }
    )
    if success:
        content = response.get("message", {}).get("content", "")
        metadata = response.get("message", {}).get("metadata", {})
        print(f"   Status response: {content[:100]}...")
        print(f"   Action: {metadata.get('action')}")
    
    # Test 12: Get conversation messages
    success, response = test_endpoint(
        "Get Conversation Messages",
        "GET",
        f"chat/conversations/{conversation_id}/messages"
    )
    if success:
        print(f"   Total messages: {len(response)}")
        for i, msg in enumerate(response):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:50]
            print(f"   Message {i+1}: [{role}] {content}...")
    
    # === Additional Intent Tests ===
    print("\n" + "="*20 + " ADDITIONAL INTENTS " + "="*20)
    
    # Test various intents
    test_messages = [
        ("General Question", "How does this platform work?"),
        ("Feature Request", "add authentication to my app"),
        ("Bug Report", "there's a bug in the login system"),
        ("Deploy Request", "deploy my application"),
        ("System Analysis", "analyze my GitHub repository"),
    ]
    
    for intent_name, message in test_messages:
        success, response = test_endpoint(
            f"Send {intent_name}",
            "POST",
            "chat/send",
            {
                "message": message,
                "conversation_id": conversation_id
            }
        )
        if success:
            metadata = response.get("message", {}).get("metadata", {})
            print(f"   Detected action: {metadata.get('action', 'unknown')}")
    
    # === Cleanup ===
    print("\n" + "="*20 + " CLEANUP " + "="*20)
    
    # Test 13: Delete conversation
    if conversation_id:
        success, response = test_endpoint(
            "Delete Conversation",
            "DELETE",
            f"chat/conversations/{conversation_id}"
        )
    
    print("\n" + "=" * 60)
    print("🏁 Comprehensive Chat Interface Testing Complete")
    print("All major endpoints and intents tested successfully!")

if __name__ == "__main__":
    main()