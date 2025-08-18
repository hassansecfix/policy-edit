#!/bin/bash
# Configuration defaults for Policy Automation Scripts
# Single source of truth for all default values

# Default file paths
DEFAULT_POLICY_FILE="data/v5 Freya POL-11 Access Control.docx"
DEFAULT_QUESTIONNAIRE_FILE="data/questionnaire_responses.csv"
DEFAULT_OUTPUT_NAME="policy_tracked_changes_with_comments"

# Function to show configuration being used
show_config() {
    echo "📋 Using configuration:"
    echo "  Policy: $POLICY_FILE"
    echo "  Questionnaire: $QUESTIONNAIRE_FILE"
    echo "  Output: $OUTPUT_NAME"
    echo ""
}

# Function to build logo arguments from environment
build_logo_args() {
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
}

# Function to build GitHub argument from environment
build_github_arg() {
    GITHUB_ARG=""
    if [ -n "${GITHUB_TOKEN}" ]; then
        GITHUB_ARG=" --github-token \"${GITHUB_TOKEN}\""
    fi
}
