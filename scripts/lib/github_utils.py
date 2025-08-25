"""
GitHub Actions and API Utilities

This module handles GitHub Actions workflow triggering and file verification:
- Workflow dispatching with parameters
- File verification on GitHub
- Artifact handling and download management
- Repository validation and URL handling
"""

import os
import time
import requests
import subprocess
from typing import Dict, Any, Optional, Tuple


class GitHubActionsManager:
    """
    Manages GitHub Actions workflows and file operations.
    
    Handles workflow triggering, file verification, and artifact management.
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize with GitHub token."""
        self.github_token = github_token or os.environ.get('GITHUB_TOKEN')
        self.repo_owner: Optional[str] = None
        self.repo_name: Optional[str] = None
        self._extract_repo_info()
    
    def _extract_repo_info(self) -> None:
        """Extract repository information from environment or git."""
        # First try environment variables (for production deployment)
        self.repo_owner = os.environ.get('GITHUB_REPO_OWNER')
        self.repo_name = os.environ.get('GITHUB_REPO_NAME')
        
        # If environment variables are not set, try git (for local development)
        if not self.repo_owner or not self.repo_name:
            self._extract_repo_from_git()
    
    def _extract_repo_from_git(self) -> None:
        """Extract repository information from git remote URL."""
        try:
            if not os.path.exists('.git'):
                return
                
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                return
            
            repo_url = result.stdout.strip()
            # Extract owner/repo from URL
            if 'github.com' in repo_url:
                if repo_url.endswith('.git'):
                    repo_url = repo_url[:-4]
                parts = repo_url.split('/')
                self.repo_owner = parts[-2]
                self.repo_name = parts[-1]
                print(f"✅ Repository info from git: {self.repo_owner}/{self.repo_name}")
        except Exception:
            pass
    
    def verify_file_on_github(self, file_path: str, max_retries: int = 6, delay: int = 5) -> bool:
        """
        Verify a file exists on GitHub with retries.
        
        Args:
            file_path: Path to file on GitHub
            max_retries: Maximum number of retry attempts
            delay: Delay between retries in seconds
            
        Returns:
            True if file exists, False otherwise
        """
        if not self.github_token or not self.repo_owner or not self.repo_name:
            print("❌ GitHub credentials not configured")
            return False
        
        print(f"🔍 Checking file on GitHub: {file_path}")
        api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}"
        print(f"   API URL: {api_url}")
        
        for attempt in range(max_retries):
            try:
                headers = {
                    'Authorization': f'token {self.github_token}',
                    'Accept': 'application/vnd.github.v3+json'
                }
                
                response = requests.get(api_url, headers=headers, timeout=10)
                print(f"   Attempt {attempt + 1}: Status {response.status_code}")
                
                if response.status_code == 200:
                    print(f"✅ File verified on GitHub: {file_path}")
                    # Show file info
                    try:
                        file_info = response.json()
                        print(f"   File size: {file_info.get('size', 'unknown')} bytes")
                        print(f"   SHA: {file_info.get('sha', 'unknown')[:8]}...")
                    except:
                        pass
                    return True
                elif response.status_code == 404:
                    print(f"⏳ File not found (404) on attempt {attempt + 1}/{max_retries}")
                    if attempt == 0:
                        # On first failure, check what files ARE available in the directory
                        self._debug_directory_contents(file_path)
                    
                    if attempt < max_retries - 1:
                        print(f"   Waiting {delay} seconds before retry...")
                        time.sleep(delay)
                elif response.status_code == 401:
                    print(f"❌ Authentication failed (401) - check GITHUB_TOKEN")
                    return False
                elif response.status_code == 403:
                    print(f"❌ Access forbidden (403) - check repository permissions")
                    return False
                else:
                    print(f"⚠️  Unexpected response {response.status_code}: {response.text[:200]}")
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                    
            except requests.exceptions.Timeout:
                print(f"⚠️  Request timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
            except Exception as e:
                print(f"⚠️  Error checking file {file_path} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                
        return False
    
    def _debug_directory_contents(self, file_path: str) -> None:
        """Debug what files are available in the directory."""
        try:
            dir_path = '/'.join(file_path.split('/')[:-1]) if '/' in file_path else ''
            if dir_path:
                dir_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/{dir_path}"
                headers = {
                    'Authorization': f'token {self.github_token}',
                    'Accept': 'application/vnd.github.v3+json'
                }
                dir_response = requests.get(dir_url, headers=headers, timeout=10)
                if dir_response.status_code == 200:
                    files = dir_response.json()
                    available_files = [f['name'] for f in files if isinstance(f, dict)]
                    print(f"   📁 Available files in {dir_path}/: {available_files}")
                else:
                    print(f"   📁 Could not list directory {dir_path} (status {dir_response.status_code})")
        except Exception as e:
            print(f"   📁 Error listing directory: {e}")
    
    def trigger_workflow(self, workflow_params: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Trigger GitHub Actions workflow.
        
        Args:
            workflow_params: Dictionary with workflow parameters including:
                - input_docx: Path to input DOCX file
                - edits_csv: Path to edits JSON file
                - output_docx: Path for output file
                
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.github_token:
            return self._provide_manual_instructions(workflow_params)
        
        if not self.repo_owner or not self.repo_name:
            return False, "Repository information not available"
        
        # Verify files exist on GitHub before triggering workflow
        print("🔍 Verifying files are available on GitHub...")
        files_to_verify = [workflow_params.get('input_docx'), workflow_params.get('edits_csv')]
        
        for file_path in files_to_verify:
            if file_path and not self.verify_file_on_github(file_path):
                return False, f"File verification failed: {file_path}"
        
        print("✅ All files verified on GitHub - proceeding with workflow trigger")
        
        # Additional small delay to ensure GitHub is fully ready
        print("⏳ Final 3-second delay for GitHub processing...")
        time.sleep(3)
        
        # Trigger workflow
        api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/actions/workflows/redline-docx.yml/dispatches"
        
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        data = {
            'ref': 'main',
            'inputs': {
                'input_docx': workflow_params.get('input_docx'),
                'edits_csv': workflow_params.get('edits_csv'),
                'output_docx': workflow_params.get('output_docx')
            }
        }
        
        print(f"🚀 Triggering workflow with parameters:")
        print(f"   - DOCX: {workflow_params.get('input_docx')}")
        print(f"   - JSON: {workflow_params.get('edits_csv')}")
        print(f"   - Output: {workflow_params.get('output_docx')}")
        
        try:
            response = requests.post(api_url, headers=headers, json=data)
            
            if response.status_code == 204:
                print(f"✅ GitHub Actions workflow triggered successfully!")
                print(f"🔗 Check progress: https://github.com/{self.repo_owner}/{self.repo_name}/actions")
                return True, "Workflow triggered"
            else:
                return False, f"GitHub API error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return False, f"GitHub Actions trigger failed: {e}"
    
    def _provide_manual_instructions(self, workflow_params: Dict[str, Any]) -> Tuple[bool, str]:
        """Provide manual workflow trigger instructions."""
        print("\n🔗 GitHub Actions Manual Trigger Required:")
        print("=" * 50)
        print("1. Go to your GitHub repository")
        print("2. Click 'Actions' tab")
        print("3. Find 'Redline DOCX (LibreOffice headless)' workflow")
        print("4. Click 'Run workflow'")
        print("5. Fill in these values:")
        print(f"   - Input DOCX path: {workflow_params.get('input_docx')}")
        print(f"   - Edits CSV/JSON path: {workflow_params.get('edits_csv')}")
        print(f"   - Output DOCX path: {workflow_params.get('output_docx')}")
        print("6. Click 'Run workflow' button")
        print("7. Wait for completion and download from Artifacts")
        print("=" * 50)
        return True, "Manual trigger instructions provided"


def create_workflow_params(input_docx: str, edits_json: str, output_name: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create workflow parameters for GitHub Actions.
    
    Args:
        input_docx: Path to input DOCX file
        edits_json: Path to edits JSON file
        output_name: Base name for output
        user_id: Optional user ID for output isolation
        
    Returns:
        Dictionary of workflow parameters
    """
    # Use user_id for output isolation, fallback to timestamp if not provided
    output_prefix = user_id if user_id else f"run-{int(time.time())}"
    
    return {
        'input_docx': input_docx,
        'edits_csv': edits_json,
        'output_docx': f'build/{output_prefix}_{output_name}.docx'
    }


def clean_policy_for_github(policy_path: str) -> Tuple[str, bool]:
    """
    Create a clean copy of the policy file for GitHub Actions.
    
    Args:
        policy_path: Path to original policy file
        
    Returns:
        Tuple of (cleaned_path: str, success: bool)
    """
    cleaned_policy_path = policy_path.replace('.docx', '_cleaned_for_github.docx')
    
    try:
        import shutil
        # Create clean copy for GitHub Actions
        shutil.copy2(policy_path, cleaned_policy_path)
        print(f"📄 Creating clean policy copy for GitHub Actions: {cleaned_policy_path}")
        
        # Remove highlighting from the GitHub Actions copy
        try:
            # Import from our lib directory
            import sys
            from pathlib import Path
            lib_path = str(Path(__file__).parent)
            if lib_path not in sys.path:
                sys.path.append(lib_path)
            
            from docx_utils import clean_docx_highlighting
            success, message = clean_docx_highlighting(cleaned_policy_path)
            
            if success:
                print(f"✅ Removed highlighting from GitHub Actions copy: {message}")
                return cleaned_policy_path, True
            else:
                print(f"⚠️ Could not clean GitHub Actions copy: {message}")
                print("⚠️ GitHub Actions will use original file (may contain highlighting)")
                return policy_path, False
                
        except Exception as e:
            print(f"⚠️ Error during highlighting cleanup: {e}")
            print("⚠️ GitHub Actions will use original file (may contain highlighting)")
            return policy_path, False
            
    except Exception as e:
        print(f"⚠️ Error creating clean copy for GitHub Actions: {e}")
        print("⚠️ GitHub Actions will use original file (may contain highlighting)")
        return policy_path, False


def cleanup_temp_files(*file_paths: str) -> None:
    """
    Clean up temporary files created during processing.
    
    Args:
        *file_paths: Variable number of file paths to clean up
    """
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
                print(f"🧹 Cleaned up temporary file: {file_path}")
            except Exception as e:
                print(f"⚠️ Could not clean up temporary file {file_path}: {e}")
