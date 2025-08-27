#!/usr/bin/env python3
"""
Complete Policy Automation - End-to-End Flow (Refactored)

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
import json
from pathlib import Path
from typing import Optional, Tuple

# Add the scripts directory to Python path
sys.path.append(str(Path(__file__).parent))

# Import our modular utilities
from lib import (
    # Command utilities
    generate_user_id, validate_api_key, setup_file_paths, show_startup_info,
    run_command, convert_xlsx_to_csv, generate_edits_with_ai,
    # Git utilities
    commit_and_push_files,
    # GitHub utilities  
    GitHubActionsManager, create_workflow_params, clean_policy_for_github, cleanup_temp_files,
    # Logo utilities
    process_logo_operations, inject_logo_metadata, cleanup_logo_file
)


class AutomationOrchestrator:
    """
    Main orchestrator for the complete policy automation workflow.
    
    Coordinates all steps from questionnaire processing to final DOCX generation.
    """
    
    def __init__(self, args):
        """Initialize with command line arguments."""
        self.args = args
        self.user_id = generate_user_id(args.user_id)
        self.api_key = validate_api_key(args.api_key, self._should_skip_api())
        self.github_token = args.github_token or os.environ.get('GITHUB_TOKEN')
        
        # Setup file paths with user isolation
        self.file_paths = setup_file_paths(self.user_id, args.output_name)
        
        # Track created files for cleanup
        self.created_logo_file: Optional[str] = None
        self.temp_files: list = []
    
    def _should_skip_api(self) -> bool:
        """Determine if API calls should be skipped."""
        skip_api_env = os.environ.get('SKIP_API_CALL', '').lower()
        return self.args.skip_api or skip_api_env in ['true', '1', 'yes', 'on']
    
    def process_questionnaire_input(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Process questionnaire input (Excel/CSV/JSON/Environment).
        
        Returns:
            Tuple of (questionnaire_csv_path, questionnaire_json_data)
        """
        if self.args.questionnaire_env_data:
            return self._process_environment_data()
        elif self.args.questionnaire:
            return self._process_questionnaire_file()
        else:
            print("❌ Error: Either --questionnaire (file path) or --questionnaire-env-data must be provided!")
            sys.exit(1)
    
    def _process_environment_data(self) -> Tuple[None, str]:
        """Process questionnaire data from environment variable."""
        print("\n📊 STEP 1: Using Environment Variable Questionnaire Data (production mode)")
        env_data = os.environ.get('QUESTIONNAIRE_ANSWERS_DATA')
        if not env_data:
            print("❌ Error: QUESTIONNAIRE_ANSWERS_DATA environment variable not set!")
            sys.exit(1)
        
        print(f"✅ Loaded questionnaire data from environment variable ({len(env_data)} characters)")
        return None, env_data  # No CSV file needed for environment approach
    
    def _process_questionnaire_file(self) -> Tuple[Optional[str], Optional[str]]:
        """Process questionnaire from file (Excel/CSV/JSON)."""
        questionnaire = self.args.questionnaire
        
        if questionnaire.endswith('.json'):
            # Direct JSON input from localStorage approach
            print("\n📊 STEP 1: Using Direct JSON Questionnaire Data (localStorage mode)")
            with open(questionnaire, 'r', encoding='utf-8') as f:
                questionnaire_json_data = json.dumps(json.load(f))
            print(f"✅ Loaded questionnaire JSON from: {questionnaire}")
            return None, questionnaire_json_data  # No CSV file needed for JSON approach
            
        elif questionnaire.endswith(('.xlsx', '.xls')):
            print("\n📊 STEP 1: Converting Excel to CSV")
            success, output = convert_xlsx_to_csv(questionnaire, self.file_paths['questionnaire_csv'])
            if not success:
                print(f"❌ Excel conversion failed: {output}")
                sys.exit(1)
            return self.file_paths['questionnaire_csv'], None
            
        else:
            # Already CSV, just use it directly
            print(f"\n📊 STEP 1: Using existing CSV: {questionnaire}")
            return questionnaire, None
    
    def generate_ai_edits(self, questionnaire_csv: Optional[str], questionnaire_json: Optional[str]) -> bool:
        """
        Generate JSON instructions using AI or use existing file.
        
        Args:
            questionnaire_csv: Path to CSV file (may be None)
            questionnaire_json: JSON data string (may be None)
            
        Returns:
            True if successful, False otherwise
        """
        skip_api = self._should_skip_api()
        
        if skip_api:
            print("\n🔄 STEP 2: Using Existing JSON File (API Skipped)")
        else:
            print("\n🧠 STEP 2: Generating Edits with Claude Sonnet 4")
        
        success, output = generate_edits_with_ai(
            self.args.policy, 
            questionnaire_csv, 
            self.file_paths['prompt_path'], 
            self.file_paths['policy_instructions_path'], 
            self.file_paths['edits_json'], 
            self.api_key, 
            skip_api, 
            questionnaire_json
        )
        
        if not success:
            print(f"❌ AI generation failed: {output}")
            return False
        
        return True
    
    def process_logo_operations_step(self, questionnaire_json_data: Optional[str], questionnaire_csv: Optional[str]) -> None:
        """Process logo operations and inject metadata."""
        try:
            # Handle CLI logo injection
            if self.args.logo:
                inject_logo_metadata(self.file_paths['edits_json'], self.args.logo)
                print("🖼️  Injected CLI logo metadata into edits JSON")
                return
            
            # Process logo operations from questionnaire data
            self.created_logo_file = process_logo_operations(
                self.file_paths['edits_json'],
                self.user_id,
                questionnaire_json_data,
                questionnaire_csv
            )
            
        except Exception as e:
            print(f"⚠️  Could not process logo metadata: {e}")
    
    def trigger_github_workflow(self) -> bool:
        """
        Trigger GitHub Actions workflow.
        
        Returns:
            True if successful, False otherwise
        """
        if self.args.skip_github:
            print("\n⏭️  STEP 3: Skipped GitHub Actions (--skip-github)")
            return True
        
        print("\n⚙️  STEP 3: Triggering Automated Tracked Changes")
        
        # Create clean policy copy for GitHub Actions
        github_policy_path, cleanup_success = clean_policy_for_github(self.args.policy)
        if cleanup_success:
            self.temp_files.append(github_policy_path)
        
        # Prepare files for commit
        files_to_commit = [self.file_paths['edits_json']]
        if self.created_logo_file:
            files_to_commit.append(self.created_logo_file)
        if github_policy_path != self.args.policy:  # Only add if we created a cleaned copy
            files_to_commit.append(github_policy_path)
        
        # Commit and push files to GitHub
        print("📤 Committing and pushing files to GitHub...")
        success, message = commit_and_push_files(files_to_commit)
        if not success:
            print(f"❌ Failed to push files: {message}")
            print("💡 You'll need to manually commit and push the files")
            return False
        else:
            print(f"✅ {message}")
        
        # Trigger GitHub Actions workflow
        github_manager = GitHubActionsManager(self.github_token)
        workflow_params = create_workflow_params(
            github_policy_path, 
            self.file_paths['edits_json'], 
            self.args.output_name, 
            self.user_id
        )
        
        success, message = github_manager.trigger_workflow(workflow_params)
        if not success:
            print(f"❌ GitHub Actions trigger failed: {message}")
            return False
        
        return True
    
    def show_completion_summary(self) -> None:
        """Display completion summary and next steps."""
        print("\n🎉 AUTOMATION COMPLETE!")
        print("=" * 50)
        print("✅ Generated Files:")
        
        if self.file_paths['questionnaire_csv']:
            print(f"   📊 Questionnaire CSV: {self.file_paths['questionnaire_csv']}")
        print(f"   📋 JSON Instructions: {self.file_paths['edits_json']}")
        if self.created_logo_file:
            print(f"   🖼️  Logo File: {self.created_logo_file}")
        
        if not self.args.skip_github:
            output_prefix = self.user_id
            print(f"   📄 Final DOCX: build/{output_prefix}_{self.args.output_name}.docx (via GitHub Actions)")
            print(f"   🏷️  Artifact Name: redlined-docx-<run_id>-<run_number>")
            print("\n🔍 Next Steps:")
            print("1. Check GitHub Actions for completion")
            print("2. Download the result from Artifacts")
            print("3. Open in LibreOffice Writer")
            print("4. Review tracked changes and accept/reject")
        else:
            print(f"\n🔗 Manual Step: Run GitHub Actions with {self.file_paths['edits_json']}")
        
        print("\n🏆 Your policy is ready for review with automated suggestions!")
    
    def _should_stop_after_json(self) -> bool:
        """Check if automation should stop after generating JSON edits."""
        return os.getenv('STOP_AFTER_JSON', '').lower() in ('true', '1', 'yes', 'on')
    
    def _show_json_only_completion(self) -> None:
        """Show completion message when stopping after JSON generation only."""
        print("\n🛑 AUTOMATION STOPPED AFTER JSON GENERATION")
        print("=" * 50)
        print("✅ Generated Files:")
        print(f"   📋 JSON Instructions: {self.file_paths['edits_json']}")
        if self.created_logo_file:
            print(f"   🖼️  Logo File: {self.created_logo_file}")
        
        print("\n💡 Environment Variable STOP_AFTER_JSON=true detected")
        print("🔍 Next Steps:")
        print("1. Review the generated JSON file")
        print("2. Test the JSON with the tracked changes system")
        print("3. Set STOP_AFTER_JSON=false to continue full automation")
        print(f"\n📁 JSON Location: {self.file_paths['edits_json']}")
        print("🚀 Ready for manual processing or continued automation!")
    
    def cleanup(self) -> None:
        """Clean up temporary files and resources."""
        # Clean up user-specific logo file
        cleanup_logo_file(self.created_logo_file, self.user_id)
        
        # Clean up temporary files
        cleanup_temp_files(*self.temp_files)
    
    def run(self) -> None:
        """Execute the complete automation workflow."""
        try:
            # Show startup information
            show_startup_info(
                self.args.policy,
                self.args.questionnaire,
                self.args.output_name,
                self.user_id,
                self.args.questionnaire_env_data
            )
            
            # Step 1: Process questionnaire input
            questionnaire_csv, questionnaire_json_data = self.process_questionnaire_input()
            
            # Step 2: Generate AI edits
            if not self.generate_ai_edits(questionnaire_csv, questionnaire_json_data):
                sys.exit(1)
            
            # Check if we should stop after JSON generation
            if self._should_stop_after_json():
                self._show_json_only_completion()
                return
            
            # Process logo operations
            self.process_logo_operations_step(questionnaire_json_data, questionnaire_csv)
            
            # Step 3: Trigger GitHub Actions
            if not self.trigger_github_workflow():
                sys.exit(1)
            
            # Show completion summary
            self.show_completion_summary()
            
        except KeyboardInterrupt:
            print("\n⏹️  Automation cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            sys.exit(1)
        finally:
            self.cleanup()


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(description='Complete Policy Automation - End-to-End Flow')
    
    # Required arguments
    parser.add_argument('--policy', required=True, 
                       help='Path to policy DOCX file')
    parser.add_argument('--output-name', required=True, 
                       help='Base name for output files (e.g., "acme_policy")')
    
    # Questionnaire input options
    parser.add_argument('--questionnaire', 
                       help='Path to questionnaire Excel/CSV/JSON file')
    parser.add_argument('--questionnaire-env-data', action='store_true',
                       help='Read questionnaire data from QUESTIONNAIRE_ANSWERS_DATA environment variable')
    
    # API and authentication
    parser.add_argument('--api-key', 
                       help='Claude API key (or set CLAUDE_API_KEY env var)')
    parser.add_argument('--github-token', 
                       help='GitHub token for auto-triggering (optional)')
    
    # Control options
    parser.add_argument('--skip-github', action='store_true', 
                       help='Skip GitHub Actions step')
    parser.add_argument('--skip-api', action='store_true', 
                       help='Skip API call and use existing JSON file (for testing/development)')
    
    # Optional features
    parser.add_argument('--logo', 
                       help='Optional path to company logo image (png/jpg) to insert in header')
    parser.add_argument('--user-id', 
                       help='Unique user identifier for multi-user isolation (auto-generated if not provided)')
    
    return parser


def main():
    """Main entry point for the automation script."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Create and run the automation orchestrator
    orchestrator = AutomationOrchestrator(args)
    orchestrator.run()


if __name__ == "__main__":
    main()
