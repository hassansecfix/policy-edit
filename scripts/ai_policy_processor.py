#!/usr/bin/env python3
"""
AI Policy Processor - Automated JSON Generation with Claude Sonnet 4

This script takes a policy DOCX file, questionnaire CSV, and AI prompt,
then uses Claude Sonnet 4 to generate the perfect JSON instructions file.

Usage:
    python3 ai_policy_processor.py \
        --policy data/policy.docx \
        --questionnaire data/questionnaire.csv \
        --prompt data/prompt.md \
        --policy-instructions [AUTO-DETECTED FROM CONFIG] \
        --output edits/ai_generated_edits.json \
        --api-key YOUR_CLAUDE_API_KEY

Environment Variables:
    CLAUDE_API_KEY: Your Anthropic Claude API key
"""

import os
import sys
import argparse
from pathlib import Path

# Add the lib directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

from lib.highlighting_cleanup import clean_docx_highlighting
from lib.content_loader import load_file_content, load_questionnaire_from_environment
from lib.claude_api import call_claude_api
from lib.config import get_policy_instructions_path
from lib.json_utils import (
    extract_json_from_response, 
    validate_json_content, 
    show_json_stats,
    format_json_for_output
)


class PolicyProcessor:
    """
    Main class for processing policy documents with AI.
    
    Handles the complete workflow from file loading to JSON generation.
    """
    
    def __init__(self, args):
        """Initialize the processor with command line arguments."""
        self.args = args
        self.skip_api = self._determine_skip_api()
        self.api_key = self._get_api_key()
    
    def _determine_skip_api(self) -> bool:
        """Determine if API calls should be skipped."""
        skip_api_env = os.environ.get('SKIP_API_CALL', '').lower()
        return self.args.skip_api or skip_api_env in ['true', '1', 'yes', 'on']
    
    def _get_api_key(self) -> str:
        """Get the Claude API key from arguments or environment."""
        if self.skip_api:
            return ""
        
        api_key = self.args.api_key or os.environ.get('CLAUDE_API_KEY')
        if not api_key:
            print("❌ Error: Claude API key required!")
            print("   Set CLAUDE_API_KEY environment variable or use --api-key")
            print("   Get your key from: https://console.anthropic.com/")
            print("   Or use --skip-api to use existing JSON file for testing")
            sys.exit(1)
        return api_key
    
    def process(self) -> None:
        """Run the complete policy processing workflow."""
        try:
            if self.skip_api:
                self._handle_skip_api_mode()
                return
            
            self._show_startup_info()
            content = self._load_input_files()
            response = self._call_ai_api(content)
            json_content = self._process_ai_response(response)
            self._save_output(json_content)
            self._show_success_info(json_content)
            
        except FileNotFoundError as e:
            print(f"❌ File Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    def _handle_skip_api_mode(self) -> None:
        """Handle the skip API mode for testing/development."""
        if not Path(self.args.output).exists():
            print("❌ Error: --skip-api specified but output JSON file doesn't exist!")
            print(f"   Expected file: {self.args.output}")
            print("   Either run without --skip-api first, or provide an existing JSON file")
            sys.exit(1)
        
        print("🔄 SKIP_API_CALL enabled - Using existing JSON file for testing/development")
        print(f"📁 Using existing file: {self.args.output}")
        
        # Validate the existing JSON file
        with open(self.args.output, 'r', encoding='utf-8') as f:
            content = f.read()
        validate_json_content(content)
        
        show_json_stats(content)
        print(f"\n💰 API call skipped - cost savings for testing/development!")
    
    def _show_startup_info(self) -> None:
        """Display startup information."""
        print("🤖 AI Policy Processor Starting (JSON Mode)...")
        print(f"📋 Policy: {self.args.policy}")
        
        if self.args.questionnaire_env_data:
            print(f"📊 Questionnaire: Environment variable data")
        else:
            print(f"📊 Questionnaire: {self.args.questionnaire}")
            
        print(f"📝 Main Prompt: {self.args.prompt}")
        print(f"📜 Policy Instructions: {self.args.policy_instructions}")
        print(f"💾 Output: {self.args.output}")
    
    def _load_input_files(self) -> dict:
        """Load all input files and return their content."""
        print("\n📂 Loading input files...")
        
        # Load policy content
        policy_content = load_file_content(self.args.policy)
        
        # Load questionnaire content
        if self.args.questionnaire_env_data:
            print("📊 Loading questionnaire data from environment variable...")
            questionnaire_content = load_questionnaire_from_environment()
        else:
            print("📊 Loading questionnaire data from file...")
            questionnaire_content = load_file_content(self.args.questionnaire)
        
        # Load prompt and instructions
        prompt_content = load_file_content(self.args.prompt)
        policy_instructions_content = load_file_content(self.args.policy_instructions)
        
        # Show loading status
        print(f"✅ Policy loaded: {len(policy_content)} characters")
        print(f"✅ Questionnaire loaded: {questionnaire_content.count('Question')} questions detected")
        print(f"✅ Main prompt loaded: {len(prompt_content)} characters")
        print(f"✅ Policy instructions loaded: {len(policy_instructions_content)} characters")
        
        return {
            'policy': policy_content,
            'questionnaire': questionnaire_content,
            'prompt': prompt_content,
            'policy_instructions': policy_instructions_content
        }
    
    def _call_ai_api(self, content: dict) -> str:
        """Call the Claude AI API with the loaded content."""
        print("\n🧠 Calling Claude Sonnet 4 API...")
        response = call_claude_api(
            content['prompt'],
            content['questionnaire'], 
            content['policy_instructions'],
            content['policy'],
            self.api_key
        )
        print("✅ AI response received")
        return response
    
    def _process_ai_response(self, response: str) -> str:
        """Process the AI response and extract/validate JSON."""
        print("\n🔍 Extracting JSON from AI response...")
        content = extract_json_from_response(response)
        
        print("✅ Validating JSON format...")
        validate_json_content(content)
        
        return content
    
    def _save_output(self, content: str) -> None:
        """Save the generated JSON to the output file."""
        output_path = Path(self.args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Format the JSON for better readability
        formatted_content = format_json_for_output(content)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        
        print(f"\n🎉 SUCCESS! Generated JSON instructions:")
        print(f"📁 Saved to: {output_path}")
    
    def _show_success_info(self, content: str) -> None:
        """Display success information and statistics."""
        show_json_stats(content)
        
        print(f"\n🚀 Next Step: Use this JSON with the tracked changes system!")
        print(f"   JSON → Automation → GitHub Actions → Tracked Changes DOCX")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description='AI Policy Processor - Generate JSON instructions with Claude Sonnet 4'
    )
    
    # Required arguments
    parser.add_argument('--policy', required=True, help='Path to policy DOCX file')
    parser.add_argument('--prompt', required=True, help='Path to AI prompt markdown file (prompt.md)')
    parser.add_argument('--policy-instructions', 
                       help='Path to policy processing instructions (defaults to centralized config)',
                       default=get_policy_instructions_path())
    parser.add_argument('--output', required=True, help='Output path for generated JSON file')
    
    # Questionnaire input (mutually exclusive)
    questionnaire_group = parser.add_mutually_exclusive_group(required=True)
    questionnaire_group.add_argument('--questionnaire', help='Path to questionnaire CSV/JSON file')
    questionnaire_group.add_argument('--questionnaire-env-data', action='store_true',
                                    help='Read questionnaire data from QUESTIONNAIRE_ANSWERS_DATA environment variable')
    
    # Optional arguments
    parser.add_argument('--api-key', help='Claude API key (or set CLAUDE_API_KEY env var)')
    parser.add_argument('--skip-api', action='store_true', 
                       help='Skip API call and use existing JSON file (for testing/development)')
    
    return parser


def validate_arguments(args) -> None:
    """Validate command line arguments."""
    if not args.questionnaire and not args.questionnaire_env_data:
        print("❌ Error: Either --questionnaire (file path) or --questionnaire-env-data must be provided!")
        sys.exit(1)
    
    if args.questionnaire and args.questionnaire_env_data:
        print("❌ Error: Cannot use both --questionnaire and --questionnaire-env-data at the same time!")
        sys.exit(1)


def main():
    """Main entry point for the AI policy processor."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Create and run the processor
    processor = PolicyProcessor(args)
    processor.process()


if __name__ == "__main__":
    main()
