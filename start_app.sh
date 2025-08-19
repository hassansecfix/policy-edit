#!/bin/bash

# Policy Automation App - Complete Startup Script
# This script starts both the Flask API backend and Next.js frontend

echo "🚀 Starting Policy Automation App"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    jobs -p | xargs -r kill 2>/dev/null
    pkill -f "python3 app.py" 2>/dev/null
    pkill -f "next-server" 2>/dev/null
    echo -e "${GREEN}✅ Services stopped${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if we're in the right directory
if [ ! -d "web_ui" ] || [ ! -d "web_app" ]; then
    echo -e "${RED}❌ Error: Run this script from the policy-edit project root${NC}"
    echo -e "${BLUE}💡 Current directory should contain 'web_ui' and 'web_app' folders${NC}"
    exit 1
fi

# Start Flask API in background
echo -e "${BLUE}🐍 Starting Flask API backend...${NC}"
cd web_ui

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -q -r requirements.txt

echo -e "${GREEN}🔧 Starting Flask API on http://localhost:5001...${NC}"
python3 app.py &
FLASK_PID=$!

# Wait a moment for Flask to start
sleep 3

# Check if Flask started successfully
if ! curl -s http://localhost:5001/api/status > /dev/null 2>&1; then
    echo -e "${RED}❌ Failed to start Flask API${NC}"
    cleanup
    exit 1
fi

echo -e "${GREEN}✅ Flask API started successfully${NC}"

# Start Next.js frontend
echo -e "${BLUE}⚛️  Starting Next.js frontend...${NC}"
cd ../web_app

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing Node.js dependencies...${NC}"
    npm install
fi

echo -e "${GREEN}🌐 Starting Next.js on http://localhost:3000...${NC}"
npm run dev &
NEXTJS_PID=$!

echo ""
echo -e "${GREEN}✅ Dashboard started successfully!${NC}"
echo -e "${BLUE}🔗 Frontend: http://localhost:3000${NC}"
echo -e "${BLUE}📡 API: http://localhost:5001${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both services${NC}"
echo ""

# Wait for both processes
wait $FLASK_PID $NEXTJS_PID
