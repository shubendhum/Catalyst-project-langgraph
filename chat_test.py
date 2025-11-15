#!/usr/bin/env python3
"""
Focused test for Chat Interface endpoints
"""

import requests
import json
import time

BASE_URL = "https://dev-sandbox-90.preview.emergentagent.com/api"

def test_endpoint(name, method, endpoint, data=None, expected_status=200):
    """Test a single endpoint"""
    url = f"{BASE_URL}/{endpoint}"
    headers = {'Content-Type': 'application/json'}
    
    print(f"\n🔍 Testing {name}")
    print(f"   {method} {url}")
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=30)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=30)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == expected_status:
            print("   ✅ PASSED")
            try:
                return True, response.json()
            except:
                return True, response.text
        else:
            print(f"   ❌ FAILED - Expected {expected_status}")
            print(f"   Response: {response.text[:200]}")
            return False, {}
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False, {}

def main():
    print("🚀 Testing Chat Interface Endpoints")
    print("=" * 50)
    
    conversation_id = None
    
    # Test 1: Set LLM Config (Emergent)
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
    
    # Test 3: Create Conversation
    success, response = test_endpoint(
        "Create Conversation",
        "POST",
        "chat/conversations"
    )
    
    if success and "id" in response:
        conversation_id = response["id"]
        print(f"   Conversation ID: {conversation_id}")
    
    # Test 4: List Conversations
    success, response = test_endpoint(
        "List Conversations",
        "GET",
        "chat/conversations"
    )
    
    # Test 5: Get Specific Conversation
    if conversation_id:
        success, response = test_endpoint(
            "Get Conversation",
            "GET",
            f"chat/conversations/{conversation_id}"
        )
    
    # Test 6: Send Help Message
    if conversation_id:
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
            print(f"   Response length: {len(content)} chars")
    
    # Test 7: Send Create Project Message
    if conversation_id:
        success, response = test_endpoint(
            "Send Create Project Message",
            "POST",
            "chat/send",
            {
                "message": "create a new project called TestChatApp",
                "conversation_id": conversation_id
            }
        )
        
        if success:
            metadata = response.get("message", {}).get("metadata", {})
            if metadata.get("project_id"):
                print(f"   Project created: {metadata.get('project_id')}")
    
    # Test 8: Send Status Message
    if conversation_id:
        success, response = test_endpoint(
            "Send Status Message",
            "POST",
            "chat/send",
            {
                "message": "what's the status?",
                "conversation_id": conversation_id
            }
        )
    
    # Test 9: Get Conversation Messages
    if conversation_id:
        success, response = test_endpoint(
            "Get Conversation Messages",
            "GET",
            f"chat/conversations/{conversation_id}/messages"
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} messages")
    
    # Test 10: Delete Conversation
    if conversation_id:
        success, response = test_endpoint(
            "Delete Conversation",
            "DELETE",
            f"chat/conversations/{conversation_id}"
        )
    
    print("\n" + "=" * 50)
    print("🏁 Chat Interface Testing Complete")

if __name__ == "__main__":
    main()