"""
Configuration constants and utility functions for the Policy Automation Web UI.

This module contains:
- Application configuration constants
- File paths and naming conventions
- GitHub API configuration
- Utility functions used across the application
"""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict


# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================

# Flask application settings
APP_SECRET_KEY = 'policy-automation-secret-key-2024'
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 5001

# File paths and naming conventions
DEFAULT_POLICY_FILE = 'data/v5 Freya POL-11 Access Control.docx'
DEFAULT_OUTPUT_NAME = 'policy_tracked_changes_with_comments'

# GitHub API configuration
GITHUB_API_BASE = 'https://api.github.com'
GITHUB_API_TIMEOUT = 10
WORKFLOW_FILENAME = 'redline-docx.yml'

# Automation configuration
MAX_ENV_SIZE = 32 * 1024  # 32KB conservative limit for environment variables
WORKFLOW_MONITORING_DELAY = 5  # seconds between workflow checks
WORKFLOW_MONITORING_RETRIES = 6  # maximum retries for finding new workflows

# Log level indicators
LOG_LEVELS = {
    'ERROR': ['❌', 'Error:', 'failed'],
    'SUCCESS': ['✅', 'SUCCESS', 'completed'],
    'WARNING': ['⚠️', 'Warning:', '💰'],
    'INFO': []  # default level
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_project_root() -> Path:
    """Get the project root directory (parent of web_ui)."""
    return Path(__file__).parent.parent


def setup_cors_headers(response):
    """Add CORS headers to a Flask response."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response


def get_log_level(message: str) -> str:
    """Determine log level based on message content."""
    for level, indicators in LOG_LEVELS.items():
        if any(indicator in message for indicator in indicators):
            return level.lower()
    return 'info'


def get_environment_debug_info() -> Dict[str, str]:
    """Get debug information about environment variables."""
    return {
        'CLAUDE_API_KEY': '***PRESENT***' if os.environ.get('CLAUDE_API_KEY') else 'NOT SET',
        'GITHUB_REPO_OWNER': os.environ.get('GITHUB_REPO_OWNER', 'NOT SET'),
        'GITHUB_REPO_NAME': os.environ.get('GITHUB_REPO_NAME', 'NOT SET'),
        'GIT_USER_NAME': os.environ.get('GIT_USER_NAME', 'NOT SET'),
        'GIT_USER_EMAIL': os.environ.get('GIT_USER_EMAIL', 'NOT SET'),
        'GITHUB_TOKEN': '***PRESENT***' if os.environ.get('GITHUB_TOKEN') else 'NOT SET'
    }


def is_recent_workflow(created_at: str, max_age_minutes: int = 2) -> bool:
    """Check if a workflow was created recently."""
    try:
        created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        age = now - created_time
        return age <= timedelta(minutes=max_age_minutes)
    except Exception:
        return False
