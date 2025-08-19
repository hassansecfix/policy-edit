#!/usr/bin/env python3
"""
Test script to debug Anthropic API key issues
"""

import os
import sys

def test_anthropic_import():
    """Test if anthropic package can be imported"""
    try:
        import anthropic
        print(f"✅ Anthropic package imported successfully")
        print(f"   Version: {anthropic.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import anthropic: {e}")
        return False

def test_api_key_format():
    """Test if the API key is properly formatted"""
    api_key = os.environ.get('CLAUDE_API_KEY', '')
    
    if not api_key:
        print("❌ CLAUDE_API_KEY environment variable not set")
        return False
    
    print(f"✅ CLAUDE_API_KEY found")
    print(f"   Length: {len(api_key)} characters")
    print(f"   Starts with: {api_key[:8]}...")
    print(f"   Ends with: ...{api_key[-4:]}")
    
    # Check if it looks like a valid Anthropic API key
    if api_key.startswith('sk-ant-'):
        print("✅ API key format looks correct (starts with 'sk-ant-')")
        return True
    else:
        print("⚠️  API key format may be incorrect (should start with 'sk-ant-')")
        return False

def test_anthropic_client():
    """Test creating an Anthropic client"""
    if not test_anthropic_import():
        return False
    
    api_key = os.environ.get('CLAUDE_API_KEY', '')
    if not api_key:
        return False
    
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        print("✅ Anthropic client created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create Anthropic client: {e}")
        return False

def test_simple_api_call():
    """Test a simple API call"""
    if not test_anthropic_client():
        return False
    
    try:
        import anthropic
        api_key = os.environ.get('CLAUDE_API_KEY', '')
        client = anthropic.Anthropic(api_key=api_key)
        
        # Test with a simple message
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        print("✅ Simple API call successful")
        print(f"   Response: {message.content[0].text}")
        return True
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Anthropic API Configuration")
    print("=" * 50)
    
    tests = [
        ("Package Import", test_anthropic_import),
        ("API Key Format", test_api_key_format),
        ("Client Creation", test_anthropic_client),
        ("Simple API Call", test_simple_api_call),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n📊 Test Results Summary")
    print("=" * 50)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All tests passed! Your Anthropic configuration is working.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
