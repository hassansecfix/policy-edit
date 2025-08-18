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
from pathlib import Path
import requests

# Import our other scripts
sys.path.append(str(Path(__file__).parent))

def run_command(cmd, description):
    """Run a shell command and handle errors."""
    print(f"🔄 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ {description} failed!")
        print(f"Error: {result.stderr}")
        return False, result.stderr
    
    print(f"✅ {description} completed")
    return True, result.stdout

def convert_xlsx_to_csv(xlsx_path, csv_path):
    """Convert Excel questionnaire to CSV."""
    cmd = f"python3 scripts/xlsx_to_csv_converter.py '{xlsx_path}' '{csv_path}'"
    return run_command(cmd, "Converting Excel to CSV")

def generate_edits_with_ai(policy_path, questionnaire_csv, prompt_path, policy_instructions_path, output_json, api_key):
    """Generate JSON instructions using AI."""
    
    # Generate JSON with AI
    print("🧠 Step 2: Generating JSON instructions with Claude Sonnet 4...")
    cmd = f"""python3 scripts/ai_policy_processor.py \
        --policy '{policy_path}' \
        --questionnaire '{questionnaire_csv}' \
        --prompt '{prompt_path}' \
        --policy-instructions '{policy_instructions_path}' \
        --output '{output_json}' \
        --api-key '{api_key}'"""
    
    return run_command(cmd, "Generating JSON instructions")

def commit_and_push_json(edits_json):
    """Commit and push the generated JSON file to GitHub."""
    try:
        # Add the JSON file
        result = subprocess.run(['git', 'add', edits_json], capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"Failed to add JSON: {result.stderr}"
        
        # Commit the JSON file
        commit_msg = f"Add AI-generated edits JSON: {edits_json}"
        result = subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True)
        if result.returncode != 0:
            # Check if it's because there are no changes
            if "nothing to commit" in result.stdout:
                print("✅ JSON file already committed")
                return True, "No changes to commit"
            return False, f"Failed to commit JSON: {result.stderr}"
        
        # Push to GitHub
        result = subprocess.run(['git', 'push'], capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"Failed to push JSON: {result.stderr}"
        
        print("✅ JSON file committed and pushed to GitHub")
        return True, "JSON pushed successfully"
        
    except Exception as e:
        return False, f"Git operations failed: {e}"

def trigger_github_actions(policy_path, edits_json, output_name, github_token=None):
    """Trigger GitHub Actions workflow (manual instructions if no token)."""
    
    # First, commit and push the JSON file
    print("📤 Committing and pushing JSON to GitHub...")
    success, message = commit_and_push_json(edits_json)
    if not success:
        print(f"❌ Failed to push JSON: {message}")
        print("💡 You'll need to manually commit and push the JSON file")
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
        print(f"   - Output DOCX path: build/{output_name}.docx")
        print("6. Click 'Run workflow' button")
        print("7. Wait for completion and download from Artifacts")
        print("=" * 50)
        return True, "Manual trigger instructions provided"
    
    # Auto-trigger with GitHub API (if token provided)
    try:
        # Get repository info from git remote
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            return False, "Could not get repository URL"
        
        repo_url = result.stdout.strip()
        # Extract owner/repo from URL
        if 'github.com' in repo_url:
            if repo_url.endswith('.git'):
                repo_url = repo_url[:-4]
            parts = repo_url.split('/')
            owner = parts[-2]
            repo = parts[-1]
        else:
            return False, "Not a GitHub repository"
        
        # Trigger workflow
        api_url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/redline-docx.yml/dispatches"
        
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        data = {
            'ref': 'main',
            'inputs': {
                'input_docx': policy_path,
                'edits_csv': edits_json,
                'output_docx': f'build/{output_name}.docx'
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
    parser.add_argument('--logo', help='Optional path to company logo image (png/jpg) to insert in header')
    parser.add_argument('--logo-width-mm', type=int, help='Optional logo width in millimeters')
    parser.add_argument('--logo-height-mm', type=int, help='Optional logo height in millimeters')
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.environ.get('CLAUDE_API_KEY')
    if not api_key:
        print("❌ Error: Claude API key required!")
        print("   Set CLAUDE_API_KEY environment variable or use --api-key")
        print("   Get your key from: https://console.anthropic.com/")
        sys.exit(1)
    
    # GitHub token (optional)
    github_token = args.github_token or os.environ.get('GITHUB_TOKEN')
    
    print("🚀 Complete Policy Automation Starting...")
    print("=" * 50)
    print(f"📋 Policy Document: {args.policy}")
    print(f"📊 Questionnaire: {args.questionnaire}")
    print(f"📝 Output Name: {args.output_name}")
    print(f"🤖 AI: Claude Sonnet 4")
    print(f"⚙️  Automation: GitHub Actions")
    print("=" * 50)
    
    # Create intermediate file paths
    questionnaire_csv = f"data/{args.output_name}_questionnaire.csv"
    edits_json = f"edits/{args.output_name}_edits.json"
    prompt_path = "data/prompt.md"
    policy_instructions_path = "data/updated_policy_instructions_v4.0.md"
    
    try:
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
        print("\n🧠 STEP 2: Generating Edits with Claude Sonnet 4")
        success, output = generate_edits_with_ai(
            args.policy, questionnaire_csv, prompt_path, policy_instructions_path, 
            edits_json, api_key
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
                    # Fallback to local logo file if it exists
                    local_logo_path = "data/company_logo.png"
                    if os.path.exists(local_logo_path):
                        data['metadata']['logo_path'] = local_logo_path
                        print(f"🖼️  Fallback: Using local logo file {local_logo_path}")
                    else:
                        print("⚠️  Logo operation generated but no local logo file found at data/company_logo.png")
            
            with open(edits_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"⚠️  Could not process logo metadata: {e}")
        
        # Step 3: Trigger GitHub Actions
        if not args.skip_github:
            print("\n⚙️  STEP 3: Triggering Automated Tracked Changes")
            success, output = trigger_github_actions(
                args.policy, edits_json, args.output_name, github_token
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
        
        if not args.skip_github:
            print(f"   📄 Final DOCX: build/{args.output_name}.docx (via GitHub Actions)")
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
