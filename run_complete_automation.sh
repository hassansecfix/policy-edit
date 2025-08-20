#!/bin/bash
# Complete AI Automation - From Questionnaire to Tracked Changes DOCX
# This script runs the full end-to-end workflow using GitHub Actions

set -e  # Exit on any error

# Load shared configuration (single source of truth)
source "$(dirname "$0")/config.sh"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "💡 Create a .env file with:"
    echo "   CLAUDE_API_KEY=your_api_key_here"
    echo ""
    echo "📖 Get your Claude API key from: https://console.anthropic.com/"
    exit 1
fi

# Source environment variables and set configuration (single source of truth)
echo "🔑 Loading environment variables..."
source .env

if [ -z "$CLAUDE_API_KEY" ]; then
    echo "❌ Error: CLAUDE_API_KEY not set in .env file!"
    echo "💡 Add this line to your .env file:"
    echo "   CLAUDE_API_KEY=your_api_key_here"
    exit 1
fi

# Use environment variables with fallback to defaults (single source of truth)
POLICY_FILE="${POLICY_FILE:-$DEFAULT_POLICY_FILE}"
OUTPUT_NAME="${OUTPUT_NAME:-$DEFAULT_OUTPUT_NAME}"
# NOTE: Questionnaire file removed - system now uses localStorage data via web UI only

echo "❌ DEPRECATED: Direct shell script automation is no longer supported"
echo "=" * 50
echo "🌐 Please use the web UI for automation:"
echo "   1. Start the web app: cd web_app && npm run dev"
echo "   2. Complete the questionnaire in the browser"
echo "   3. Run automation from the web interface"
echo ""
echo "📱 The system now uses localStorage for questionnaire data"
echo "   This script cannot access browser localStorage"
echo "=" * 50
exit 1

echo "🤖 Starting AI-powered policy automation..."
echo ""

# Build optional arguments from environment
build_logo_args
build_github_arg

# Check for skip API configuration
SKIP_API_ARG=""
if [[ "${SKIP_API_CALL}" == "true" ]] || [[ "${SKIP_API_CALL}" == "TRUE" ]] || [[ "${SKIP_API_CALL}" == "True" ]]; then
    SKIP_API_ARG=" --skip-api"
    echo "💰 SKIP_API_CALL enabled - will use existing JSON file"
fi

# Generate unique user ID for multi-user isolation
USER_ID="${USER_ID:-$(date +%s)-$$}"
echo "🔑 User ID: $USER_ID (for multi-user isolation)"

# Run the complete automation
eval "python3 scripts/complete_automation.py \
    --policy \"$POLICY_FILE\" \
    --questionnaire \"$QUESTIONNAIRE_FILE\" \
    --output-name \"$OUTPUT_NAME\" \
    --user-id \"$USER_ID\" \
    --api-key \"$CLAUDE_API_KEY\"${LOGO_ARGS}${GITHUB_ARG}${SKIP_API_ARG}"

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Automation completed successfully!"
    echo "=" * 50
    echo "📋 What happened:"
    echo "  1. ✅ AI analyzed your policy and questionnaire"
    echo "  2. ✅ Generated intelligent edits"
    echo "  3. ✅ Triggered GitHub Actions for DOCX generation"
    echo ""
    echo "🔗 Next steps:"
    echo "  1. Check GitHub Actions for completion status"
    echo "  2. Download the result from GitHub Actions artifacts"
    echo "  3. Review tracked changes in LibreOffice Writer"
    echo ""
    echo "📄 Expected output file: build/${USER_ID}_${OUTPUT_NAME}.docx"
    echo "🏷️  Artifact name: redlined-docx-<run_id>-<run_number>"
    echo "🔑 Your User ID: $USER_ID (use this to track your specific run)"
    echo "🏆 Your customized policy is ready for review!"
else
    echo ""
    echo "❌ Automation failed!"
    echo "💡 Check the error messages above for details"
    exit 1
fi
