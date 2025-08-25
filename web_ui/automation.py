"""
Automation runner for the Policy Automation Web UI.

This module handles:
- Running automation scripts with proper environment setup
- Real-time progress tracking and logging
- File management and cleanup
- Integration with GitHub Actions monitoring
"""

import os
import subprocess
import threading
import time
import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from config import (
    DEFAULT_POLICY_FILE, DEFAULT_OUTPUT_NAME, MAX_ENV_SIZE,
    WORKFLOW_MONITORING_RETRIES, WORKFLOW_MONITORING_DELAY,
    get_project_root, get_log_level, get_environment_debug_info, is_recent_workflow
)
from models import GeneratedFile
from github_monitor import GitHubActionsMonitor


class AutomationRunner:
    """
    Manages the policy automation process.
    
    This class handles:
    - Running automation scripts with proper environment setup
    - Real-time progress tracking and logging
    - File management and cleanup
    - Integration with GitHub Actions monitoring
    """
    
    def __init__(self, socketio_instance):
        self.socketio = socketio_instance
        self.process: Optional[subprocess.Popen] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.github_monitor = GitHubActionsMonitor()
        
        # Progress tracking
        self.steps = [
            "Preparing environment",
            "Processing questionnaire",
            "Generating AI edits",
            "Triggering GitHub Actions",
            "Complete"
        ]
        self.current_step = 0
    
    def emit_log(self, message: str, level: str = "info", step: Optional[int] = None) -> None:
        """Emit a log message to all connected WebSocket clients."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.socketio.emit('log_message', {
            'timestamp': timestamp,
            'message': message,
            'level': level,
            'step': step
        })
    
    def update_progress(self, step: int, status: str = "active") -> None:
        """Update the current progress step and notify clients."""
        self.current_step = step
        progress_percent = (step / len(self.steps)) * 100
        
        self.socketio.emit('progress_update', {
            'step': step,
            'status': status,
            'progress': progress_percent
        })
    
    def _validate_questionnaire_data(self, questionnaire_answers: Dict) -> bool:
        """Validate that questionnaire data is present and valid."""
        if not questionnaire_answers or len(questionnaire_answers) == 0:
            self.emit_log(
                "❌ No questionnaire answers provided from localStorage! "
                "Please complete the questionnaire first.",
                "error"
            )
            self.update_progress(1, "error")
            return False
        
        self.emit_log(
            f"📊 Using direct questionnaire answers ({len(questionnaire_answers)} fields)",
            "success"
        )
        return True
    
    def _validate_policy_file(self) -> Tuple[bool, Optional[Path]]:
        """Validate that the policy file exists."""
        policy_file = os.environ.get('POLICY_FILE', DEFAULT_POLICY_FILE)
        policy_path = get_project_root() / policy_file
        
        if not policy_path.exists():
            self.emit_log(f"❌ Policy file not found: {policy_file}", "error")
            self.update_progress(1, "error")
            return False, None
        
        return True, policy_path
    
    def _prepare_questionnaire_data(self, questionnaire_answers: Dict) -> Tuple[Dict[str, str], Optional[str]]:
        """
        Prepare questionnaire data for automation script.
        
        Returns:
            Tuple of (environment variables, temporary file path)
        """
        env = os.environ.copy()
        temp_file_path = None
        
        try:
            questionnaire_json_str = json.dumps(questionnaire_answers)
            data_size = len(questionnaire_json_str)
            
            if data_size <= MAX_ENV_SIZE:
                # Small data - use environment variable (production-friendly)
                env['QUESTIONNAIRE_ANSWERS_DATA'] = questionnaire_json_str
                env['QUESTIONNAIRE_SOURCE'] = 'direct_api'
                self.emit_log("📊 Using environment variable for questionnaire data", "info")
                self.emit_log(f"📏 Data size: {data_size} characters", "info")
            else:
                # Large data - use temporary file approach
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                temp_file.write(questionnaire_json_str)
                temp_file.close()
                
                temp_file_path = temp_file.name
                env['QUESTIONNAIRE_ANSWERS_JSON'] = temp_file_path
                env['QUESTIONNAIRE_SOURCE'] = 'direct_api'
                
                self.emit_log("📊 Using temporary file for questionnaire data (large size)", "warning")
                self.emit_log(f"📏 Data size: {data_size} characters (>{MAX_ENV_SIZE} limit)", "info")
                self.emit_log(f"📄 Temp file: {temp_file_path}", "info")
            
            return env, temp_file_path
            
        except Exception as e:
            self.emit_log(f"❌ Failed to serialize questionnaire data: {str(e)}", "error")
            raise
    
    def _setup_automation_environment(self, skip_api: bool, user_id: Optional[str], 
                                    questionnaire_answers: Dict) -> Tuple[Dict[str, str], Optional[str]]:
        """Setup environment variables for the automation script."""
        env, temp_file_path = self._prepare_questionnaire_data(questionnaire_answers)
        
        # Configure API skipping
        if skip_api:
            env['SKIP_API_CALL'] = 'true'
            self.emit_log("💰 API call will be skipped (using existing JSON)", "warning")
        
        # Configure user ID for multi-user isolation
        if user_id:
            env['USER_ID'] = user_id
            self.emit_log(f"👤 User ID: {user_id}", "info")
        
        # Log logo data presence for debugging
        has_logo = '_logo_base64_data' in questionnaire_answers
        self.emit_log(f"🔍 DEBUG: Logo data present in questionnaire: {has_logo}", "info")
        
        if has_logo:
            logo_data = questionnaire_answers.get('_logo_base64_data', {})
            logo_value = logo_data.get('value', '')
            has_base64 = 'base64,' in str(logo_value)
            self.emit_log(
                f"🔍 DEBUG: Logo value type: {type(logo_value)}, contains base64: {has_base64}",
                "info"
            )
        
        # Log environment debug info
        debug_info = get_environment_debug_info()
        self.emit_log(f"🔍 Environment variables: {debug_info}", "info")
        
        return env, temp_file_path
    
    def _execute_automation_script(self, env: Dict[str, str]) -> bool:
        """Execute the automation script and handle real-time output."""
        script_path = get_project_root() / "quick_automation.sh"
        
        try:
            self.process = subprocess.Popen(
                [str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                env=env,
                cwd=get_project_root()
            )
            
            # Process output line by line
            while self.running and self.process.poll() is None:
                line = self.process.stdout.readline()
                if line:
                    clean_line = line.strip()
                    if clean_line:
                        level = get_log_level(clean_line)
                        self.emit_log(clean_line, level)
                        self._update_progress_from_output(clean_line)
            
            return self.process.returncode == 0
            
        except Exception as e:
            self.emit_log(f"❌ Failed to execute automation script: {str(e)}", "error")
            return False
    
    def _update_progress_from_output(self, line: str) -> None:
        """Update progress based on automation script output."""
        if "STEP 2:" in line:
            self.update_progress(3, "active")
        elif "STEP 3:" in line:
            self.update_progress(4, "active")
        elif "GitHub Actions workflow triggered successfully" in line:
            self.emit_log("🔍 Monitoring GitHub Actions workflow...", "info")
            self._start_github_monitoring()
        elif "AUTOMATION COMPLETE" in line:
            self.update_progress(4, "completed")
            self.update_progress(5, "completed")
    
    def _start_github_monitoring(self) -> None:
        """Start monitoring the latest GitHub Actions workflow."""
        try:
            self.emit_log("⏳ Waiting for new workflow to appear in GitHub API...", "info")
            
            # Try to find the workflow run with retries
            for attempt in range(WORKFLOW_MONITORING_RETRIES):
                time.sleep(WORKFLOW_MONITORING_DELAY)
                
                runs = self.github_monitor.get_latest_workflow_runs(limit=3)
                
                if runs:
                    latest_run = runs[0]
                    
                    if is_recent_workflow(latest_run.created_at):
                        self.emit_log(
                            f"📊 Found recent workflow run #{latest_run.id} (status: {latest_run.status})",
                            "success"
                        )
                        self.github_monitor.monitor_workflow(latest_run.id, self._github_workflow_callback)
                        return
                    else:
                        self.emit_log(
                            f"⏳ Latest workflow run is older than expected, waiting... "
                            f"(attempt {attempt+1}/{WORKFLOW_MONITORING_RETRIES})",
                            "info"
                        )
                else:
                    self.emit_log(
                        f"⏳ No workflow runs found yet, waiting... "
                        f"(attempt {attempt+1}/{WORKFLOW_MONITORING_RETRIES})",
                        "info"
                    )
            
            # Could not find a recent workflow
            self.emit_log("⚠️ Could not find a recent workflow run to monitor after waiting", "warning")
            self.emit_log("💡 Check your GitHub Actions manually - the workflow may still be running", "info")
            
        except Exception as e:
            self.emit_log(f"❌ Error starting GitHub monitoring: {str(e)}", "error")
    
    def _github_workflow_callback(self, data: Dict[str, Any]) -> None:
        """Handle GitHub workflow status updates and artifacts."""
        if 'artifacts' in data:
            self._handle_workflow_artifacts(data['artifacts'])
        elif 'status' in data:
            self._handle_workflow_status_update(data)
    
    def _handle_workflow_artifacts(self, artifacts: List[Dict]) -> None:
        """Process workflow artifacts and emit download links."""
        self.emit_log(f"📦 {len(artifacts)} artifacts available from GitHub Actions", "success")
        
        output_name = os.environ.get('OUTPUT_NAME', DEFAULT_OUTPUT_NAME)
        files = []
        
        for artifact in artifacts:
            files.append(GeneratedFile(
                name=f"{output_name}.docx",
                path=f"github_artifact_{artifact['id']}",
                size=f"{artifact.get('size_in_bytes', 0) / 1024:.1f} KB",
                type='docx',
                download_url=artifact.get('archive_download_url'),
                artifact_id=str(artifact['id'])
            ))
        
        self.socketio.emit('files_ready', {'files': [file.__dict__ for file in files]})
    
    def _handle_workflow_status_update(self, data: Dict[str, Any]) -> None:
        """Handle workflow status updates."""
        status = data['status']
        conclusion = data.get('conclusion')
        
        status_messages = {
            'in_progress': ("⚙️ GitHub Actions workflow is running...", "info"),
            'queued': ("⏳ GitHub Actions workflow is queued...", "info"),
        }
        
        if status in status_messages:
            message, level = status_messages[status]
            self.emit_log(message, level)
        elif status == 'completed':
            if conclusion == 'success':
                self.emit_log("✅ GitHub Actions workflow completed successfully!", "success")
                self.update_progress(5, "completed")
            elif conclusion == 'failure':
                self.emit_log("❌ GitHub Actions workflow failed", "error")
                self.update_progress(4, "error")
            elif conclusion == 'cancelled':
                self.emit_log("⏹️ GitHub Actions workflow was cancelled", "warning")
                self.update_progress(4, "error")
    
    def _cleanup_temp_file(self, temp_file_path: Optional[str]) -> None:
        """Clean up temporary files."""
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                self.emit_log(f"🗑️  Cleaned up temp file: {temp_file_path}", "info")
            except Exception as e:
                self.emit_log(f"⚠️  Warning: Could not clean up temp file {temp_file_path}: {e}", "warning")
    
    def find_generated_files(self) -> List[GeneratedFile]:
        """Find and return all generated DOCX files."""
        files = []
        base_path = get_project_root()
        
        # Check build directory
        build_path = base_path / "build"
        if build_path.exists():
            output_name = os.environ.get('OUTPUT_NAME', DEFAULT_OUTPUT_NAME)
            docx_files = list(build_path.glob(f"{output_name}*.docx"))
            
            for docx_file in docx_files:
                size = docx_file.stat().st_size
                files.append(GeneratedFile(
                    name=f'Policy Document - {docx_file.name}',
                    path=f'build/{docx_file.name}',
                    size=f"{size / 1024:.1f} KB",
                    type='docx'
                ))
        
        # Check root directory (exclude original policy file)
        original_policy = os.environ.get('POLICY_FILE', DEFAULT_POLICY_FILE)
        docx_files = list(base_path.glob("*.docx"))
        
        for docx_file in docx_files:
            if docx_file.name not in original_policy and 'data/' not in str(docx_file):
                size = docx_file.stat().st_size
                files.append(GeneratedFile(
                    name=f'Policy Document - {docx_file.name}',
                    path=docx_file.name,
                    size=f"{size / 1024:.1f} KB",
                    type='docx'
                ))
        
        return files
    
    def run_automation(self, skip_api: bool = False, questionnaire_answers: Optional[Dict] = None,
                      timestamp: Optional[int] = None, user_id: Optional[str] = None) -> bool:
        """
        Run the complete automation process.
        
        Args:
            skip_api: Whether to skip API calls and use existing data
            questionnaire_answers: User questionnaire responses
            timestamp: Timestamp of the request
            user_id: Unique user identifier for multi-user isolation
            
        Returns:
            True if automation completed successfully, False otherwise
        """
        temp_file_path = None
        
        try:
            self.running = True
            self.emit_log("🚀 Starting Policy Automation...", "success")
            
            # Step 1: Validation
            self.update_progress(1, "active")
            self.emit_log("📋 Preparing environment and checking files...", "info")
            
            if not self._validate_questionnaire_data(questionnaire_answers or {}):
                return False
            
            is_valid, policy_path = self._validate_policy_file()
            if not is_valid:
                return False
            
            self.emit_log("✅ Policy file and localStorage questionnaire answers ready", "success")
            self.update_progress(1, "completed")
            
            # Step 2: Environment setup
            self.update_progress(2, "active")
            self.emit_log("🔧 Building automation command...", "info")
            
            env, temp_file_path = self._setup_automation_environment(
                skip_api, user_id, questionnaire_answers or {}
            )
            
            self.emit_log(f"📂 Source: localStorage ({len(questionnaire_answers or {})} fields)", "info")
            self.update_progress(2, "completed")
            
            # Step 3: Execute automation
            self.update_progress(3, "active")
            self.emit_log("🤖 Running automation script...", "info")
            
            success = self._execute_automation_script(env)
            
            if success:
                self.emit_log("🎉 Automation completed successfully!", "success")
                self.update_progress(5, "completed")
                
                # Check for generated files
                files = self.find_generated_files()
                if files:
                    self.emit_log("📄 Policy document is ready for download", "success")
                    file_names = [f.name for f in files]
                    self.emit_log(f"📄 Found {len(files)} document(s): {', '.join(file_names)}", "info")
                    self.socketio.emit('files_ready', {'files': [f.__dict__ for f in files]})
                else:
                    self.emit_log("📄 No policy documents found yet", "warning")
                
                return True
            else:
                self.emit_log("❌ Automation failed with errors", "error")
                self.update_progress(self.current_step, "error")
                return False
                
        except Exception as e:
            self.emit_log(f"❌ Unexpected error: {str(e)}", "error")
            self.update_progress(self.current_step, "error")
            return False
        finally:
            self.running = False
            self._cleanup_temp_file(temp_file_path)
    
    def stop(self) -> None:
        """Stop the automation process gracefully."""
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                time.sleep(2)
                if self.process.poll() is None:
                    self.process.kill()
                self.emit_log("⏹️ Automation stopped by user", "warning")
            except Exception:
                pass
