"""
Shared utilities library for policy automation scripts.

This package provides common functionality used across multiple automation scripts:
- docx_utils: DOCX document processing and highlighting removal
- file_utils: File content loading and filtering for API efficiency
- claude_api: Claude AI API integration and response handling
- json_utils: JSON extraction, validation, and processing
- git_utils: Git operations and repository management
- github_utils: GitHub Actions workflow triggering
- logo_utils: Logo processing and metadata management
- command_utils: Command execution utilities
"""

# Version information
__version__ = "1.0.0"
__author__ = "Policy Automation Team"

# Import commonly used functions for easier access
from .docx_utils import clean_docx_highlighting, extract_docx_content
from .file_utils import load_file_content, filter_base64_from_csv  
from .claude_api import call_claude_api
from .json_utils import extract_json_from_response, validate_json_content
from .git_utils import commit_and_push_files, GitManager
from .github_utils import GitHubActionsManager, create_workflow_params, clean_policy_for_github, cleanup_temp_files
from .logo_utils import process_logo_operations, inject_logo_metadata, cleanup_logo_file
from .command_utils import run_command, generate_user_id, validate_api_key, setup_file_paths, show_startup_info, convert_xlsx_to_csv, generate_edits_with_ai

# Define what gets imported with "from lib import *"
__all__ = [
    # DOCX utilities
    'clean_docx_highlighting',
    'extract_docx_content', 
    # File utilities
    'load_file_content',
    'filter_base64_from_csv',
    # AI utilities
    'call_claude_api',
    'extract_json_from_response',
    'validate_json_content',
    # Git utilities
    'commit_and_push_files',
    'GitManager',
    # GitHub utilities
    'GitHubActionsManager',
    'create_workflow_params',
    'clean_policy_for_github',
    'cleanup_temp_files',
    # Logo utilities
    'process_logo_operations',
    'inject_logo_metadata',
    'cleanup_logo_file',
    # Command utilities
    'run_command',
    'generate_user_id',
    'validate_api_key',
    'setup_file_paths',
    'show_startup_info',
    'convert_xlsx_to_csv',
    'generate_edits_with_ai'
]