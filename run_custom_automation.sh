#!/bin/bash
# Customizable Complete AI Automation Script
# Modify the variables below or pass arguments to customize the run

set -e  # Exit on any error

# Load shared configuration (single source of truth)
source "$(dirname "$0")/config.sh"

# Custom default for this script (adds timestamp)
DEFAULT_OUTPUT_NAME_WITH_TIMESTAMP="${DEFAULT_OUTPUT_NAME}_$(date +%Y%m%d_%H%M%S)"

# Help function
show_help() {
    echo "Usage: $0 [policy_file] [questionnaire_file] [output_name]"
    echo ""
    echo "Configuration (single source of truth):"
    echo "  1. Set in .env file: POLICY_FILE, QUESTIONNAIRE_FILE, OUTPUT_NAME"
    echo "  2. Or pass as command line arguments (overrides .env)"
    echo "  3. Or use defaults if neither is set"
    echo ""
    echo "Arguments:"
    echo "  policy_file        Path to policy DOCX (overrides POLICY_FILE in .env)"
    echo "  questionnaire_file Path to questionnaire CSV (overrides QUESTIONNAIRE_FILE in .env)"
    echo "  output_name        Output name prefix (overrides OUTPUT_NAME in .env)"
    echo ""
    echo "Examples:"
    echo "  $0                                          # Use .env or defaults"
    echo "  $0 data/my_policy.docx                     # Override policy only"
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

# Validation - check .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo ""
    echo "📝 Create .env file with:"
    echo "CLAUDE_API_KEY=your_claude_api_key_here"
    echo ""
    echo "🔑 Get your Claude API key from: https://console.anthropic.com/"
    exit 1
fi

# Load environment variables and set configuration (single source of truth)
echo "🔑 Loading environment..."
source .env

if [ -z "$CLAUDE_API_KEY" ]; then
    echo "❌ Error: CLAUDE_API_KEY not found in .env!"
    exit 1
fi

# Configuration priority: 1) Command line args, 2) Environment variables, 3) Defaults
POLICY_FILE="${1:-${POLICY_FILE:-$DEFAULT_POLICY_FILE}}"
QUESTIONNAIRE_FILE="${2:-${QUESTIONNAIRE_FILE:-$DEFAULT_QUESTIONNAIRE_FILE}}"
OUTPUT_NAME="${3:-${OUTPUT_NAME:-$DEFAULT_OUTPUT_NAME_WITH_TIMESTAMP}}"

echo "🚀 Complete AI Automation (Customizable)"
echo "=" * 50
show_config
echo "=" * 50

# Validation - check files exist
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

echo "🤖 Running AI automation..."
echo ""

# Build optional arguments from environment
build_logo_args
build_github_arg

# Execute the automation (passing questionnaire to both automation and libre scripts)
eval "python3 scripts/complete_automation.py \
    --policy \"$POLICY_FILE\" \
    --questionnaire \"$QUESTIONNAIRE_FILE\" \
    --output-name \"$OUTPUT_NAME\" \
    --api-key \"$CLAUDE_API_KEY\"${LOGO_ARGS}${GITHUB_ARG}"

echo ""
echo "🎉 Automation completed!"
echo "📄 Expected output: build/${OUTPUT_NAME}.docx (via GitHub Actions)"
