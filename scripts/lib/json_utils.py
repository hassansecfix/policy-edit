"""
JSON utilities for processing Claude API responses and validation.
"""

import json
import re
from typing import Dict, Any


def extract_json_from_response(response: str) -> str:
    """
    Extract JSON content from Claude's response text.
    
    Args:
        response: Raw response text from Claude API
        
    Returns:
        Clean JSON string
        
    Raises:
        ValueError: If no valid JSON is found
    """
    # Look for JSON block markers
    json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()
    
    # Look for plain JSON starting with {
    json_match = re.search(r'(\{.*\})', response, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()
    
    # If no JSON found, assume the entire response is JSON
    try:
        json.loads(response)
        return response.strip()
    except json.JSONDecodeError:
        raise ValueError("No valid JSON found in response")


def validate_json_content(content: str) -> Dict[str, Any]:
    """
    Validate JSON content structure and format.
    
    Args:
        content: JSON string to validate
        
    Returns:
        Parsed JSON data if valid
        
    Raises:
        ValueError: If JSON is invalid or missing required fields
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    
    # Check required top-level structure
    if not isinstance(data, dict):
        raise ValueError("JSON must be an object at top level")
    
    if 'metadata' not in data:
        raise ValueError("Missing required 'metadata' section")
    
    if 'instructions' not in data:
        raise ValueError("Missing required 'instructions' section")
    
    instructions = data['instructions']
    if not isinstance(instructions, dict):
        raise ValueError("'instructions' must be an object")
    
    if 'operations' not in instructions:
        raise ValueError("Missing required 'operations' array in instructions")
    
    operations = instructions['operations']
    if not isinstance(operations, list):
        raise ValueError("'operations' must be an array")
    
    # Validate each operation
    for i, op in enumerate(operations):
        if not isinstance(op, dict):
            raise ValueError(f"Operation {i} must be an object")
        
        required_fields = ['target_text', 'action', 'replacement', 'comment']
        for field in required_fields:
            if field not in op:
                raise ValueError(f"Operation {i} missing required field '{field}'")
    
    print(f"✅ JSON validation passed - {len(operations)} operations found")
    return data


def show_json_stats(content: str) -> None:
    """
    Display statistics about the JSON content.
    
    Args:
        content: JSON string to analyze
    """
    try:
        data = json.loads(content)
        
        # Basic stats
        operations = data.get('instructions', {}).get('operations', [])
        metadata = data.get('metadata', {})
        
        print(f"\n📊 JSON Statistics:")
        print(f"   Total operations: {len(operations)}")
        print(f"   Company: {metadata.get('company_name', 'Unknown')}")
        print(f"   Format version: {metadata.get('format_version', 'Unknown')}")
        print(f"   Generator: {metadata.get('generator', 'Unknown')}")
        
        # Count action types
        action_counts = {}
        for op in operations:
            action = op.get('action', 'unknown')
            action_counts[action] = action_counts.get(action, 0) + 1
        
        if action_counts:
            print(f"   Action breakdown:")
            for action, count in sorted(action_counts.items()):
                print(f"     - {action}: {count}")
        
        # File size
        size_kb = len(content) / 1024
        print(f"   File size: {size_kb:.1f} KB")
        
    except Exception as e:
        print(f"⚠️  Could not analyze JSON stats: {e}")


def format_json_for_output(content: str) -> str:
    """
    Format JSON content for clean output.
    
    Args:
        content: JSON string to format
        
    Returns:
        Formatted JSON string
    """
    try:
        data = json.loads(content)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        return content
