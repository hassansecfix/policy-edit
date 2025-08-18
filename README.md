# Policy Edit Automation (Lean Setup)

Automate policy editing with AI and generate a DOCX with tracked changes you can accept/reject in Word or LibreOffice.

## Overview

Flow at a glance:

```
[Policy DOCX]        [Questionnaire XLSX/CSV]        [Logo Image]
       \                 /                                /
        \   (if XLSX)   /                                /
         -> xlsx_to_csv_converter.py                    /
                   |                                   /
                   v                                  /
          ai_policy_processor.py (Claude)            /
                   |                                /
                   v                               /
         edits/*.json (AI detects logo           /
         placeholders + generates operations)   /
                   |                           /
        (local) apply_tracked_edits_libre.py  /
         (uses logo metadata if provided) ----
                   |
                   v
     build/<output>.docx with tracked changes + logo replacements

           (optional GitHub Actions path)
                   |
                   v
               redline workflow
                   |
                   v
     build/<output>.docx from CI artifacts
```

- **Deletes and replaces** become real tracked changes.
- **Comments on replacements** are attached to the deletion half for better Google Docs threading.
- **Logo placeholders** are automatically detected by AI and replaced with your company logo.

## Quick start

1. Create `.env` with your Claude API key and optional configuration:

```bash
CLAUDE_API_KEY=your_key_here

# Optional: Customize file paths (single source of truth)
# POLICY_FILE=data/v5 Freya POL-11 Access Control.docx
# QUESTIONNAIRE_FILE=data/secfix_questionnaire_responses_consulting.csv
# OUTPUT_NAME=policy_tracked_changes_with_comments
```

2. Run the default automation:

```bash
./quick_automation.sh
```

This uses:

- Policy: `data/v5 Freya POL-11 Access Control.docx`
- Questionnaire: `data/secfix_questionnaire_responses_consulting.csv`
- Output name: `policy_tracked_changes_with_comments`

## Configuration (Single Source of Truth)

The system uses a priority-based configuration system:

1. **Command line arguments** (highest priority)
2. **Environment variables** in `.env` file
3. **Built-in defaults** (lowest priority)

### Environment Configuration

Set these in your `.env` file to customize defaults:

```bash
# File paths
POLICY_FILE=data/your_policy.docx
QUESTIONNAIRE_FILE=data/your_responses.csv
OUTPUT_NAME=custom_output_name

# Logo settings
LOGO_PATH=data/company_logo.png
LOGO_WIDTH_MM=35
LOGO_HEIGHT_MM=0
```

### Custom runs

- Use environment configuration:

```bash
./run_complete_automation.sh
```

- Override with command line arguments:

```bash
./run_custom_automation.sh <policy.docx> <questionnaire.{xlsx|csv}> <output_name>
```

- Mix approaches (CLI args override env vars):

```bash
# Set QUESTIONNAIRE_FILE in .env, but override policy via CLI
./run_custom_automation.sh data/different_policy.docx
```

## What the automation does

- Converts questionnaire to CSV only if you pass an `.xlsx` file
- Calls Claude via `ai_policy_processor.py` to:
  - Analyze the policy document for the `[ADD COMPANY LOGO]` placeholder in the header
  - Generate JSON operations for text replacements, deletions, and logo insertions
  - Include logo operations when logo is provided (URL or local file)
- If logo flags are provided, injects logo metadata into the JSON
- Optionally triggers a GitHub Actions workflow to create the final DOCX
- Prints paths to the generated files

## Scripts in this repo

- `scripts/complete_automation.py`: Orchestrates end-to-end flow (convert → AI → trigger CI)
- `scripts/ai_policy_processor.py`: Calls Claude to generate policy edit instructions (JSON)
- `scripts/xlsx_to_csv_converter.py`: Converts questionnaire XLSX → CSV when required
- `scripts/apply_tracked_edits_libre.py`: Applies edits with tracked changes (local or in CI)
- Runners: `quick_automation.sh`, `run_complete_automation.sh`, `run_custom_automation.sh`

## Current project structure

```
.
├── README.md
├── env.example                    # Configuration template
├── quick_automation.sh            # Fastest setup
├── run_complete_automation.sh     # Production automation
├── run_custom_automation.sh       # Flexible configuration
├── edits/
│   └── policy_tracked_changes_with_comments_edits.json
├── data/
│   ├── company_logo.png
│   ├── prompt.md
│   ├── questionnaire_responses.csv
│   ├── secfix_questionnaire_responses_consulting.csv
│   ├── updated_policy_instructions_v4.0.md
│   └── v5 Freya POL-11 Access Control.docx
├── scripts/
│   ├── ai_policy_processor.py
│   ├── apply_tracked_edits_libre.py
│   ├── complete_automation.py
│   └── xlsx_to_csv_converter.py
└── build/
```

## Requirements

- Python 3
- LibreOffice (for local generation and review)
- Claude API key in `.env` for AI generation
- Optional: GitHub Actions workflow in your remote repo if you use CI path

## Logo Setup

Configure logo insertion using the single source of truth (`.env` file):

1. **Place logo file** in the project (e.g., `data/company_logo.png`)
2. **Add logo configuration to `.env`**:
   ```bash
   # Logo settings (single source of truth)
   LOGO_PATH=data/company_logo.png
   LOGO_WIDTH_MM=35
   LOGO_HEIGHT_MM=0  # 0 = preserve aspect ratio
   ```
3. **Ensure your policy document** contains the `[ADD COMPANY LOGO]` placeholder in the header

### Logo Priority System

When you run automation, the system uses this priority order:

1. **Questionnaire URL**: Automatically extracts and downloads logo from questionnaire CSV
2. **Environment variable**: Uses `LOGO_PATH` from `.env` if questionnaire has no logo URL
3. **Default fallback**: Uses `data/company_logo.png` if neither above is available

Claude will:

- Detect the `[ADD COMPANY LOGO]` placeholder in your policy header
- Generate a `"replace_with_logo"` operation for the placeholder
- Apply the logo using the priority system above
- Add tracking comments for the logo replacement

## Tips

- **Configuration**: Use `.env` file as your single source of truth for all settings
- **Flexibility**: Command line arguments can override any environment variable when needed
- **Comments**: For replacements, comments are attached to the deletion redline so Google Docs shows them as replies to the suggestion
- **Iteration**: You can run local generation to iterate quickly, then switch to CI when you want artifacted outputs
- **Logo detection**: Automatic - the system detects `[ADD COMPANY LOGO]` and uses the configured logo source
