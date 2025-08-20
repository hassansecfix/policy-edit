# Production Environment Setup for Git Push

## Required Environment Variables

To enable git push functionality in production, set these environment variables:

### 1. GitHub Repository Info (Required for Auto-Configuration)

```bash
export GITHUB_REPO_OWNER="your_github_username"
export GITHUB_REPO_NAME="your_repository_name"
```

### 2. GitHub Authentication

```bash
export GITHUB_TOKEN="your_github_personal_access_token"
```

**How to get GitHub token:**

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` permissions
3. Copy the token and set it as environment variable

### 3. Git Identity (Optional but Recommended)

```bash
export GIT_USER_NAME="Your Name"
export GIT_USER_EMAIL="your.email@example.com"
```

### 4. For Render/Heroku/Cloud Platforms:

**Render:**

1. Go to your service dashboard
2. Environment tab
3. Add these variables:
   - `GITHUB_REPO_OWNER` = your_github_username
   - `GITHUB_REPO_NAME` = your_repository_name
   - `GITHUB_TOKEN` = your_token_here
   - `GIT_USER_NAME` = Your Name
   - `GIT_USER_EMAIL` = your.email@example.com

**Heroku:**

```bash
heroku config:set GITHUB_REPO_OWNER=your_github_username
heroku config:set GITHUB_REPO_NAME=your_repository_name
heroku config:set GITHUB_TOKEN=your_token_here
heroku config:set GIT_USER_NAME="Your Name"
heroku config:set GIT_USER_EMAIL="your.email@example.com"
```

## What The Script Auto-Configures

✅ **Git Remote:** Automatically adds `origin` remote using `GITHUB_REPO_OWNER/GITHUB_REPO_NAME`
✅ **Authentication:** Sets up token-based authentication using `GITHUB_TOKEN`
✅ **Git Identity:** Configures user name/email from environment variables

## Testing the Setup

Run this to test if git push will work:

```bash
python3 scripts/complete_automation.py \
  --policy data/policy.docx \
  --questionnaire data/questionnaire.xlsx \
  --output-name "test_policy" \
  --skip-api
```

## Troubleshooting

If you see authentication errors, the script will now provide specific solutions:

- **"Git remote 'origin' not configured"** → Set GITHUB_REPO_OWNER and GITHUB_REPO_NAME
- **"authentication failed"** → Verify GITHUB_TOKEN permissions
- **"permission denied"** → Check repository access rights

## What Changed

✅ **FIXED:** Git push now works in production environments
✅ **ADDED:** Automatic git remote configuration using environment variables
✅ **ADDED:** Automatic token authentication setup
✅ **ADDED:** Detailed error messages with solutions
✅ **REMOVED:** Production environment skipping logic

The script will now automatically configure git and attempt push in all environments!
