#!/bin/bash

# Simple Local Automation Runner
# No LibreOffice UNO required - uses python-docx directly

set -e

# Default values
DEFAULT_POLICY="data/v5 Freya POL-11 Access Control.docx"
DEFAULT_QUESTIONNAIRE="data/questionnaire_responses.csv"
DEFAULT_OUTPUT_NAME="policy_simple_$(date +%Y%m%d_%H%M%S)"

# Override with arguments if provided
POLICY_FILE="${1:-$DEFAULT_POLICY}"
QUESTIONNAIRE_FILE="${2:-$DEFAULT_QUESTIONNAIRE}"
OUTPUT_NAME="${3:-$DEFAULT_OUTPUT_NAME}"

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "📋 Loading environment from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

echo "🚀 Simple Local Policy Automation"
echo "=================================="
echo "📋 Policy: $POLICY_FILE"
echo "📊 Questionnaire: $QUESTIONNAIRE_FILE"
echo "📝 Output: $OUTPUT_NAME"
echo "=================================="

# Check if python-docx is installed
if ! python3 -c "import docx" 2>/dev/null; then
    echo "📦 Installing required packages..."
    pip3 install python-docx requests anthropic
fi

# Create build directory
mkdir -p build

# Run the simple automation
python3 scripts/simple_local_automation.py \
    --policy "$POLICY_FILE" \
    --questionnaire "$QUESTIONNAIRE_FILE" \
    --output-name "$OUTPUT_NAME" \
    ${LOGO_PATH:+--logo "$LOGO_PATH"} \
    ${LOGO_WIDTH_MM:+--logo-width-mm "$LOGO_WIDTH_MM"} \
    ${LOGO_HEIGHT_MM:+--logo-height-mm "$LOGO_HEIGHT_MM"}

echo ""
echo "🎉 Simple automation complete!"
echo "📁 Check your file at: build/${OUTPUT_NAME}.docx"
