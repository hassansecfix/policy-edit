#!/bin/bash
# Customizable Complete AI Automation Script
# Modify the variables below or pass arguments to customize the run

set -e  # Exit on any error

# Default configuration (modify these as needed)
DEFAULT_POLICY="data/v5 Freya POL-11 Access Control.docx"
DEFAULT_QUESTIONNAIRE="data/questionnaire_responses.csv"
DEFAULT_OUTPUT="policy_tracked_changes_with_comments_$(date +%Y%m%d_%H%M%S)"

# Parse command line arguments
POLICY_FILE="${1:-$DEFAULT_POLICY}"
QUESTIONNAIRE_FILE="${2:-$DEFAULT_QUESTIONNAIRE}"
OUTPUT_NAME="${3:-$DEFAULT_OUTPUT}"

# Help function
show_help() {
    echo "Usage: $0 [policy_file] [questionnaire_file] [output_name]"
    echo ""
    echo "Arguments:"
    echo "  policy_file        Path to policy DOCX (default: $DEFAULT_POLICY)"
    echo "  questionnaire_file Path to questionnaire CSV (default: $DEFAULT_QUESTIONNAIRE)"
    echo "  output_name        Output name prefix (default: $DEFAULT_OUTPUT)"
    echo ""
    echo "Examples:"
    echo "  $0"
    echo "  $0 data/my_policy.docx"
    echo "  $0 data/my_policy.docx data/my_responses.csv"
    echo "  $0 data/my_policy.docx data/my_responses.csv \"custom_policy_v2\""
    echo ""
    echo "Requirements:"
    echo "  - .env file with CLAUDE_API_KEY=your_key"
    echo "  - Policy DOCX file"
    echo "  - Questionnaire CSV file"
}

# Check for help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

echo "🚀 Complete AI Automation (Customizable)"
echo "=" * 50
echo "📋 Policy: $POLICY_FILE"
echo "📊 Questionnaire: $QUESTIONNAIRE_FILE" 
echo "📝 Output: $OUTPUT_NAME"
echo "=" * 50

# Validation
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo ""
    echo "📝 Create .env file with:"
    echo "CLAUDE_API_KEY=your_claude_api_key_here"
    echo ""
    echo "🔑 Get your Claude API key from: https://console.anthropic.com/"
    exit 1
fi

if [ ! -f "$POLICY_FILE" ]; then
    echo "❌ Error: Policy file not found: $POLICY_FILE"
    echo ""
    echo "💡 Available policy files:"
    find data/ -name "*.docx" 2>/dev/null || echo "   No DOCX files found in data/"
    exit 1
fi

if [ ! -f "$QUESTIONNAIRE_FILE" ]; then
    echo "❌ Error: Questionnaire file not found: $QUESTIONNAIRE_FILE"
    echo ""
    echo "💡 Available CSV files:"
    find data/ -name "*.csv" 2>/dev/null || echo "   No CSV files found in data/"
    exit 1
fi

# Load environment and run
echo "🔑 Loading environment..."
source .env

if [ -z "$CLAUDE_API_KEY" ]; then
    echo "❌ Error: CLAUDE_API_KEY not found in .env!"
    exit 1
fi

echo "🤖 Running AI automation..."
echo ""

# Execute the automation
python3 scripts/complete_automation.py \
    --policy "$POLICY_FILE" \
    --questionnaire "$QUESTIONNAIRE_FILE" \
    --output-name "$OUTPUT_NAME" \
    --api-key "$CLAUDE_API_KEY"

echo ""
echo "🎉 Automation completed!"
echo "📄 Expected output: build/${OUTPUT_NAME}.docx (via GitHub Actions)"
