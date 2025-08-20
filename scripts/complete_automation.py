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

def generate_edits_with_ai(policy_path, questionnaire_csv, prompt_path, policy_instructions_path, output_json, api_key, skip_api=False):
    """Generate JSON instructions using AI or use existing file."""
    
    if skip_api:
        print("🔄 Step 2: Using existing JSON file (API call skipped for testing/development)...")
        cmd = f"""python3 scripts/ai_policy_processor.py \
            --policy '{policy_path}' \
            --questionnaire '{questionnaire_csv}' \
            --prompt '{prompt_path}' \
            --policy-instructions '{policy_instructions_path}' \
            --output '{output_json}' \
            --skip-api"""
    else:
        print("🧠 Step 2: Generating JSON instructions with Claude Sonnet 4...")
        cmd = f"""python3 scripts/ai_policy_processor.py \
            --policy '{policy_path}' \
            --questionnaire '{questionnaire_csv}' \
            --prompt '{prompt_path}' \
            --policy-instructions '{policy_instructions_path}' \
            --output '{output_json}' \
            --api-key '{api_key}'"""
    
    return run_command(cmd, "Processing JSON instructions")

def commit_and_push_json(edits_json, logo_file=None):
    """Commit and push the generated JSON file and optional logo file to GitHub."""
    try:
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
        
        # Add the JSON file
        result = subprocess.run(['git', 'add', edits_json], capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"Failed to add JSON: {result.stderr}"
        
        # Add the logo file if it exists and was created
        if logo_file and os.path.exists(logo_file):
            result = subprocess.run(['git', 'add', logo_file], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"⚠️  Warning: Failed to add logo file {logo_file}: {result.stderr}")
            else:
                print(f"✅ Added logo file to git: {logo_file}")
        
        # Commit the files
        files_to_commit = [edits_json]
        if logo_file and os.path.exists(logo_file):
            files_to_commit.append(logo_file)
        
        commit_msg = f"Add AI-generated files: {', '.join(files_to_commit)}"
        result = subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True)
        if result.returncode != 0:
            # Check if it's because there are no changes
            if "nothing to commit" in result.stdout:
                print("✅ Files already committed")
                return True, "No changes to commit"
            return False, f"Failed to commit files: {result.stderr}"
        
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
        
        # Try pushing with explicit origin and branch
        result = subprocess.run(['git', 'push', 'origin', current_branch], capture_output=True, text=True)
        if result.returncode != 0:
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
                if 'does not appear to be a git repository' in error_msg.lower():
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
    parser.add_argument('--questionnaire', required=True, help='Path to questionnaire Excel/CSV file')
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
        
        # Step 1: Convert Excel to CSV (if needed)
        if args.questionnaire.endswith(('.xlsx', '.xls')):
            print("\n📊 STEP 1: Converting Excel to CSV")
            success, output = convert_xlsx_to_csv(args.questionnaire, questionnaire_csv)
            if not success:
                print(f"❌ Excel conversion failed: {output}")
                sys.exit(1)
        else:
            # Already CSV, just copy/link it
            questionnaire_csv = args.questionnaire
            print(f"\n📊 STEP 1: Using existing CSV: {questionnaire_csv}")
        
        # Step 2: Generate edits with AI (JSON only)
        if skip_api:
            print("\n🔄 STEP 2: Using Existing JSON File (API Skipped)")
        else:
            print("\n🧠 STEP 2: Generating Edits with Claude Sonnet 4")
        success, output = generate_edits_with_ai(
            args.policy, questionnaire_csv, prompt_path, policy_instructions_path, 
            edits_json, api_key, skip_api
        )
        if not success:
            print(f"❌ AI generation failed: {output}")
            sys.exit(1)

        # If logo was provided via CLI, inject metadata. Otherwise, check if we need fallback logic
        try:
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
                
                if has_logo_operations and not data['metadata'].get('logo_path'):
                    # ONLY check for user's embedded logo data - NO FALLBACKS
                    local_logo_path = f"data/{user_id}_company_logo.png"
                    
                    # Try to extract logo from user's questionnaire CSV
                    try:
                        logo_created = False
                        if os.path.exists(questionnaire_csv):
                            with open(questionnaire_csv, 'r', encoding='utf-8') as f:
                                csv_content = f.read()
                            
                            # First, try to find base64 data entry (newer format)
                            for line in csv_content.split('\n'):
                                if line.startswith('99;Logo Base64 Data;_logo_base64_data;'):
                                    parts = line.split(';', 4)
                                    if len(parts) >= 5:
                                        base64_data = parts[4]
                                        # Remove data URL prefix if present
                                        if ',' in base64_data:
                                            base64_data = base64_data.split(',')[1]
                                        
                                        # Create logo file from user's base64 data
                                        logo_buffer = base64.b64decode(base64_data)
                                        with open(local_logo_path, 'wb') as f:
                                            f.write(logo_buffer)
                                        
                                        data['metadata']['logo_path'] = local_logo_path
                                        created_logo_file = local_logo_path  # Track for git commit
                                        print(f"🖼️  Created logo file from user's base64 data")
                                        logo_created = True
                                        break
                            
                            # Fallback: check if user provided a file path reference
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
                            
                    except Exception as e:
                        print(f"⚠️  Failed to process user's logo data: {e}")
            
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
        
    except KeyboardInterrupt:
        print("\n⏹️  Automation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
