#!/usr/bin/env python3
"""
Test script to verify backend functionality
"""

import os
import requests
import json
import sys

def test_backend_status():
    """Test if the backend is accessible and working"""
    
    # Get the backend URL from environment or use a default
    backend_url = os.environ.get('BACKEND_URL', 'http://localhost:5001')
    
    print(f"🧪 Testing Backend at: {backend_url}")
    print("=" * 50)
    
    try:
        # Test 1: Basic connectivity
        print("\n🔍 Test 1: Basic Connectivity")
        print("-" * 30)
        response = requests.get(f"{backend_url}/api/status", timeout=10)
        
        if response.status_code == 200:
            print("✅ Backend is accessible")
            data = response.json()
            print(f"   Policy exists: {data.get('policy_exists', 'N/A')}")
            print(f"   Questionnaire exists: {data.get('questionnaire_exists', 'N/A')}")
            print(f"   API key configured: {data.get('api_key_configured', 'N/A')}")
            print(f"   Skip API: {data.get('skip_api', 'N/A')}")
            return True
        else:
            print(f"❌ Backend returned status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend - connection refused")
        print("   Make sure your backend is running and accessible")
        return False
    except requests.exceptions.Timeout:
        print("❌ Backend request timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_environment_variables():
    """Test if required environment variables are set"""
    print("\n🔍 Test 2: Environment Variables")
    print("-" * 30)
    
    required_vars = ['CLAUDE_API_KEY', 'GITHUB_REPO_OWNER', 'GITHUB_REPO_NAME']
    all_set = True
    
    for var in required_vars:
        value = os.environ.get(var, '')
        if value:
            print(f"✅ {var}: {value[:8]}...{value[-4:] if len(value) > 12 else ''}")
        else:
            print(f"❌ {var}: Not set")
            all_set = False
    
    return all_set

def main():
    """Run all tests"""
    print("🧪 Backend Configuration Test")
    print("=" * 50)
    
    # Test environment variables
    env_ok = test_environment_variables()
    
    # Test backend connectivity
    backend_ok = test_backend_status()
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 50)
    print(f"Environment Variables: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"Backend Connectivity: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    
    if env_ok and backend_ok:
        print("\n🎉 All tests passed! Your backend is properly configured.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        
        if not env_ok:
            print("\n💡 To fix environment variables:")
            print("   1. Go to your Render dashboard")
            print("   2. Navigate to Environment Variables")
            print("   3. Add the missing variables")
            
        if not backend_ok:
            print("\n💡 To fix backend connectivity:")
            print("   1. Make sure your backend is deployed and running")
            print("   2. Check the URL in your vercel.json")
            print("   3. Verify the backend is accessible from the internet")
    
    return 0 if (env_ok and backend_ok) else 1

if __name__ == "__main__":
    # Set this to your actual backend URL for testing
    os.environ['BACKEND_URL'] = 'https://policy-configurator-api.onrender.com'
    sys.exit(main())
