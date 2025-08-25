"""
GitHub Actions monitoring and integration for the Policy Automation Web UI.

This module handles:
- Monitoring GitHub Actions workflow runs in real-time
- Downloading artifacts from completed workflows
- Extracting repository information from git or environment variables
- Making authenticated requests to the GitHub API
"""

import os
import subprocess
import threading
import time
import re
import requests
from typing import List, Optional, Callable, Any, Dict

from config import (
    GITHUB_API_BASE, GITHUB_API_TIMEOUT, WORKFLOW_FILENAME,
    WORKFLOW_MONITORING_DELAY, get_project_root
)
from models import WorkflowRun


class GitHubActionsMonitor:
    """
    Handles monitoring and interaction with GitHub Actions workflows.
    
    This class provides functionality to:
    - Monitor workflow runs in real-time
    - Download artifacts from completed workflows
    - Extract repository information from git or environment variables
    """
    
    def __init__(self):
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.repo_owner: Optional[str] = None
        self.repo_name: Optional[str] = None
        self.workflow_run_id: Optional[int] = None
        self._extract_repo_info()
    
    def _extract_repo_info(self) -> None:
        """Extract GitHub repository info from environment variables or git remote."""
        # First try environment variables (for production deployment)
        self.repo_owner = os.environ.get('GITHUB_REPO_OWNER')
        self.repo_name = os.environ.get('GITHUB_REPO_NAME')
        
        # If environment variables are not set, try git (for local development)
        if not self.repo_owner or not self.repo_name:
            self._extract_repo_from_git()
    
    def _extract_repo_from_git(self) -> None:
        """Extract repository information from git remote URL."""
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                cwd=get_project_root(),
                timeout=5
            )
            
            if result.returncode == 0:
                url = result.stdout.strip()
                if 'github.com' in url:
                    # Parse GitHub URL (both HTTPS and SSH formats)
                    match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', url)
                    if match:
                        self.repo_owner = match.group(1)
                        self.repo_name = match.group(2)
        except Exception:
            # Git command failed or not available - use environment variables only
            pass
    
    def _make_github_request(self, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Make an authenticated request to the GitHub API."""
        if not self.github_token or not self.repo_owner or not self.repo_name:
            return None
        
        url = f"{GITHUB_API_BASE}/repos/{self.repo_owner}/{self.repo_name}/{endpoint}"
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        try:
            return requests.get(url, headers=headers, timeout=GITHUB_API_TIMEOUT, **kwargs)
        except requests.RequestException:
            return None
    
    def get_latest_workflow_runs(self, limit: int = 5) -> List[WorkflowRun]:
        """Get recent workflow runs for the specified workflow."""
        response = self._make_github_request(
            f'actions/workflows/{WORKFLOW_FILENAME}/runs',
            params={'per_page': limit}
        )
        
        if not response or response.status_code != 200:
            return []
        
        runs_data = response.json().get('workflow_runs', [])
        return [
            WorkflowRun(
                id=run['id'],
                status=run['status'],
                conclusion=run['conclusion'],
                created_at=run['created_at'],
                updated_at=run['updated_at'],
                html_url=run['html_url']
            )
            for run in runs_data
        ]
    
    def monitor_workflow(self, run_id: int, callback: Optional[Callable] = None) -> None:
        """Monitor a specific workflow run in a separate thread."""
        self.workflow_run_id = run_id
        thread = threading.Thread(
            target=self._monitor_workflow_thread,
            args=(run_id, callback),
            daemon=True
        )
        thread.start()
    
    def _monitor_workflow_thread(self, run_id: int, callback: Optional[Callable]) -> None:
        """Monitor workflow run in a separate thread."""
        while True:
            try:
                response = self._make_github_request(f'actions/runs/{run_id}')
                
                if response and response.status_code == 200:
                    run_data = response.json()
                    status = run_data['status']
                    
                    if callback:
                        callback(run_data)
                    
                    # Stop monitoring if workflow is complete
                    if status == 'completed':
                        self._check_artifacts(run_id, callback)
                        break
                
                time.sleep(WORKFLOW_MONITORING_DELAY)
                
            except Exception as e:
                print(f"Error monitoring workflow: {e}")
                break
    
    def _check_artifacts(self, run_id: int, callback: Optional[Callable]) -> None:
        """Check for workflow artifacts and notify callback."""
        response = self._make_github_request(f'actions/runs/{run_id}/artifacts')
        
        if response and response.status_code == 200:
            artifacts = response.json().get('artifacts', [])
            if artifacts and callback:
                callback({'artifacts': artifacts})
