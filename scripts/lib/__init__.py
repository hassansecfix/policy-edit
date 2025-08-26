"""
Shared utilities library for policy automation scripts.

This package provides common functionality used across multiple automation scripts:
- highlighting_cleanup: DOCX highlighting removal and cleanup utilities
- content_loader: File content loading and filtering for API efficiency
- claude_api: Claude AI API integration and response handling
- json_utils: JSON extraction, validation, and processing
- git_utils: Git operations and repository management
- github_utils: GitHub Actions workflow triggering
- logo_utils: Logo processing and metadata management
- shell_executor: Command execution utilities
"""

# Version information
__version__ = "1.0.0"
__author__ = "Policy Automation Team"

# Import commonly used functions for easier access
from .highlighting_cleanup import clean_docx_highlighting, extract_docx_content
from .content_loader import load_file_content, filter_base64_from_csv  
from .claude_api import call_claude_api
from .json_utils import extract_json_from_response, validate_json_content
from .git_utils import commit_and_push_files, GitManager
from .github_utils import GitHubActionsManager, create_workflow_params, clean_policy_for_github, cleanup_temp_files
from .logo_utils import process_logo_operations, inject_logo_metadata, cleanup_logo_file
from .shell_executor import run_command, generate_user_id, validate_api_key, setup_file_paths, show_startup_info, convert_xlsx_to_csv, generate_edits_with_ai

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