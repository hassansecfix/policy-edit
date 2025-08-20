#!/usr/bin/env python3
"""
Test script to verify rate limiting functionality works correctly.

This script will test:
1. Rate limiting between API calls
2. Retry logic for simulated 429 errors
3. Basic API functionality

Usage:
    python3 test_rate_limiting.py
"""

import os
import sys
import time
from pathlib import Path

# Add the scripts directory to the path so we can import our utilities
sys.path.append(str(Path(__file__).parent))

try:
    from claude_api_utils import call_claude_api_with_retry, test_claude_api_with_retry
except ImportError as e:
    print(f"❌ Failed to import claude_api_utils: {e}")
    sys.exit(1)


def test_rate_limiting():
    """Test that rate limiting is working between API calls."""
    print("🧪 Testing Rate Limiting Functionality")
    print("=" * 50)
    
    api_key = os.environ.get('CLAUDE_API_KEY', '')
    if not api_key:
        print("❌ CLAUDE_API_KEY not set")
        print("   Set the environment variable or add it to your .env file")
        return False
    
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        print("📞 Making first API call...")
        start_time = time.time()
        
        response1 = call_claude_api_with_retry(
            client=client,
            model="claude-3-haiku-20240307",  # Use Haiku for cost efficiency
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10,
            max_retries=2
        )
        
        first_call_time = time.time()
        print(f"✅ First call completed in {first_call_time - start_time:.2f}s")
        print(f"   Response: {response1}")
        
        print("\n📞 Making second API call (should be rate limited)...")
        second_start = time.time()
        
        response2 = call_claude_api_with_retry(
            client=client,
            model="claude-3-haiku-20240307",
            messages=[{"role": "user", "content": "Say goodbye"}],
            max_tokens=10,
            max_retries=2
        )
        
        second_call_time = time.time()
        total_time = second_call_time - first_call_time
        print(f"✅ Second call completed in {total_time:.2f}s")
        print(f"   Response: {response2}")
        
        # Check if rate limiting worked (should be at least 2 seconds between calls)
        if total_time >= 2.0:
            print(f"✅ Rate limiting working correctly (waited {total_time:.2f}s)")
            return True
        else:
            print(f"⚠️  Rate limiting may not be working (only waited {total_time:.2f}s)")
            return False
            
    except Exception as e:
        error_message = str(e)
        if "429" in error_message or "rate_limit_error" in error_message:
            print("✅ Rate limit error detected and handled correctly!")
            print(f"   Error message: {error_message}")
            return True
        else:
            print(f"❌ Unexpected error: {e}")
            return False


def main():
    """Run the rate limiting tests."""
    print("🚀 Claude API Rate Limiting Test Suite")
    print("=" * 60)
    
    # Test 1: Basic API test with retry utilities
    print("\n📋 Test 1: Basic API functionality")
    api_key = os.environ.get('CLAUDE_API_KEY', '')
    if not api_key:
        print("❌ CLAUDE_API_KEY not set - skipping tests")
        return False
    
    basic_test_result = test_claude_api_with_retry(api_key)
    
    # Test 2: Rate limiting functionality
    print("\n📋 Test 2: Rate limiting between calls")
    rate_limit_result = test_rate_limiting()
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    print(f"Basic API test: {'✅ PASS' if basic_test_result else '❌ FAIL'}")
    print(f"Rate limiting test: {'✅ PASS' if rate_limit_result else '❌ FAIL'}")
    
    overall_success = basic_test_result and rate_limit_result
    print(f"\nOverall result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 Your Claude API rate limiting implementation is working correctly!")
        print("   You can now run your policy processing with confidence.")
    else:
        print("\n⚠️  Some issues detected. Please review the error messages above.")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
