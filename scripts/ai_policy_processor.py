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
from pathlib import Path
import anthropic
import json

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

def extract_csv_from_response(response_text):
    """Extract CSV content from Claude's response."""
    # Look for CSV blocks in the response
    csv_patterns = [
        r'```csv\n(.*?)\n```',
        r'```\n(Find,Replace,.*?)\n```',
        r'## CSV FOR AUTOMATED PROCESSING\n\n```csv\n(.*?)\n```'
    ]
    
    for pattern in csv_patterns:
        match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
        if match:
            csv_content = match.group(1).strip()
            # Validate it starts with proper header
            if csv_content.startswith('Find,Replace'):
                return csv_content
    
    # Fallback: look for any content that starts with "Find,Replace"
    lines = response_text.split('\n')
    csv_start = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('Find,Replace'):
            csv_start = i
            break
    
    if csv_start >= 0:
        # Extract from header until we hit non-CSV content
        csv_lines = [lines[csv_start]]
        for i in range(csv_start + 1, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
            if line.startswith('```') or line.startswith('#') or line.startswith('**'):
                break
            # Simple CSV validation
            if ',' in line and not line.startswith('Find,Replace'):
                csv_lines.append(line)
        
        if len(csv_lines) > 1:  # Header + at least one data row
            return '\n'.join(csv_lines)
    
    raise ValueError("Could not extract valid CSV from Claude's response")

def validate_csv_content(csv_content):
    """Validate the generated CSV has the correct format."""
    lines = csv_content.strip().split('\n')
    
    if len(lines) < 2:
        raise ValueError("CSV must have header + at least one data row")
    
    # Check header
    header = lines[0].strip()
    expected_header = "Find,Replace,MatchCase,WholeWord,Wildcards,Description,Rule"
    if header != expected_header:
        raise ValueError(f"Invalid CSV header. Expected: {expected_header}, Got: {header}")
    
    # Validate each data row
    for i, line in enumerate(lines[1:], 2):
        if not line.strip():
            continue
        
        # Basic CSV validation
        try:
            reader = csv.reader([line])
            row = next(reader)
            if len(row) < 7:
                raise ValueError(f"Row {i} has {len(row)} columns, expected 7")
        except Exception as e:
            raise ValueError(f"Invalid CSV format on line {i}: {e}")
    
    return True

def call_claude_api(prompt_content, questionnaire_content, policy_content, api_key):
    """Call Claude Sonnet 4 API to generate edits CSV."""
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # Construct the full prompt
    full_prompt = f"""
{prompt_content}

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

Please analyze the questionnaire data and generate the complete CSV file for automated policy customization according to the instructions above.

CRITICAL: Your response must include a properly formatted CSV block that can be directly used by the automation system.
"""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Claude Sonnet 4
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
    parser = argparse.ArgumentParser(description='AI Policy Processor - Generate edits CSV with Claude Sonnet 4')
    parser.add_argument('--policy', required=True, help='Path to policy DOCX file')
    parser.add_argument('--questionnaire', required=True, help='Path to questionnaire CSV file')
    parser.add_argument('--prompt', required=True, help='Path to AI prompt markdown file')
    parser.add_argument('--output', required=True, help='Output path for generated CSV file')
    parser.add_argument('--api-key', help='Claude API key (or set CLAUDE_API_KEY env var)')
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.environ.get('CLAUDE_API_KEY')
    if not api_key:
        print("❌ Error: Claude API key required!")
        print("   Set CLAUDE_API_KEY environment variable or use --api-key")
        print("   Get your key from: https://console.anthropic.com/")
        sys.exit(1)
    
    print("🤖 AI Policy Processor Starting...")
    print(f"📋 Policy: {args.policy}")
    print(f"📊 Questionnaire: {args.questionnaire}")
    print(f"📝 Prompt: {args.prompt}")
    print(f"💾 Output: {args.output}")
    
    try:
        # Load input files
        print("\n📂 Loading input files...")
        policy_content = load_file_content(args.policy)
        questionnaire_content = load_file_content(args.questionnaire)
        prompt_content = load_file_content(args.prompt)
        
        print(f"✅ Policy loaded: {len(policy_content)} characters")
        print(f"✅ Questionnaire loaded: {questionnaire_content.count('Question')} questions detected")
        print(f"✅ Prompt loaded: {len(prompt_content)} characters")
        
        # Call Claude API
        print("\n🧠 Calling Claude Sonnet 4 API...")
        response = call_claude_api(prompt_content, questionnaire_content, policy_content, api_key)
        
        print("✅ AI response received")
        
        # Extract CSV from response
        print("\n🔍 Extracting CSV from AI response...")
        csv_content = extract_csv_from_response(response)
        
        # Validate CSV
        print("✅ Validating CSV format...")
        validate_csv_content(csv_content)
        
        # Save output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        print(f"\n🎉 SUCCESS! Generated edits CSV:")
        print(f"📁 Saved to: {output_path}")
        
        # Show CSV stats
        csv_lines = csv_content.strip().split('\n')
        print(f"📊 CSV Stats: {len(csv_lines)-1} edit rules generated")
        
        # Show first few lines as preview
        print("\n📋 CSV Preview:")
        for i, line in enumerate(csv_lines[:4]):
            print(f"   {line}")
        if len(csv_lines) > 4:
            print(f"   ... and {len(csv_lines)-4} more rows")
        
        print(f"\n🚀 Next Step: Use this CSV with the automation system!")
        print(f"   GitHub Actions → 'Redline DOCX' → Input your policy + this CSV")
        
    except FileNotFoundError as e:
        print(f"❌ File Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
