# Policy Automation Web UI

A modern web interface for the Policy Automation system with real-time logs, progress tracking, and file downloads.

## Features

- **Real-time Logs**: Watch automation progress with live log streaming
- **Progress Tracking**: Visual progress indicator with step-by-step status
- **File Downloads**: Download generated files directly from the UI
- **GitHub Actions Integration**: Monitor workflow status and download artifacts
- **API Cost Savings**: Skip API calls during testing with existing JSON files

## Quick Start

1. **Start the web UI:**
   ```bash
   cd web_ui
   ./start_ui.sh
   ```

2. **Access the dashboard:**
   Open your browser and go to http://localhost:5000

3. **Run automation:**
   - Check that all configuration is ready (green badges)
   - Enable "Skip API Call" to use existing JSON files during testing
   - Click "Start Policy Automation"
   - Watch the logs and progress in real-time

## Configuration

The web UI reads configuration from your main `.env` file:

- `CLAUDE_API_KEY` - Your Anthropic API key (not needed if skipping API)
- `GITHUB_TOKEN` - GitHub token for monitoring workflows (optional)
- `SKIP_API_CALL=true` - Skip API calls and use existing JSON files
- `POLICY_FILE` - Path to policy document
- `QUESTIONNAIRE_FILE` - Path to questionnaire CSV

## Architecture

- **Backend**: Flask with WebSocket support for real-time communication
- **Frontend**: Bootstrap UI with Socket.IO for live updates
- **Automation**: Integrates with existing shell scripts
- **GitHub Integration**: Monitors workflows and downloads artifacts

## Screenshots

The dashboard provides:
- Configuration status indicators
- One-click automation start
- Real-time log streaming with color coding
- Step-by-step progress tracking
- Download section for generated files

## Troubleshooting

- **Port 5000 in use**: Change the port in `app.py` line 530
- **Missing dependencies**: Run `pip install -r requirements.txt` in the web_ui directory  
- **GitHub integration not working**: Make sure `GITHUB_TOKEN` is set in your `.env` file
- **Files not downloading**: Check file permissions and paths

## Development

To run in development mode:
```bash
cd web_ui
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export FLASK_ENV=development
python3 app.py
```