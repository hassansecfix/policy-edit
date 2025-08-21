#!/usr/bin/env python3
"""
Complete Policy Automation - End-to-End Flow

This script provides complete automation from questionnaire to final DOCX with tracked changes:
1. Converts Excel questionnaire to CSV
2. Calls Claude Sonnet 4 to generate edits CSV
3. Triggers GitHub Actions to create tracked changes DOCX
4. Downloads the result

Usage:
    python3 complete_automation.py \
        --policy data/policy.docx \
        --questionnaire data/questionnaire.xlsx \
        --output-name "customized_policy" \
        --api-key YOUR_CLAUDE_API_KEY

Environment Variables:
    CLAUDE_API_KEY: Your Anthropic Claude API key
    GITHUB_TOKEN: Your GitHub token (optional, for auto-triggering)
"""

import os
import sys
import argparse
import subprocess
import time
import json
import base64
from pathlib import Path
import requests

# Import our other scripts
sys.path.append(str(Path(__file__).parent))

def run_command(cmd, description):
    """Run a shell command and handle errors."""
    print(f"🔄 {description}...")
    
    # For AI processing commands, show real-time output to see base64 filtering logs
    if 'ai_policy_processor.py' in cmd:
        try:
            # Use real-time output for AI processing to show filtering logs
            result = subprocess.run(cmd, shell=True, text=True)
            if result.returncode != 0:
                print(f"❌ {description} failed with exit code {result.returncode}!")
                print(f"Command was: {cmd}")
                return False, f"Command failed with exit code {result.returncode}"
            print(f"✅ {description} completed")
            return True, ""
        except Exception as e:
            print(f"❌ {description} failed with exception: {e}")
            return False, str(e)
    else:
        # Use captured output for other commands
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ {description} failed!")
            error_msg = result.stderr.strip() if result.stderr.strip() else result.stdout.strip()
            if not error_msg:
                error_msg = f"Command failed with exit code {result.returncode} but no error message"
            print(f"Error: {error_msg}")
            print(f"Command was: {cmd}")
            return False, error_msg
        
        print(f"✅ {description} completed")
        return True, result.stdout

def convert_xlsx_to_csv(xlsx_path, csv_path):
    """Convert Excel questionnaire to CSV."""
    cmd = f"python3 scripts/xlsx_to_csv_converter.py '{xlsx_path}' '{csv_path}'"
    return run_command(cmd, "Converting Excel to CSV")

def generate_edits_with_ai(policy_path, questionnaire_csv, prompt_path, policy_instructions_path, output_json, api_key, skip_api=False, questionnaire_json=None):
    """Generate JSON instructions using AI or use existing file."""
    
    temp_json_file = None
    
    try:
        # Determine questionnaire parameter based on input type
        if questionnaire_json:
            # Check if we can use environment variable approach (production-friendly)
            env_data = os.environ.get('QUESTIONNAIRE_ANSWERS_DATA')
            if env_data and len(questionnaire_json) == len(env_data):
                # Use environment variable approach - no temp files needed!
                questionnaire_param = f"--questionnaire-env-data"
                print("🧠 Step 2: Using environment variable questionnaire data (production mode)...")
            else:
                # Fallback to temp file approach 
                import tempfile
                import json
                
                temp_json_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                json.dump(json.loads(questionnaire_json), temp_json_file, indent=2)
                temp_json_file.close()
                
                questionnaire_param = f"--questionnaire '{temp_json_file.name}'"
                print("🧠 Step 2: Using temp file questionnaire data (fallback mode)...")
                print(f"📁 Temp JSON file: {temp_json_file.name}")
        else:
            # Use file path (legacy approach)
            questionnaire_param = f"--questionnaire '{questionnaire_csv}'"
            print("🧠 Step 2: Using questionnaire file (legacy mode)...")
        
        if skip_api:
            print("🔄 API call skipped for testing/development...")
            cmd = f"""python3 scripts/ai_policy_processor.py \
                --policy '{policy_path}' \
                {questionnaire_param} \
                --prompt '{prompt_path}' \
                --policy-instructions '{policy_instructions_path}' \
                --output '{output_json}' \
                --skip-api"""
        else:
            print("🧠 Generating JSON instructions with Claude Sonnet 4...")
            cmd = f"""python3 scripts/ai_policy_processor.py \
                --policy '{policy_path}' \
                {questionnaire_param} \
                --prompt '{prompt_path}' \
                --policy-instructions '{policy_instructions_path}' \
                --output '{output_json}' \
                --api-key '{api_key}'"""
        
        result = run_command(cmd, "Processing JSON instructions")
        
        return result
        
    finally:
        # Clean up temporary file
        if temp_json_file and os.path.exists(temp_json_file.name):
            try:
                os.unlink(temp_json_file.name)
                print(f"🗑️  Cleaned up temp file: {temp_json_file.name}")
            except Exception as e:
                print(f"⚠️  Warning: Could not clean up temp file {temp_json_file.name}: {e}")

def commit_and_push_json(edits_json, logo_file=None):
    """Commit and push the generated JSON file and optional logo file to GitHub."""
    try:
        # Debug environment information
        print(f"🔧 Environment Debug Info:")
        print(f"   Working Directory: {os.getcwd()}")
        print(f"   JSON File Path: {edits_json}")
        print(f"   JSON File Absolute Path: {os.path.abspath(edits_json)}")
        
        # Check if we're in the right directory
        expected_files = ['data', 'edits', 'scripts', '.git']
        missing_dirs = [d for d in expected_files if not os.path.exists(d)]
        if missing_dirs:
            print(f"⚠️  Missing expected directories: {missing_dirs}")
            print(f"📁 Current directory contents: {os.listdir('.')}")
        else:
            print(f"✅ All expected directories present")
        
        # Ensure we have a git repository
        if not os.path.exists('.git'):
            return False, "No git repository found - .git directory missing"
        
        # Ensure git remote origin exists and get the URL
        remote_check = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                    capture_output=True, text=True)
        if remote_check.returncode != 0:
            # Try to auto-configure remote using environment variables
            repo_owner = os.environ.get('GITHUB_REPO_OWNER')
            repo_name = os.environ.get('GITHUB_REPO_NAME')
            
            if repo_owner and repo_name:
                repo_url = f"https://github.com/{repo_owner}/{repo_name}.git"
                print(f"🔧 Auto-configuring git remote: {repo_url}")
                
                # Add the remote
                add_remote_result = subprocess.run(['git', 'remote', 'add', 'origin', repo_url], 
                                                 capture_output=True, text=True)
                if add_remote_result.returncode != 0:
                    return False, f"Failed to add git remote: {add_remote_result.stderr}"
                
                print(f"✅ Git remote 'origin' configured automatically")
                remote_url = repo_url
            else:
                return False, "Git remote 'origin' not configured and GITHUB_REPO_OWNER/GITHUB_REPO_NAME not set"
        else:
            remote_url = remote_check.stdout.strip()
        
        print(f"🔗 Git remote URL: {remote_url}")
        
        # Set up authentication for production environments
        github_token = os.environ.get('GITHUB_TOKEN')
        if github_token and 'https://github.com/' in remote_url:
            # Configure git to use token authentication for HTTPS
            repo_url_with_token = remote_url.replace('https://github.com/', f'https://{github_token}@github.com/')
            subprocess.run(['git', 'remote', 'set-url', 'origin', repo_url_with_token], capture_output=True)
            print("🔐 Configured git authentication using GITHUB_TOKEN")
        elif not github_token and 'https://github.com/' in remote_url:
            print("⚠️  GITHUB_TOKEN not set - authentication may fail in production")
            print("💡 Set GITHUB_TOKEN environment variable for production git push")
        
        # Configure git identity if environment variables are set
        git_user_name = os.environ.get('GIT_USER_NAME')
        git_user_email = os.environ.get('GIT_USER_EMAIL')
        
        if git_user_name and git_user_email:
            subprocess.run(['git', 'config', 'user.name', git_user_name], capture_output=True)
            subprocess.run(['git', 'config', 'user.email', git_user_email], capture_output=True)
            print(f"✅ Git identity configured: {git_user_name} <{git_user_email}>")
        
        # CRITICAL: Check if we're in detached HEAD state BEFORE committing
        print("🔍 Checking repository state before committing...")
        status_check = subprocess.run(['git', 'status'], capture_output=True, text=True)
        if status_check.returncode == 0 and "HEAD detached" in status_check.stdout:
            print("🚨 Repository is in detached HEAD state - fixing before commit...")
            
            # Try to checkout main branch
            checkout_main = subprocess.run(['git', 'checkout', 'main'], capture_output=True, text=True)
            if checkout_main.returncode == 0:
                print("✅ Successfully switched to main branch")
            else:
                print(f"⚠️  Could not checkout main: {checkout_main.stderr}")
                # Try to create main branch if it doesn't exist
                create_main = subprocess.run(['git', 'checkout', '-b', 'main'], capture_output=True, text=True)
                if create_main.returncode == 0:
                    print("✅ Created and switched to main branch")
                else:
                    print(f"❌ Could not create main branch: {create_main.stderr}")
                    return False, "Cannot fix detached HEAD state - unable to checkout or create main branch"
        else:
            print("✅ Repository is in proper branch state")
        
        # Verify JSON file exists before adding
        if not os.path.exists(edits_json):
            return False, f"JSON file does not exist: {edits_json}"
        
        print(f"📁 Verified JSON file exists: {edits_json}")
        print(f"📊 File size: {os.path.getsize(edits_json)} bytes")
        
        # Add the JSON file
        print(f"📝 Adding JSON file to git: {edits_json}")
        result = subprocess.run(['git', 'add', edits_json], capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"Failed to add JSON: {result.stderr}"
        
        # Verify the file was actually added to git
        status_result = subprocess.run(['git', 'status', '--porcelain', edits_json], capture_output=True, text=True)
        if status_result.returncode == 0 and status_result.stdout.strip():
            print(f"✅ JSON file staged for commit: {edits_json}")
        else:
            return False, f"JSON file was not properly staged. Git status: {status_result.stdout}"
        
        # Add the logo file if it exists and was created
        files_to_commit = [edits_json]
        if logo_file and os.path.exists(logo_file):
            print(f"🖼️  Adding logo file to git: {logo_file}")
            result = subprocess.run(['git', 'add', logo_file], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"⚠️  Warning: Failed to add logo file {logo_file}: {result.stderr}")
            else:
                # Verify logo file was staged
                logo_status = subprocess.run(['git', 'status', '--porcelain', logo_file], capture_output=True, text=True)
                if logo_status.returncode == 0 and logo_status.stdout.strip():
                    print(f"✅ Logo file staged for commit: {logo_file}")
                    files_to_commit.append(logo_file)
                else:
                    print(f"⚠️  Logo file was not properly staged")
        
        # Check if there are actually files to commit
        staged_files = subprocess.run(['git', 'diff', '--cached', '--name-only'], capture_output=True, text=True)
        if staged_files.returncode == 0:
            staged_list = staged_files.stdout.strip().split('\n') if staged_files.stdout.strip() else []
            print(f"📋 Files staged for commit: {staged_list}")
            
            if not staged_list:
                print("⚠️  No files are staged for commit")
                # Check if files are already committed
                for file_path in files_to_commit:
                    untracked = subprocess.run(['git', 'ls-files', '--error-unmatch', file_path], capture_output=True, text=True)
                    if untracked.returncode == 0:
                        print(f"✅ File already tracked in git: {file_path}")
                    else:
                        return False, f"File not staged and not tracked: {file_path}"
                return True, "Files already committed to git"
        
        # Commit the files
        commit_msg = f"Add AI-generated files: {', '.join(files_to_commit)}"
        print(f"💾 Committing files with message: {commit_msg}")
        result = subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True)
        if result.returncode != 0:
            # Check both stdout and stderr for "nothing to commit"
            output = result.stdout + result.stderr
            if "nothing to commit" in output.lower():
                print("✅ No changes to commit (files already committed)")
                return True, "No changes to commit"
            return False, f"Failed to commit files. Stdout: {result.stdout}. Stderr: {result.stderr}"
        
        print(f"✅ Successfully committed files")
        
        # Verify the commit was successful
        verify_commit = subprocess.run(['git', 'log', '--oneline', '-1'], capture_output=True, text=True)
        if verify_commit.returncode == 0:
            print(f"🔍 Latest commit: {verify_commit.stdout.strip()}")
        else:
            print("⚠️  Could not verify latest commit")
        
        # Push to GitHub with explicit remote and branch
        # First, try to get the current branch name
        branch_result = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True)
        current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 and branch_result.stdout.strip() else None
        
        # Fallback for older Git versions
        if not current_branch:
            branch_result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True)
            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 and branch_result.stdout.strip() else 'main'
        
        # Final validation
        if not current_branch or current_branch == 'HEAD':
            print("⚠️  Could not determine current branch, using 'main'")
            current_branch = 'main'
        
        print(f"🔄 Pushing to branch: {current_branch}")
        
        # First, try to pull latest changes to avoid conflicts
        print("⬇️  Pulling latest changes from remote...")
        pull_result = subprocess.run(['git', 'pull', 'origin', current_branch], capture_output=True, text=True)
        if pull_result.returncode != 0:
            print(f"⚠️  Pull failed or not needed: {pull_result.stderr.strip()}")
            # Continue anyway - might be first push or empty repo
        else:
            print("✅ Successfully pulled latest changes")
        
        # Try pushing with explicit origin and branch
        result = subprocess.run(['git', 'push', 'origin', current_branch], capture_output=True, text=True)
        if result.returncode != 0:
            # Check if it's the "fetch first" error - try pulling and pushing again
            if 'fetch first' in result.stderr or 'rejected' in result.stderr:
                print(f"🔄 Push rejected, trying pull with rebase...")
                
                # Try pull with rebase to handle conflicts
                rebase_result = subprocess.run(['git', 'pull', '--rebase', 'origin', current_branch], capture_output=True, text=True)
                if rebase_result.returncode == 0:
                    print("✅ Successfully rebased local changes")
                    # Try push again
                    retry_result = subprocess.run(['git', 'push', 'origin', current_branch], capture_output=True, text=True)
                    if retry_result.returncode == 0:
                        print(f"✅ Successfully pushed after rebase to origin/{current_branch}")
                        committed_files = "JSON and logo files" if logo_file else "JSON file"
                        print(f"✅ {committed_files} committed and pushed to GitHub")
                        return True, f"{committed_files} pushed successfully"
                    else:
                        print(f"❌ Push still failed after rebase: {retry_result.stderr.strip()}")
                else:
                    print(f"❌ Rebase failed: {rebase_result.stderr.strip()}")
            
            # Fallback: try setting upstream and pushing
            print(f"⚠️  Initial push failed, trying to set upstream...")
            print(f"    Error: {result.stderr.strip()}")
            
            # Try with upstream flag
            upstream_result = subprocess.run(['git', 'push', '--set-upstream', 'origin', current_branch], capture_output=True, text=True)
            if upstream_result.returncode != 0:
                # Provide detailed error information for troubleshooting
                error_msg = upstream_result.stderr.strip() or result.stderr.strip()
                print(f"\n🔴 Git Push Failed - Troubleshooting Info:")
                print(f"   Remote URL: {remote_url}")
                print(f"   Branch: {current_branch}")
                print(f"   Error: {error_msg}")
                
                # Suggest solutions based on error type
                if 'fetch first' in error_msg.lower() or 'rejected' in error_msg.lower():
                    print(f"\n💡 Solutions for git sync issues:")
                    print(f"   1. Repository is out of sync - run: git pull origin main")
                    print(f"   2. Force sync: git fetch origin && git reset --hard origin/main")
                    print(f"   3. Manual commit: git add . && git commit -m 'Manual sync' && git push")
                    print(f"   4. Check for multiple processes modifying the repo simultaneously")
                elif 'does not appear to be a git repository' in error_msg.lower():
                    print(f"\n💡 Solutions:")
                    print(f"   1. Set GITHUB_TOKEN environment variable")
                    print(f"   2. Verify remote URL: git remote get-url origin")
                    print(f"   3. Check repository permissions")
                elif 'authentication failed' in error_msg.lower():
                    print(f"\n💡 Solutions:")
                    print(f"   1. Set GITHUB_TOKEN environment variable")
                    print(f"   2. Verify token has push permissions")
                elif 'permission denied' in error_msg.lower():
                    print(f"\n💡 Solutions:")
                    print(f"   1. Verify GITHUB_TOKEN has push access")
                    print(f"   2. Check repository permissions")
                
                return False, f"Failed to push to git: {error_msg}"
            else:
                print(f"✅ Set upstream branch and pushed to origin/{current_branch}")
        else:
            print(f"✅ Pushed to origin/{current_branch}")
        
        # CRITICAL: Verify the push actually worked by checking remote status
        print("🔍 Verifying push was successful...")
        
        # Check if local and remote are in sync
        fetch_result = subprocess.run(['git', 'fetch', 'origin'], capture_output=True, text=True)
        if fetch_result.returncode == 0:
            print("✅ Fetched latest remote state")
        else:
            print(f"⚠️  Fetch failed: {fetch_result.stderr}")
        
        # Check git status to see if we're ahead/behind remote
        status_result = subprocess.run(['git', 'status', '-uno'], capture_output=True, text=True)
        if status_result.returncode == 0:
            status_output = status_result.stdout
            print(f"📊 Git status after push:")
            print(f"   {status_output.strip()}")
            
            # CRITICAL: Check for detached HEAD state
            if "HEAD detached" in status_output:
                print("🚨 CRITICAL ISSUE: Repository is in detached HEAD state!")
                print("   This means commits are not attached to any branch and won't be pushed.")
                print("   Attempting to fix by switching to main branch...")
                
                # Get the current commit hash
                commit_hash_result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True)
                if commit_hash_result.returncode == 0:
                    current_commit = commit_hash_result.stdout.strip()
                    print(f"   Current commit: {current_commit}")
                    
                    # Try to switch to main branch and cherry-pick the commit
                    checkout_result = subprocess.run(['git', 'checkout', 'main'], capture_output=True, text=True)
                    if checkout_result.returncode == 0:
                        print("✅ Successfully switched to main branch")
                        
                        # Cherry-pick the commit to main
                        cherry_pick_result = subprocess.run(['git', 'cherry-pick', current_commit], capture_output=True, text=True)
                        if cherry_pick_result.returncode == 0:
                            print("✅ Successfully applied commit to main branch")
                            
                            # Now push again
                            final_push = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
                            if final_push.returncode == 0:
                                print("✅ Successfully pushed commit to main branch")
                            else:
                                print(f"❌ Failed to push after fixing detached HEAD: {final_push.stderr}")
                                return False, f"Failed to push after fixing detached HEAD: {final_push.stderr}"
                        else:
                            print(f"❌ Failed to cherry-pick commit: {cherry_pick_result.stderr}")
                            # Try alternative: reset main to the commit
                            reset_result = subprocess.run(['git', 'reset', '--hard', current_commit], capture_output=True, text=True)
                            if reset_result.returncode == 0:
                                print("✅ Reset main branch to include our commit")
                                final_push = subprocess.run(['git', 'push', 'origin', 'main', '--force-with-lease'], capture_output=True, text=True)
                                if final_push.returncode == 0:
                                    print("✅ Force-pushed main branch with our commit")
                                else:
                                    print(f"❌ Failed to force-push: {final_push.stderr}")
                                    return False, f"Failed to force-push after detached HEAD fix: {final_push.stderr}"
                            else:
                                return False, f"Failed to fix detached HEAD state: {reset_result.stderr}"
                    else:
                        return False, f"Failed to checkout main branch: {checkout_result.stderr}"
                else:
                    return False, "Could not determine current commit hash"
                    
            elif "ahead of" in status_output:
                print("🚨 WARNING: Local is still ahead of remote - push may have failed!")
                return False, "Local repository is still ahead of remote after push - push failed"
            elif "behind" in status_output:
                print("⚠️  Local is behind remote - unexpected state")
            elif "up to date" in status_output:
                print("✅ Local and remote are in sync")
        
        # Verify remote URL is correct
        remote_url_check = subprocess.run(['git', 'remote', 'get-url', 'origin'], capture_output=True, text=True)
        if remote_url_check.returncode == 0:
            actual_remote = remote_url_check.stdout.strip()
            print(f"🔗 Confirmed remote URL: {actual_remote}")
        
        # Check what branch we're actually on
        actual_branch = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True)
        if actual_branch.returncode == 0 and actual_branch.stdout.strip():
            current_actual_branch = actual_branch.stdout.strip()
            print(f"🌿 Confirmed current branch: {current_actual_branch}")
            if current_actual_branch != current_branch:
                print(f"🚨 WARNING: Branch mismatch! Pushed to {current_branch} but on {current_actual_branch}")
        
        # List recent commits to verify our commit is there
        recent_commits = subprocess.run(['git', 'log', '--oneline', '-3'], capture_output=True, text=True)
        if recent_commits.returncode == 0:
            print(f"📜 Recent commits:")
            for line in recent_commits.stdout.strip().split('\n'):
                print(f"   {line}")
        
        committed_files = "JSON and logo files" if logo_file else "JSON file"
        print(f"✅ {committed_files} committed and pushed to GitHub")
        return True, f"{committed_files} pushed successfully"
        
    except Exception as e:
        return False, f"Git operations failed: {e}"

def trigger_github_actions(policy_path, edits_json, output_name, github_token=None, logo_file=None, user_id=None):
    """Trigger GitHub Actions workflow (manual instructions if no token)."""
    import time
    
    # First, commit and push the JSON file and logo file (if created)
    print("📤 Committing and pushing files to GitHub...")
    success, message = commit_and_push_json(edits_json, logo_file)
    if not success:
        print(f"❌ Failed to push files: {message}")
        print("💡 You'll need to manually commit and push the files")
    else:
        print(f"✅ {message}")
    
    if not github_token:
        print("\n🔗 GitHub Actions Manual Trigger Required:")
        print("=" * 50)
        print("1. Go to your GitHub repository")
        print("2. Click 'Actions' tab")
        print("3. Find 'Redline DOCX (LibreOffice headless)' workflow")
        print("4. Click 'Run workflow'")
        print("5. Fill in these values:")
        print(f"   - Input DOCX path: {policy_path}")
        print(f"   - Edits CSV/JSON path: {edits_json}")
        output_prefix = user_id if user_id else f"run-{int(time.time())}"
        print(f"   - Output DOCX path: build/{output_prefix}_{output_name}.docx")
        print("6. Click 'Run workflow' button")
        print("7. Wait for completion and download from Artifacts")
        print("=" * 50)
        return True, "Manual trigger instructions provided"
    
    # Auto-trigger with GitHub API (if token provided)
    try:
        # Get repository info from environment variables first, then git
        repo_owner = os.environ.get('GITHUB_REPO_OWNER')
        repo_name = os.environ.get('GITHUB_REPO_NAME')
        
        if repo_owner and repo_name:
            print(f"✅ Repository info from environment: {repo_owner}/{repo_name}")
            owner = repo_owner
            repo = repo_name
        else:
            # Fallback to git remote (for local development)
            if not os.path.exists('.git'):
                return False, "No git repository and GITHUB_REPO_OWNER/GITHUB_REPO_NAME environment variables not set"
                
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                return False, "Could not get repository URL from git and environment variables not set"
            
            repo_url = result.stdout.strip()
            # Extract owner/repo from URL
            if 'github.com' in repo_url:
                if repo_url.endswith('.git'):
                    repo_url = repo_url[:-4]
                parts = repo_url.split('/')
                owner = parts[-2]
                repo = parts[-1]
                print(f"✅ Repository info from git: {owner}/{repo}")
            else:
                return False, "Not a GitHub repository"
        
        # Verify files exist on GitHub before triggering workflow
        print("🔍 Verifying files are available on GitHub...")
        
        def verify_file_on_github(file_path, max_retries=6, delay=5):
            """Verify a file exists on GitHub with retries."""
            print(f"🔍 Checking file on GitHub: {file_path}")
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
            print(f"   API URL: {api_url}")
            
            for attempt in range(max_retries):
                try:
                    headers = {
                        'Authorization': f'token {github_token[:8]}...{github_token[-4:]}' if github_token else 'NO_TOKEN',
                        'Accept': 'application/vnd.github.v3+json'
                    }
                    
                    # Use actual token for request
                    actual_headers = {
                        'Authorization': f'token {github_token}',
                        'Accept': 'application/vnd.github.v3+json'
                    }
                    
                    response = requests.get(api_url, headers=actual_headers, timeout=10)
                    
                    print(f"   Attempt {attempt + 1}: Status {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"✅ File verified on GitHub: {file_path}")
                        # Show file info
                        try:
                            file_info = response.json()
                            print(f"   File size: {file_info.get('size', 'unknown')} bytes")
                            print(f"   SHA: {file_info.get('sha', 'unknown')[:8]}...")
                        except:
                            pass
                        return True
                    elif response.status_code == 404:
                        print(f"⏳ File not found (404) on attempt {attempt + 1}/{max_retries}")
                        if attempt == 0:
                            # On first failure, check what files ARE available in the directory
                            try:
                                dir_path = '/'.join(file_path.split('/')[:-1]) if '/' in file_path else ''
                                if dir_path:
                                    dir_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{dir_path}"
                                    dir_response = requests.get(dir_url, headers=actual_headers, timeout=10)
                                    if dir_response.status_code == 200:
                                        files = dir_response.json()
                                        available_files = [f['name'] for f in files if isinstance(f, dict)]
                                        print(f"   📁 Available files in {dir_path}/: {available_files}")
                                    else:
                                        print(f"   📁 Could not list directory {dir_path} (status {dir_response.status_code})")
                            except Exception as e:
                                print(f"   📁 Error listing directory: {e}")
                        
                        if attempt < max_retries - 1:
                            print(f"   Waiting {delay} seconds before retry...")
                            time.sleep(delay)
                    elif response.status_code == 401:
                        print(f"❌ Authentication failed (401) - check GITHUB_TOKEN")
                        return False
                    elif response.status_code == 403:
                        print(f"❌ Access forbidden (403) - check repository permissions")
                        return False
                    else:
                        print(f"⚠️  Unexpected response {response.status_code}: {response.text[:200]}")
                        if attempt < max_retries - 1:
                            time.sleep(delay)
                        
                except requests.exceptions.Timeout:
                    print(f"⚠️  Request timeout on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                except Exception as e:
                    print(f"⚠️  Error checking file {file_path} (attempt {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                    
            return False
        
        # Check both required files
        files_to_verify = [policy_path, edits_json]
        all_files_verified = True
        
        for file_path in files_to_verify:
            if not verify_file_on_github(file_path):
                print(f"❌ File verification failed: {file_path}")
                all_files_verified = False
        
        if not all_files_verified:
            return False, "One or more files not available on GitHub after multiple retries. Please check your git push and try again."
        
        print("✅ All files verified on GitHub - proceeding with workflow trigger")
        
        # Additional small delay to ensure GitHub is fully ready
        print("⏳ Final 3-second delay for GitHub processing...")
        time.sleep(3)
        
        # Trigger workflow
        api_url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/redline-docx.yml/dispatches"
        
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Use user_id for output isolation, fallback to timestamp if not provided
        output_prefix = user_id if user_id else f"run-{int(time.time())}"
        
        data = {
            'ref': 'main',
            'inputs': {
                'input_docx': policy_path,
                'edits_csv': edits_json,
                'output_docx': f'build/{output_prefix}_{output_name}.docx'
            }
        }
        
        print(f"🚀 Triggering workflow with parameters:")
        print(f"   - DOCX: {policy_path}")
        print(f"   - JSON: {edits_json}")
        print(f"   - Output: build/{output_prefix}_{output_name}.docx")
        
        response = requests.post(api_url, headers=headers, json=data)
        
        if response.status_code == 204:
            print(f"✅ GitHub Actions workflow triggered successfully!")
            print(f"🔗 Check progress: https://github.com/{owner}/{repo}/actions")
            return True, "Workflow triggered"
        else:
            return False, f"GitHub API error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, f"GitHub Actions trigger failed: {e}"

def main():
    parser = argparse.ArgumentParser(description='Complete Policy Automation - End-to-End Flow')
    parser.add_argument('--policy', required=True, help='Path to policy DOCX file')
    parser.add_argument('--questionnaire', help='Path to questionnaire Excel/CSV/JSON file')
    parser.add_argument('--questionnaire-env-data', action='store_true', help='Read questionnaire data from QUESTIONNAIRE_ANSWERS_DATA environment variable')
    parser.add_argument('--output-name', required=True, help='Base name for output files (e.g., "acme_policy")')
    parser.add_argument('--api-key', help='Claude API key (or set CLAUDE_API_KEY env var)')
    parser.add_argument('--github-token', help='GitHub token for auto-triggering (optional)')
    parser.add_argument('--skip-github', action='store_true', help='Skip GitHub Actions step')
    parser.add_argument('--skip-api', action='store_true', help='Skip API call and use existing JSON file (for testing/development)')
    parser.add_argument('--logo', help='Optional path to company logo image (png/jpg) to insert in header')
    parser.add_argument('--logo-width-mm', type=int, help='Optional logo width in millimeters')
    parser.add_argument('--logo-height-mm', type=int, help='Optional logo height in millimeters')
    parser.add_argument('--user-id', help='Unique user identifier for multi-user isolation (auto-generated if not provided)')
    
    args = parser.parse_args()
    
    # Check for skip API configuration
    skip_api_env = os.environ.get('SKIP_API_CALL', '').lower()
    skip_api = args.skip_api or skip_api_env in ['true', '1', 'yes', 'on']
    
    # Get API key (only required if not skipping API)
    api_key = args.api_key or os.environ.get('CLAUDE_API_KEY')
    if not skip_api and not api_key:
        print("❌ Error: Claude API key required!")
        print("   Set CLAUDE_API_KEY environment variable or use --api-key")
        print("   Get your key from: https://console.anthropic.com/")
        print("   Or use --skip-api to use existing JSON file for testing")
        sys.exit(1)
    
    # GitHub token (optional)
    github_token = args.github_token or os.environ.get('GITHUB_TOKEN')
    
    # Generate unique user ID for multi-user isolation
    user_id = args.user_id
    if not user_id:
        import time
        import random
        timestamp = int(time.time())
        random_suffix = random.randint(1000, 9999)
        user_id = f"user-{timestamp}-{random_suffix}"
        print(f"🔑 Generated user ID: {user_id}")
    else:
        print(f"🔑 Using provided user ID: {user_id}")
    
    print("🚀 Complete Policy Automation Starting...")
    print("=" * 50)
    print(f"📋 Policy Document: {args.policy}")
    print(f"📊 Questionnaire: {args.questionnaire}")
    print(f"📝 Output Name: {args.output_name}")
    print(f"👤 User ID: {user_id}")
    print(f"🤖 AI: Claude Sonnet 4")
    print(f"⚙️  Automation: GitHub Actions")
    print("=" * 50)
    
    # Create intermediate file paths with user isolation
    questionnaire_csv = f"data/{user_id}_{args.output_name}_questionnaire.csv"
    edits_json = f"edits/{user_id}_{args.output_name}_edits.json"
    prompt_path = "data/prompt.md"
    policy_instructions_path = "data/updated_policy_instructions_v4.0.md"
    
    try:
        # Track created logo file for git commit
        created_logo_file = None
        
        # Step 1: Handle questionnaire input (Excel/CSV/JSON/Environment)
        questionnaire_json_data = None
        
        if args.questionnaire_env_data:
            # Use environment variable data (production-friendly approach)
            print("\n📊 STEP 1: Using Environment Variable Questionnaire Data (production mode)")
            env_data = os.environ.get('QUESTIONNAIRE_ANSWERS_DATA')
            if not env_data:
                print("❌ Error: QUESTIONNAIRE_ANSWERS_DATA environment variable not set!")
                sys.exit(1)
            
            questionnaire_json_data = env_data
            questionnaire_csv = None  # Not needed for environment approach
            print(f"✅ Loaded questionnaire data from environment variable ({len(env_data)} characters)")
            
        elif args.questionnaire:
            if args.questionnaire.endswith('.json'):
                # Direct JSON input from localStorage approach
                print("\n📊 STEP 1: Using Direct JSON Questionnaire Data (localStorage mode)")
                with open(args.questionnaire, 'r', encoding='utf-8') as f:
                    questionnaire_json_data = json.dumps(json.load(f))
                questionnaire_csv = None  # Not needed for JSON approach
                print(f"✅ Loaded questionnaire JSON from: {args.questionnaire}")
            elif args.questionnaire.endswith(('.xlsx', '.xls')):
                print("\n📊 STEP 1: Converting Excel to CSV")
                success, output = convert_xlsx_to_csv(args.questionnaire, questionnaire_csv)
                if not success:
                    print(f"❌ Excel conversion failed: {output}")
                    sys.exit(1)
            else:
                # Already CSV, just copy/link it
                questionnaire_csv = args.questionnaire
                print(f"\n📊 STEP 1: Using existing CSV: {questionnaire_csv}")
        else:
            print("❌ Error: Either --questionnaire (file path) or --questionnaire-env-data must be provided!")
            sys.exit(1)
        
        # Step 2: Generate edits with AI (JSON only)
        if skip_api:
            print("\n🔄 STEP 2: Using Existing JSON File (API Skipped)")
        else:
            print("\n🧠 STEP 2: Generating Edits with Claude Sonnet 4")
        success, output = generate_edits_with_ai(
            args.policy, questionnaire_csv, prompt_path, policy_instructions_path, 
            edits_json, api_key, skip_api, questionnaire_json_data
        )
        if not success:
            print(f"❌ AI generation failed: {output}")
            sys.exit(1)

        # If logo was provided via CLI, inject metadata. Otherwise, check if we need fallback logic
        try:
            import json
            with open(edits_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data.setdefault('metadata', {})
            
            # Check if CLI logo provided
            if args.logo or args.logo_width_mm or args.logo_height_mm:
                if args.logo:
                    data['metadata']['logo_path'] = args.logo
                if args.logo_width_mm is not None:
                    data['metadata']['logo_width_mm'] = args.logo_width_mm
                if args.logo_height_mm is not None:
                    data['metadata']['logo_height_mm'] = args.logo_height_mm
                print("🖼️  Injected CLI logo metadata into edits JSON")
            else:
                # Check if there are logo operations but no local logo path set
                operations = data.get('instructions', {}).get('operations', [])
                has_logo_operations = any(op.get('action') == 'replace_with_logo' for op in operations)
                
                print(f"🔍 DEBUG: has_logo_operations = {has_logo_operations}")
                print(f"🔍 DEBUG: existing logo_path = {data['metadata'].get('logo_path')}")
                
                if has_logo_operations and not data['metadata'].get('logo_path'):
                    print("🔍 DEBUG: Logo operations found and no existing logo path - attempting to create PNG from base64")
                    
                    # Try to extract logo from original environment variable data (before API filtering)
                    try:
                        logo_created = False
                        
                        # First, try environment variable data (contains original base64)
                        env_data = os.environ.get('QUESTIONNAIRE_ANSWERS_DATA')
                        print(f"🔍 DEBUG: Environment data exists: {bool(env_data)}")
                        if env_data:
                            try:
                                json_data = json.loads(env_data)
                                
                                # Debug: Show what keys we have
                                print(f"🔍 DEBUG: Environment JSON keys: {list(json_data.keys())}")
                                
                                # Look for base64 logo data in JSON (check both possible keys)
                                logo_data = json_data.get('_logo_base64_data', {})
                                if not logo_data:
                                    # Fallback: check the original form field name
                                    logo_data = json_data.get('onboarding.company_logo', {})
                                    print(f"🔍 DEBUG: Using onboarding.company_logo instead of _logo_base64_data")
                                
                                print(f"🔍 DEBUG: Logo data found: {bool(logo_data)}")
                                if logo_data:
                                    print(f"🔍 DEBUG: Logo data type: {type(logo_data)}")
                                    print(f"🔍 DEBUG: Logo data keys: {logo_data.keys() if isinstance(logo_data, dict) else 'Not a dict'}")
                                
                                if isinstance(logo_data, dict) and 'value' in logo_data:
                                    base64_value = logo_data['value']
                                    print(f"🔍 DEBUG: base64_value type: {type(base64_value)}")
                                    print(f"🔍 DEBUG: base64_value preview: {str(base64_value)[:100]}...")
                                    
                                    # Check if it's a dict with 'data' field (file upload format)
                                    if isinstance(base64_value, dict) and 'data' in base64_value:
                                        base64_value = base64_value['data']
                                        print(f"🔍 DEBUG: Extracted data field from nested dict")
                                    
                                    if isinstance(base64_value, str) and 'base64,' in base64_value:
                                        # Extract base64 data
                                        base64_data = base64_value.split('base64,')[1]
                                        
                                        # Create user-specific logo file from base64 data
                                        logo_buffer = base64.b64decode(base64_data)
                                        logo_path = f"data/{user_id}_company_logo.png"
                                        os.makedirs("data", exist_ok=True)
                                        
                                        with open(logo_path, 'wb') as logo_file:
                                            logo_file.write(logo_buffer)
                                        
                                        data['metadata']['logo_path'] = logo_path
                                        created_logo_file = logo_path  # Track for cleanup
                                        print(f"🖼️  Created user-specific logo: {logo_path} ({len(logo_buffer)} bytes)")
                                        print(f"✅ Logo will be processed by existing PNG logic!")
                                        logo_created = True
                                        
                            except (json.JSONDecodeError, KeyError, Exception) as e:
                                print(f"⚠️  Could not extract logo from environment data: {e}")
                                import traceback
                                print(f"🔍 DEBUG: Full error trace: {traceback.format_exc()}")
                        
                        # Fallback: try CSV file (for backward compatibility)
                        print(f"🔍 DEBUG: logo_created after env processing = {logo_created}")
                        if not logo_created and os.path.exists(questionnaire_csv):
                            print(f"🔍 DEBUG: Trying CSV fallback: {questionnaire_csv}")
                            with open(questionnaire_csv, 'r', encoding='utf-8') as f:
                                csv_content = f.read()
                            
                            # Look for base64 data entry (this will be filtered, so likely won't work)
                            for line in csv_content.split('\n'):
                                if '_logo_base64_data' in line and 'file_upload' in line:
                                    parts = line.split(';', 4)
                                    if len(parts) >= 5 and not 'REMOVED_FOR_API_EFFICIENCY' in parts[4]:
                                        base64_data = parts[4]
                                        # Remove data URL prefix if present
                                        if ',' in base64_data:
                                            base64_data = base64_data.split(',')[1]
                                        
                                        # Create user-specific logo file from CSV base64 data
                                        logo_buffer = base64.b64decode(base64_data)
                                        logo_path = f"data/{user_id}_company_logo.png"
                                        os.makedirs("data", exist_ok=True)
                                        
                                        with open(logo_path, 'wb') as logo_file:
                                            logo_file.write(logo_buffer)
                                        
                                        data['metadata']['logo_path'] = logo_path
                                        created_logo_file = logo_path  # Track for cleanup
                                        print(f"🖼️  Created user-specific logo from CSV: {logo_path} ({len(logo_buffer)} bytes)")
                                        print(f"✅ Logo will be processed by existing PNG logic!")
                                        logo_created = True
                                        break
                            
                            # Fallback: check if user provided a file path reference
                            print(f"🔍 DEBUG: logo_created after CSV processing = {logo_created}")
                            if not logo_created:
                                for line in csv_content.split('\n'):
                                    if 'company_logo' in line and 'File upload' in line:
                                        parts = line.split(';')
                                        if len(parts) >= 5:
                                            file_path = parts[4].strip()
                                            if file_path and os.path.exists(file_path):
                                                data['metadata']['logo_path'] = file_path
                                                print(f"🖼️  Using logo file from questionnaire: {file_path}")
                                                logo_created = True
                                                break
                        
                        if not logo_created:
                            print("⚠️  No user logo found - skipping logo operations")
                            print(f"🔍 DEBUG: logo_created final status = {logo_created}")
                            
                    except Exception as e:
                        print(f"⚠️  Failed to process user's logo data: {e}")
                else:
                    if not has_logo_operations:
                        print("🔍 DEBUG: No logo operations found in JSON - no logo processing needed")
                    if data['metadata'].get('logo_path'):
                        print(f"🔍 DEBUG: Existing logo path found: {data['metadata'].get('logo_path')}")
            
            with open(edits_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"⚠️  Could not process logo metadata: {e}")
        
        # Step 3: Trigger GitHub Actions
        if not args.skip_github:
            print("\n⚙️  STEP 3: Triggering Automated Tracked Changes")
            success, output = trigger_github_actions(
                args.policy, edits_json, args.output_name, github_token, created_logo_file, user_id
            )
            if not success:
                print(f"❌ GitHub Actions trigger failed: {output}")
                sys.exit(1)
        else:
            print("\n⏭️  STEP 3: Skipped GitHub Actions (--skip-github)")
        
        # Success summary
        print("\n🎉 AUTOMATION COMPLETE!")
        print("=" * 50)
        print("✅ Generated Files:")
        print(f"   📊 Questionnaire CSV: {questionnaire_csv}")
        print(f"   📋 JSON Instructions: {edits_json}")
        if created_logo_file:
            print(f"   🖼️  Logo File: {created_logo_file}")
        
        if not args.skip_github:
            output_prefix = user_id if user_id else f"run-{int(time.time())}"
            print(f"   📄 Final DOCX: build/{output_prefix}_{args.output_name}.docx (via GitHub Actions)")
            print(f"   🏷️  Artifact Name: redlined-docx-<run_id>-<run_number>")
            print("\n🔍 Next Steps:")
            print("1. Check GitHub Actions for completion")
            print("2. Download the result from Artifacts")
            print("3. Open in LibreOffice Writer")
            print("4. Review tracked changes and accept/reject")
        else:
            print(f"\n🔗 Manual Step: Run GitHub Actions with {edits_json}")
        
        print("\n🏆 Your policy is ready for review with automated suggestions!")
        
        # Clean up user-specific logo file if it was created from base64 data
        if created_logo_file and created_logo_file.startswith('data/') and user_id in created_logo_file:
            try:
                os.unlink(created_logo_file)
                print(f"🧹 Cleaned up user logo file: {created_logo_file}")
            except Exception as e:
                print(f"⚠️  Warning: Could not clean up logo file: {e}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Automation cancelled by user")
        # Clean up user logo file if it was created
        if 'created_logo_file' in locals() and created_logo_file and created_logo_file.startswith('data/'):
            try:
                os.unlink(created_logo_file)
                print(f"🧹 Cleaned up user logo file")
            except:
                pass
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        # Clean up user logo file if it was created
        if 'created_logo_file' in locals() and created_logo_file and created_logo_file.startswith('data/'):
            try:
                os.unlink(created_logo_file)
                print(f"🧹 Cleaned up user logo file")
            except:
                pass
        sys.exit(1)

if __name__ == "__main__":
    main()
