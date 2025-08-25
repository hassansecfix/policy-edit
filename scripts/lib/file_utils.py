"""
File Processing Utilities

This module provides utilities for loading and processing various file types:
- Loading content from DOCX, CSV, JSON, and Markdown files
- Filtering base64 data for API efficiency
- Converting between formats
"""

import json
from pathlib import Path
from typing import Dict, Any

from .docx_utils import extract_docx_content


def filter_base64_from_csv(csv_content: str) -> str:
    """
    Filter out base64 logo data from CSV content to save API tokens.
    
    Args:
        csv_content: Raw CSV content
        
    Returns:
        Filtered CSV content with base64 data replaced by placeholders
    """
    lines = csv_content.split('\n')
    filtered_lines = []
    
    for line in lines:
        # Check if this line contains base64 logo data
        if ';Logo Base64 Data;_logo_base64_data;' in line:
            # Find where the actual base64 data starts (after "data:image/")
            if 'data:image/' in line and 'base64,' in line:
                # Split at base64, and keep everything before it + placeholder
                base64_start = line.find('base64,') + 7  # +7 for "base64,"
                if base64_start > 6:  # Valid base64 start found
                    before_base64 = line[:base64_start]
                    base64_data = line[base64_start:]
                    filtered_line = before_base64 + '[BASE64_DATA_REMOVED_FOR_API_EFFICIENCY]'
                    filtered_lines.append(filtered_line)
                    print(f"🖼️  FILTERED: Removed {len(base64_data):,} chars of base64 logo data to save API tokens!")
                    print(f"💰 API Cost Savings: ~${len(base64_data) * 0.000003:.2f} per request")
                else:
                    filtered_lines.append(line)
            else:
                # Fallback: try the old method with semicolon splitting
                parts = line.split(';', 4)
                if len(parts) >= 5:
                    # Keep the structure but replace data with placeholder
                    filtered_line = ';'.join(parts[:4]) + ';[BASE64_LOGO_DATA_REMOVED_FOR_API_EFFICIENCY]'
                    filtered_lines.append(filtered_line)
                    print(f"🖼️  Filtered out base64 logo data ({len(parts[4])} chars) to save API tokens")
                else:
                    filtered_lines.append(line)
        else:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)


def convert_json_to_csv_format(json_data: Dict[str, Any]) -> str:
    """
    Convert JSON questionnaire answers to CSV-like format for AI processing.
    
    Args:
        json_data: Dictionary of questionnaire answers
        
    Returns:
        CSV-formatted string
    """
    csv_lines = ['Question Number;Question Text;field;Response Type;User Response']
    
    for field, answer_data in json_data.items():
        if isinstance(answer_data, dict):
            question_number = answer_data.get('questionNumber', 0)
            question_text = answer_data.get('questionText', field)
            response_type = answer_data.get('responseType', 'text')
            value = answer_data.get('value', '')
            
            # Handle different value types
            if isinstance(value, dict) and 'data' in value:
                # File upload - use filename or placeholder
                value = value.get('name', 'uploaded_file')
            elif isinstance(value, (list, dict)):
                value = str(value)
            
            csv_line = f"{question_number};{question_text};{field};{response_type};{value}"
            csv_lines.append(csv_line)
    
    return '\n'.join(csv_lines)


def load_file_content(file_path: str) -> str:
    """
    Load content from various file types.
    
    Args:
        file_path: Path to file to load
        
    Returns:
        File content as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: If file can't be read
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Handle DOCX files
    if file_path.suffix.lower() == '.docx':
        return extract_docx_content(str(file_path), filter_highlighted=True)
    
    # Handle JSON files (questionnaire responses)
    elif file_path.suffix.lower() == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        content = convert_json_to_csv_format(json_data)
        print(f"📊 Converted {len(json_data)} JSON answers to CSV format for AI processing")
        return content
    
    # Handle CSV files with base64 filtering
    elif file_path.suffix.lower() == '.csv':
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return filter_base64_from_csv(content)
    
    # Handle Markdown and other text files
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()


def load_questionnaire_from_environment() -> str:
    """
    Load questionnaire data from environment variable and convert to CSV format.
    
    Returns:
        CSV-formatted questionnaire data
        
    Raises:
        ValueError: If environment variable is not set or invalid
    """
    import os
    
    env_data = os.environ.get('QUESTIONNAIRE_ANSWERS_DATA')
    if not env_data:
        raise ValueError("QUESTIONNAIRE_ANSWERS_DATA environment variable not set")
    
    try:
        # Parse and convert JSON to CSV-like format
        json_data = json.loads(env_data)
        csv_lines = ['Question Number;Question Text;field;Response Type;User Response']
        
        for field, answer_data in json_data.items():
            if isinstance(answer_data, dict):
                question_number = answer_data.get('questionNumber', 0)
                question_text = answer_data.get('questionText', field)  # Use field as fallback
                response_type = answer_data.get('responseType', 'text')
                value = answer_data.get('value', '')
                
                # Handle different value types
                if isinstance(value, dict) and 'data' in value:
                    # File upload - use filename or placeholder
                    value = value.get('name', 'uploaded_file')
                elif field == '_logo_base64_data' and isinstance(value, str):
                    # Special case: logo base64 data - set correct metadata for existing filter
                    response_type = 'file_upload'  # Override for logo data
                    question_text = 'Logo Base64 Data'  # Override for logo data
                    # Note: base64 filtering will be applied by existing logic below
                elif isinstance(value, (list, dict)):
                    value = str(value)
                
                csv_line = f"{question_number};{question_text};{field};{response_type};{value}"
                csv_lines.append(csv_line)
        
        # Create CSV content and apply base64 filtering ONLY for API (keep original in env)
        raw_csv_content = '\n'.join(csv_lines)
        questionnaire_content = filter_base64_from_csv(raw_csv_content)
        print(f"📊 Converted {len(json_data)} JSON answers from environment to CSV format")
        print(f"🖼️  Note: Original base64 logo data preserved in environment for automation scripts")
        
        return questionnaire_content
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in environment variable: {e}")
