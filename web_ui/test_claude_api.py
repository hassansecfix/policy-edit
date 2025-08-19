#!/usr/bin/env python3
"""
Test script to verify Claude API functionality from backend perspective
"""

import os
import sys
import requests
import json

def test_backend_claude_integration():
    """Test if the backend can successfully make Claude API calls"""
    
    backend_url = "https://policy-configurator-api.onrender.com"
    
    print("🧪 Testing Backend Claude API Integration")
    print("=" * 60)
    
    try:
        # Step 1: Check backend status
        print("\n🔍 Step 1: Checking Backend Status")
        print("-" * 40)
        response = requests.get(f"{backend_url}/api/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend status check successful")
            print(f"   API key configured: {data.get('api_key_configured')}")
            print(f"   Skip API: {data.get('skip_api')}")
            print(f"   Policy exists: {data.get('policy_exists')}")
            print(f"   Questionnaire exists: {data.get('questionnaire_exists')}")
        else:
            print(f"❌ Backend status check failed: {response.status_code}")
            return False
        
        # Step 2: Start automation (this will trigger Claude API call)
        print("\n🔍 Step 2: Starting Automation (Triggers Claude API)")
        print("-" * 40)
        
        start_response = requests.post(
            f"{backend_url}/api/start",
            json={"skip_api": False},
            timeout=30  # Longer timeout for automation
        )
        
        if start_response.status_code == 200:
            print("✅ Automation started successfully")
            print("   This should trigger a Claude API call...")
        else:
            print(f"❌ Failed to start automation: {start_response.status_code}")
            print(f"   Response: {start_response.text}")
            return False
        
        # Step 3: Wait a moment and check status
        print("\n🔍 Step 3: Checking Automation Status")
        print("-" * 40)
        
        import time
        time.sleep(5)  # Wait for automation to start
        
        status_response = requests.get(f"{backend_url}/api/status", timeout=10)
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"   Automation running: {status_data.get('automation_running')}")
            
            if status_data.get('automation_running'):
                print("   ✅ Automation is running - Claude API call should be in progress")
            else:
                print("   ⚠️  Automation stopped - may have failed")
        else:
            print(f"   ❌ Status check failed: {status_response.status_code}")
        
        # Step 4: Stop automation
        print("\n🔍 Step 4: Stopping Automation")
        print("-" * 40)
        
        stop_response = requests.post(f"{backend_url}/api/stop", timeout=10)
        if stop_response.status_code == 200:
            print("✅ Automation stopped successfully")
        else:
            print(f"❌ Failed to stop automation: {stop_response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_local_claude_api():
    """Test Claude API locally to verify API key works"""
    
    print("\n🧪 Testing Local Claude API Key")
    print("=" * 60)
    
    api_key = os.environ.get('CLAUDE_API_KEY', '')
    if not api_key:
        print("❌ CLAUDE_API_KEY not set locally")
        return False
    
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        # Test with a simple message
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        print("✅ Local Claude API call successful")
        print(f"   Response: {message.content[0].text}")
        return True
        
    except Exception as e:
        print(f"❌ Local Claude API call failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Comprehensive Claude API Integration Test")
    print("=" * 60)
    
    # Test 1: Local Claude API
    local_ok = test_local_claude_api()
    
    # Test 2: Backend Claude integration
    backend_ok = test_backend_claude_integration()
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 60)
    print(f"Local Claude API: {'✅ PASS' if local_ok else '❌ FAIL'}")
    print(f"Backend Integration: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    
    if local_ok and backend_ok:
        print("\n🎉 All tests passed! Your Claude integration is working.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        
        if not local_ok:
            print("\n💡 Local API key issue:")
            print("   - Check your CLAUDE_API_KEY format")
            print("   - Verify the key is valid and active")
            
        if not backend_ok:
            print("\n💡 Backend integration issue:")
            print("   - Check your Render environment variables")
            print("   - Verify CLAUDE_API_KEY is set in Render")
            print("   - Check Render logs for detailed error messages")
    
    return 0 if (local_ok and backend_ok) else 1

if __name__ == "__main__":
    sys.exit(main())
