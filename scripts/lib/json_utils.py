"""
JSON Processing Utilities

This module handles JSON operations for the AI policy processor:
- Extracting JSON from Claude API responses
- Validating JSON structure and content
- JSON parsing and formatting
"""

import json
import re
from typing import Dict, Any


def extract_json_from_response(response_text: str) -> str:
    """
    Extract JSON content from Claude's response.
    
    Args:
        response_text: Raw response text from Claude API
        
    Returns:
        Extracted JSON content as string
        
    Raises:
        ValueError: If no valid JSON can be extracted
    """
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
    return _extract_json_by_braces(response_text)


def _extract_json_by_braces(response_text: str) -> str:
    """
    Extract JSON by tracking opening and closing braces.
    
    Args:
        response_text: Raw response text
        
    Returns:
        Extracted JSON content
        
    Raises:
        ValueError: If no valid JSON structure found
    """
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


def validate_json_content(content: str) -> bool:
    """
    Validate the generated JSON has the correct format.
    
    Args:
        content: JSON content as string
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If JSON is invalid or missing required fields
    """
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    
    # Check required structure
    if 'metadata' not in parsed:
        raise ValueError("JSON must have 'metadata' section")
    
    if 'instructions' not in parsed:
        raise ValueError("JSON must have 'instructions' section")
    
    # Validate metadata
    _validate_metadata(parsed['metadata'])
    
    # Validate instructions
    _validate_instructions(parsed['instructions'])
    
    return True


def _validate_metadata(metadata: Dict[str, Any]) -> None:
    """Validate the metadata section of the JSON."""
    required_metadata = ['generated_timestamp', 'company_name', 'format_version', 'total_operations', 'generator']
    for field in required_metadata:
        if field not in metadata:
            raise ValueError(f"Missing required metadata field: {field}")


def _validate_instructions(instructions: Dict[str, Any]) -> None:
    """Validate the instructions section of the JSON."""
    if 'operations' not in instructions:
        raise ValueError("Instructions must have 'operations' array")
    
    operations = instructions['operations']
    if not isinstance(operations, list) or len(operations) == 0:
        raise ValueError("Operations must be a non-empty array")
    
    # Validate each operation
    for i, operation in enumerate(operations):
        _validate_operation(operation, i + 1)


def _validate_operation(operation: Dict[str, Any], operation_number: int) -> None:
    """Validate a single operation in the JSON."""
    # Check required fields
    required_fields = ['target_text', 'action', 'comment', 'comment_author']
    for field in required_fields:
        if field not in operation:
            raise ValueError(f"Operation {operation_number} missing required field: {field}")
    
    # Check action is valid
    valid_actions = ['replace', 'delete', 'comment', 'replace_with_logo']
    if operation['action'] not in valid_actions:
        raise ValueError(f"Operation {operation_number} has invalid action: {operation['action']}")
    
    # Replacement field is optional for 'comment' and 'replace_with_logo' actions, required for others
    if operation['action'] in ['replace', 'delete']:
        if 'replacement' not in operation:
            raise ValueError(f"Operation {operation_number} with action '{operation['action']}' missing required field: replacement")
    
    # Ensure replacement field exists (set to empty string if missing)
    if 'replacement' not in operation:
        operation['replacement'] = ''


def show_json_stats(content: str) -> None:
    """
    Display statistics about the generated JSON.
    
    Args:
        content: JSON content as string
    """
    try:
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
            
    except Exception as e:
        print(f"⚠️ Could not parse JSON stats: {e}")


def format_json_for_output(content: str) -> str:
    """
    Format JSON content for pretty output.
    
    Args:
        content: Raw JSON content
        
    Returns:
        Formatted JSON string
    """
    try:
        parsed = json.loads(content)
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        return content  # Return as-is if parsing fails
