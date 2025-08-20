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

## Interactive Questionnaire Flow

The system now includes an interactive web-based questionnaire that collects user responses before automation:

### New Flow:

1. **User accesses the web interface**
2. **Interactive questionnaire appears** - 20 questions asked one by one
3. **User answers are collected and validated**
4. **Responses are saved** as `data/user_questionnaire_responses.csv`
5. **Automation proceeds** using the user's responses instead of pre-filled data

### Question Types Supported:

- **Text input** - Company name, address, etc.
- **Radio buttons** - Yes/No questions, policy choices
- **Dropdown menus** - Tool selections, timeframes, approvers
- **Number input** - Employee count, contractor count
- **Email/User selector** - Policy owners, approvers
- **Date picker** - Effective dates
- **File upload** - Company logos

### Key Features:

- **Progress tracking** with visual progress bar
- **Validation** - ensures all questions are answered before proceeding
- **Navigation** - Previous/Next buttons for easy movement
- **Auto-save** - Responses are saved when questionnaire is completed
- **Smart fallback** - System uses user responses if available, falls back to default questionnaire if not

### Files Added:

- `data/questions.csv` - Question definitions extracted from original questionnaire
- `web_app/src/components/Questionnaire.tsx` - Main questionnaire component
- `web_app/src/components/QuestionInput.tsx` - Individual question input handlers
- `web_app/src/app/api/questions/route.ts` - API endpoint to serve questions
- `web_app/src/app/api/answers/route.ts` - API endpoint to save user responses

## Quick start

1. Set up your environment variables by copying the template:

```bash
cp env.example .env
# Edit .env and add your required variables
```

**Required for all environments:**

- `CLAUDE_API_KEY` - Your Anthropic Claude API key

**Required for production deployment (Render, Railway, etc.):**

- `GITHUB_TOKEN` - Your GitHub personal access token (for git push)
- `GITHUB_REPO_OWNER` - Your GitHub username
- `GITHUB_REPO_NAME` - Your repository name
- `GIT_USER_NAME` - Your full name for git commits
- `GIT_USER_EMAIL` - Your email for git commits

See `env.example` for complete details and optional configuration.

📋 **For detailed production setup instructions, see [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md)**

2. Run the default automation:

```bash
./quick_automation.sh
```

This uses:

- Policy: `data/v5 Freya POL-11 Access Control.docx`
- Questionnaire: `data/questionnaire_responses.csv`
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

## Web UI Dashboard

The project now includes a modern Next.js dashboard for monitoring and controlling the automation process.

### Quick Start

**🚀 Easy Way - Start Everything at Once:**

```bash
./start_app.sh
```

This script automatically starts both the Flask API backend and Next.js frontend, then opens your browser to http://localhost:3000

**☁️ Deploy to Production:**

```bash
./deploy.sh https://your-flask-api-url
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guide.

### 🔄 Multi-User Support

The system now supports **multiple users running automation simultaneously** without conflicts:

**🔑 Automatic User Isolation:**

- Each automation run gets a unique user ID (e.g., `user-1703123456-7890`)
- All generated files are prefixed with this ID to prevent conflicts
- GitHub Actions artifacts are uniquely named per run

**📋 User ID Examples:**

```bash
# Auto-generated ID (default)
./quick_automation.sh
# Output: User ID: user-1703123456-7890

# Custom ID for easy tracking
USER_ID="alice-policy-v1" ./quick_automation.sh
# Output: User ID: alice-policy-v1
```

**📄 Generated Files with User Isolation:**

```
data/user-123_acme_questionnaire.csv
data/user-123_company_logo.png
edits/user-123_acme_edits.json
build/user-123_acme.docx (via GitHub Actions)
```

**🏷️ GitHub Actions Artifacts:**

```
Artifact Name: redlined-docx-789123-45
Contains: build/user-123_acme.docx
```

This ensures that multiple users can run the automation simultaneously without overwriting each other's work.

**📖 Manual Way - Individual Services:**

1. **Start the Flask API backend:**

   ```bash
   cd web_ui
   source venv/bin/activate  # or create venv if needed
   pip install -r requirements.txt
   python3 app.py
   ```

   API runs on http://localhost:5001

2. **Start the Next.js frontend:**
   ```bash
   cd web_app
   npm install  # first time only
   npm run dev
   ```
   Dashboard runs on http://localhost:3000

### Features

- Real-time automation monitoring with WebSocket connections
- Live progress tracking and log streaming
- Modern TypeScript + Tailwind CSS interface
- File download management
- Configuration status checking

### Troubleshooting

**Common Issues:**

1. **"command not found: python"**

   - Use `python3` instead of `python` on macOS
   - Make sure you're in the `web_ui` directory and virtual environment is activated

2. **"Port 5000 is in use"**

   - This is usually macOS AirPlay Receiver
   - The app is configured to use port 5001 instead
   - Disable AirPlay Receiver in System Preferences if needed

3. **CORS errors in browser**

   - Make sure Flask backend is running on port 5001
   - Check that both services are running before accessing the dashboard

4. **Logo not appearing in GitHub Actions output** _(Fixed in latest version)_

   - **Issue**: Previously, user-uploaded logos were created locally but not committed to git
   - **Fix**: The automation now commits both JSON edits AND logo files together
   - **What happens**: When you upload a logo via questionnaire, it's extracted from base64 data, saved as `data/{user-id}_company_logo.png`, and automatically committed with the JSON instructions
   - **Verification**: Check your git history to see both files committed together after running automation

5. **Multi-user conflicts in GitHub Actions** _(Fixed in latest version)_

   - **Issue**: Multiple users running automation simultaneously could overwrite each other's files and artifacts
   - **Fix**: Comprehensive user isolation system implemented
   - **Features**:
     - **Unique User IDs**: Auto-generated timestamp-based IDs (e.g., `user-1703123456-7890`)
     - **Isolated File Names**: All files prefixed with user ID (e.g., `user-123_policy_edits.json`, `user-123_company_logo.png`)
     - **Unique Artifacts**: GitHub Actions artifacts named `redlined-docx-{run_id}-{run_number}`
     - **Isolated Output**: Final DOCX files named `build/{user_id}_{output_name}.docx`
   - **Manual Override**: Set `USER_ID` environment variable for custom identification
   - **Tracking**: Each run displays its User ID for easy identification of results

6. **Git sync issues and "CSV/JSON missing" workflow errors** _(Fixed in latest version)_

   - **Issue**: Production environments experienced git push failures and workflow failures due to timing/sync issues
   - **Root Cause**:
     - Git repository becoming out of sync with remote (causing push failures)
     - Files not immediately available on GitHub after push (causing workflow failures)
   - **Fix**: Enhanced git synchronization and file verification
   - **Features**:
     - **Automatic Sync**: Pulls latest changes before pushing to prevent conflicts
     - **Rebase Recovery**: Automatically attempts `git pull --rebase` if standard push fails
     - **File Verification**: Waits up to 30 seconds to verify files exist on GitHub before triggering workflow
     - **Detailed Error Messages**: Specific troubleshooting steps for different git failure scenarios
   - **Manual Recovery**: Use `fix_git_sync.sh` script for manual intervention when needed
   - **Prevention**: Ensures single automation process per repository to avoid conflicts

7. **"Failed to fetch" errors**
   - Ensure Flask backend is running: `curl http://localhost:5001/api/status`
   - Check that virtual environment is activated in Flask terminal

## Current project structure

```
.
├── README.md
├── start_app.sh                   # Start both Flask API and Next.js frontend
├── config.sh                      # Shared configuration defaults (DRY)
├── env.example                    # Configuration template
├── quick_automation.sh            # Fastest setup
├── run_complete_automation.sh     # Production automation
├── run_custom_automation.sh       # Flexible configuration
├── web_ui/                        # Flask API backend
│   ├── app.py
│   ├── requirements.txt
│   └── README.md
├── web_app/                       # Next.js frontend
│   ├── src/
│   ├── package.json
│   └── next.config.ts
├── edits/
│   └── policy_tracked_changes_with_comments_edits.json
├── data/
│   ├── company_logo.png
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

- **Python 3** - For running automation scripts
- **LibreOffice** - For local generation and review
- **Environment Variables** - Set up in `.env` file (see `env.example`):
  - `CLAUDE_API_KEY` - Required for AI generation
  - For production: `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`, `GIT_USER_NAME`, `GIT_USER_EMAIL`
- **Optional:** GitHub Actions workflow in your remote repo if you use CI path

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
