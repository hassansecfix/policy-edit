"""
Shell Command Execution Utilities

This module provides utilities for running shell commands and subprocess operations:
- Command execution with proper error handling
- Real-time output for specific command types
- Environment setup and validation
- User ID generation for multi-user isolation
"""

import os
import sys
import subprocess
import time
import random
from typing import Tuple, Optional
from pathlib import Path


def run_command(cmd: str, description: str) -> Tuple[bool, str]:
    """
    Run a shell command and handle errors.
    
    Args:
        cmd: Command to execute
        description: Human-readable description of the command
        
    Returns:
        Tuple of (success: bool, output_or_error: str)
    """
    print(f"🔄 {description}...")
    
    # For AI processing commands, show real-time output to see base64 filtering logs
    if 'ai_policy_processor.py' in cmd:
        try:
            # Use real-time output for AI processing to show filtering logs
            result = subprocess.run(cmd, shell=True, text=True)
            if result.returncode != 0:
                print(f"❌ {description} failed with exit code {result.returncode}!")
                print(f"Command was: {cmd}")
                return False, f"Command failed with exit code {result.returncode}"
            print(f"✅ {description} completed")
            return True, ""
        except Exception as e:
            print(f"❌ {description} failed with exception: {e}")
            return False, str(e)
    else:
        # Use captured output for other commands
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ {description} failed!")
            error_msg = result.stderr.strip() if result.stderr.strip() else result.stdout.strip()
            if not error_msg:
                error_msg = f"Command failed with exit code {result.returncode} but no error message"
            print(f"Error: {error_msg}")
            print(f"Command was: {cmd}")
            return False, error_msg
        
        print(f"✅ {description} completed")
        return True, result.stdout


def convert_xlsx_to_csv(xlsx_path: str, csv_path: str) -> Tuple[bool, str]:
    """
    Convert Excel questionnaire to CSV.
    
    Args:
        xlsx_path: Path to input Excel file
        csv_path: Path for output CSV file
        
    Returns:
        Tuple of (success: bool, output_or_error: str)
    """
    cmd = f"python3 scripts/xlsx_to_csv_converter.py '{xlsx_path}' '{csv_path}'"
    return run_command(cmd, "Converting Excel to CSV")


def generate_edits_with_ai(policy_path: str, questionnaire_csv: Optional[str], 
                          prompt_path: str, policy_instructions_path: str, 
                          output_json: str, api_key: str, skip_api: bool = False, 
                          questionnaire_json: Optional[str] = None) -> Tuple[bool, str]:
    """
    Generate JSON instructions using AI or use existing file.
    
    Args:
        policy_path: Path to policy DOCX file
        questionnaire_csv: Path to questionnaire CSV (optional)
        prompt_path: Path to prompt file
        policy_instructions_path: Path to policy instructions
        output_json: Path for output JSON
        api_key: Claude API key
        skip_api: Whether to skip API call
        questionnaire_json: JSON questionnaire data (optional)
        
    Returns:
        Tuple of (success: bool, output_or_error: str)
    """
    temp_json_file = None
    
    try:
        # Determine questionnaire parameter based on input type
        if questionnaire_json:
            # Check if we can use environment variable approach (production-friendly)
            env_data = os.environ.get('QUESTIONNAIRE_ANSWERS_DATA')
            if env_data and len(questionnaire_json) == len(env_data):
                # Use environment variable approach - no temp files needed!
                questionnaire_param = f"--questionnaire-env-data"
                print("🧠 Step 2: Using environment variable questionnaire data (production mode)...")
            else:
                # Fallback to temp file approach 
                import tempfile
                import json
                
                temp_json_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                json.dump(json.loads(questionnaire_json), temp_json_file, indent=2)
                temp_json_file.close()
                
                questionnaire_param = f"--questionnaire '{temp_json_file.name}'"
                print("🧠 Step 2: Using temp file questionnaire data (fallback mode)...")
                print(f"📁 Temp JSON file: {temp_json_file.name}")
        else:
            # Use file path (legacy approach)
            questionnaire_param = f"--questionnaire '{questionnaire_csv}'"
            print("🧠 Step 2: Using questionnaire file (legacy mode)...")
        
        if skip_api:
            print("🔄 API call skipped for testing/development...")
            cmd = f"""python3 scripts/ai_policy_processor.py \
                --policy '{policy_path}' \
                {questionnaire_param} \
                --prompt '{prompt_path}' \
                --policy-instructions '{policy_instructions_path}' \
                --output '{output_json}' \
                --skip-api"""
        else:
            print("🧠 Generating JSON instructions with Claude Sonnet 4...")
            cmd = f"""python3 scripts/ai_policy_processor.py \
                --policy '{policy_path}' \
                {questionnaire_param} \
                --prompt '{prompt_path}' \
                --policy-instructions '{policy_instructions_path}' \
                --output '{output_json}' \
                --api-key '{api_key}'"""
        
        result = run_command(cmd, "Processing JSON instructions")
        
        return result
        
    finally:
        # Clean up temporary file AFTER the command completes
        if temp_json_file and os.path.exists(temp_json_file.name):
            try:
                os.unlink(temp_json_file.name)
                print(f"🗑️  Cleaned up temp file: {temp_json_file.name}")
            except Exception as e:
                print(f"⚠️  Warning: Could not clean up temp file {temp_json_file.name}: {e}")


def generate_user_id(provided_user_id: Optional[str] = None) -> str:
    """
    Generate or validate user ID for multi-user isolation.
    
    Args:
        provided_user_id: User-provided ID (optional)
        
    Returns:
        Valid user ID string
    """
    if provided_user_id:
        print(f"🔑 Using provided user ID: {provided_user_id}")
        return provided_user_id
    
    # Generate unique user ID for multi-user isolation
    timestamp = int(time.time())
    random_suffix = random.randint(1000, 9999)
    user_id = f"user-{timestamp}-{random_suffix}"
    print(f"🔑 Generated user ID: {user_id}")
    return user_id


def validate_api_key(api_key: Optional[str], skip_api: bool = False) -> str:
    """
    Validate and return API key.
    
    Args:
        api_key: Provided API key (optional)
        skip_api: Whether API calls will be skipped
        
    Returns:
        Valid API key string
        
    Raises:
        SystemExit: If API key is required but not provided
    """
    if skip_api:
        return ""
    
    final_api_key = api_key or os.environ.get('CLAUDE_API_KEY')
    if not final_api_key:
        print("❌ Error: Claude API key required!")
        print("   Set CLAUDE_API_KEY environment variable or use --api-key")
        print("   Get your key from: https://console.anthropic.com/")
        print("   Or use --skip-api to use existing JSON file for testing")
        sys.exit(1)
    
    return final_api_key


def setup_file_paths(user_id: str, output_name: str) -> dict:
    """
    Set up file paths for automation with user isolation.
    
    Args:
        user_id: User identifier for file isolation
        output_name: Base name for output files
        
    Returns:
        Dictionary containing file paths
    """
    return {
        'questionnaire_csv': f"data/{user_id}_{output_name}_questionnaire.csv",
        'edits_json': f"edits/{user_id}_{output_name}_edits.json",
        'prompt_path': "data/prompt.md",
        'policy_instructions_path': "data/updated_policy_instructions_v5.0_context_aware.md"
    }


def show_startup_info(policy: str, questionnaire: Optional[str], output_name: str, 
                     user_id: str, questionnaire_env_data: bool = False) -> None:
    """
    Display startup information for the automation process.
    
    Args:
        policy: Path to policy file
        questionnaire: Path to questionnaire file (optional)
        output_name: Output name
        user_id: User ID
        questionnaire_env_data: Whether using environment data
    """
    print("🚀 Complete Policy Automation Starting...")
    print("=" * 50)
    print(f"📋 Policy Document: {policy}")
    
    if questionnaire_env_data:
        print(f"📊 Questionnaire: Environment variable data")
    else:
        print(f"📊 Questionnaire: {questionnaire}")
        
    print(f"📝 Output Name: {output_name}")
    print(f"👤 User ID: {user_id}")
    print(f"🤖 AI: Claude Sonnet 4")
    print(f"⚙️  Automation: GitHub Actions")
    print("=" * 50)
