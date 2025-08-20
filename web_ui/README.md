# Policy Automation API Backend

A Flask-based API backend for the Policy Automation system. This serves as the backend API for the Next.js frontend dashboard.

## Overview

This Flask application provides:

- **RESTful API endpoints** for automation control
- **WebSocket support** for real-time communication with the frontend
- **File download endpoints** for generated documents
- **Integration** with existing Python automation scripts
- **GitHub Actions monitoring** and artifact downloading

## API Endpoints

- `GET /api/status` - System configuration status
- `POST /api/start` - Start automation process
- `POST /api/stop` - Stop automation process
- `GET /api/download/<path>` - Download generated files
- WebSocket endpoints for real-time logs and progress

## Quick Start

1. **Install dependencies:**

   ```bash
   cd web_ui
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Start the API backend:**

   ```bash
   python3 app.py
   ```

   API runs on http://localhost:5001

3. **Use with Next.js frontend:**
   The API is designed to work with the Next.js dashboard in `../web_app/`

## Configuration

The API reads configuration from your main `.env` file:

- `CLAUDE_API_KEY` - Your Anthropic API key (not needed if skipping API)
- `GITHUB_TOKEN` - GitHub token for monitoring workflows (optional)
- `SKIP_API_CALL=true` - Skip API calls and use existing JSON files
- `POLICY_FILE` - Path to policy document
- NOTE: QUESTIONNAIRE_FILE removed - system now uses localStorage data only

## Architecture

- **Flask** - Web framework with CORS support
- **Flask-SocketIO** - WebSocket support for real-time communication
- **Automation Integration** - Calls existing shell scripts and Python modules
- **File Management** - Serves generated files for download
- **GitHub API Integration** - Monitors workflows and downloads artifacts

## Development

For development with auto-reload:

```bash
cd web_ui
source venv/bin/activate
export FLASK_ENV=development
python3 app.py
```

## API-Only

Note: This is now an API-only backend. The UI has been moved to a separate Next.js application in `../web_app/`. This Flask app no longer serves HTML templates or static files.
