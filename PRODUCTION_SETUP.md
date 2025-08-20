# Production Environment Setup for Git Push

## Required Environment Variables

To enable git push functionality in production, set these environment variables:

### 1. GitHub Authentication

```bash
export GITHUB_TOKEN="your_github_personal_access_token"
```

**How to get GitHub token:**

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` permissions
3. Copy the token and set it as environment variable

### 2. Git Identity (Optional but Recommended)

```bash
export GIT_USER_NAME="Your Name"
export GIT_USER_EMAIL="your.email@example.com"
```

### 3. For Render/Heroku/Cloud Platforms:

**Render:**

1. Go to your service dashboard
2. Environment tab
3. Add these variables:
   - `GITHUB_TOKEN` = your_token_here
   - `GIT_USER_NAME` = Your Name
   - `GIT_USER_EMAIL` = your.email@example.com

**Heroku:**

```bash
heroku config:set GITHUB_TOKEN=your_token_here
heroku config:set GIT_USER_NAME="Your Name"
heroku config:set GIT_USER_EMAIL="your.email@example.com"
```

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

- **"does not appear to be a git repository"** → Set GITHUB_TOKEN
- **"authentication failed"** → Verify token permissions
- **"permission denied"** → Check repository access rights

## What Changed

✅ **FIXED:** Git push now works in production environments
✅ **ADDED:** Automatic token authentication setup
✅ **ADDED:** Detailed error messages with solutions
✅ **REMOVED:** Production environment skipping logic

The script will now attempt git push in all environments and provide helpful troubleshooting if it fails.
