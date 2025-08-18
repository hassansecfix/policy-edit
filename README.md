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

1. Create `.env` with your Claude API key:

```
CLAUDE_API_KEY=your_key_here
```

2. Run the default automation:

```
./quick_automation.sh
```

This uses:

- Policy: `data/v5 Freya POL-11 Access Control.docx`
- Questionnaire: `data/questionnaire_responses.csv`
- Output name: `policy_tracked_changes_with_comments`

## Custom runs

- Same defaults, but explicit script:

```
./run_complete_automation.sh
```

- Custom files and output name:

```
./run_custom_automation.sh <policy.docx> <questionnaire.{xlsx|csv}> <output_name>
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
├── quick_automation.sh
├── run_complete_automation.sh
├── run_custom_automation.sh
├── edits/
│   └── secfix_with_authors_edits.json
├── data/
│   ├── prompt.md
│   ├── questionnaire_responses.csv
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

To add your company logo:

1. **Place logo file** in the project (e.g., `data/company_logo.png`)
2. **Set environment variables** in `.env`:
   ```
   LOGO_PATH=data/company_logo.png
   LOGO_WIDTH_MM=35
   LOGO_HEIGHT_MM=0  # 0 = preserve aspect ratio
   ```
3. **Ensure your policy document** contains the `[ADD COMPANY LOGO]` placeholder in the header

When you run automation, Claude will:

- Detect the `[ADD COMPANY LOGO]` placeholder in your policy header
- Generate a `"replace_with_logo"` operation for the placeholder
- System automatically:
  1. First tries to use logo URL from questionnaire (downloads it)
  2. Falls back to local logo file (`data/company_logo.png`) if URL fails
  3. Replaces the placeholder with your logo image + adds comments

## Tips

- For replacements, comments are attached to the deletion redline so Google Docs shows them as replies to the suggestion
- You can run local generation to iterate quickly, then switch to CI when you want artifacted outputs
- Logo detection is automatic - the system detects `[ADD COMPANY LOGO]` and uses your local logo file
