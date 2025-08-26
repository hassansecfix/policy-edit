"""
Git Operations Utilities

This module handles all Git operations for the automation system:
- Repository configuration and validation
- File staging and committing
- Branch management and pushing
- Authentication setup
"""

import os
import subprocess
import time
from typing import List, Optional, Tuple


class GitManager:
    """
    Manages Git operations for the automation system.
    
    Handles repository configuration, file operations, and remote synchronization.
    """
    
    def __init__(self, repo_path: str = "."):
        """Initialize GitManager with repository path."""
        self.repo_path = repo_path
        self.repo_owner: Optional[str] = None
        self.repo_name: Optional[str] = None
        self._extract_repo_info()
    
    def _extract_repo_info(self) -> None:
        """Extract GitHub repository info from environment variables or git remote."""
        # First try environment variables (for production deployment)
        self.repo_owner = os.environ.get('GITHUB_REPO_OWNER')
        self.repo_name = os.environ.get('GITHUB_REPO_NAME')
        
        # If environment variables are not set, try git (for local development)
        if not self.repo_owner or not self.repo_name:
            self._extract_repo_from_git()
    
    def _extract_repo_from_git(self) -> None:
        """Extract repository information from git remote URL."""
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
                timeout=5
            )
            
            if result.returncode == 0:
                url = result.stdout.strip()
                if 'github.com' in url:
                    # Parse GitHub URL (both HTTPS and SSH formats)
                    import re
                    match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', url)
                    if match:
                        self.repo_owner = match.group(1)
                        self.repo_name = match.group(2)
        except Exception:
            # Git command failed or not available - use environment variables only
            pass
    
    def validate_repository(self) -> Tuple[bool, str]:
        """Validate that we're in a proper Git repository."""
        # Debug environment information
        print(f"🔧 Environment Debug Info:")
        print(f"   Working Directory: {os.getcwd()}")
        print(f"   Repository Path: {self.repo_path}")
        
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
        
        return True, "Repository validation successful"
    
    def setup_remote_and_auth(self) -> Tuple[bool, str]:
        """Setup git remote and authentication."""
        # Ensure git remote origin exists and get the URL
        remote_check = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                    capture_output=True, text=True)
        if remote_check.returncode != 0:
            # Try to auto-configure remote using environment variables
            if self.repo_owner and self.repo_name:
                repo_url = f"https://github.com/{self.repo_owner}/{self.repo_name}.git"
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
        
        return True, f"Remote and auth configured for {remote_url}"
    
    def setup_user_identity(self) -> None:
        """Configure git identity if environment variables are set."""
        git_user_name = os.environ.get('GIT_USER_NAME')
        git_user_email = os.environ.get('GIT_USER_EMAIL')
        
        if git_user_name and git_user_email:
            subprocess.run(['git', 'config', 'user.name', git_user_name], capture_output=True)
            subprocess.run(['git', 'config', 'user.email', git_user_email], capture_output=True)
            print(f"✅ Git identity configured: {git_user_name} <{git_user_email}>")
    
    def ensure_proper_branch(self) -> Tuple[bool, str]:
        """Ensure we're on a proper branch (not detached HEAD)."""
        print("🔍 Checking repository state before committing...")
        status_check = subprocess.run(['git', 'status'], capture_output=True, text=True)
        if status_check.returncode == 0 and "HEAD detached" in status_check.stdout:
            print("🚨 Repository is in detached HEAD state - fixing before commit...")
            
            # Check for untracked files that might conflict with checkout
            untracked_check = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], 
                                           capture_output=True, text=True)
            if untracked_check.returncode == 0 and untracked_check.stdout.strip():
                untracked_files = untracked_check.stdout.strip().split('\n')
                print(f"📄 Found {len(untracked_files)} untracked files that might conflict with checkout")
                
                # Stage untracked files temporarily to avoid conflicts
                for file in untracked_files:
                    if file.strip():
                        stage_result = subprocess.run(['git', 'add', file.strip()], capture_output=True, text=True)
                        if stage_result.returncode == 0:
                            print(f"📝 Staged untracked file: {file.strip()}")
                        else:
                            print(f"⚠️  Could not stage file {file.strip()}: {stage_result.stderr}")
            
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
        
        return True, "Branch state is proper"
    
    def add_and_stage_files(self, files_to_commit: List[str]) -> Tuple[bool, str, List[str]]:
        """Add and stage files for commit."""
        successfully_staged = []
        
        for file_path in files_to_commit:
            # Verify file exists before adding
            if not os.path.exists(file_path):
                print(f"⚠️  File does not exist: {file_path}")
                continue
            
            print(f"📝 Adding file to git: {file_path}")
            print(f"📊 File size: {os.path.getsize(file_path)} bytes")
            
            # Add the file
            result = subprocess.run(['git', 'add', file_path], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"⚠️  Warning: Failed to add file {file_path}: {result.stderr}")
                continue
            
            # Verify the file was actually added to git
            status_result = subprocess.run(['git', 'status', '--porcelain', file_path], capture_output=True, text=True)
            if status_result.returncode == 0 and status_result.stdout.strip():
                print(f"✅ File staged for commit: {file_path}")
                successfully_staged.append(file_path)
            else:
                print(f"⚠️  File was not properly staged: {file_path}")
        
        if not successfully_staged:
            return False, "No files were successfully staged", []
        
        return True, f"Successfully staged {len(successfully_staged)} files", successfully_staged
    
    def commit_files(self, files_to_commit: List[str]) -> Tuple[bool, str]:
        """Commit the staged files."""
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
        
        return True, "Files committed successfully"
    
    def push_to_remote(self) -> Tuple[bool, str]:
        """Push committed changes to remote repository."""
        # Get the current branch name
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
            return self._handle_push_failure(result, current_branch)
        else:
            print(f"✅ Pushed to origin/{current_branch}")
            return True, f"Successfully pushed to {current_branch}"
    
    def _handle_push_failure(self, result: subprocess.CompletedProcess, current_branch: str) -> Tuple[bool, str]:
        """Handle push failures with various recovery strategies."""
        # Check if it's the "fetch first" error - try pulling and pushing again
        if 'fetch first' in result.stderr or 'rejected' in result.stderr:
            print(f"🔄 Push rejected, handling divergent branches...")
            
            # First, configure pull strategy to avoid divergent branches error
            subprocess.run(['git', 'config', 'pull.rebase', 'true'], capture_output=True)
            print("⚙️  Configured pull strategy: rebase")
            
            # Check if this is a production environment (Render, Heroku, etc.)
            is_production = any(env in os.environ for env in ['RENDER', 'HEROKU', 'CI', 'GITHUB_ACTIONS'])
            
            if is_production:
                print("🏭 Detected production environment - using force sync strategy")
                sync_success = self._handle_production_sync(current_branch)
            else:
                print("💻 Using local development sync strategy")
                sync_success = self._handle_local_sync(current_branch)
            
            if sync_success:
                # Try push again after successful sync
                retry_result = subprocess.run(['git', 'push', 'origin', current_branch], capture_output=True, text=True)
                if retry_result.returncode == 0:
                    print(f"✅ Successfully pushed after sync to origin/{current_branch}")
                    return True, f"Successfully pushed after sync"
                else:
                    print(f"❌ Push still failed after sync: {retry_result.stderr.strip()}")
            else:
                print("❌ Failed to sync with remote repository")
        
        # Fallback: try setting upstream and pushing
        print(f"⚠️  Initial push failed, trying to set upstream...")
        print(f"    Error: {result.stderr.strip()}")
        
        # Try with upstream flag
        upstream_result = subprocess.run(['git', 'push', '--set-upstream', 'origin', current_branch], capture_output=True, text=True)
        if upstream_result.returncode != 0:
            error_msg = upstream_result.stderr.strip() or result.stderr.strip()
            self._provide_push_troubleshooting(error_msg)
            return False, f"Failed to push to git: {error_msg}"
        else:
            print(f"✅ Set upstream branch and pushed to origin/{current_branch}")
            return True, f"Successfully set upstream and pushed"
    
    def _handle_production_sync(self, current_branch: str) -> bool:
        """Handle Git sync in production environments with force strategies."""
        print("📥 Fetching latest remote state...")
        
        # Fetch latest remote state
        fetch_result = subprocess.run(['git', 'fetch', 'origin'], capture_output=True, text=True)
        if fetch_result.returncode != 0:
            print(f"❌ Fetch failed: {fetch_result.stderr.strip()}")
            return False
        
        # Get remote commit hash
        remote_hash_result = subprocess.run(['git', 'rev-parse', f'origin/{current_branch}'], capture_output=True, text=True)
        if remote_hash_result.returncode != 0:
            print(f"❌ Could not get remote commit hash: {remote_hash_result.stderr.strip()}")
            return False
        
        remote_hash = remote_hash_result.stdout.strip()
        print(f"🎯 Remote commit: {remote_hash}")
        
        # Check if our files are already in remote
        local_files_result = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], capture_output=True, text=True)
        if local_files_result.returncode == 0 and local_files_result.stdout.strip():
            staged_files = local_files_result.stdout.strip().split('\n')
            print(f"📋 Files to preserve: {staged_files}")
            
            # Create a temporary commit with our changes
            temp_commit_result = subprocess.run(['git', 'stash', 'push', '-m', 'Production sync temp'], capture_output=True, text=True)
            if temp_commit_result.returncode == 0:
                print("💾 Temporarily stashed local changes")
                
                # Reset to remote state
                reset_result = subprocess.run(['git', 'reset', '--hard', f'origin/{current_branch}'], capture_output=True, text=True)
                if reset_result.returncode == 0:
                    print(f"🔄 Reset to remote state: {remote_hash}")
                    
                    # Restore our changes
                    stash_pop_result = subprocess.run(['git', 'stash', 'pop'], capture_output=True, text=True)
                    if stash_pop_result.returncode == 0:
                        print("♻️  Restored local changes on top of remote state")
                        
                        # Re-add and commit our files
                        for file in staged_files:
                            subprocess.run(['git', 'add', file.strip()], capture_output=True)
                        
                        commit_result = subprocess.run(['git', 'commit', '-m', 'Production sync: re-apply changes'], capture_output=True, text=True)
                        if commit_result.returncode == 0:
                            print("✅ Successfully re-applied changes after sync")
                            return True
                        else:
                            print(f"❌ Failed to re-commit changes: {commit_result.stderr.strip()}")
                    else:
                        print(f"⚠️  Stash pop had conflicts - manual resolution needed")
                        # Try to apply changes manually
                        subprocess.run(['git', 'reset', '--hard'], capture_output=True)
                        for file in staged_files:
                            subprocess.run(['git', 'add', file.strip()], capture_output=True)
                        commit_result = subprocess.run(['git', 'commit', '-m', 'Production sync: force apply changes'], capture_output=True, text=True)
                        return commit_result.returncode == 0
                else:
                    print(f"❌ Failed to reset to remote: {reset_result.stderr.strip()}")
            else:
                print(f"❌ Failed to stash changes: {temp_commit_result.stderr.strip()}")
        
        return False
    
    def _handle_local_sync(self, current_branch: str) -> bool:
        """Handle Git sync in local development with safer strategies."""
        print("💻 Using gentle sync for local development...")
        
        # Try pull with rebase first
        rebase_result = subprocess.run(['git', 'pull', '--rebase', 'origin', current_branch], capture_output=True, text=True)
        if rebase_result.returncode == 0:
            print("✅ Successfully rebased local changes")
            return True
        else:
            print(f"❌ Rebase failed: {rebase_result.stderr.strip()}")
            
            # Check if it's a conflict that can be resolved
            if 'conflict' in rebase_result.stderr.lower():
                print("⚠️  Rebase conflicts detected - aborting rebase")
                subprocess.run(['git', 'rebase', '--abort'], capture_output=True)
                
                # Try merge instead
                print("🔀 Trying merge strategy instead...")
                merge_result = subprocess.run(['git', 'pull', '--no-rebase', 'origin', current_branch], capture_output=True, text=True)
                if merge_result.returncode == 0:
                    print("✅ Successfully merged remote changes")
                    return True
                else:
                    print(f"❌ Merge also failed: {merge_result.stderr.strip()}")
            
            return False
    
    def _provide_push_troubleshooting(self, error_msg: str) -> None:
        """Provide detailed troubleshooting information for push failures."""
        print(f"\n🔴 Git Push Failed - Troubleshooting Info:")
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
    
    def verify_push_success(self) -> Tuple[bool, str]:
        """Verify that the push was actually successful."""
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
            
            # Check for issues
            if "HEAD detached" in status_output:
                return self._handle_detached_head()
            elif "ahead of" in status_output:
                print("🚨 WARNING: Local is still ahead of remote - push may have failed!")
                return False, "Local repository is still ahead of remote after push - push failed"
            elif "behind" in status_output:
                print("⚠️  Local is behind remote - unexpected state")
            elif "up to date" in status_output:
                print("✅ Local and remote are in sync")
        
        return True, "Push verification successful"
    
    def _handle_detached_head(self) -> Tuple[bool, str]:
        """Handle detached HEAD state after push."""
        print("🚨 CRITICAL ISSUE: Repository is in detached HEAD state!")
        print("   This means commits are not attached to any branch and won't be pushed.")
        print("   Attempting to fix by switching to main branch...")
        
        # Get the current commit hash
        commit_hash_result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True)
        if commit_hash_result.returncode == 0:
            current_commit = commit_hash_result.stdout.strip()
            print(f"   Current commit: {current_commit}")
            
            # Check for untracked files that might conflict with checkout
            untracked_check = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], 
                                           capture_output=True, text=True)
            if untracked_check.returncode == 0 and untracked_check.stdout.strip():
                untracked_files = untracked_check.stdout.strip().split('\n')
                print(f"📄 Found {len(untracked_files)} untracked files that might conflict with checkout")
                
                # Stage untracked files temporarily to avoid conflicts
                for file in untracked_files:
                    if file.strip():
                        stage_result = subprocess.run(['git', 'add', file.strip()], capture_output=True, text=True)
                        if stage_result.returncode == 0:
                            print(f"📝 Staged untracked file: {file.strip()}")
                        else:
                            print(f"⚠️  Could not stage file {file.strip()}: {stage_result.stderr}")
            
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
                        return True, "Fixed detached HEAD and pushed successfully"
                    else:
                        print(f"❌ Failed to push after fixing detached HEAD: {final_push.stderr}")
                        return False, f"Failed to push after fixing detached HEAD: {final_push.stderr}"
                else:
                    return self._try_reset_approach(current_commit)
            else:
                return False, f"Failed to checkout main branch: {checkout_result.stderr}"
        else:
            return False, "Could not determine current commit hash"
    
    def _try_reset_approach(self, current_commit: str) -> Tuple[bool, str]:
        """Try alternative approach using git reset."""
        print(f"❌ Failed to cherry-pick commit, trying reset approach...")
        # Try alternative: reset main to the commit
        reset_result = subprocess.run(['git', 'reset', '--hard', current_commit], capture_output=True, text=True)
        if reset_result.returncode == 0:
            print("✅ Reset main branch to include our commit")
            final_push = subprocess.run(['git', 'push', 'origin', 'main', '--force-with-lease'], capture_output=True, text=True)
            if final_push.returncode == 0:
                print("✅ Force-pushed main branch with our commit")
                return True, "Fixed detached HEAD with reset and force-pushed"
            else:
                print(f"❌ Failed to force-push: {final_push.stderr}")
                return False, f"Failed to force-push after detached HEAD fix: {final_push.stderr}"
        else:
            return False, f"Failed to fix detached HEAD state: {reset_result.stderr}"


def commit_and_push_files(files_to_commit: List[str], repo_path: str = ".") -> Tuple[bool, str]:
    """
    High-level function to commit and push files to Git repository.
    
    Args:
        files_to_commit: List of file paths to commit
        repo_path: Path to repository (defaults to current directory)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        git_manager = GitManager(repo_path)
        
        # Step 1: Validate repository
        success, message = git_manager.validate_repository()
        if not success:
            return False, message
        
        # Step 2: Setup remote and authentication
        success, message = git_manager.setup_remote_and_auth()
        if not success:
            return False, message
        
        # Step 3: Setup user identity
        git_manager.setup_user_identity()
        
        # Step 4: Ensure proper branch
        success, message = git_manager.ensure_proper_branch()
        if not success:
            return False, message
        
        # Step 5: Add and stage files
        success, message, staged_files = git_manager.add_and_stage_files(files_to_commit)
        if not success:
            return False, message
        
        # Step 6: Commit files
        success, message = git_manager.commit_files(staged_files)
        if not success:
            return False, message
        
        # Step 7: Push to remote
        success, message = git_manager.push_to_remote()
        if not success:
            return False, message
        
        # Step 8: Verify push success
        success, message = git_manager.verify_push_success()
        if not success:
            return False, message
        
        return True, f"Successfully committed and pushed {len(staged_files)} files"
        
    except Exception as e:
        return False, f"Git operations failed: {e}"
