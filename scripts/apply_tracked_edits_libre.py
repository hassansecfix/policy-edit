#!/usr/bin/env python3
"""
Apply Find/Replace edits to a DOCX using LibreOffice in headless mode,
recording each change as a tracked change (accept/rejectable).

Run with LibreOffice's bundled Python so the 'uno' module is available, e.g.:
  macOS : /Applications/LibreOffice.app/Contents/Resources/python
  Linux : /usr/lib/libreoffice/program/python
  Win   : "C:\\Program Files\\LibreOffice\\program\\python.exe"

Usage:
  python apply_tracked_edits_libre.py --in input.docx --csv edits.csv --out output.docx [--launch]

Flags:
  --launch  : try to start a headless LibreOffice listener automatically
              (socket: 127.0.0.1:2002, urp)

CSV columns (header optional, but recommended):
  Find,Replace,MatchCase,WholeWord,Wildcards,Description,Rule,Comment,Author
  - Booleans: TRUE/FALSE, Yes/No, 1/0
  - Wildcards uses ICU regex (standard regex).
  - Comment: Optional comment to add to the tracked change
  - Author: Author name for the tracked change and comment
"""

import argparse
import os
import sys
from pathlib import Path

# Add lib directory to path for our custom modules
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

# Import our modular utilities
from libre_office_utils import LibreOfficeManager
from document_processing import DocumentProcessor, bool_from_str
from instruction_parser import EditFileReader, validate_format
from logo_processing import LogoProcessor
from comment_utils import CommentManager


class TrackedChangesProcessor:
    """
    Main processor for applying tracked changes to DOCX documents using LibreOffice.
    """
    
    def __init__(self, args):
        """Initialize the processor with command line arguments."""
        self.args = args
        self.lo_manager = LibreOfficeManager(fast_mode=args.fast)
        
        # Validate input files
        DocumentProcessor.validate_input_files(args.in_path, args.csv_path)
        
        # Convert paths to absolute
        self.input_path = os.path.abspath(args.in_path)
        self.output_path = os.path.abspath(args.out_path)
        self.csv_path = os.path.abspath(args.csv_path)
    
    def process(self) -> None:
        """Execute the complete tracked changes processing workflow."""
        try:
            # Step 1: Document preparation and highlighting cleanup
            cleaned_input_path, cleanup_success = self._prepare_document()
            
            # Check for highlighting-only mode
            if DocumentProcessor.check_highlighting_only_mode():
                DocumentProcessor.handle_highlighting_only_mode(
                    self.input_path, self.output_path, 
                    cleaned_input_path if cleanup_success else None)
                return
            
            # Step 2: Setup LibreOffice connection
            self._setup_libreoffice()
            
            # Step 3: Load and process document
            doc = self._load_document(cleaned_input_path if cleanup_success else self.input_path)
            
            try:
                # Step 4: Process operations
                self._process_all_operations(doc)
                
                # Step 5: Save document
                self.lo_manager.save_document(doc, self.output_path)
                
                # Step 6: Verify final document
                DocumentProcessor.verify_final_document(self.output_path)
                
            finally:
                # Always close document
                try:
                    doc.close(True)
                except:
                    pass
            
        finally:
            # Cleanup temporary files
            if cleanup_success and cleaned_input_path != self.input_path:
                DocumentProcessor.cleanup_temporary_files(cleaned_input_path)
    
    def _prepare_document(self) -> tuple:
        """
        Prepare document by removing highlighting.
        
        Returns:
            Tuple of (cleaned_path, success_flag)
        """
        return DocumentProcessor.clean_document_highlighting(self.input_path)
    
    def _setup_libreoffice(self) -> None:
        """Setup LibreOffice connection."""
        if self.args.launch:
            self.lo_manager.ensure_listener()
        
        if not self.lo_manager.connect():
            sys.exit(1)
    
    def _load_document(self, document_path: str):
        """Load document and setup basic properties."""
        doc = self.lo_manager.load_document(document_path)
        
        # Check document content accessibility
        DocumentProcessor.check_document_content(doc)
        
        # Setup document author and properties - ALWAYS use Secfix AI
        self.lo_manager.setup_document_author(doc, "Secfix AI")
        
        # Initially disable tracking - will be enabled after logo operations
        self.lo_manager.enable_tracking(doc, enabled=False)
        
        return doc
    
    def _process_all_operations(self, doc) -> None:
        """Process all operations: logos, comments, and text replacements."""
        # Step 1: Process logo operations FIRST (without tracking)
        self._process_logo_operations(doc)
        
        # Step 2: Enable tracking for all subsequent operations
        print(f"🔄 Enabling tracking for text replacements and other changes...")
        self.lo_manager.enable_tracking(doc, enabled=True)
        print(f"✅ Tracking enabled - all subsequent changes will be tracked")
        
        # Step 3: Process comment-only operations
        self._process_comment_operations(doc)
        
        # Step 4: Process text replacement operations
        self._process_text_replacements(doc)
    
    def _process_logo_operations(self, doc) -> None:
        """Process logo replacement operations."""
        if not self.csv_path.endswith('.json'):
            return
        
        # Get operations and metadata (v5.2 format)
        all_operations = list(EditFileReader.read_edits(self.csv_path))
        metadata = EditFileReader.get_metadata(self.csv_path)
        
        # Process logo operations
        logo_processor = LogoProcessor(doc)
        logo_processor.process_logo_operations(all_operations, metadata)
    
    def _process_comment_operations(self, doc) -> None:
        """Process comment-only operations."""
        if not self.csv_path.endswith('.json'):
            return
        
        # Get comment operations (v5.2 format)
        all_operations = list(EditFileReader.get_comment_operations(self.csv_path))
        
        # Process comments
        comment_manager = CommentManager(doc, self.lo_manager.smgr)
        comment_manager.process_comment_operations(all_operations)
    
    def _process_text_replacements(self, doc) -> None:
        """Process text replacement operations with tracked changes."""
        comment_manager = CommentManager(doc, self.lo_manager.smgr)
        
        # Validate format before processing
        if not validate_format(self.csv_path):
            raise ValueError(f"File {self.csv_path} is not in valid format")
        
        for row in EditFileReader.read_edits(self.csv_path):
            find = (row.get("target_text") or "").strip()
            repl = (row.get("replacement") or "")
            if not find:
                continue
            
            # v5.2 format uses simple replacement - no complex matching options needed
            match_case = True  # Make all text operations case sensitive
            whole_word = False  # AI has already determined exact target_text
            wildcards = False   # AI has already determined exact target_text
            comment_text = (row.get("comment") or "").strip()
            author_name = (row.get("comment_author") or "Secfix AI").strip()
            
            # SAFETY: Ensure author is always Secfix AI (override any other values)
            if author_name != "Secfix AI":
                print(f"⚠️ Author was '{author_name}', overriding to 'Secfix AI'")
                author_name = "Secfix AI"
            
            # CRITICAL: Set author BEFORE EVERY SINGLE REPLACEMENT
            print(f"🚨 SETTING AUTHOR TO '{author_name}' BEFORE PROCESSING '{find}'")
            comment_manager.update_document_author(author_name)
            
            # DOUBLE CHECK: Also set it directly on the document
            try:
                doc.setPropertyValue("RedlineAuthor", author_name)
                print(f"✅ Double-confirmed RedlineAuthor = '{author_name}' for this replacement")
            except Exception as e:
                print(f"❌ Failed double-check: {e}")
            
            # Perform replacement
            replaced_count, prev_redlines_count = self._perform_replacement(
                doc, find, repl, match_case, whole_word, wildcards)
            
            # Add comment if provided and replacements were made
            if comment_text and replaced_count > 0:
                print(f"🔍 DEBUG: About to add comment for '{find}' -> '{repl}': '{comment_text[:80]}...'")
                
                # CRITICAL: Force LibreOffice to flush/commit tracked changes before accessing redlines
                try:
                    # Method 1: Force document update
                    doc.update()
                    print(f"🔄 DEBUG: Forced document update after replacement")
                except Exception as e1:
                    print(f"🔍 DEBUG: Document update failed: {e1}")
                
                try:
                    # Method 2: Force redlines refresh  
                    doc.getPropertyValue("RecordChanges")  # Just accessing this can force refresh
                    print(f"🔄 DEBUG: Accessed RecordChanges property to force refresh")
                except Exception as e2:
                    print(f"🔍 DEBUG: RecordChanges access failed: {e2}")
                
                comment_manager.add_comment_to_replacements(
                    find, repl, comment_text, author_name, 
                    match_case, whole_word, prev_redlines_count)
            elif comment_text and replaced_count == 0:
                print(f"❌ DEBUG: Comment not added because no replacements made for '{find}'")
            elif not comment_text:
                print(f"🔍 DEBUG: No comment to add for '{find}'")
            
            # Log results
            if replaced_count > 0:
                if self.args.fast and replaced_count > 10:
                    print(f"⚡ Replaced {replaced_count} occurrences by {author_name} (fast mode)")
                else:
                    print(f"Replaced {replaced_count} occurrence(s) of '{find}' with '{repl}' by {author_name}")
    
    def _perform_replacement(self, doc, find: str, repl: str, match_case: bool, 
                           whole_word: bool, wildcards: bool) -> tuple:
        """
        Perform text replacement and return counts.
        
        Returns:
            Tuple of (replaced_count, previous_redlines_count)
        """
        # Capture redlines count before replacement
        prev_redlines_count = 0
        try:
            prev_redlines = doc.getPropertyValue("Redlines")
            if prev_redlines:
                prev_redlines_count = prev_redlines.getCount()
        except Exception:
            prev_redlines_count = 0
        
        # DEBUG: Test if the text can be found at all
        print(f"🔍 DEBUG SEARCH: Looking for '{find}' in document...")
        search_desc = doc.createSearchDescriptor()
        search_desc.SearchString = find
        search_desc.SearchCaseSensitive = match_case
        search_desc.SearchWords = whole_word
        test_find = doc.findFirst(search_desc)
        
        if test_find:
            found_text = test_find.getString()
            print(f"✅ DEBUG SEARCH: Found text: '{found_text}'")
            print(f"🔍 DEBUG SEARCH: Text length: {len(found_text)} vs search length: {len(find)}")
        else:
            print(f"❌ DEBUG SEARCH: Text '{find}' NOT FOUND in document!")
            # Try case-insensitive search as fallback
            search_desc.SearchCaseSensitive = False
            test_find_ci = doc.findFirst(search_desc)
            if test_find_ci:
                found_text_ci = test_find_ci.getString()
                print(f"💡 DEBUG SEARCH: Found case-insensitive: '{found_text_ci}'")
            else:
                print(f"❌ DEBUG SEARCH: Not found even with case-insensitive search")
        
        # Create replace descriptor
        rd = doc.createReplaceDescriptor()
        rd.SearchString = find
        rd.ReplaceString = repl
        rd.SearchCaseSensitive = match_case
        rd.SearchWords = whole_word
        
        # Use ICU regex if requested
        try:
            rd.setPropertyValue("RegularExpressions", bool(wildcards))
        except Exception:
            pass
        
        # Perform the replacement
        count_replaced = doc.replaceAll(rd)
        print(f"🔍 DEBUG REPLACEMENT: Replaced {count_replaced} occurrences of '{find}'")
        
        return count_replaced, prev_redlines_count


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Apply tracked edits to DOCX via LibreOffice (headless UNO).")
    
    parser.add_argument("--in", dest="in_path", required=True, 
                       help="Input .docx")
    parser.add_argument("--csv", dest="csv_path", required=True, 
                       help="CSV with columns: Find,Replace,MatchCase,WholeWord,Wildcards OR JSON with operations format")
    parser.add_argument("--out", dest="out_path", required=True, 
                       help="Output .docx (will be overwritten)")
    parser.add_argument("--launch", action="store_true", 
                       help="Launch a headless LibreOffice UNO listener if not already running")
    parser.add_argument("--logo", dest="logo_path", 
                       help="Optional path to company logo image (png/jpg) to insert in header")
    parser.add_argument("--questionnaire", dest="questionnaire_csv", 
                       help="Optional path to questionnaire CSV for logo URL extraction")
    parser.add_argument("--fast", action="store_true", 
                       help="Enable fast mode: use shorter timeouts, minimal retries, optimized logo downloads")
    
    return parser


def main():
    """Main entry point for the tracked changes processor."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Create and run processor
    processor = TrackedChangesProcessor(args)
    processor.process()


if __name__ == "__main__":
    main()
