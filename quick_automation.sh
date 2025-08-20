#!/bin/bash
# Quick Automation - Uses your exact command with smart defaults

set -e

echo "⚡ Quick AI Automation"
echo "Uses your current setup with smart environment handling"
echo ""

# Check for required environment variables (for production deployment)
if [ -n "$CLAUDE_API_KEY" ]; then
    echo "✅ CLAUDE_API_KEY found in environment variables"
elif [ -f ".env" ]; then
    echo "🔧 Loading environment from .env file..."
    source .env
    if [ -z "$CLAUDE_API_KEY" ]; then
        echo "❌ CLAUDE_API_KEY not found in .env file"
        echo "⚠️  Please edit .env and add your CLAUDE_API_KEY"
        echo "🔑 Get it from: https://console.anthropic.com/"
        exit 1
    fi
else
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

# Load shared configuration (single source of truth)
source "$(dirname "$0")/config.sh"

# Prioritize user questionnaire file if it exists
if [[ -f "data/user_questionnaire_responses.csv" ]]; then
    QUESTIONNAIRE_FILE="data/user_questionnaire_responses.csv"
    echo "📊 Using user-provided questionnaire responses"
else
    QUESTIONNAIRE_FILE="${QUESTIONNAIRE_FILE:-$DEFAULT_QUESTIONNAIRE_FILE}"
    echo "📊 Using default questionnaire responses"
fi

# Configuration (single source of truth) - use env vars with fallbacks
POLICY_FILE="${POLICY_FILE:-$DEFAULT_POLICY_FILE}"
# QUESTIONNAIRE_FILE already set above based on user file availability
OUTPUT_NAME="${OUTPUT_NAME:-$DEFAULT_OUTPUT_NAME}"

show_config

# Build optional arguments from environment
build_logo_args
build_github_arg

# Check for user uploaded company logo
LOGO_ARGS=""
if [[ -f "data/company_logo.png" ]]; then
    LOGO_ARGS=" --logo data/company_logo.png"
    echo "🖼️  Found user uploaded logo: data/company_logo.png"
else
    echo "📷 No user logo found - will use original logo from policy document"
fi

# Check for skip API configuration
SKIP_API_ARG=""
if [[ "${SKIP_API_CALL}" == "true" ]] || [[ "${SKIP_API_CALL}" == "TRUE" ]] || [[ "${SKIP_API_CALL}" == "True" ]]; then
    SKIP_API_ARG=" --skip-api"
    echo "💰 SKIP_API_CALL enabled - will use existing JSON file"
fi

# Generate unique user ID for multi-user isolation
USER_ID="${USER_ID:-$(date +%s)-$$}"
echo "🔑 User ID: $USER_ID (for multi-user isolation)"

eval "python3 scripts/complete_automation.py \
  --policy \"$POLICY_FILE\" \
  --questionnaire \"$QUESTIONNAIRE_FILE\" \
  --output-name \"$OUTPUT_NAME\" \
  --user-id \"$USER_ID\" \
  --api-key \"$CLAUDE_API_KEY\"${LOGO_ARGS}${GITHUB_ARG}${SKIP_API_ARG}"

echo ""
echo "✨ Done! Check GitHub Actions for your results."
