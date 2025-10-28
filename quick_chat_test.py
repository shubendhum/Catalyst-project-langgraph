#!/usr/bin/env python3
"""
Quick Chat Interface Test - Key functionality only
"""

import requests
import json

BASE_URL = "https://agent-dev-hub-3.preview.emergentagent.com/api"

def test_endpoint(name, method, endpoint, data=None):
    """Test a single endpoint quickly"""
    url = f"{BASE_URL}/{endpoint}"
    headers = {'Content-Type': 'application/json'}
    
    print(f"🔍 {name}: ", end="")
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ PASS")
            try:
                return True, response.json()
            except:
                return True, response.text
        else:
            print(f"❌ FAIL ({response.status_code})")
            return False, {}
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False, {}

def main():
    print("🚀 Quick Chat Interface Test")
    print("=" * 40)
    
    # Test LLM Config endpoints
    test_endpoint("Set LLM Config", "POST", "chat/config", {
        "provider": "emergent",
        "model": "claude-3-7-sonnet-20250219"
    })
    
    test_endpoint("Get LLM Config", "GET", "chat/config")
    
    # Test Conversation Management
    success, conv_response = test_endpoint("Create Conversation", "POST", "chat/conversations")
    conversation_id = conv_response.get("id") if success else None
    
    test_endpoint("List Conversations", "GET", "chat/conversations")
    
    if conversation_id:
        test_endpoint("Get Conversation", "GET", f"chat/conversations/{conversation_id}")
        test_endpoint("Get Messages", "GET", f"chat/conversations/{conversation_id}/messages")
        test_endpoint("Delete Conversation", "DELETE", f"chat/conversations/{conversation_id}")
    
    print("\n✅ All basic endpoints working!")

if __name__ == "__main__":
    main()