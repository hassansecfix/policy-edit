"""
Document Processing Utilities

This module provides utilities for document processing operations,
including highlighting cleanup, document preparation, and validation.
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Tuple, Optional


class DocumentProcessor:
    """
    Handles document processing operations like highlighting cleanup and preparation.
    """
    
    @staticmethod
    def clean_document_highlighting(input_path: str) -> Tuple[str, bool]:
        """
        Create a clean copy of the input document with highlighting removed.
        
        Args:
            input_path: Path to the input document
            
        Returns:
            Tuple of (cleaned_file_path, success_flag)
        """
        print("🎨 Pre-processing: Removing default highlighting from source document...")
        
        # Create a temporary cleaned copy for processing
        cleaned_path = input_path.replace('.docx', '_cleaned_for_processing.docx')
        
        try:
            # First copy the original to our temp location
            shutil.copy2(input_path, cleaned_path)
            print(f"📄 Created working copy: {cleaned_path}")
            
            # Clean highlighting using python-docx (safe method)
            success = DocumentProcessor._remove_highlighting(cleaned_path)
            
            if success:
                print("✅ Successfully removed highlighting from working copy")
                return cleaned_path, True
            else:
                print("⚠️ Could not clean highlighting")
                print("⚠️ Proceeding with original document (may contain highlighting)")
                # Clean up the failed copy
                if os.path.exists(cleaned_path):
                    os.unlink(cleaned_path)
                return input_path, False
                
        except Exception as e:
            print(f"⚠️ Error during highlighting cleanup: {e}")
            print("⚠️ Proceeding with original document (may contain highlighting)")
            # Clean up the failed copy
            if os.path.exists(cleaned_path):
                os.unlink(cleaned_path)
            return input_path, False
    
    @staticmethod
    def _remove_highlighting(file_path: str) -> bool:
        """
        Remove highlighting from a document using the ai_policy_processor function.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add the scripts directory to Python path to import our cleaning function
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if script_dir not in sys.path:
                sys.path.append(script_dir)
            
            from ai_policy_processor import clean_docx_highlighting
            
            # Clean highlighting from the working copy
            success, message = clean_docx_highlighting(file_path)
            
            if success:
                print(f"✅ Highlighting removal: {message}")
                return True
            else:
                print(f"⚠️ Highlighting removal failed: {message}")
                return False
                
        except Exception as e:
            print(f"⚠️ Error during highlighting cleanup: {e}")
            return False
    
    @staticmethod
    def check_highlighting_only_mode() -> bool:
        """
        Check if we're in highlighting-only mode (for testing).
        
        Returns:
            True if highlighting-only mode is enabled
        """
        return os.environ.get('HIGHLIGHTING_ONLY', '').lower() in ['true', '1', 'yes', 'on']
    
    @staticmethod
    def handle_highlighting_only_mode(input_path: str, output_path: str, cleaned_path: Optional[str] = None) -> None:
        """
        Handle highlighting-only mode by copying cleaned document to output.
        
        Args:
            input_path: Original input document path
            output_path: Where to save the output
            cleaned_path: Path to cleaned document (if available)
        """
        print("🧪 HIGHLIGHTING_ONLY mode enabled - skipping LibreOffice processing")
        print("🎨 Only removing highlighting and saving clean document")
        
        source_path = cleaned_path if cleaned_path else input_path
        
        try:
            shutil.copy2(source_path, output_path)
            print(f"✅ Saved highlight-cleaned document to: {output_path}")
            print("🔍 Please check if highlighting has been removed from the output document")
            
            # Clean up temporary files
            if cleaned_path and cleaned_path != input_path and os.path.exists(cleaned_path):
                try:
                    os.unlink(cleaned_path)
                    print(f"🧹 Cleaned up temporary file: {cleaned_path}")
                except Exception as e:
                    print(f"⚠️ Could not clean up temporary file: {e}")
                    
        except Exception as e:
            print(f"❌ Failed to copy document: {e}")
            raise
    
    @staticmethod
    def validate_input_files(input_path: str, csv_path: str) -> None:
        """
        Validate that required input files exist.
        
        Args:
            input_path: Path to input DOCX file
            csv_path: Path to CSV/JSON file
            
        Raises:
            SystemExit: If files don't exist
        """
        if not os.path.exists(input_path):
            print("Input DOCX not found:", input_path, file=sys.stderr)
            sys.exit(2)
        if not os.path.exists(csv_path):
            print("CSV/JSON not found:", csv_path, file=sys.stderr)
            sys.exit(2)
    
    @staticmethod
    def check_document_content(doc) -> None:
        """
        Debug function to check document content accessibility.
        
        Args:
            doc: LibreOffice document object
        """
        try:
            print("🔍 DEBUG: Checking if LibreOffice sees any highlighting in the loaded document...")
            # Simple check - count paragraphs to verify document is loaded
            paragraphs = doc.getText().createEnumeration()
            para_count = 0
            while paragraphs.hasMoreElements():
                para_count += 1
                if para_count > 10:  # Don't count all paragraphs, just verify we can access content
                    break
            print(f"🔍 DEBUG: Document has at least {para_count} paragraphs accessible to LibreOffice")
        except Exception as e:
            print(f"🔍 DEBUG: Error checking document content: {e}")
    
    @staticmethod
    def verify_final_document(output_path: str) -> None:
        """
        Verify the final document for highlighting presence.
        
        Args:
            output_path: Path to the output document
        """
        try:
            print("🔍 DEBUG: Checking saved document for highlighting with python-docx...")
            
            # Add the scripts directory to Python path
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if script_dir not in sys.path:
                sys.path.append(script_dir)
            
            from ai_policy_processor import clean_docx_highlighting
            
            # Create a test copy to check highlighting without modifying the output
            test_path = output_path.replace('.docx', '_test_check.docx')
            shutil.copy2(output_path, test_path)
            
            # Try to clean highlighting from the test copy
            success, message = clean_docx_highlighting(test_path)
            
            if "Removed highlighting from" in message:
                highlighting_count = message.split("Removed highlighting from ")[1].split(" text runs")[0]
                print(f"⚠️ DEBUG: Found {highlighting_count} highlighted text runs in the final output!")
                print("⚠️ DEBUG: This means LibreOffice processing restored highlighting somehow")
            else:
                print("✅ DEBUG: No highlighting found in final output - all clean!")
            
            # Clean up test file
            if os.path.exists(test_path):
                os.unlink(test_path)
                
        except Exception as e:
            print(f"🔍 DEBUG: Could not check final document for highlighting: {e}")
    
    @staticmethod
    def cleanup_temporary_files(*file_paths: str) -> None:
        """
        Clean up temporary files created during processing.
        
        Args:
            *file_paths: Variable number of file paths to clean up
        """
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                    print(f"🧹 Cleaned up temporary file: {file_path}")
                except Exception as e:
                    print(f"⚠️ Could not clean up temporary file {file_path}: {e}")


def bool_from_str(s, default=False):
    """
    Convert string to boolean value.
    
    Args:
        s: String value to convert
        default: Default value if conversion fails
        
    Returns:
        Boolean value
    """
    if s is None:
        return default
    s = str(s).strip().lower()
    return s in ("1", "true", "yes", "y")
