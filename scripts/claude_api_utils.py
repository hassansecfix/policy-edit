#!/usr/bin/env python3
"""
Claude API Utilities - Rate limiting and retry logic for Claude API calls

This module provides utilities for making robust Claude API calls with:
- Exponential backoff retry logic for rate limits (429 errors)
- Built-in rate limiting to prevent hitting API limits
- Proper error handling for different error types
- Comprehensive logging for debugging

Usage:
    from claude_api_utils import call_claude_api_with_retry
    
    response = call_claude_api_with_retry(
        client=your_anthropic_client,
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=1000
    )
"""

import time
import random
import warnings

# Suppress deprecation warnings for the Claude API
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Rate limiting globals
_last_api_call_time = None
_min_time_between_calls = 2.0  # Minimum 2 seconds between API calls


def enforce_rate_limit():
    """Enforce rate limiting to prevent hitting API limits."""
    global _last_api_call_time, _min_time_between_calls
    
    if _last_api_call_time is not None:
        time_since_last_call = time.time() - _last_api_call_time
        if time_since_last_call < _min_time_between_calls:
            sleep_time = _min_time_between_calls - time_since_last_call
            print(f"⏱️  Rate limiting: waiting {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
    
    _last_api_call_time = time.time()


def call_claude_api_with_retry(client, model, messages, max_tokens=4000, temperature=0.1, max_retries=5, **kwargs):
    """
    Call Claude API with built-in retry logic and rate limiting.
    
    Args:
        client: Anthropic client instance
        model: Model name (e.g., "claude-3-5-sonnet-20241022")
        messages: List of message dictionaries
        max_tokens: Maximum tokens in response
        temperature: Temperature for response generation
        max_retries: Maximum number of retry attempts
        **kwargs: Additional arguments to pass to client.messages.create()
    
    Returns:
        Response text from Claude API
        
    Raises:
        Exception: If API call fails after all retries
    """
    
    # Retry logic with exponential backoff for rate limiting
    for attempt in range(max_retries):
        try:
            print(f"🔄 API attempt {attempt + 1}/{max_retries}...")
            
            # Enforce rate limiting before each API call
            enforce_rate_limit()
            
            message = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
                **kwargs
            )
            
            print("✅ API call successful!")
            return message.content[0].text
        
        except Exception as e:
            error_message = str(e)
            print(f"⚠️  API attempt {attempt + 1} failed: {error_message}")
            
            # Check if it's a rate limit error (429)
            if "429" in error_message or "rate_limit_error" in error_message:
                if attempt < max_retries - 1:  # Don't wait on the last attempt
                    # Exponential backoff with jitter
                    base_delay = 2 ** attempt  # 1, 2, 4, 8, 16 seconds
                    jitter = random.uniform(0.5, 1.5)  # Add randomness to avoid thundering herd
                    delay = base_delay * jitter
                    
                    print(f"⏱️  Rate limit exceeded. Waiting {delay:.1f} seconds before retry...")
                    print("💡 Tip: Consider reducing the frequency of API calls or upgrading your Anthropic plan")
                    time.sleep(delay)
                    continue
                else:
                    print("❌ Maximum retries exceeded for rate limiting")
                    raise Exception(f"Claude API rate limit exceeded after {max_retries} attempts. Please wait before trying again or upgrade your Anthropic plan. Original error: {e}")
            
            # Check if it's a different type of error
            elif "400" in error_message or "invalid_request_error" in error_message:
                print("❌ Invalid request - not retrying")
                raise Exception(f"Claude API invalid request error: {e}")
            
            elif "401" in error_message or "authentication_error" in error_message:
                print("❌ Authentication failed - check your API key")
                raise Exception(f"Claude API authentication error: {e}")
            
            elif "500" in error_message or "internal_server_error" in error_message:
                if attempt < max_retries - 1:
                    # Brief wait for server errors
                    delay = 1 + random.uniform(0, 1)
                    print(f"⏱️  Server error. Waiting {delay:.1f} seconds before retry...")
                    time.sleep(delay)
                    continue
                else:
                    print("❌ Server error - maximum retries exceeded")
                    raise Exception(f"Claude API server error after {max_retries} attempts: {e}")
            
            else:
                # Unknown error - don't retry
                print("❌ Unknown error - not retrying")
                raise Exception(f"Claude API call failed: {e}")
    
    # This should never be reached, but just in case
    raise Exception(f"Claude API call failed after {max_retries} attempts")


def test_claude_api_with_retry(api_key, model="claude-3-haiku-20240307", max_tokens=10):
    """
    Test function to verify Claude API connectivity with retry logic.
    
    Args:
        api_key: Anthropic API key
        model: Model to test with (defaults to Haiku for cost efficiency)
        max_tokens: Maximum tokens for test response
    
    Returns:
        True if successful, False otherwise
    """
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        response = call_claude_api_with_retry(
            client=client,
            model=model,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=max_tokens,
            max_retries=3  # Fewer retries for testing
        )
        
        print(f"✅ Test API call successful - Response: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Test API call failed: {e}")
        return False


if __name__ == "__main__":
    # Test the utility if run directly
    import os
    
    api_key = os.environ.get('CLAUDE_API_KEY', '')
    if not api_key:
        print("❌ CLAUDE_API_KEY not set")
        exit(1)
    
    print("🧪 Testing Claude API utilities...")
    success = test_claude_api_with_retry(api_key)
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
