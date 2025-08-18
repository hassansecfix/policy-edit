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

eval "python3 scripts/complete_automation.py \
  --policy \"data/v5 Freya POL-11 Access Control.docx\" \
  --questionnaire \"data/questionnaire_responses.csv\" \
  --output-name \"policy_tracked_changes_with_comments\" \
  --api-key \"$CLAUDE_API_KEY\"${LOGO_ARGS}${GITHUB_ARG}"

echo ""
echo "✨ Done! Check GitHub Actions for your results."
