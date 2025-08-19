#!/bin/bash
# Quick Automation - Uses your exact command with smart defaults

set -e

echo "⚡ Quick AI Automation"
echo "Uses your current setup with smart environment handling"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "🔧 Setting up environment file..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "📝 Created .env from template"
        echo "⚠️  Please edit .env and add your CLAUDE_API_KEY"
        echo "🔑 Get it from: https://console.anthropic.com/"
        echo ""
        echo "After adding your API key, run this script again."
        exit 1
    else
        echo "❌ No environment template found"
        exit 1
    fi
fi

# Your exact command with environment loading
echo "🚀 Running your automation command..."
echo ""

source .env

# Load shared configuration (single source of truth)
source "$(dirname "$0")/config.sh"

# Configuration (single source of truth) - use env vars with fallbacks
POLICY_FILE="${POLICY_FILE:-$DEFAULT_POLICY_FILE}"
QUESTIONNAIRE_FILE="${QUESTIONNAIRE_FILE:-$DEFAULT_QUESTIONNAIRE_FILE}"
OUTPUT_NAME="${OUTPUT_NAME:-$DEFAULT_OUTPUT_NAME}"

show_config

# Build optional arguments from environment
build_logo_args
build_github_arg

# Check for skip API configuration
SKIP_API_ARG=""
if [[ "${SKIP_API_CALL}" == "true" ]] || [[ "${SKIP_API_CALL}" == "TRUE" ]] || [[ "${SKIP_API_CALL}" == "True" ]]; then
    SKIP_API_ARG=" --skip-api"
    echo "💰 SKIP_API_CALL enabled - will use existing JSON file"
fi

eval "python3 scripts/complete_automation.py \
  --policy \"$POLICY_FILE\" \
  --questionnaire \"$QUESTIONNAIRE_FILE\" \
  --output-name \"$OUTPUT_NAME\" \
  --api-key \"$CLAUDE_API_KEY\"${LOGO_ARGS}${GITHUB_ARG}${SKIP_API_ARG}"

echo ""
echo "✨ Done! Check GitHub Actions for your results."
