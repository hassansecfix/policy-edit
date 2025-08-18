#!/bin/bash
# Complete AI Automation - From Questionnaire to Tracked Changes DOCX
# This script runs the full end-to-end workflow using GitHub Actions

set -e  # Exit on any error

# Configuration - modify these as needed
POLICY_FILE="data/v5 Freya POL-11 Access Control.docx"
QUESTIONNAIRE_FILE="data/secfix_questionnaire_responses_consulting.csv"
OUTPUT_NAME="policy_tracked_changes_with_comments"

echo "🚀 Complete AI Automation Starting..."
echo "=" * 50
echo "📋 Policy: $POLICY_FILE"
echo "📊 Questionnaire: $QUESTIONNAIRE_FILE"
echo "📝 Output name: $OUTPUT_NAME"
echo "🤖 AI: Claude Sonnet 4"
echo "⚙️  Processing: GitHub Actions"
echo "=" * 50

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "💡 Create a .env file with:"
    echo "   CLAUDE_API_KEY=your_api_key_here"
    echo ""
    echo "📖 Get your Claude API key from: https://console.anthropic.com/"
    exit 1
fi

# Check if input files exist
if [ ! -f "$POLICY_FILE" ]; then
    echo "❌ Error: Policy file not found: $POLICY_FILE"
    exit 1
fi

if [ ! -f "$QUESTIONNAIRE_FILE" ]; then
    echo "❌ Error: Questionnaire file not found: $QUESTIONNAIRE_FILE"
    exit 1
fi

# Source environment variables and run the automation
echo "🔑 Loading environment variables..."
source .env

if [ -z "$CLAUDE_API_KEY" ]; then
    echo "❌ Error: CLAUDE_API_KEY not set in .env file!"
    echo "💡 Add this line to your .env file:"
    echo "   CLAUDE_API_KEY=your_api_key_here"
    exit 1
fi

echo "🤖 Starting AI-powered policy automation..."
echo ""

# Optional logo args from env
LOGO_ARGS=""
if [ -n "${LOGO_PATH}" ]; then
  LOGO_ARGS+=" --logo \"${LOGO_PATH}\""
fi
if [ -n "${LOGO_WIDTH_MM}" ]; then
  LOGO_ARGS+=" --logo-width-mm ${LOGO_WIDTH_MM}"
fi
if [ -n "${LOGO_HEIGHT_MM}" ]; then
  LOGO_ARGS+=" --logo-height-mm ${LOGO_HEIGHT_MM}"
fi

# Optional GitHub token
GITHUB_ARG=""
if [ -n "${GITHUB_TOKEN}" ]; then
  GITHUB_ARG=" --github-token \"${GITHUB_TOKEN}\""
fi

# Run the complete automation
eval "python3 scripts/complete_automation.py \
    --policy \"$POLICY_FILE\" \
    --questionnaire \"$QUESTIONNAIRE_FILE\" \
    --output-name \"$OUTPUT_NAME\" \
    --api-key \"$CLAUDE_API_KEY\"${LOGO_ARGS}${GITHUB_ARG}"

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
    echo "📄 Expected output file: build/${OUTPUT_NAME}.docx"
    echo "🏆 Your customized policy is ready for review!"
else
    echo ""
    echo "❌ Automation failed!"
    echo "💡 Check the error messages above for details"
    exit 1
fi
