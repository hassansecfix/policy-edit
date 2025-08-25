#!/usr/bin/env python3
"""
Policy Automation Web UI - Main Flask Application

This is the main entry point for the Policy Automation Web UI.
It provides REST API endpoints and WebSocket communication for the automation system.

The application is organized into separate modules:
- models.py: Data classes and type definitions
- config.py: Configuration constants and utility functions  
- github_monitor.py: GitHub Actions integration
- automation.py: Automation process management
"""

import os
import sys
import signal
import time
import zipfile
import io
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, send_file, Response
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

# Add the parent directory to sys.path for script imports
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# Import our custom modules
from config import (
    APP_SECRET_KEY, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_POLICY_FILE, 
    DEFAULT_OUTPUT_NAME, setup_cors_headers, get_project_root, get_environment_debug_info
)
from models import GeneratedFile
from automation import AutomationRunner


# =============================================================================
# FLASK APPLICATION SETUP
# =============================================================================

def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = APP_SECRET_KEY
    
    # Add CORS headers to all responses
    @app.after_request
    def after_request(response):
        return setup_cors_headers(response)
    
    return app


# Create Flask app and SocketIO
app = create_app()
socketio = SocketIO(app, cors_allowed_origins="*")

# Global automation runner instance
runner = AutomationRunner(socketio)


# =============================================================================
# REST API ENDPOINTS
# =============================================================================

@app.route('/')
def health_check():
    """Health check endpoint for API status."""
    return jsonify({
        'status': 'running',
        'service': 'Policy Automation API',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/test-cors')
def test_cors():
    """Simple test endpoint for CORS verification."""
    return jsonify({'message': 'CORS test', 'success': True})


@app.route('/api/status')
def get_status():
    """
    Get current system status and configuration.
    
    Returns information about:
    - Policy file existence
    - API key configuration
    - Automation status
    - Environment variables (for debugging)
    """
    policy_file = os.environ.get('POLICY_FILE', DEFAULT_POLICY_FILE)
    policy_path = get_project_root() / policy_file
    
    api_key = os.environ.get('CLAUDE_API_KEY', '')
    skip_api = os.environ.get('SKIP_API_CALL', '').lower() in ['true', '1', 'yes', 'on']
    
    return jsonify({
        'policy_exists': policy_path.exists(),
        'questionnaire_exists': True,  # Always true - we only use localStorage data
        'api_key_configured': bool(api_key) or skip_api,
        'skip_api': skip_api,
        'automation_running': runner.running,
        'policy_file': policy_file,
        'questionnaire_mode': 'localStorage_only',
        'questionnaire_note': 'System only uses localStorage data - no CSV file dependencies',
        'supports_direct_api': True,
        'env_vars_debug': get_environment_debug_info()
    })


@app.route('/api/start', methods=['POST'])
def start_automation():
    """
    Start the policy automation process.
    
    Expects JSON payload with:
    - questionnaire_answers: User responses from the web interface
    - skip_api: Whether to skip API calls (for testing)
    - user_id: Unique identifier for multi-user isolation
    - timestamp: Request timestamp
    """
    if runner.running:
        return jsonify({'error': 'Automation is already running'}), 400
    
    data = request.get_json() or {}
    print(f"🔍 DEBUG: Full request data keys: {list(data.keys())}")
    
    # Extract request parameters
    skip_api = data.get('skip_api', False)
    questionnaire_answers = data.get('questionnaire_answers', {})
    user_id = data.get('user_id')
    timestamp = data.get('timestamp', int(time.time() * 1000))
    
    print(f"🔍 DEBUG: Questionnaire answers count: {len(questionnaire_answers)}")
    print(f"🔍 DEBUG: User ID: {user_id}")
    print(f"🚀 Starting automation with {len(questionnaire_answers)} questionnaire answers")
    print(f"📊 Answer fields: {list(questionnaire_answers.keys())}")
    
    # Start automation in a separate thread
    runner.thread = threading.Thread(
        target=runner.run_automation,
        args=(skip_api, questionnaire_answers, timestamp, user_id),
        daemon=True
    )
    runner.thread.start()
    
    return jsonify({
        'message': 'Automation started',
        'answerCount': len(questionnaire_answers),
        'userId': user_id,
        'timestamp': timestamp
    })


@app.route('/api/stop', methods=['POST'])
def stop_automation():
    """Stop the automation process."""
    runner.stop()
    return jsonify({'message': 'Stop signal sent'})


@app.route('/api/download/<path:filename>')
def download_file(filename: str):
    """
    Download a generated file or GitHub artifact.
    
    Handles two types of downloads:
    1. Regular files: Files generated locally by the automation
    2. GitHub artifacts: Files from GitHub Actions workflows
    """
    # Handle GitHub artifacts
    if filename.startswith('github_artifact_'):
        artifact_id = filename.replace('github_artifact_', '')
        return download_github_artifact(artifact_id)
    
    # Handle regular files
    file_path = get_project_root() / filename
    
    print(f"Download request for: {filename}")
    print(f"Looking for file at: {file_path.absolute()}")
    print(f"File exists: {file_path.exists()}")
    
    if file_path.exists() and file_path.is_file():
        return send_file(str(file_path.absolute()), as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404


def download_github_artifact(artifact_id: str):
    """
    Download and extract DOCX file from GitHub Actions artifact.
    
    This function:
    1. Downloads the artifact zip file from GitHub
    2. Extracts the DOCX file from the zip
    3. Returns the DOCX file with a user-friendly name
    """
    github_token = os.environ.get('GITHUB_TOKEN')
    
    if not github_token or not runner.github_monitor.repo_owner or not runner.github_monitor.repo_name:
        return jsonify({'error': 'GitHub access not configured'}), 400
    
    try:
        # Download artifact from GitHub
        response = runner.github_monitor._make_github_request(f'actions/artifacts/{artifact_id}/zip')
        
        if not response or response.status_code != 200:
            error_msg = f'Failed to download artifact from GitHub (status: {response.status_code if response else "No response"})'
            return jsonify({'error': error_msg}), 500
        
        # Extract DOCX from zip file
        zip_data = io.BytesIO(response.content)
        
        try:
            with zipfile.ZipFile(zip_data, 'r') as zip_file:
                # Find the first .docx file in the zip (exclude macOS metadata)
                docx_files = [f for f in zip_file.namelist() 
                            if f.endswith('.docx') and not f.startswith('__MACOSX')]
                
                if not docx_files:
                    return jsonify({'error': 'No DOCX file found in artifact'}), 404
                
                # Extract the first DOCX file
                docx_filename = docx_files[0]
                docx_content = zip_file.read(docx_filename)
                
                # Generate user-friendly filename
                output_name = os.environ.get('OUTPUT_NAME', DEFAULT_OUTPUT_NAME)
                friendly_filename = f"{output_name}.docx"
                
                return Response(
                    docx_content,
                    headers={
                        'Content-Disposition': f'attachment; filename="{friendly_filename}"',
                        'Content-Type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    }
                )
                
        except zipfile.BadZipFile:
            return jsonify({'error': 'Invalid zip file from GitHub artifact'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500


# =============================================================================
# WEBSOCKET EVENT HANDLERS
# =============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection to WebSocket."""
    emit('log_message', {
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'message': '🔌 Client connected to Policy Automation Dashboard',
        'level': 'info'
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection from WebSocket."""
    print('Client disconnected from WebSocket')


@socketio.on('clear_logs')
def handle_clear_logs():
    """Handle request to clear logs in the UI."""
    emit('logs_cleared', broadcast=True)


# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

def main():
    """
    Main entry point for the Policy Automation Web UI.
    
    This function:
    1. Sets up graceful shutdown handling
    2. Starts the Flask application with SocketIO
    3. Handles keyboard interrupts cleanly
    """
    print("🚀 Starting Policy Automation Web UI...")
    print(f"📁 Working directory: {Path.cwd()}")
    print(f"🌐 Server will start on http://{DEFAULT_HOST}:{DEFAULT_PORT}")
    
    # Set up graceful shutdown
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down gracefully...")
        if runner.running:
            runner.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        socketio.run(
            app,
            debug=False,
            host=DEFAULT_HOST,
            port=DEFAULT_PORT,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")


if __name__ == '__main__':
    main()
