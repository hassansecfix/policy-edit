#!/usr/bin/env python3
"""
Policy Automation Web UI
A Flask-based web interface for the policy automation system with real-time logs
"""

import os
import sys
import threading
import subprocess
import time
import json
import requests
import signal
import re
import glob
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

# Add the parent directory to sys.path so we can import our scripts
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'policy-automation-secret-key-2024'

# Manual CORS headers
@app.after_request
def after_request(response):
    print("CORS: Adding headers to response")  # Debug output
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
automation_process = None
automation_thread = None
automation_running = False

def find_latest_questionnaire_file(base_path):
    """Find the most recent questionnaire responses file"""
    data_dir = Path(base_path) / "data"
    
    # Look for user-specific timestamped files first
    user_files_pattern = str(data_dir / "user_questionnaire_responses_*.csv")
    user_files = glob.glob(user_files_pattern)
    
    if user_files:
        # Sort by timestamp in filename (newest first)
        user_files.sort(key=lambda x: int(x.split('_')[-1].replace('.csv', '')), reverse=True)
        latest_file = user_files[0]
        relative_path = Path(latest_file).relative_to(base_path)
        print(f"📊 Found timestamped questionnaire file: {relative_path}")
        return str(relative_path), Path(latest_file), "user_timestamped"
    
    # Fall back to main user questionnaire file
    main_user_file = data_dir / "user_questionnaire_responses.csv"
    if main_user_file.exists():
        relative_path = Path("data/user_questionnaire_responses.csv")
        print(f"📊 Found main user questionnaire file: {relative_path}")
        return str(relative_path), main_user_file, "user_main"
    
    # Fall back to default questionnaire file
    default_file = os.environ.get('QUESTIONNAIRE_FILE', 'data/secfix_questionnaire_responses_consulting.csv')
    default_path = Path(base_path) / default_file
    if default_path.exists():
        print(f"📊 Using default questionnaire file: {default_file}")
        return default_file, default_path, "default"
    
    # No questionnaire file found
    print("❌ No questionnaire file found")
    return None, None, "none"

class GitHubActionsMonitor:
    def __init__(self):
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.repo_owner = None
        self.repo_name = None
        self.workflow_run_id = None
        self._get_repo_info()
        
    def _get_repo_info(self):
        """Extract GitHub repository info from environment variables or git remote"""
        # First try environment variables (for production deployment)
        self.repo_owner = os.environ.get('GITHUB_REPO_OWNER')
        self.repo_name = os.environ.get('GITHUB_REPO_NAME')
        
        # If environment variables are not set, try git (for local development)
        if not self.repo_owner or not self.repo_name:
            try:
                result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                      capture_output=True, text=True, cwd=Path.cwd())
                if result.returncode == 0:
                    url = result.stdout.strip()
                    # Parse GitHub URL (both HTTPS and SSH formats)
                    if 'github.com' in url:
                        # Extract owner/repo from URL
                        match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', url)
                        if match:
                            self.repo_owner = match.group(1)
                            self.repo_name = match.group(2)
            except:
                pass
    
    def get_latest_workflow_runs(self, workflow_name="redline-docx.yml", limit=5):
        """Get recent workflow runs"""
        if not self.github_token or not self.repo_owner or not self.repo_name:
            return []
            
        try:
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/actions/workflows/{workflow_name}/runs"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.get(url, headers=headers, params={'per_page': limit})
            
            if response.status_code == 200:
                runs = response.json().get('workflow_runs', [])
                return [{
                    'id': run['id'],
                    'status': run['status'],
                    'conclusion': run['conclusion'],
                    'created_at': run['created_at'],
                    'updated_at': run['updated_at'],
                    'html_url': run['html_url']
                } for run in runs]
        except Exception as e:
            print(f"Error fetching workflow runs: {e}")
        
        return []
    
    def monitor_workflow(self, run_id, callback=None):
        """Monitor a specific workflow run"""
        if not self.github_token or not self.repo_owner or not self.repo_name:
            return
            
        self.workflow_run_id = run_id
        thread = threading.Thread(target=self._monitor_workflow_thread, args=(run_id, callback))
        thread.daemon = True
        thread.start()
        
    def _monitor_workflow_thread(self, run_id, callback):
        """Monitor workflow in a separate thread"""
        while True:
            try:
                url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/actions/runs/{run_id}"
                headers = {
                    'Authorization': f'token {self.github_token}',
                    'Accept': 'application/vnd.github.v3+json'
                }
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    run = response.json()
                    status = run['status']
                    conclusion = run['conclusion']
                    
                    if callback:
                        callback(run)
                    
                    # Stop monitoring if workflow is complete
                    if status == 'completed':
                        # Check for artifacts
                        self._check_artifacts(run_id, callback)
                        break
                        
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Error monitoring workflow: {e}")
                break
                
    def _check_artifacts(self, run_id, callback):
        """Check for workflow artifacts"""
        try:
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/actions/runs/{run_id}/artifacts"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                artifacts = response.json().get('artifacts', [])
                if artifacts and callback:
                    callback({'artifacts': artifacts})
                    
        except Exception as e:
            print(f"Error checking artifacts: {e}")

class AutomationRunner:
    def __init__(self):
        self.process = None
        self.thread = None
        self.running = False
        self.github_monitor = GitHubActionsMonitor()
        self.steps = [
            "Preparing environment",
            "Processing questionnaire", 
            "Generating AI edits",
            "Triggering GitHub Actions",
            "Complete"
        ]
        self.current_step = 0
        
    def emit_log(self, message, level="info", step=None):
        """Emit a log message to all connected clients"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        socketio.emit('log_message', {
            'timestamp': timestamp,
            'message': message,
            'level': level,
            'step': step
        })
        
    def update_progress(self, step, status="active"):
        """Update progress step"""
        self.current_step = step
        socketio.emit('progress_update', {
            'step': step,
            'status': status,
            'progress': (step / len(self.steps)) * 100
        })
        
    def run_automation(self, skip_api=False):
        """Run the automation process"""
        try:
            self.running = True
            self.emit_log("🚀 Starting Policy Automation...", "success")
            
            # Step 1: Preparation
            self.update_progress(1, "active")
            self.emit_log("📋 Preparing environment and checking files...", "info")
            time.sleep(1)
            
            # Check if files exist (paths relative to parent directory)
            base_path = Path(__file__).parent.parent
            policy_file = os.environ.get('POLICY_FILE', 'data/v5 Freya POL-11 Access Control.docx')
            
            # Find the latest questionnaire file
            questionnaire_file, questionnaire_path, questionnaire_source = find_latest_questionnaire_file(base_path)
            
            if questionnaire_source == "user_timestamped":
                self.emit_log("📊 Using user-provided timestamped questionnaire responses", "success")
            elif questionnaire_source == "user_main":
                self.emit_log("📊 Using user-provided main questionnaire responses", "success")
            elif questionnaire_source == "default":
                self.emit_log("📊 Using default questionnaire responses", "info")
            else:
                self.emit_log("❌ No questionnaire file found", "error")
            
            policy_path = base_path / policy_file
            
            if not policy_path.exists():
                self.emit_log(f"❌ Policy file not found: {policy_file}", "error")
                self.update_progress(1, "error")
                return False
                
            if not questionnaire_file or not questionnaire_path or not questionnaire_path.exists():
                self.emit_log(f"❌ Questionnaire file not found: {questionnaire_file or 'No file detected'}", "error")
                self.update_progress(1, "error")
                return False
                
            self.emit_log("✅ All required files found", "success")
            self.update_progress(1, "completed")
            
            # Step 2: Build command
            self.update_progress(2, "active")
            self.emit_log("🔧 Building automation command...", "info")
            
            # Build the command - use the working shell script approach but with proper error handling
            base_path = Path(__file__).parent.parent
            script_path = base_path / "quick_automation.sh"
            
            # Set environment variables
            env = os.environ.copy()
            if skip_api:
                env['SKIP_API_CALL'] = 'true'
                self.emit_log("💰 API call will be skipped (using existing JSON)", "warning")
            
            # Pass the specific questionnaire file to the automation script
            env['QUESTIONNAIRE_FILE'] = questionnaire_file
            self.emit_log(f"📋 Questionnaire file: {questionnaire_file}", "info")
            self.emit_log(f"📂 File source: {questionnaire_source}", "info")
                
            self.update_progress(2, "completed")
            
            # Step 3: Run automation
            self.update_progress(3, "active")
            self.emit_log("🤖 Running automation script...", "info")
            
            # Debug: Log environment variables being passed
            debug_env_vars = {
                'CLAUDE_API_KEY': '***PRESENT***' if env.get('CLAUDE_API_KEY') else 'NOT SET',
                'GITHUB_REPO_OWNER': env.get('GITHUB_REPO_OWNER', 'NOT SET'),
                'GITHUB_REPO_NAME': env.get('GITHUB_REPO_NAME', 'NOT SET'),
                'GIT_USER_NAME': env.get('GIT_USER_NAME', 'NOT SET'),
                'GIT_USER_EMAIL': env.get('GIT_USER_EMAIL', 'NOT SET')
            }
            self.emit_log(f"🔍 Environment variables: {debug_env_vars}", "info")
            
            # Execute the script and capture output in real-time
            self.process = subprocess.Popen(
                [str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                env=env,
                cwd=str(base_path)  # Run from the project root directory
            )
            
            # Read output line by line
            while self.running and self.process.poll() is None:
                line = self.process.stdout.readline()
                if line:
                    clean_line = line.strip()
                    if clean_line:
                        # Parse the log level based on emoji/content
                        level = "info"
                        if any(emoji in clean_line for emoji in ["❌", "Error:", "failed"]):
                            level = "error"
                        elif any(emoji in clean_line for emoji in ["✅", "SUCCESS", "completed"]):
                            level = "success"
                        elif any(emoji in clean_line for emoji in ["⚠️", "Warning:", "💰"]):
                            level = "warning"
                            
                        self.emit_log(clean_line, level)
                        
                        # Update progress based on log content
                        if "STEP 2:" in clean_line:
                            self.update_progress(3, "active")
                        elif "STEP 3:" in clean_line:
                            self.update_progress(4, "active")
                        elif "GitHub Actions workflow triggered successfully" in clean_line:
                            self.emit_log("🔍 Monitoring GitHub Actions workflow...", "info")
                            # Extract workflow URL if available and start monitoring
                            self.start_github_monitoring()
                        elif "AUTOMATION COMPLETE" in clean_line:
                            self.update_progress(4, "completed")
                            self.update_progress(5, "completed")
                            
            # Check final result
            if self.process.returncode == 0:
                self.emit_log("🎉 Automation completed successfully!", "success")
                self.update_progress(5, "completed")
                
                # Check for generated files
                self.check_generated_files()
                
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
            
    def start_github_monitoring(self):
        """Start monitoring the latest GitHub Actions workflow with retry logic"""
        try:
            # Wait for the new workflow to appear in the API (GitHub has a small delay)
            self.emit_log("⏳ Waiting for new workflow to appear in GitHub API...", "info")
            
            # Try to find the workflow run with retries
            max_retries = 6  # Try for ~30 seconds
            retry_delay = 5  # seconds
            
            for attempt in range(max_retries):
                time.sleep(retry_delay)  # Wait before checking
                
                runs = self.github_monitor.get_latest_workflow_runs(limit=3)  # Get more runs to find the latest
                
                if runs:
                    # Get the most recent run (should be our newly triggered one)
                    latest_run = runs[0]
                    run_id = latest_run['id']
                    status = latest_run['status']
                    
                    # Check if this run was created recently (within last 2 minutes)
                    from datetime import datetime, timezone, timedelta
                    created_time = datetime.fromisoformat(latest_run['created_at'].replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    age = now - created_time
                    
                    if age <= timedelta(minutes=2):  # Recent workflow
                        self.emit_log(f"📊 Found recent workflow run #{run_id} (status: {status})", "success")
                        
                        # Start monitoring with callback
                        self.github_monitor.monitor_workflow(run_id, self.github_workflow_callback)
                        return
                    else:
                        self.emit_log(f"⏳ Latest workflow run is older than expected, waiting... (attempt {attempt+1}/{max_retries})", "info")
                else:
                    self.emit_log(f"⏳ No workflow runs found yet, waiting... (attempt {attempt+1}/{max_retries})", "info")
            
            # If we get here, we couldn't find a recent workflow
            self.emit_log("⚠️ Could not find a recent workflow run to monitor after waiting", "warning")
            self.emit_log("💡 Check your GitHub Actions manually - the workflow may still be running", "info")
            
        except Exception as e:
            self.emit_log(f"❌ Error starting GitHub monitoring: {str(e)}", "error")
            
    def github_workflow_callback(self, data):
        """Callback for GitHub workflow updates"""
        if 'artifacts' in data:
            # Artifacts are available
            artifacts = data['artifacts']
            self.emit_log(f"📦 {len(artifacts)} artifacts available from GitHub Actions", "success")
            
            # Convert artifacts to download format
            files = []
            output_name = os.environ.get('OUTPUT_NAME', 'policy_tracked_changes_with_comments')
            for artifact in artifacts:
                files.append({
                    'name': f"{output_name}.docx",
                    'path': f"github_artifact_{artifact['id']}",
                    'size': f"{artifact.get('size_in_bytes', 0) / 1024:.1f} KB",
                    'type': 'docx',
                    'download_url': artifact.get('archive_download_url'),
                    'artifact_id': artifact['id']
                })
            
            socketio.emit('files_ready', {'files': files})
            
        elif 'status' in data:
            # Workflow status update
            status = data['status']
            conclusion = data.get('conclusion')
            
            if status == 'in_progress':
                self.emit_log("⚙️ GitHub Actions workflow is running...", "info")
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
            elif status == 'queued':
                self.emit_log("⏳ GitHub Actions workflow is queued...", "info")
            
    def check_generated_files(self):
        """Check for generated files and emit download links"""
        files_found = []
        
        # Get project root directory (parent of web_ui)
        base_path = Path(__file__).parent.parent
        
        # Check for local DOCX output in build directory
        build_path = base_path / "build"
        if build_path.exists():
            output_name = os.environ.get('OUTPUT_NAME', 'policy_tracked_changes_with_comments')
            docx_files = list(build_path.glob(f"{output_name}*.docx"))
            for docx_file in docx_files:
                size = docx_file.stat().st_size
                files_found.append({
                    'name': f'Policy Document - {docx_file.name}',
                    'path': f'build/{docx_file.name}',  # Relative to project root
                    'size': f"{size / 1024:.1f} KB",
                    'type': 'docx'
                })
        
        # Check for any DOCX files in the root directory (from LibreOffice output)
        # Exclude the original policy file
        original_policy = os.environ.get('POLICY_FILE', 'data/v5 Freya POL-11 Access Control.docx')
        docx_files = list(base_path.glob("*.docx"))
        for docx_file in docx_files:
            # Skip the original policy file and any files in the data directory
            if docx_file.name not in original_policy and 'data/' not in str(docx_file):
                size = docx_file.stat().st_size
                files_found.append({
                    'name': f'Policy Document - {docx_file.name}',
                    'path': f'{docx_file.name}',  # Relative to project root
                    'size': f"{size / 1024:.1f} KB",
                    'type': 'docx'
                })
            
        if files_found:
            self.emit_log("📄 Policy document is ready for download", "success")
            self.emit_log(f"📄 Found {len(files_found)} document(s): {', '.join([f['name'] for f in files_found])}", "info")
            socketio.emit('files_ready', {'files': files_found})
        else:
            self.emit_log("📄 No policy documents found yet", "warning")
            
    def stop(self):
        """Stop the automation process"""
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                time.sleep(2)
                if self.process.poll() is None:
                    self.process.kill()
                self.emit_log("⏹️ Automation stopped by user", "warning")
            except:
                pass

# Global runner instance
runner = AutomationRunner()

@app.route('/')
def health_check():
    """Health check endpoint for API"""
    response = jsonify({
        'status': 'running',
        'service': 'Policy Automation API',
        'timestamp': datetime.now().isoformat()
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    print("Added CORS headers to health check")
    return response

@app.route('/test-cors')
def test_cors():
    """Simple test endpoint for CORS"""
    response = jsonify({'message': 'CORS test', 'success': True})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    print("Test CORS endpoint called")
    return response

@app.route('/api/status')
def get_status():
    """Get current system status"""
    # Check file existence - paths are relative to the parent directory
    base_path = Path(__file__).parent.parent
    policy_file = os.environ.get('POLICY_FILE', 'data/v5 Freya POL-11 Access Control.docx')
    
    # Find the latest questionnaire file
    questionnaire_file, questionnaire_path, questionnaire_source = find_latest_questionnaire_file(base_path)
    
    api_key = os.environ.get('CLAUDE_API_KEY', '')
    skip_api = os.environ.get('SKIP_API_CALL', '').lower() in ['true', '1', 'yes', 'on']
    
    # Resolve paths relative to project root
    policy_path = base_path / policy_file
    
    # Check if we have user questionnaire files available
    user_files_pattern = str(base_path / "data" / "user_questionnaire_responses_*.csv")
    user_files = glob.glob(user_files_pattern)
    main_user_file = base_path / "data" / "user_questionnaire_responses.csv"
    user_questionnaire_available = len(user_files) > 0 or main_user_file.exists()
    
    # Debug: Check environment variables
    env_vars_debug = {
        'CLAUDE_API_KEY': '***PRESENT***' if api_key else 'NOT SET',
        'GITHUB_REPO_OWNER': os.environ.get('GITHUB_REPO_OWNER', 'NOT SET'),
        'GITHUB_REPO_NAME': os.environ.get('GITHUB_REPO_NAME', 'NOT SET'),
        'GIT_USER_NAME': os.environ.get('GIT_USER_NAME', 'NOT SET'),
        'GIT_USER_EMAIL': os.environ.get('GIT_USER_EMAIL', 'NOT SET'),
        'GITHUB_TOKEN': '***PRESENT***' if os.environ.get('GITHUB_TOKEN') else 'NOT SET'
    }
    
    response = jsonify({
        'policy_exists': policy_path.exists(),
        'questionnaire_exists': questionnaire_path is not None and questionnaire_path.exists(),
        'api_key_configured': bool(api_key) or skip_api,
        'skip_api': skip_api,
        'automation_running': runner.running,
        'policy_file': policy_file,
        'questionnaire_file': questionnaire_file or 'No questionnaire file found',
        'questionnaire_source': questionnaire_source,
        'user_questionnaire_available': user_questionnaire_available,
        'user_timestamped_files': len(user_files),
        'env_vars_debug': env_vars_debug
    })
    
    # Add CORS headers directly
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    
    return response

@app.route('/api/start', methods=['POST'])
def start_automation():
    """Start the automation process"""
    if runner.running:
        return jsonify({'error': 'Automation is already running'}), 400
        
    data = request.get_json() or {}
    skip_api = data.get('skip_api', False)
    
    # Start automation in a separate thread
    runner.thread = threading.Thread(target=runner.run_automation, args=(skip_api,))
    runner.thread.daemon = True
    runner.thread.start()
    
    return jsonify({'message': 'Automation started'})

@app.route('/api/stop', methods=['POST'])
def stop_automation():
    """Stop the automation process"""
    runner.stop()
    return jsonify({'message': 'Stop signal sent'})

@app.route('/api/download/<path:filename>')
def download_file(filename):
    """Download a generated file"""
    # Handle GitHub artifacts
    if filename.startswith('github_artifact_'):
        artifact_id = filename.replace('github_artifact_', '')
        return download_github_artifact(artifact_id)
    
    # Handle regular files - need to resolve relative to project root
    base_path = Path(__file__).parent.parent
    file_path = base_path / filename
    
    print(f"Download request for: {filename}")
    print(f"Looking for file at: {file_path.absolute()}")
    print(f"File exists: {file_path.exists()}")
    
    if file_path.exists() and file_path.is_file():
        response = send_file(str(file_path.absolute()), as_attachment=True)
        # Add CORS headers to download response
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    else:
        response = jsonify({'error': 'File not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404

def download_github_artifact(artifact_id):
    """Download and extract DOCX file from GitHub Actions artifact"""
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token or not runner.github_monitor.repo_owner or not runner.github_monitor.repo_name:
        return jsonify({'error': 'GitHub access not configured'}), 400
        
    try:
        # Get artifact download URL
        url = f"https://api.github.com/repos/{runner.github_monitor.repo_owner}/{runner.github_monitor.repo_name}/actions/artifacts/{artifact_id}/zip"
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Download the zip file
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            # Extract DOCX from the zip file
            import zipfile
            import io
            from flask import Response
            
            # Create a BytesIO object from the zip content
            zip_data = io.BytesIO(response.content)
            
            try:
                with zipfile.ZipFile(zip_data, 'r') as zip_file:
                    # Find the first .docx file in the zip
                    docx_files = [f for f in zip_file.namelist() if f.endswith('.docx') and not f.startswith('__MACOSX')]
                    
                    if not docx_files:
                        return jsonify({'error': 'No DOCX file found in artifact'}), 404
                    
                    # Use the first DOCX file found
                    docx_filename = docx_files[0]
                    
                    # Extract the DOCX file content
                    docx_content = zip_file.read(docx_filename)
                    
                    # Generate a user-friendly filename using OUTPUT_NAME from env
                    output_name = os.environ.get('OUTPUT_NAME', 'policy_tracked_changes_with_comments')
                    friendly_filename = f"{output_name}.docx"
                    
                    # Return the DOCX file directly
                    return Response(
                        docx_content,
                        headers={
                            'Content-Disposition': f'attachment; filename="{friendly_filename}"',
                            'Content-Type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                        }
                    )
                    
            except zipfile.BadZipFile:
                return jsonify({'error': 'Invalid zip file from GitHub artifact'}), 500
                
        else:
            return jsonify({'error': f'Failed to download artifact from GitHub (status: {response.status_code})'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('log_message', {
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'message': f'🔌 Client connected to Policy Automation Dashboard',
        'level': 'info'
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('clear_logs')
def handle_clear_logs():
    """Handle request to clear logs"""
    emit('logs_cleared', broadcast=True)

if __name__ == '__main__':
    print("🚀 Starting Policy Automation Web UI...")
    print(f"📁 Working directory: {Path.cwd()}")
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down gracefully...")
        if runner.running:
            runner.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        socketio.run(app, debug=False, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")