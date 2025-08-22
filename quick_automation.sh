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

# ONLY support localStorage/direct API questionnaire data - NO CSV file fallbacks
if [[ "$QUESTIONNAIRE_SOURCE" == "direct_api" ]]; then
    if [[ -n "$QUESTIONNAIRE_ANSWERS_DATA" ]]; then
        # Use environment variable approach (production-friendly, no temp files)
        echo "📊 Using localStorage questionnaire answers via environment variable"
        echo "📏 Data size: ${#QUESTIONNAIRE_ANSWERS_DATA} characters"
        QUESTIONNAIRE_INPUT_METHOD="env_var"
    elif [[ -n "$QUESTIONNAIRE_ANSWERS_JSON" ]]; then
        # Fallback to temp file approach (legacy)
        echo "📊 Using localStorage questionnaire answers: $QUESTIONNAIRE_ANSWERS_JSON"
        QUESTIONNAIRE_JSON_FILE="$QUESTIONNAIRE_ANSWERS_JSON"
        QUESTIONNAIRE_INPUT_METHOD="temp_file"
    else
        echo "❌ ERROR: No localStorage questionnaire data found!"
        echo "   QUESTIONNAIRE_SOURCE: ${QUESTIONNAIRE_SOURCE:-not set}"
        echo "   QUESTIONNAIRE_ANSWERS_DATA: ${QUESTIONNAIRE_ANSWERS_DATA:+SET (${#QUESTIONNAIRE_ANSWERS_DATA} chars)}"
        echo "   QUESTIONNAIRE_ANSWERS_JSON: ${QUESTIONNAIRE_ANSWERS_JSON:-not set}"
        echo ""
        echo "📝 Please complete the questionnaire in the web interface first."
        echo "   The system now ONLY supports localStorage data - no CSV file fallbacks."
        exit 1
    fi
else
    echo "❌ ERROR: Invalid questionnaire source!"
    echo "   QUESTIONNAIRE_SOURCE: ${QUESTIONNAIRE_SOURCE:-not set}"
    echo "   Expected: direct_api"
    exit 1
fi

# Configuration (single source of truth) - use env vars with fallbacks
POLICY_FILE="${POLICY_FILE:-$DEFAULT_POLICY_FILE}"
OUTPUT_NAME="${OUTPUT_NAME:-$DEFAULT_OUTPUT_NAME}"

show_config

# Build optional arguments from environment
build_logo_args
build_github_arg

# Logo handling - the Python automation will extract logo from localStorage if available
# No need to check for logo files here since they get created during the automation process
LOGO_ARGS=""
echo "🖼️  Logo will be extracted from localStorage during automation if provided"

# Check for skip API configuration
SKIP_API_ARG=""
if [[ "${SKIP_API_CALL}" == "true" ]] || [[ "${SKIP_API_CALL}" == "TRUE" ]] || [[ "${SKIP_API_CALL}" == "True" ]]; then
    SKIP_API_ARG=" --skip-api"
    echo "💰 SKIP_API_CALL enabled - will use existing JSON file"
fi

# Generate unique user ID for multi-user isolation
USER_ID="${USER_ID:-$(date +%s)-$$}"
echo "🔑 User ID: $USER_ID (for multi-user isolation)"

# Pass questionnaire source to Python script
export QUESTIONNAIRE_SOURCE="${QUESTIONNAIRE_SOURCE:-file}"

# Build questionnaire argument based on input method
if [[ "$QUESTIONNAIRE_INPUT_METHOD" == "env_var" ]]; then
    # Pass environment variable data directly to the automation script
    QUESTIONNAIRE_ARG="--questionnaire-env-data"
    echo "🔧 Using environment variable data approach (production-friendly)"
elif [[ "$QUESTIONNAIRE_INPUT_METHOD" == "temp_file" ]]; then
    # Use temp file approach (legacy)
    QUESTIONNAIRE_ARG="--questionnaire \"$QUESTIONNAIRE_JSON_FILE\""
    echo "🔧 Using temp file approach (legacy)"
else
    echo "❌ ERROR: Unknown questionnaire input method: $QUESTIONNAIRE_INPUT_METHOD"
    exit 1
fi

eval "python3 scripts/complete_automation.py \
  --policy \"$POLICY_FILE\" \
  $QUESTIONNAIRE_ARG \
  --output-name \"$OUTPUT_NAME\" \
  --user-id \"$USER_ID\" \
  --api-key \"$CLAUDE_API_KEY\"${LOGO_ARGS}${GITHUB_ARG}${SKIP_API_ARG}"

echo ""
echo "✨ Done! Check GitHub Actions for your results."
