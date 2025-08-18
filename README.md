# Policy Edit Automation (Lean Setup)

Automate policy editing with AI and generate a DOCX with tracked changes you can accept/reject in Word or LibreOffice.

## Overview

Flow at a glance:

```
[Policy DOCX]        [Questionnaire XLSX/CSV]
       \                 /
        \   (if XLSX)   /
         -> xlsx_to_csv_converter.py
                   |
                   v
          ai_policy_processor.py (Claude)
                   |
                   v
         edits/*.json (instructions + optional metadata: logo_path, logo_width_mm, logo_height_mm)
                   |
        (local) apply_tracked_edits_libre.py
                   |
                   v
     build/<output>.docx with tracked changes

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
- Calls Claude via `ai_policy_processor.py` to produce JSON instructions
- If provided, injects logo metadata (path/size) into the JSON
- Optionally triggers a GitHub Actions workflow to create the final DOCX
- Prints paths to the generated files

## Local mode (no CI)

If you prefer to generate the tracked DOCX locally with LibreOffice UNO:

```
/Applications/LibreOffice.app/Contents/Resources/python \
  scripts/apply_tracked_edits_libre.py \
  --in "data/v5 Freya POL-11 Access Control.docx" \
  --csv "edits/secfix_with_authors_edits.json" \
  --out "build/secfix_with_authors.docx" \
  --logo "data/company_logo.png" \
  --logo-width-mm 35 \
  --logo-height-mm 0 \
  --launch
```

Notes:

- `--csv` also accepts the JSON instructions format used here
- `--launch` starts a headless LibreOffice listener if needed
- To add a header logo, either pass CLI flags to the end‑to‑end script (or set .env):
  - LOGO_PATH, LOGO_WIDTH_MM, LOGO_HEIGHT_MM

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

## Tips

- For replacements, comments are attached to the deletion redline so Google Docs shows them as replies to the suggestion
- You can run local generation to iterate quickly, then switch to CI when you want artifacted outputs
