#!/bin/bash
# Start the Policy Automation Web UI

set -e

echo "🚀 Starting Policy Automation Web UI..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📋 Installing dependencies..."
pip install -r requirements.txt

# Load environment from parent directory
if [ -f "../.env" ]; then
    echo "🔑 Loading environment variables from ../.env"
    set -a  # automatically export all variables
    source ../.env
    set +a  # stop auto-exporting
fi

# Start the web application
echo "🌐 Starting web server..."
echo "📱 Access the dashboard at: http://localhost:5000"
echo "⏹️  Press Ctrl+C to stop"
echo ""

python3 app.py