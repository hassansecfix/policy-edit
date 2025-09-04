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
                comment_manager.add_comment_to_replacements(
                    find, repl, comment_text, author_name, 
                    match_case, whole_word, prev_redlines_count)
            
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
        
        # Perform the replacement in main document
        count_replaced = doc.replaceAll(rd)
        
        # If no replacement in main doc, try headers and footers
        if count_replaced == 0:
            count_replaced = self._try_header_footer_replacement(doc, find, repl, match_case, whole_word)
        
        # If still no replacement and it's complex text, try flexible search
        if count_replaced == 0 and (len(find) > 10 or " " in find):
            print(f"⚠️ Primary replacement failed for '{find[:50]}...', trying flexible search...")
            count_replaced = self._try_flexible_replacement(doc, find, repl, match_case)
        
        return count_replaced, prev_redlines_count
    
    def _try_header_footer_replacement(self, doc, find: str, repl: str, match_case: bool, whole_word: bool) -> int:
        """Try replacement in document headers and footers."""
        total_replaced = 0
        
        try:
            # Get all page styles
            page_styles = doc.getStyleFamilies().getByName("PageStyles")
            
            for i in range(page_styles.getCount()):
                page_style = page_styles.getByIndex(i)
                
                # Check headers
                if page_style.getPropertyValue("HeaderIsOn"):
                    header_text = page_style.getPropertyValue("HeaderText")
                    replaced = self._replace_in_text_content(header_text, find, repl, match_case, whole_word, "header")
                    total_replaced += replaced
                
                # Check footers  
                if page_style.getPropertyValue("FooterIsOn"):
                    footer_text = page_style.getPropertyValue("FooterText")
                    replaced = self._replace_in_text_content(footer_text, find, repl, match_case, whole_word, "footer")
                    total_replaced += replaced
            
            if total_replaced > 0:
                print(f"✅ Header/Footer replacement succeeded: {total_replaced} occurrences")
                
        except Exception as e:
            print(f"⚠️ Header/Footer replacement failed: {e}")
        
        return total_replaced
    
    def _replace_in_text_content(self, text_content, find: str, repl: str, match_case: bool, whole_word: bool, location: str) -> int:
        """Replace text within a specific text content (header/footer)."""
        try:
            # Create replace descriptor for this text content
            rd = text_content.createReplaceDescriptor()
            rd.SearchString = find
            rd.ReplaceString = repl
            rd.SearchCaseSensitive = match_case
            rd.SearchWords = whole_word
            
            # Perform replacement
            count_replaced = text_content.replaceAll(rd)
            
            if count_replaced > 0:
                print(f"✅ Found and replaced {count_replaced} occurrence(s) in {location}")
            
            return count_replaced
            
        except Exception as e:
            print(f"⚠️ Replacement in {location} failed: {e}")
            return 0
    
    def _try_flexible_replacement(self, doc, find: str, repl: str, match_case: bool) -> int:
        """Try flexible replacement for text that might have line breaks or formatting."""
        
        # Strategy 1: Flexible whitespace regex (handles line breaks, multiple spaces)
        flexible_pattern = find.replace(" ", r"\s+")
        count_replaced = self._try_regex_replacement(doc, flexible_pattern, repl, match_case, "whitespace-flexible")
        if count_replaced > 0:
            return count_replaced
        
        # Strategy 2: Case-insensitive search if original was case-sensitive
        if match_case:
            count_replaced = self._try_case_insensitive_replacement(doc, find, repl)
            if count_replaced > 0:
                return count_replaced
        
        # Strategy 3: Remove punctuation and try again (for text with periods, commas, etc.)
        import re
        clean_find = re.sub(r'[^\w\s]', '', find)  # Remove punctuation
        if clean_find != find:
            count_replaced = self._try_regex_replacement(doc, clean_find.replace(" ", r"\s+"), repl, False, "punctuation-free")
            if count_replaced > 0:
                return count_replaced
        
        # Strategy 4: Word-by-word fuzzy matching
        count_replaced = self._try_fuzzy_word_matching(doc, find, repl, match_case)
        if count_replaced > 0:
            return count_replaced
        
        # Strategy 5: Partial text matching (for very long strings)
        if len(find) > 50:
            # Try matching just the first part of the text
            first_part = find[:30].strip()
            count_replaced = self._try_partial_text_replacement(doc, find, first_part, repl, match_case)
            if count_replaced > 0:
                return count_replaced
        
        print(f"❌ All {5} flexible replacement strategies failed for '{find[:50]}...'")
        return 0
    
    def _try_regex_replacement(self, doc, pattern: str, repl: str, match_case: bool, strategy_name: str) -> int:
        """Try regex-based replacement."""
        try:
            rd = doc.createReplaceDescriptor()
            rd.SearchString = pattern
            rd.ReplaceString = repl
            rd.SearchCaseSensitive = match_case
            rd.SearchWords = False
            rd.setPropertyValue("RegularExpressions", True)
            
            count_replaced = doc.replaceAll(rd)
            if count_replaced > 0:
                print(f"✅ {strategy_name} regex replacement succeeded: {count_replaced} occurrences")
            return count_replaced
        except Exception as e:
            print(f"⚠️ {strategy_name} regex failed: {e}")
            return 0
    
    def _try_case_insensitive_replacement(self, doc, find: str, repl: str) -> int:
        """Try case-insensitive replacement."""
        try:
            rd = doc.createReplaceDescriptor()
            rd.SearchString = find
            rd.ReplaceString = repl
            rd.SearchCaseSensitive = False  # Case insensitive
            rd.SearchWords = False
            
            count_replaced = doc.replaceAll(rd)
            if count_replaced > 0:
                print(f"✅ Case-insensitive replacement succeeded: {count_replaced} occurrences")
            return count_replaced
        except Exception:
            return 0
    
    def _try_fuzzy_word_matching(self, doc, find: str, repl: str, match_case: bool) -> int:
        """Try fuzzy word-by-word matching."""
        words = find.split()
        if len(words) < 2:
            return 0
        
        try:
            # Search for the first few words as a phrase
            search_phrase = " ".join(words[:min(3, len(words))])
            search_desc = doc.createSearchDescriptor()
            search_desc.SearchString = search_phrase
            search_desc.SearchCaseSensitive = match_case
            search_desc.SearchWords = False
            
            found_range = doc.findFirst(search_desc)
            replaced_count = 0
            
            while found_range and replaced_count == 0:
                try:
                    # Expand range to capture full text
                    text_cursor = found_range.getText().createTextCursorByRange(found_range)
                    text_cursor.goRight(len(find) + 50, True)  # Extra buffer for formatting
                    expanded_text = text_cursor.getString()
                    
                    # Normalize whitespace for comparison
                    normalized_expanded = ' '.join(expanded_text.split())
                    normalized_find = ' '.join(find.split())
                    
                    if (match_case and normalized_find in normalized_expanded) or \
                       (not match_case and normalized_find.lower() in normalized_expanded.lower()):
                        # Found a match, replace the entire expanded range
                        text_cursor.setString(repl)
                        replaced_count = 1
                        print(f"✅ Fuzzy word matching succeeded: {replaced_count} occurrences")
                        break
                        
                except Exception as e:
                    print(f"⚠️ Fuzzy matching error: {e}")
                    break
                
                # Find next occurrence
                found_range = doc.findNext(found_range, search_desc)
            
            return replaced_count
        except Exception as e:
            print(f"⚠️ Fuzzy word matching failed: {e}")
            return 0
    
    def _try_partial_text_replacement(self, doc, full_find: str, partial_find: str, repl: str, match_case: bool) -> int:
        """Try finding by partial text then replacing full context."""
        try:
            search_desc = doc.createSearchDescriptor()
            search_desc.SearchString = partial_find
            search_desc.SearchCaseSensitive = match_case
            search_desc.SearchWords = False
            
            found_range = doc.findFirst(search_desc)
            replaced_count = 0
            
            while found_range and replaced_count == 0:
                try:
                    # Expand to get more context
                    text_cursor = found_range.getText().createTextCursorByRange(found_range)
                    text_cursor.goRight(len(full_find) + 100, True)
                    expanded_text = text_cursor.getString()
                    
                    # Check if the full text is present in the expanded area
                    normalized_expanded = ' '.join(expanded_text.split())
                    normalized_full = ' '.join(full_find.split())
                    
                    if (match_case and normalized_full in normalized_expanded) or \
                       (not match_case and normalized_full.lower() in normalized_expanded.lower()):
                        # Replace the full context
                        text_cursor.setString(repl)
                        replaced_count = 1
                        print(f"✅ Partial text replacement succeeded: {replaced_count} occurrences")
                        break
                        
                except Exception as e:
                    print(f"⚠️ Partial text replacement error: {e}")
                    break
                
                found_range = doc.findNext(found_range, search_desc)
            
            return replaced_count
        except Exception as e:
            print(f"⚠️ Partial text replacement failed: {e}")
            return 0


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
