
# GitHub Actions Workflow Instructions

## Setup
1. Push this entire project to a GitHub repository
2. Ensure your files are in the correct locations:
   - Input DOCX: docs/test_input.docx
   - Edits CSV: edits/edits_sample.csv

## Running the Workflow
1. Go to your repository on GitHub
2. Click the "Actions" tab
3. Find "Redline DOCX (LibreOffice headless)" workflow
4. Click "Run workflow"
5. Fill in the parameters:
   - Input DOCX path: docs/test_input.docx
   - Edits CSV path: edits/edits_sample.csv
   - Output DOCX path: build/output_with_tracked_changes.docx
6. Click "Run workflow"

## Download Results
1. Wait for the workflow to complete (usually 1-2 minutes)
2. Click on the completed workflow run
3. Download the "redlined-docx" artifact
4. Extract and open the DOCX file

## Why This Works
- GitHub Actions runs on Ubuntu Linux
- LibreOffice Python UNO works reliably on Linux
- No local setup issues to worry about
