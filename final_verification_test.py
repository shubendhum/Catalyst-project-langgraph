#!/usr/bin/env python3
"""
Final verification test for all chat interface functionality
"""

import requests
import json

BASE_URL = "https://catalyst-agents.preview.emergentagent.com/api"

def test_endpoint(name, method, endpoint, data=None, timeout=15):
    """Test endpoint with detailed logging"""
    url = f"{BASE_URL}/{endpoint}"
    headers = {'Content-Type': 'application/json'}
    
    print(f"\n🔍 {name}")
    print(f"   URL: {method} {url}")
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=timeout)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=timeout)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS")
            try:
                result = response.json()
                return True, result
            except:
                return True, response.text
        else:
            print(f"   ❌ FAILED")
            print(f"   Error: {response.text[:200]}")
            return False, {}
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False, {}

def main():
    print("🚀 Final Verification Test - Chat Interface")
    print("Testing all scenarios from review request")
    print("=" * 60)
    
    results = {
        "llm_config": [],
        "conversations": [],
        "messages": [],
        "errors": []
    }
    
    # === LLM Configuration Tests ===
    print("\n📋 LLM CONFIGURATION ENDPOINTS")
    
    # Test all three providers
    providers = [
        ("emergent", "claude-3-7-sonnet-20250219", None, None),
        ("anthropic", "claude-3-sonnet-20240229", "test-key", None),
        ("bedrock", "anthropic.claude-3-sonnet-20240229-v1:0", None, {
            "access_key_id": "test-key",
            "secret_access_key": "test-secret",
            "region": "us-east-1"
        })
    ]
    
    for provider, model, api_key, aws_config in providers:
        success, response = test_endpoint(
            f"Set LLM Config ({provider.title()})",
            "POST",
            "chat/config",
            {
                "provider": provider,
                "model": model,
                "api_key": api_key,
                "aws_config": aws_config
            }
        )
        results["llm_config"].append((provider, success))
    
    # Get current config
    success, response = test_endpoint("Get LLM Config", "GET", "chat/config")
    if success:
        print(f"   Current: {response.get('provider')} - {response.get('model')}")
    
    # Reset to emergent for testing
    test_endpoint(
        "Reset to Emergent",
        "POST",
        "chat/config",
        {"provider": "emergent", "model": "claude-3-7-sonnet-20250219"}
    )
    
    # === Conversation Management ===
    print("\n💬 CONVERSATION MANAGEMENT")
    
    success, conv_response = test_endpoint("Create Conversation", "POST", "chat/conversations")
    conversation_id = conv_response.get("id") if success else None
    results["conversations"].append(("create", success))
    
    success, response = test_endpoint("List Conversations", "GET", "chat/conversations")
    results["conversations"].append(("list", success))
    
    if conversation_id:
        success, response = test_endpoint(
            "Get Conversation", 
            "GET", 
            f"chat/conversations/{conversation_id}"
        )
        results["conversations"].append(("get", success))
    
    # === Message Handling ===
    print("\n📨 MESSAGE HANDLING & INTENTS")
    
    if conversation_id:
        # Test different intents
        test_messages = [
            ("help", "Help intent"),
            ("create a new project called TestApp", "Create project intent"),
            ("what's the status?", "Status intent"),
        ]
        
        for message, description in test_messages:
            success, response = test_endpoint(
                f"Send Message: {description}",
                "POST",
                "chat/send",
                {
                    "message": message,
                    "conversation_id": conversation_id
                },
                timeout=30  # Longer timeout for LLM calls
            )
            results["messages"].append((description, success))
            
            if success:
                metadata = response.get("message", {}).get("metadata", {})
                print(f"   Action: {metadata.get('action', 'unknown')}")
        
        # Get all messages
        success, response = test_endpoint(
            "Get Messages",
            "GET",
            f"chat/conversations/{conversation_id}/messages"
        )
        if success:
            print(f"   Total messages in conversation: {len(response)}")
    
    # === Cleanup ===
    if conversation_id:
        success, response = test_endpoint(
            "Delete Conversation",
            "DELETE",
            f"chat/conversations/{conversation_id}"
        )
        results["conversations"].append(("delete", success))
    
    # === Results Summary ===
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS SUMMARY")
    print("=" * 60)
    
    print("\n🔧 LLM Configuration:")
    for provider, success in results["llm_config"]:
        status = "✅" if success else "❌"
        print(f"   {status} {provider.title()} provider")
    
    print("\n💬 Conversation Management:")
    for operation, success in results["conversations"]:
        status = "✅" if success else "❌"
        print(f"   {status} {operation.title()} conversation")
    
    print("\n📨 Message Handling:")
    for intent, success in results["messages"]:
        status = "✅" if success else "❌"
        print(f"   {status} {intent}")
    
    # Overall assessment
    total_tests = len(results["llm_config"]) + len(results["conversations"]) + len(results["messages"])
    passed_tests = sum([
        sum(success for _, success in results["llm_config"]),
        sum(success for _, success in results["conversations"]),
        sum(success for _, success in results["messages"])
    ])
    
    print(f"\n🎯 OVERALL: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - Chat interface fully functional!")
    else:
        print("⚠️  Some tests failed - see details above")

if __name__ == "__main__":
    main()