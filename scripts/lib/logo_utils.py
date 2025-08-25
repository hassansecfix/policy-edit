"""
Logo Processing Utilities

This module handles logo extraction, processing, and metadata management:
- Base64 logo data extraction from questionnaire responses
- Logo file creation and management
- Metadata injection into JSON files
"""

import os
import json
import base64
from typing import Dict, Any, Optional, Tuple


def extract_logo_from_questionnaire_data(json_data: Dict[str, Any], user_id: str) -> Tuple[Optional[str], bool]:
    """
    Extract and create logo file from questionnaire JSON data.
    
    Args:
        json_data: Questionnaire JSON data containing potential logo
        user_id: User ID for file naming
        
    Returns:
        Tuple of (logo_path: Optional[str], success: bool)
    """
    try:
        print(f"🔍 DEBUG: JSON data keys: {list(json_data.keys())}")
        
        # Look for base64 logo data in JSON (check both possible keys)
        logo_data = json_data.get('_logo_base64_data', {})
        if not logo_data:
            # Fallback: check the original form field name
            original_logo_data = json_data.get('onboarding.company_logo', {})
            if isinstance(original_logo_data, dict) and 'value' in original_logo_data:
                # Extract the file upload data
                file_data = original_logo_data['value']
                if isinstance(file_data, dict) and 'data' in file_data:
                    # Convert to the expected format
                    logo_data = {
                        'questionNumber': 99,
                        'field': '_logo_base64_data', 
                        'value': file_data['data']  # This should be the base64 data URL
                    }
                    print(f"🔍 DEBUG: Converted onboarding.company_logo to _logo_base64_data format")
                else:
                    print(f"🔍 DEBUG: onboarding.company_logo data structure unexpected: {type(file_data)}")
            else:
                print(f"🔍 DEBUG: onboarding.company_logo not found or invalid structure")
        
        print(f"🔍 DEBUG: Logo data found: {bool(logo_data)}")
        if logo_data:
            print(f"🔍 DEBUG: Logo data type: {type(logo_data)}")
            print(f"🔍 DEBUG: Logo data keys: {logo_data.keys() if isinstance(logo_data, dict) else 'Not a dict'}")
        
        if isinstance(logo_data, dict) and 'value' in logo_data:
            return _process_logo_value(logo_data['value'], user_id)
        
        return None, False
        
    except Exception as e:
        print(f"⚠️  Could not extract logo from questionnaire data: {e}")
        import traceback
        print(f"🔍 DEBUG: Full error trace: {traceback.format_exc()}")
        return None, False


def _process_logo_value(base64_value: Any, user_id: str) -> Tuple[Optional[str], bool]:
    """Process the logo value and create logo file."""
    print(f"🔍 DEBUG: base64_value type: {type(base64_value)}")
    print(f"🔍 DEBUG: base64_value preview: {str(base64_value)[:100]}...")
    
    # Check if it's a dict with 'data' field (file upload format)
    if isinstance(base64_value, dict) and 'data' in base64_value:
        base64_value = base64_value['data']
        print(f"🔍 DEBUG: Extracted data field from nested dict")
    
    # Check if the data was filtered out
    if isinstance(base64_value, str) and 'BASE64_DATA_REMOVED_FOR_API_EFFICIENCY' in base64_value:
        print(f"❌ ERROR: Base64 data was filtered out! The environment variable contains filtered data.")
        print(f"🔍 DEBUG: This means the filtering happened before the environment variable was set.")
        return None, False
    
    elif isinstance(base64_value, str) and 'base64,' in base64_value:
        # Extract base64 data
        base64_data = base64_value.split('base64,')[1]
        
        # Create user-specific logo file from base64 data
        try:
            logo_buffer = base64.b64decode(base64_data)
            # Use the same directory as JSON files (which works in production)
            logo_path = f"edits/{user_id}_company_logo.png"
            os.makedirs("edits", exist_ok=True)
            
            with open(logo_path, 'wb') as logo_file:
                logo_file.write(logo_buffer)
            
            print(f"🖼️  Created user-specific logo: {logo_path} ({len(logo_buffer)} bytes)")
            print(f"✅ Logo will be processed by existing PNG logic!")
            return logo_path, True
            
        except Exception as e:
            print(f"❌ Failed to create logo file: {e}")
            return None, False
    
    return None, False


def extract_logo_from_csv(csv_path: str, user_id: str) -> Tuple[Optional[str], bool]:
    """
    Extract logo from CSV file (fallback method).
    
    Args:
        csv_path: Path to CSV file
        user_id: User ID for file naming
        
    Returns:
        Tuple of (logo_path: Optional[str], success: bool)
    """
    if not os.path.exists(csv_path):
        return None, False
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        # Look for base64 data entry (this will be filtered, so likely won't work)
        for line in csv_content.split('\n'):
            if '_logo_base64_data' in line and 'file_upload' in line:
                parts = line.split(';', 4)
                if len(parts) >= 5 and not 'REMOVED_FOR_API_EFFICIENCY' in parts[4]:
                    base64_data = parts[4]
                    # Remove data URL prefix if present
                    if ',' in base64_data:
                        base64_data = base64_data.split(',')[1]
                    
                    # Create user-specific logo file from CSV base64 data
                    try:
                        logo_buffer = base64.b64decode(base64_data)
                        # Use the same directory as JSON files (which works in production)
                        logo_path = f"edits/{user_id}_company_logo.png"
                        os.makedirs("edits", exist_ok=True)
                        
                        with open(logo_path, 'wb') as logo_file:
                            logo_file.write(logo_buffer)
                        
                        print(f"🖼️  Created user-specific logo from CSV: {logo_path} ({len(logo_buffer)} bytes)")
                        print(f"✅ Logo will be processed by existing PNG logic!")
                        return logo_path, True
                        
                    except Exception as e:
                        print(f"❌ Failed to create logo from CSV: {e}")
                        break
        
        # Fallback: check if user provided a file path reference
        for line in csv_content.split('\n'):
            if 'company_logo' in line and 'File upload' in line:
                parts = line.split(';')
                if len(parts) >= 5:
                    file_path = parts[4].strip()
                    if file_path and os.path.exists(file_path):
                        print(f"🖼️  Using logo file from questionnaire: {file_path}")
                        return file_path, True
        
        return None, False
        
    except Exception as e:
        print(f"⚠️  Failed to process logo data from CSV: {e}")
        return None, False


def inject_logo_metadata(edits_json_path: str, logo_path: Optional[str]) -> bool:
    """
    Inject logo metadata into edits JSON file.
    
    Args:
        edits_json_path: Path to edits JSON file
        logo_path: Path to logo file (if any)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(edits_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data.setdefault('metadata', {})
        
        if logo_path:
            data['metadata']['logo_path'] = logo_path
            print("🖼️  Injected logo metadata into edits JSON")
        
        with open(edits_json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        print(f"⚠️  Could not inject logo metadata: {e}")
        return False


def process_logo_operations(edits_json_path: str, user_id: str, 
                          questionnaire_json_data: Optional[str] = None,
                          questionnaire_csv_path: Optional[str] = None) -> Optional[str]:
    """
    Process logo operations and return created logo file path.
    
    Args:
        edits_json_path: Path to edits JSON file
        user_id: User ID for file naming
        questionnaire_json_data: JSON questionnaire data (if available)
        questionnaire_csv_path: CSV questionnaire path (fallback)
        
    Returns:
        Path to created logo file, or None if no logo processed
    """
    try:
        # Check if there are logo operations in the JSON
        with open(edits_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        operations = data.get('instructions', {}).get('operations', [])
        has_logo_operations = any(op.get('action') == 'replace_with_logo' for op in operations)
        
        existing_logo_path = data.get('metadata', {}).get('logo_path')
        logo_file_exists = existing_logo_path and os.path.exists(existing_logo_path)
        
        print(f"🔍 DEBUG: has_logo_operations = {has_logo_operations}")
        print(f"🔍 DEBUG: existing logo_path = {existing_logo_path}")
        print(f"🔍 DEBUG: logo_file_exists = {logo_file_exists}")
        
        if has_logo_operations and not logo_file_exists:
            print("🔍 DEBUG: Logo operations found and logo file missing - attempting to create PNG from base64")
            
            created_logo_path = None
            
            # Try to extract logo from questionnaire data
            if questionnaire_json_data:
                try:
                    json_data = json.loads(questionnaire_json_data)
                    created_logo_path, success = extract_logo_from_questionnaire_data(json_data, user_id)
                    if success:
                        inject_logo_metadata(edits_json_path, created_logo_path)
                        return created_logo_path
                except Exception as e:
                    print(f"⚠️  Could not extract logo from JSON data: {e}")
            
            # Fallback to CSV if available
            if not created_logo_path and questionnaire_csv_path:
                created_logo_path, success = extract_logo_from_csv(questionnaire_csv_path, user_id)
                if success:
                    inject_logo_metadata(edits_json_path, created_logo_path)
                    return created_logo_path
            
            if not created_logo_path:
                print("⚠️  No user logo found - skipping logo operations")
        else:
            if not has_logo_operations:
                print("🔍 DEBUG: No logo operations found in JSON - no logo processing needed")
            if existing_logo_path:
                print(f"🔍 DEBUG: Existing logo path found: {existing_logo_path}")
        
        return None
        
    except Exception as e:
        print(f"⚠️  Failed to process logo operations: {e}")
        return None


def cleanup_logo_file(logo_path: Optional[str], user_id: str) -> None:
    """
    Clean up user-specific logo file if it was created from base64 data.
    
    Args:
        logo_path: Path to logo file to clean up
        user_id: User ID to verify it's a user-specific file
    """
    if logo_path and logo_path.startswith('edits/') and user_id in logo_path:
        try:
            if os.path.exists(logo_path):
                os.unlink(logo_path)
                print(f"🧹 Cleaned up user logo file: {logo_path}")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up logo file: {e}")
