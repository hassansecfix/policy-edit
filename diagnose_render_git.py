#!/usr/bin/env python3
"""
Diagnostic script for git issues on Render
Run this on your Render environment to diagnose the problem
"""

import os
import subprocess
import json
from pathlib import Path

def run_cmd(cmd, desc):
    """Run command and return result safely"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return {
            'command': cmd,
            'description': desc,
            'returncode': result.returncode,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'success': result.returncode == 0
        }
    except Exception as e:
        return {
            'command': cmd,
            'description': desc,
            'error': str(e),
            'success': False
        }

def main():
    print("🔍 Render Git Diagnosis Tool")
    print("=" * 50)
    
    # Environment info
    print("\n🌍 ENVIRONMENT INFO:")
    env_vars = ['PWD', 'HOME', 'USER', 'RENDER', 'GITHUB_TOKEN', 'GITHUB_REPO_OWNER', 'GITHUB_REPO_NAME']
    for var in env_vars:
        value = os.environ.get(var, 'NOT SET')
        if 'TOKEN' in var and value != 'NOT SET':
            value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***HIDDEN***"
        print(f"   {var}: {value}")
    
    # Working directory
    print(f"\n📁 WORKING DIRECTORY:")
    print(f"   Current: {os.getcwd()}")
    print(f"   Contents: {os.listdir('.')}")
    
    # Git diagnostics
    commands = [
        ("pwd", "Current directory"),
        ("ls -la", "Directory listing"),
        ("git --version", "Git version"),
        ("git config --list", "Git configuration"),
        ("git status", "Git status"),
        ("git branch -a", "All branches"),
        ("git remote -v", "Git remotes"),
        ("git log --oneline -5", "Recent commits"),
        ("git ls-files edits/", "Tracked files in edits/"),
        ("ls -la edits/", "Edits directory contents"),
        ("git diff --cached", "Staged changes"),
        ("git diff HEAD~1 --name-only", "Files changed in last commit"),
    ]
    
    results = []
    for cmd, desc in commands:
        print(f"\n🔧 {desc}:")
        result = run_cmd(cmd, desc)
        results.append(result)
        
        if result['success']:
            print(f"   ✅ {cmd}")
            if result['stdout']:
                for line in result['stdout'].split('\n')[:10]:  # Limit output
                    print(f"      {line}")
                if len(result['stdout'].split('\n')) > 10:
                    print(f"      ... ({len(result['stdout'].split('\n')) - 10} more lines)")
        else:
            print(f"   ❌ {cmd}")
            if result.get('stderr'):
                print(f"      Error: {result['stderr']}")
            if result.get('error'):
                print(f"      Exception: {result['error']}")
    
    # Test file creation and git operations
    print(f"\n🧪 TEST GIT OPERATIONS:")
    test_file = "test_render_git.txt"
    
    try:
        # Create test file
        with open(test_file, 'w') as f:
            f.write(f"Test file created at {os.getcwd()}\n")
        print(f"   ✅ Created test file: {test_file}")
        
        # Try git operations
        test_commands = [
            f"git add {test_file}",
            "git status --porcelain",
            f"git commit -m 'Test commit from Render diagnostic'",
            "git log --oneline -1",
            "git push origin main",
            "git status -uno"
        ]
        
        for cmd in test_commands:
            result = run_cmd(cmd, f"Test: {cmd}")
            if result['success']:
                print(f"   ✅ {cmd}")
                if result['stdout']:
                    print(f"      Output: {result['stdout']}")
            else:
                print(f"   ❌ {cmd}")
                if result['stderr']:
                    print(f"      Error: {result['stderr']}")
        
        # Clean up
        run_cmd(f"rm -f {test_file}", "Cleanup test file")
        
    except Exception as e:
        print(f"   ❌ Test operations failed: {e}")
    
    # GitHub API test
    print(f"\n🐙 GITHUB API TEST:")
    github_token = os.environ.get('GITHUB_TOKEN')
    repo_owner = os.environ.get('GITHUB_REPO_OWNER', 'hassantayyab')
    repo_name = os.environ.get('GITHUB_REPO_NAME', 'policy-edit')
    
    if github_token:
        import requests
        try:
            # Test API access
            api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
            headers = {'Authorization': f'token {github_token}'}
            response = requests.get(api_url, headers=headers)
            
            print(f"   API URL: {api_url}")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                repo_info = response.json()
                print(f"   ✅ Repository accessible")
                print(f"   Default Branch: {repo_info.get('default_branch')}")
                print(f"   Clone URL: {repo_info.get('clone_url')}")
            else:
                print(f"   ❌ API Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ GitHub API test failed: {e}")
    else:
        print(f"   ⚠️  GITHUB_TOKEN not available")
    
    print(f"\n✅ Diagnosis complete!")
    print(f"📧 Share this output with the developer for analysis")

if __name__ == "__main__":
    main()
