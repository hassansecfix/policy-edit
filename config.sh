#!/bin/bash
# Configuration defaults for Policy Automation Scripts
# Single source of truth for all default values

# Default file paths
DEFAULT_POLICY_FILE="data/v5 Freya POL-11 Access Control.docx"
DEFAULT_OUTPUT_NAME="policy_tracked_changes_with_comments"
DEFAULT_POLICY_INSTRUCTIONS="data/updated_policy_instructions_v4.2.md"
# To change policy instructions version, update the path above
# Available versions: v4.0, v4.1, v4.2, v5.0_context_aware
# NOTE: Questionnaire data now comes from localStorage only - no file needed

# Function to show configuration being used
show_config() {
    echo "📋 Using configuration:"
    echo "  Policy: $POLICY_FILE"
    echo "  Policy Instructions: $DEFAULT_POLICY_INSTRUCTIONS"
    echo "  Questionnaire: localStorage data only (no file)"
    echo "  Output: $OUTPUT_NAME"
    echo ""
}

# Function to build logo arguments from environment
build_logo_args() {
    LOGO_ARGS=""
    if [ -n "${LOGO_PATH}" ]; then
        LOGO_ARGS+=" --logo \"${LOGO_PATH}\""
    fi
}

# Function to build GitHub argument from environment
build_github_arg() {
    GITHUB_ARG=""
    if [ -n "${GITHUB_TOKEN}" ]; then
        GITHUB_ARG=" --github-token \"${GITHUB_TOKEN}\""
    fi
}
