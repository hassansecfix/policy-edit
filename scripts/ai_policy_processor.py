#!/usr/bin/env python3
"""
AI Policy Processor - Automated CSV Generation with Claude Sonnet 4

This script takes a policy DOCX file, questionnaire CSV, and AI prompt,
then uses Claude Sonnet 4 to generate the perfect edits CSV file.

Usage:
    python3 ai_policy_processor.py \
        --policy data/policy.docx \
        --questionnaire data/questionnaire.csv \
        --prompt data/updated_policy_instructions_v4.0.md \
        --output edits/ai_generated_edits.csv \
        --api-key YOUR_CLAUDE_API_KEY

Environment Variables:
    CLAUDE_API_KEY: Your Anthropic Claude API key
"""

import os
import sys
import argparse
import csv
import re
import warnings
import time
import random
from pathlib import Path
import json

# Import anthropic only when needed (not when skipping API)
anthropic = None

# Suppress deprecation warnings for the Claude API
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Rate limiting globals
_last_api_call_time = None
_min_time_between_calls = 2.0  # Minimum 2 seconds between API calls

def load_file_content(file_path):
    """Load content from various file types."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if file_path.suffix.lower() == '.csv':
        # Read CSV as formatted text
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    elif file_path.suffix.lower() == '.md':
        # Read markdown
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    elif file_path.suffix.lower() == '.docx':
        try:
            import docx
            doc = docx.Document(file_path)
            content = []
            for paragraph in doc.paragraphs:
                content.append(paragraph.text)
            return '\n'.join(content)
        except ImportError:
            return f"[DOCX FILE: {file_path.name} - Install python-docx to read content]"
    
    else:
        # Default text reading
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

def extract_json_from_response(response_text):
    """Extract JSON content from Claude's response."""
    
    # Look for JSON blocks in the response
    json_patterns = [
        r'```json\n(.*?)\n```',
        r'```\n(\{.*?\})\n```',
        r'(\{[\s\S]*?"instructions"[\s\S]*?\})'
    ]
    
    for pattern in json_patterns:
        match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            try:
                # Validate it's proper JSON
                parsed = json.loads(content)
                if 'metadata' in parsed and 'instructions' in parsed:
                    return content
            except json.JSONDecodeError:
                continue
    
    # Fallback: look for JSON structure starting with {
    lines = response_text.split('\n')
    json_start = -1
    brace_count = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('{') and json_start == -1:
            json_start = i
            brace_count += stripped.count('{') - stripped.count('}')
        elif json_start >= 0:
            brace_count += stripped.count('{') - stripped.count('}')
            if brace_count == 0:
                # Found complete JSON
                content = '\n'.join(lines[json_start:i+1])
                try:
                    parsed = json.loads(content)
                    if 'metadata' in parsed and 'instructions' in parsed:
                        return content
                except json.JSONDecodeError:
                    pass
                json_start = -1
                brace_count = 0
    
    raise ValueError("Could not extract valid JSON from Claude's response")

def validate_json_content(content):
    """Validate the generated JSON has the correct format."""
    
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    
    # Check required structure
    if 'metadata' not in parsed:
        raise ValueError("JSON must have 'metadata' section")
    
    if 'instructions' not in parsed:
        raise ValueError("JSON must have 'instructions' section")
    
    metadata = parsed['metadata']
    required_metadata = ['generated_timestamp', 'company_name', 'format_version', 'total_operations', 'generator']
    for field in required_metadata:
        if field not in metadata:
            raise ValueError(f"Missing required metadata field: {field}")
    
    # Check instructions structure
    instructions = parsed['instructions']
    if 'operations' not in instructions:
        raise ValueError("Instructions must have 'operations' array")
    
    operations = instructions['operations']
    if not isinstance(operations, list) or len(operations) == 0:
        raise ValueError("Operations must be a non-empty array")
    
    # Validate each operation
    for i, operation in enumerate(operations):
        # Check required fields
        required_fields = ['target_text', 'action', 'comment', 'comment_author']
        for field in required_fields:
            if field not in operation:
                raise ValueError(f"Operation {i+1} missing required field: {field}")
        
        # Check action is valid
        if operation['action'] not in ['replace', 'delete', 'comment', 'replace_with_logo']:
            raise ValueError(f"Operation {i+1} has invalid action: {operation['action']}")
        
        # Replacement field is optional for 'comment' and 'replace_with_logo' actions, required for others
        if operation['action'] in ['replace', 'delete']:
            if 'replacement' not in operation:
                raise ValueError(f"Operation {i+1} with action '{operation['action']}' missing required field: replacement")
        
        # Ensure replacement field exists (set to empty string if missing)
        if 'replacement' not in operation:
            operation['replacement'] = ''
    
    return True

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

def call_claude_api(prompt_content, questionnaire_content, policy_instructions_content, policy_content, api_key, max_retries=5):
    """Call Claude Sonnet 4 API to generate JSON instructions with rate limiting and retry logic."""
    
    # Import anthropic here when actually needed
    global anthropic
    if anthropic is None:
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package is required for API calls. Install it with: pip install anthropic")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # Construct the full prompt with the new JSON workflow
    full_prompt = f"""
{prompt_content}

---

## PROCESSING INSTRUCTIONS (Policy Document Specific Rules):
{policy_instructions_content}

---

## INPUT DATA FOR PROCESSING

### QUESTIONNAIRE RESPONSES (CSV FORMAT):
```csv
{questionnaire_content}
```

### POLICY DOCUMENT CONTENT (FOR REFERENCE):
```
{policy_content[:2000]}...
[Document truncated for API efficiency - full content will be processed by automation system]
```

---

Please analyze the questionnaire data and generate the complete JSON file for automated policy customization according to the processing instructions above.

CRITICAL: Your response must include a properly formatted JSON structure that follows the exact format specified in the processing instructions.
"""

    # Retry logic with exponential backoff for rate limiting
    for attempt in range(max_retries):
        try:
            print(f"🔄 API attempt {attempt + 1}/{max_retries}...")
            
            # Enforce rate limiting before each API call
            enforce_rate_limit()
            
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Claude Sonnet model
                max_tokens=4000,
                temperature=0.1,  # Low temperature for consistent, accurate output
                messages=[{
                    "role": "user",
                    "content": full_prompt
                }]
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

def main():
    parser = argparse.ArgumentParser(description='AI Policy Processor - Generate JSON instructions with Claude Sonnet 4')
    parser.add_argument('--policy', required=True, help='Path to policy DOCX file')
    parser.add_argument('--questionnaire', required=True, help='Path to questionnaire CSV file')
    parser.add_argument('--prompt', required=True, help='Path to AI prompt markdown file (prompt.md)')
    parser.add_argument('--policy-instructions', required=True, help='Path to policy processing instructions (updated_policy_instructions_v4.0.md)')
    parser.add_argument('--output', required=True, help='Output path for generated JSON file')
    parser.add_argument('--api-key', help='Claude API key (or set CLAUDE_API_KEY env var)')
    parser.add_argument('--skip-api', action='store_true', help='Skip API call and use existing JSON file (for testing/development)')
    
    args = parser.parse_args()
    
    # Check for skip API configuration
    skip_api_env = os.environ.get('SKIP_API_CALL', '').lower()
    skip_api = args.skip_api or skip_api_env in ['true', '1', 'yes', 'on']
    
    if skip_api:
        # Check if output file already exists
        if not Path(args.output).exists():
            print("❌ Error: --skip-api specified but output JSON file doesn't exist!")
            print(f"   Expected file: {args.output}")
            print("   Either run without --skip-api first, or provide an existing JSON file")
            sys.exit(1)
        
        print("🔄 SKIP_API_CALL enabled - Using existing JSON file for testing/development")
        print(f"📁 Using existing file: {args.output}")
        
        # Validate the existing JSON file
        try:
            with open(args.output, 'r', encoding='utf-8') as f:
                content = f.read()
            validate_json_content(content)
            
            # Show stats from existing file
            parsed = json.loads(content)
            operations_count = len(parsed['instructions']['operations'])
            company_name = parsed['metadata']['company_name']
            
            print(f"✅ Using existing JSON: {operations_count} operations for {company_name}")
            
            # Show operation types summary
            actions = {}
            for op in parsed['instructions']['operations']:
                action = op['action']
                actions[action] = actions.get(action, 0) + 1
            
            print("\n📋 Operations Summary (from existing file):")
            for action, count in actions.items():
                print(f"   {action}: {count} operations")
            
            print(f"\n💰 API call skipped - cost savings for testing/development!")
            return
            
        except Exception as e:
            print(f"❌ Error validating existing JSON file: {e}")
            sys.exit(1)
    
    # Get API key (only if not skipping API)
    api_key = args.api_key or os.environ.get('CLAUDE_API_KEY')
    if not api_key:
        print("❌ Error: Claude API key required!")
        print("   Set CLAUDE_API_KEY environment variable or use --api-key")
        print("   Get your key from: https://console.anthropic.com/")
        print("   Or use --skip-api to use existing JSON file for testing")
        sys.exit(1)
    
    print("🤖 AI Policy Processor Starting (JSON Mode)...")
    print(f"📋 Policy: {args.policy}")
    print(f"📊 Questionnaire: {args.questionnaire}")
    print(f"📝 Main Prompt: {args.prompt}")
    print(f"📜 Policy Instructions: {args.policy_instructions}")
    print(f"💾 Output: {args.output}")
    
    try:
        # Load input files
        print("\n📂 Loading input files...")
        policy_content = load_file_content(args.policy)
        questionnaire_content = load_file_content(args.questionnaire)
        prompt_content = load_file_content(args.prompt)
        policy_instructions_content = load_file_content(args.policy_instructions)
        
        print(f"✅ Policy loaded: {len(policy_content)} characters")
        print(f"✅ Questionnaire loaded: {questionnaire_content.count('Question')} questions detected")
        print(f"✅ Main prompt loaded: {len(prompt_content)} characters")
        print(f"✅ Policy instructions loaded: {len(policy_instructions_content)} characters")
        
        # Call Claude API
        print("\n🧠 Calling Claude Sonnet 4 API...")
        response = call_claude_api(prompt_content, questionnaire_content, policy_instructions_content, policy_content, api_key)
        
        print("✅ AI response received")
        
        # Extract JSON from response
        print("\n🔍 Extracting JSON from AI response...")
        content = extract_json_from_response(response)
        
        # Validate JSON
        print("✅ Validating JSON format...")
        validate_json_content(content)
        
        # Save output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n🎉 SUCCESS! Generated JSON instructions:")
        print(f"📁 Saved to: {output_path}")
        
        # Show JSON stats
        parsed = json.loads(content)
        operations_count = len(parsed['instructions']['operations'])
        company_name = parsed['metadata']['company_name']
        
        print(f"📊 JSON Stats: {operations_count} operations for {company_name}")
        
        # Show operation types summary
        actions = {}
        for op in parsed['instructions']['operations']:
            action = op['action']
            actions[action] = actions.get(action, 0) + 1
        
        print("\n📋 Operations Summary:")
        for action, count in actions.items():
            print(f"   {action}: {count} operations")
        
        print(f"\n🚀 Next Step: Use this JSON with the tracked changes system!")
        print(f"   JSON → CSV Converter → GitHub Actions → Tracked Changes DOCX")
        
    except FileNotFoundError as e:
        print(f"❌ File Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
