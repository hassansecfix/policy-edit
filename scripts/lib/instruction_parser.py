"""
Simple Edit Instruction Parser

This module provides a streamlined parser for JSON operations where
AI has already made ALL grammar decisions upfront.

No grammar analyzer needed - just apply the AI decisions directly.
"""

import json
from pathlib import Path
from typing import Iterator, Dict, Any


class EditFileReader:
    """
    Simplified reader for JSON operations.
    
    Assumes AI has already made all grammar decisions upfront:
    - target_text is final (placeholder OR full sentence)
    - replacement is final (user response OR restructured sentence)
    - No downstream analysis needed
    """
    
    @staticmethod
    def read_edits(file_path: str) -> Iterator[Dict[str, str]]:
        """
        Load edits from JSON format.
        
        Args:
            file_path: Path to the JSON file
            
        Yields:
            Dictionary containing edit instructions ready for direct application
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        operations = data.get('instructions', {}).get('operations', [])
        
        for op in operations:
            action = op.get('action', 'replace')
            target_text = op.get('target_text', '')
            replacement = op.get('replacement', '')
            comment = op.get('comment', '')
            author = op.get('comment_author', 'Secfix AI')
            
            # Skip comment-only operations (handled separately)
            if action == 'comment':
                continue
                
            # Handle delete operations (empty replacement)
            if action == 'delete':
                replacement = ''
            
            # Handle replace operations - AI has already decided everything
            elif action == 'replace':
                # No processing needed - AI has already determined:
                # - target_text (placeholder OR full sentence)
                # - replacement (user response OR restructured sentence)
                pass
            
            # Handle logo replacement
            elif action == 'replace_with_logo':
                replacement = ''  # Logo will be handled by LibreOffice automation
            
            # Unknown action - skip with warning
            else:
                print(f"⚠️  Unknown action '{action}' - skipping operation")
                continue
            
            yield {
                'target_text': target_text,
                'replacement': replacement,
                'comment': comment,
                'comment_author': author,
                'action': action
            }
    
    @staticmethod
    def get_metadata(file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dictionary containing metadata
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get('metadata', {})
    
    @staticmethod
    def get_comment_operations(file_path: str) -> Iterator[Dict[str, str]]:
        """
        Get comment-only operations from JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Yields:
            Dictionary containing comment-only operations
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        operations = data.get('instructions', {}).get('operations', [])
        
        for op in operations:
            if op.get('action') == 'comment':
                yield {
                    'target_text': op.get('target_text', ''),
                    'comment': op.get('comment', ''),
                    'comment_author': op.get('comment_author', 'Secfix AI'),
                    'action': 'comment'
                }


def validate_format(file_path: str) -> bool:
    """
    Validate that the JSON file follows the expected format.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        True if valid format, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check required structure
        if 'metadata' not in data:
            print("❌ Missing 'metadata' section")
            return False
        
        if 'instructions' not in data:
            print("❌ Missing 'instructions' section")
            return False
        
        if 'operations' not in data['instructions']:
            print("❌ Missing 'operations' array")
            return False
        
        # Check format version
        format_version = data['metadata'].get('format_version', '')
        if 'ai_decision' not in format_version:
            print(f"⚠️  Format version '{format_version}' may not be fully compatible")
        
        # Check operations format
        operations = data['instructions']['operations']
        for i, op in enumerate(operations):
            required_fields = ['target_text', 'action', 'replacement', 'comment']
            for field in required_fields:
                if field not in op:
                    print(f"❌ Operation {i}: Missing required field '{field}'")
                    return False
            
            # Check for deprecated fields
            deprecated_fields = ['context', 'placeholder', 'user_response']
            for field in deprecated_fields:
                if field in op:
                    print(f"⚠️  Operation {i}: Contains deprecated field '{field}' - old format")
        
        print("✅ Valid format")
        return True
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False


# Backward compatibility function
def read_edits(file_path: str) -> Iterator[Dict[str, str]]:
    """
    Backward compatibility function for existing code.
    
    Args:
        file_path: Path to the JSON file
        
    Yields:
        Dictionary containing edit instructions
    """
    return EditFileReader.read_edits(file_path)
