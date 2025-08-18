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
from pathlib import Path
import anthropic
import json

# Suppress deprecation warnings for the Claude API
warnings.filterwarnings("ignore", category=DeprecationWarning)

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
    import json
    
    # Look for JSON blocks in the response
    json_patterns = [
        r'```json\n(.*?)\n```',
        r'```\n(\{.*?\})\n```',
        r'(\{[\s\S]*?"instructions"[\s\S]*?\})'
    ]
    
    for pattern in json_patterns:
        match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
        if match:
            json_content = match.group(1).strip()
            try:
                # Validate it's proper JSON
                parsed = json.loads(json_content)
                if 'metadata' in parsed and 'instructions' in parsed:
                    return json_content
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
                json_content = '\n'.join(lines[json_start:i+1])
                try:
                    parsed = json.loads(json_content)
                    if 'metadata' in parsed and 'instructions' in parsed:
                        return json_content
                except json.JSONDecodeError:
                    pass
                json_start = -1
                brace_count = 0
    
    raise ValueError("Could not extract valid JSON from Claude's response")

def validate_json_content(json_content):
    """Validate the generated JSON has the correct format."""
    import json
    
    try:
        parsed = json.loads(json_content)
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

def call_claude_api(prompt_content, questionnaire_content, policy_instructions_content, policy_content, api_key):
    """Call Claude Sonnet 4 API to generate JSON instructions."""
    
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

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Claude Sonnet model
            max_tokens=4000,
            temperature=0.1,  # Low temperature for consistent, accurate output
            messages=[{
                "role": "user",
                "content": full_prompt
            }]
        )
        
        return message.content[0].text
    
    except Exception as e:
        raise Exception(f"Claude API call failed: {e}")

def main():
    parser = argparse.ArgumentParser(description='AI Policy Processor - Generate JSON instructions with Claude Sonnet 4')
    parser.add_argument('--policy', required=True, help='Path to policy DOCX file')
    parser.add_argument('--questionnaire', required=True, help='Path to questionnaire CSV file')
    parser.add_argument('--prompt', required=True, help='Path to AI prompt markdown file (prompt.md)')
    parser.add_argument('--policy-instructions', required=True, help='Path to policy processing instructions (updated_policy_instructions_v4.0.md)')
    parser.add_argument('--output', required=True, help='Output path for generated JSON file')
    parser.add_argument('--api-key', help='Claude API key (or set CLAUDE_API_KEY env var)')
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.environ.get('CLAUDE_API_KEY')
    if not api_key:
        print("❌ Error: Claude API key required!")
        print("   Set CLAUDE_API_KEY environment variable or use --api-key")
        print("   Get your key from: https://console.anthropic.com/")
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
        json_content = extract_json_from_response(response)
        
        # Validate JSON
        print("✅ Validating JSON format...")
        validate_json_content(json_content)
        
        # Save output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_content)
        
        print(f"\n🎉 SUCCESS! Generated JSON instructions:")
        print(f"📁 Saved to: {output_path}")
        
        # Show JSON stats
        import json
        parsed = json.loads(json_content)
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
