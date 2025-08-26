"""
Logo Processing Utilities

This module provides utilities for logo insertion and positioning in LibreOffice documents,
including dynamic spacing calculations and multiple insertion strategies.
"""

import os
import re
from typing import Any, Dict, List, Optional, Tuple
from libre_office_utils import to_url


# Configuration constants
LOGO_SPACES_THRESHOLD = -14  # Additional spaces to remove on top of replacement text length


class LogoProcessor:
    """
    Handles logo replacement operations in LibreOffice documents.
    """
    
    def __init__(self, doc: Any):
        """
        Initialize logo processor.
        
        Args:
            doc: LibreOffice document object
        """
        self.doc = doc
        self.dynamic_spaces_to_remove = 0
    
    def process_logo_operations(self, operations: List[Dict[str, Any]], metadata: Dict[str, Any]) -> None:
        """
        Process all logo replacement operations.
        
        Args:
            operations: List of all operations from JSON
            metadata: Metadata containing logo information
        """
        # Find logo operations
        logo_operations = [op for op in operations if op.get('action') == 'replace_with_logo']
        if not logo_operations:
            return
        
        print(f"🖼️  Processing {len(logo_operations)} logo operations BEFORE tracking...")
        
        # DISABLE TRACKING COMPLETELY for logo operations
        self.doc.RecordChanges = False
        
        # Calculate dynamic spacing based on company name replacement
        self._calculate_dynamic_spacing(operations)
        
        # Process each logo operation
        for logo_op in logo_operations:
            self._process_single_logo_operation(logo_op, metadata)
    
    def _calculate_dynamic_spacing(self, operations: List[Dict[str, Any]]) -> None:
        """
        Calculate dynamic spacing based on company name replacement.
        
        Args:
            operations: List of all operations
        """
        # Look for company name replacement to calculate dynamic spacing
        for op in operations:
            if (op.get('action') == 'replace' and 
                op.get('target_text', '').strip() == '<Company name, address>'):
                target_text_op = op.get('target_text', '').strip()
                replacement_text = op.get('replacement', '')
                if replacement_text:
                    target_length = len(target_text_op)
                    replacement_length = len(replacement_text)
                    length_difference = replacement_length - target_length
                    self.dynamic_spaces_to_remove = length_difference + LOGO_SPACES_THRESHOLD
                    print(f"📏 Found company name replacement:")
                    print(f"📏   Target: '{target_text_op}' ({target_length} chars)")
                    print(f"📏   Replacement: '{replacement_text}' ({replacement_length} chars)")
                    print(f"📏   Difference: {replacement_length} - {target_length} = {length_difference}")
                    print(f"📏   Dynamic spaces to remove: {length_difference} + {LOGO_SPACES_THRESHOLD} = {self.dynamic_spaces_to_remove}")
                    break
    
    def _process_single_logo_operation(self, logo_op: Dict[str, Any], metadata: Dict[str, Any]) -> None:
        """
        Process a single logo replacement operation.
        
        Args:
            logo_op: Logo operation dictionary
            metadata: Metadata containing logo information
        """
        target_text = logo_op.get('target_text', '')
        print(f"🔍 Looking for logo placeholder: '{target_text}'")
        
        # Get logo file path from metadata
        logo_file_path = self._get_logo_file_path(metadata)
        
        if logo_file_path and os.path.exists(logo_file_path):
            self._insert_logo_with_spacing(target_text, logo_file_path)
        else:
            print(f"⚠️  No user logo data found - skipping logo replacement")
    
    def _get_logo_file_path(self, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Get logo file path from metadata.
        
        Args:
            metadata: Metadata dictionary containing logo information
            
        Returns:
            Logo file path if found, None otherwise
        """
        try:
            # Check for logo_path in metadata (your existing structure)
            if 'logo_path' in metadata:
                logo_path = metadata['logo_path']
                print(f"🔍 Found logo_path in metadata: {logo_path}")
                
                # Check if it's a relative path and make it absolute
                if not os.path.isabs(logo_path):
                    # Try to find it relative to the current working directory
                    current_dir = os.getcwd()
                    absolute_path = os.path.join(current_dir, logo_path)
                    if os.path.exists(absolute_path):
                        print(f"✅ Logo file found at: {absolute_path}")
                        return absolute_path
                    else:
                        print(f"⚠️  Logo file not found at: {absolute_path}")
                        
                        # Try to find it in the edits directory
                        edits_dir = os.path.join(current_dir, 'edits')
                        edits_path = os.path.join(edits_dir, os.path.basename(logo_path))
                        if os.path.exists(edits_path):
                            print(f"✅ Logo file found in edits directory: {edits_path}")
                            return edits_path
                        else:
                            print(f"⚠️  Logo file not found in edits directory: {edits_path}")
                            
                            # Try to find any PNG/JPG file in edits directory
                            for file in os.listdir(edits_dir):
                                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                                    found_path = os.path.join(edits_dir, file)
                                    print(f"🔍 Found image file in edits directory: {found_path}")
                                    return found_path
            
            # Fallback: look for any image file in the edits directory
            current_dir = os.getcwd()
            edits_dir = os.path.join(current_dir, 'edits')
            
            if os.path.exists(edits_dir):
                for file in os.listdir(edits_dir):
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        found_path = os.path.join(edits_dir, file)
                        print(f"🔍 Found image file in edits directory: {found_path}")
                        return found_path
            
            print(f"⚠️  No logo file found in metadata or edits directory")
            return None
            
        except Exception as e:
            print(f"❌ Error getting logo file path: {e}")
            return None
    
    def _insert_logo_with_spacing(self, target_text: str, logo_file_path: str) -> None:
        """
        Insert logo with proper spacing adjustments.
        
        Args:
            target_text: Text to replace with logo
            logo_file_path: Path to the logo file
        """
        print(f"🖼️  Using logo file: {logo_file_path}")
        
        # Handle spacing adjustments
        if self.dynamic_spaces_to_remove >= 0:
            print(f"🔄 Attempting to remove up to {self.dynamic_spaces_to_remove} spaces before '{target_text}' using multiple strategies")
            self._remove_spaces_and_insert_logo(target_text, logo_file_path)
        else:
            spaces_to_add = abs(self.dynamic_spaces_to_remove)
            print(f"🔄 Attempting to add {spaces_to_add} spaces before '{target_text}'")
            self._add_spaces_and_insert_logo(target_text, logo_file_path, spaces_to_add)
    
    def _add_spaces_and_insert_logo(self, target_text: str, logo_file_path: str, spaces_to_add: int) -> None:
        """
        Add spaces before target text and insert logo.
        
        Args:
            target_text: Text to replace with logo
            logo_file_path: Path to the logo file
            spaces_to_add: Number of spaces to add
        """
        print(f"🔄 Adding {spaces_to_add} spaces before ALL occurrences of '{target_text}'")
        
        # Add spaces by finding ALL targets and inserting spaces before each one
        search_desc = self.doc.createSearchDescriptor()
        search_desc.SearchString = target_text
        search_desc.SearchCaseSensitive = False
        search_desc.SearchWords = False
        
        # Find ALL occurrences and add spaces before each one
        spaces_added_count = 0
        found_range = self.doc.findFirst(search_desc)
        spaces_to_insert = " " * spaces_to_add
        
        while found_range:
            try:
                # Validate the found range before proceeding
                if not found_range or not found_range.getText():
                    print(f"⚠️ Invalid range found for occurrence #{spaces_added_count + 1}")
                    break
                
                # Get surrounding context for small content scenarios
                text_obj = found_range.getText()
                if not text_obj:
                    print(f"⚠️ No text object available for occurrence #{spaces_added_count + 1}")
                    found_range = self.doc.findNext(found_range, search_desc)
                    continue
                
                # Insert spaces before the target text
                cursor = text_obj.createTextCursorByRange(found_range)
                if not cursor:
                    print(f"⚠️ Could not create cursor for occurrence #{spaces_added_count + 1}")
                    found_range = self.doc.findNext(found_range, search_desc)
                    continue
                    
                # Collapse to start and validate cursor position
                cursor.collapseToStart()
                
                # Insert spaces with additional validation
                try:
                    cursor.getText().insertString(cursor, spaces_to_insert, False)
                    spaces_added_count += 1
                    print(f"✅ Added {spaces_to_add} spaces before logo placeholder #{spaces_added_count}")
                    
                    # For small content, verify the insertion worked
                    if spaces_added_count == 1:  # Only check first insertion to avoid too much output
                        self._verify_space_insertion(target_text, spaces_to_add)
                        
                except Exception as insert_e:
                    print(f"⚠️ Failed to insert spaces for occurrence #{spaces_added_count + 1}: {insert_e}")
                    # Try alternative space insertion method for small content
                    try:
                        self._alternative_space_insertion(found_range, spaces_to_insert)
                        spaces_added_count += 1
                        print(f"✅ Added {spaces_to_add} spaces using alternative method for occurrence #{spaces_added_count}")
                    except Exception as alt_e:
                        print(f"❌ Alternative space insertion also failed: {alt_e}")
                
                # Find next occurrence (search from current position)
                found_range = self.doc.findNext(found_range, search_desc)
                
            except Exception as e:
                print(f"⚠️ Error processing occurrence #{spaces_added_count + 1}: {e}")
                # Try to continue with next occurrence
                try:
                    found_range = self.doc.findNext(found_range, search_desc)
                except:
                    break
        
        if spaces_added_count == 0:
            print(f"⚠️ No occurrences of '{target_text}' found - no spaces added")
        else:
            print(f"✅ Added spaces before {spaces_added_count} logo placeholder(s)")
        
        # Now insert the logo directly
        logo_count = self._insert_logo_direct(target_text, logo_file_path)
        print(f"🎉 Successfully replaced {logo_count} logo placeholder(s) with user's logo after adding spaces")
    
    def _remove_spaces_and_insert_logo(self, target_text: str, logo_file_path: str) -> None:
        """
        Remove spaces before target text and insert logo.
        
        Args:
            target_text: Text to replace with logo
            logo_file_path: Path to the logo file
        """
        escaped_target = re.escape(target_text)
        replaced_count = 0
        
        # Debug - inspect surrounding text
        self._debug_surrounding_text(target_text)
        
        # Strategy 1: Try comprehensive whitespace regex
        replaced_count = self._try_whitespace_regex_strategy(escaped_target)
        
        # Strategy 2: Try tab and mixed whitespace patterns
        if replaced_count == 0:
            replaced_count = self._try_tab_whitespace_strategy(target_text)
        
        # Strategy 3: Manual space removal
        if replaced_count == 0:
            replaced_count = self._try_manual_space_strategy(target_text)
        
        print(f"🔄 Total replaced: {replaced_count} instances with temp placeholder")
        
        if replaced_count > 0:
            # Replace temp placeholder with actual logo
            logo_count = self._replace_placeholder_with_logo(logo_file_path)
            replaced_count = logo_count
        
        if replaced_count > 0:
            print(f"🎉 Successfully replaced {replaced_count} logo placeholder(s) with user's logo")
        else:
            print(f"❌ Could not find '{target_text}' in document")
    
    def _debug_surrounding_text(self, target_text: str) -> None:
        """Debug function to inspect text around the target."""
        try:
            search_desc = self.doc.createSearchDescriptor()
            search_desc.SearchString = target_text
            search_desc.SearchCaseSensitive = False
            search_desc.SearchWords = False
            
            found_range = self.doc.findFirst(search_desc)
            if found_range:
                # Get surrounding text to see what's actually there
                cursor = found_range.getText().createTextCursorByRange(found_range)
                cursor.goLeft(self.dynamic_spaces_to_remove + 5, True)
                cursor.gotoRange(found_range.getEnd(), True)
                surrounding_text = cursor.getString()
                
                # Show character codes for debugging
                char_codes = [f"'{char}'({ord(char)})" for char in surrounding_text[-50:]]
                print(f"🔍 Debug: Text around target (last 50 chars): {' '.join(char_codes)}")
                print(f"🔍 Debug: Full surrounding text: '{surrounding_text}'")
            else:
                print(f"🔍 Debug: Could not find target text '{target_text}' for inspection")
        except Exception as e:
            print(f"🔍 Debug: Could not inspect surrounding text: {e}")
    
    def _try_whitespace_regex_strategy(self, escaped_target: str) -> int:
        """Try comprehensive whitespace regex strategy."""
        try:
            # Pattern: up to dynamic_spaces_to_remove whitespace chars
            regex_pattern = f"[\\s\\u00A0\\u2000-\\u200A\\u202F\\u205F\\u3000]{{0,{self.dynamic_spaces_to_remove}}}{escaped_target}"
            
            rd1 = self.doc.createReplaceDescriptor()
            rd1.SearchString = regex_pattern
            rd1.ReplaceString = "__LOGO_PLACEHOLDER__"
            rd1.SearchCaseSensitive = False
            rd1.SearchWords = False
            rd1.setPropertyValue("RegularExpressions", True)
            
            replaced_count = self.doc.replaceAll(rd1)
            print(f"🔍 Strategy 1 (comprehensive whitespace regex): replaced {replaced_count} instances")
            
            if replaced_count == 0:
                # Try simpler space-only regex
                regex_pattern2 = f" {{0,{self.dynamic_spaces_to_remove}}}{escaped_target}"
                rd2 = self.doc.createReplaceDescriptor()
                rd2.SearchString = regex_pattern2
                rd2.ReplaceString = "__LOGO_PLACEHOLDER__"
                rd2.SearchCaseSensitive = False
                rd2.SearchWords = False
                rd2.setPropertyValue("RegularExpressions", True)
                
                replaced_count = self.doc.replaceAll(rd2)
                print(f"🔍 Strategy 2 (simple space regex): replaced {replaced_count} instances")
            
            return replaced_count
            
        except Exception as e:
            print(f"⚠️  Regex strategies failed: {e}")
            return 0
    
    def _try_tab_whitespace_strategy(self, target_text: str) -> int:
        """Try tab characters and mixed whitespace patterns."""
        if self.dynamic_spaces_to_remove <= 0:
            print(f"🔄 Strategy 3: SKIPPED (dynamic_spaces_to_remove = 0, no whitespace removal allowed)")
            return 0
        
        print(f"🔄 Strategy 3: Trying tabs and mixed whitespace patterns (since dynamic_spaces_to_remove = {self.dynamic_spaces_to_remove})")
        
        # Generate whitespace patterns dynamically
        whitespace_patterns = []
        
        # Add tab patterns
        max_tabs = min(5, self.dynamic_spaces_to_remove)
        for num_tabs in range(max_tabs, 0, -1):
            tabs = "\t" * num_tabs
            whitespace_patterns.append(f"{tabs}{target_text}")
        
        # Add mixed tab/space patterns
        if self.dynamic_spaces_to_remove >= 2:
            whitespace_patterns.extend([
                f"\t {target_text}",           # Tab + space
                f" \t{target_text}",           # Space + tab
            ])
        
        # Add non-breaking space patterns
        max_nbsp = min(4, self.dynamic_spaces_to_remove)
        for num_nbsp in range(max_nbsp, 0, -1):
            nbsp = "\u00A0" * num_nbsp
            whitespace_patterns.append(f"{nbsp}{target_text}")
        
        print(f"🔍 Generated {len(whitespace_patterns)} whitespace patterns for dynamic_spaces_to_remove={self.dynamic_spaces_to_remove}")
        
        replaced_count = 0
        for pattern in whitespace_patterns:
            rd_ws = self.doc.createReplaceDescriptor()
            rd_ws.SearchString = pattern
            rd_ws.ReplaceString = "__LOGO_PLACEHOLDER__"
            rd_ws.SearchCaseSensitive = False
            rd_ws.SearchWords = False
            
            count = self.doc.replaceAll(rd_ws)
            if count > 0:
                replaced_count += count
                print(f"🎯 Found and replaced {count} instance(s) with special whitespace")
                break
        
        return replaced_count
    
    def _try_manual_space_strategy(self, target_text: str) -> int:
        """Try manual space removal approach."""
        print(f"🔄 Strategy 4: Manual space removal approach")
        
        # Generate space patterns dynamically
        space_patterns = []
        for num_spaces in range(self.dynamic_spaces_to_remove, -1, -1):
            spaces = " " * num_spaces
            space_patterns.append(f"{spaces}{target_text}")
        
        print(f"🔍 Trying {len(space_patterns)} different space combinations (from {self.dynamic_spaces_to_remove} down to 0 spaces)")
        
        replaced_count = 0
        for pattern in space_patterns:
            rd3 = self.doc.createReplaceDescriptor()
            rd3.SearchString = pattern
            rd3.ReplaceString = "__LOGO_PLACEHOLDER__"
            rd3.SearchCaseSensitive = False
            rd3.SearchWords = False
            
            count = self.doc.replaceAll(rd3)
            if count > 0:
                replaced_count += count
                spaces_count = len(pattern) - len(target_text)
                print(f"🎯 Found and replaced {count} instance(s) with {spaces_count} spaces")
                break
        
        if replaced_count == 0:
            print(f"⚠️  Could not find '{target_text}' with any space combination")
        
        return replaced_count
    
    def _insert_logo_direct(self, target_text: str, logo_file_path: str) -> int:
        """
        Insert logo directly without space removal.
        
        Args:
            target_text: Text to replace with logo
            logo_file_path: Path to the logo file
            
        Returns:
            Number of logos inserted
        """
        search_desc = self.doc.createSearchDescriptor()
        search_desc.SearchString = target_text
        search_desc.SearchCaseSensitive = False
        search_desc.SearchWords = False
        
        found_range = self.doc.findFirst(search_desc)
        logo_count = 0
        
        while found_range:
            if self._insert_graphic_at_range(found_range, logo_file_path):
                logo_count += 1
            found_range = self.doc.findNext(found_range, search_desc)
        
        return logo_count
    
    def _replace_placeholder_with_logo(self, logo_file_path: str) -> int:
        """
        Replace temporary placeholders with actual logos.
        
        Args:
            logo_file_path: Path to the logo file
            
        Returns:
            Number of logos inserted
        """
        search_desc = self.doc.createSearchDescriptor()
        search_desc.SearchString = "__LOGO_PLACEHOLDER__"
        search_desc.SearchCaseSensitive = True
        search_desc.SearchWords = False
        
        found_range = self.doc.findFirst(search_desc)
        logo_count = 0
        
        while found_range:
            if self._insert_graphic_at_range(found_range, logo_file_path):
                logo_count += 1
            found_range = self.doc.findNext(found_range, search_desc)
        
        return logo_count
    
    def _insert_graphic_at_range(self, found_range: Any, logo_file_path: str) -> bool:
        """
        Insert graphic at the specified range using a different approach.
        
        Args:
            found_range: LibreOffice text range where to insert
            logo_file_path: Path to the logo file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear the target text or placeholder
            found_range.setString("")
            
            # CRITICAL: Use a different approach - insert graphic first, then set size
            print(f"🔄 Using alternative logo insertion approach...")
            
            # Method 1: Try using the document's createTextContent method directly
            try:
                # Create graphic object
                graphic = self.doc.createInstance("com.sun.star.text.GraphicObject")
                logo_file_url = to_url(logo_file_path)
                graphic.setPropertyValue("GraphicURL", logo_file_url)
                
                # Set anchor type
                try:
                    from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
                    graphic.setPropertyValue("AnchorType", AS_CHARACTER)
                    print(f"🔗 Set anchor type to AS_CHARACTER")
                except:
                    print(f"🔗 Could not set AS_CHARACTER anchor type")
                
                # INSERT FIRST - this is the key change!
                print(f"📥 Inserting graphic BEFORE setting dimensions...")
                found_range.getText().insertTextContent(found_range, graphic, False)
                
                # NOW set dimensions after insertion (when graphic is "real")
                print(f"📏 Setting dimensions AFTER insertion...")
                calculated_width = self._calculate_logo_dimensions(logo_file_path)
                target_height = 800  # 8mm in 1/100mm units
                
                # Force dimensions multiple times
                for attempt in range(3):
                    try:
                        graphic.setPropertyValue("Height", target_height)
                        graphic.setPropertyValue("Width", calculated_width)
                        graphic.setPropertyValue("SizeType", 1)  # Absolute size
                        print(f"📏 Attempt {attempt + 1}: Set size to {calculated_width}x{target_height}")
                        
                        # Also try to force aspect ratio preservation
                        self._force_aspect_ratio_preservation(graphic, calculated_width, target_height)
                        
                        # Verify the dimensions were set
                        actual_height = graphic.getPropertyValue("Height")
                        actual_width = graphic.getPropertyValue("Width")
                        print(f"📏 Verification: Actual size is {actual_width}x{actual_height}")
                        
                        if actual_height == target_height and actual_width == calculated_width:
                            print(f"✅ Dimensions successfully set and verified!")
                            break
                        else:
                            print(f"⚠️ Dimensions not set correctly, retrying...")
                            
                    except Exception as e:
                        print(f"⚠️ Attempt {attempt + 1} failed: {e}")
                        if attempt == 2:  # Last attempt
                            print(f"❌ All dimension setting attempts failed")
                
                # Set highlighting properties AFTER insertion
                self._set_graphic_highlighting_properties(graphic)
                
                # Clear any inherited highlighting
                self._clear_inherited_highlighting(graphic, found_range)
                
                print(f"✅ Logo inserted successfully using alternative approach!")
                return True
                
            except Exception as e:
                print(f"⚠️ Alternative approach failed: {e}")
                print(f"🔄 Falling back to original method...")
                
                # Fallback to original method
                return self._insert_graphic_original_method(found_range, logo_file_path)
            
        except Exception as e:
            print(f"❌ Failed to insert logo: {e}")
            return False
    
    def _insert_graphic_original_method(self, found_range: Any, logo_file_path: str) -> bool:
        """
        Original logo insertion method as fallback.
        
        Args:
            found_range: LibreOffice text range where to insert
            logo_file_path: Path to the logo file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create and insert graphic
            graphic = self.doc.createInstance("com.sun.star.text.GraphicObject")
            logo_file_url = to_url(logo_file_path)
            graphic.setPropertyValue("GraphicURL", logo_file_url)
            
            # Set anchor type
            try:
                from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
                graphic.setPropertyValue("AnchorType", AS_CHARACTER)
            except:
                pass
            
            # Calculate and set logo size
            calculated_width = self._calculate_logo_dimensions(logo_file_path)
            target_height = 800  # 8mm in 1/100mm units
            
            # Set size properties
            self._set_graphic_size(graphic, calculated_width, target_height)
            
            # CRITICAL: Set highlighting properties BEFORE insertion to prevent inheritance
            self._set_graphic_highlighting_properties(graphic)
            
            # Insert the graphic
            found_range.getText().insertTextContent(found_range, graphic, False)
            
            # Set size again after insertion (might work better)
            try:
                graphic.setPropertyValue("Height", target_height)
                graphic.setPropertyValue("Width", calculated_width)
                print(f"📏 Post-insertion: Set size to {calculated_width}x{target_height}")
            except Exception as e:
                print(f"⚠️ Could not set size after insertion: {e}")
            
            # CRITICAL: Clear any inherited highlighting after insertion
            self._clear_inherited_highlighting(graphic, found_range)
            
            # NUCLEAR OPTION: Force clear highlighting at XML level
            self._nuclear_highlighting_cleanup(found_range)
            
            print(f"✅ Logo inserted successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to insert logo: {e}")
            return False
    
    def _calculate_logo_dimensions(self, logo_file_path: str) -> int:
        """
        Calculate logo width based on aspect ratio with improved fallback methods.
        
        Args:
            logo_file_path: Path to the logo file
            
        Returns:
            Calculated width in 1/100mm units
        """
        target_height = 800  # 8mm in 1/100mm units
        calculated_width = target_height  # Default fallback for square images
        
        # Method 1: Try PIL/Pillow for most accurate dimensions
        if self._try_pil_dimensions(logo_file_path, target_height):
            return self._pil_calculated_width
        
        # Method 2: Try LibreOffice's built-in image reading capabilities
        calculated_width = self._try_libreoffice_dimensions(logo_file_path, target_height)
        if calculated_width:
            return calculated_width
        
        # Method 3: Try basic file analysis for common formats
        calculated_width = self._try_basic_image_analysis(logo_file_path, target_height)
        if calculated_width:
            return calculated_width
        
        # Method 4: Intelligent file size estimation (improved)
        calculated_width = self._estimate_width_from_file_size(logo_file_path, target_height)
        
        # Final validation and debugging
        aspect_ratio = calculated_width / target_height
        print(f"📏 Final calculated width: {calculated_width} (for height {target_height})")
        print(f"📏 Final aspect ratio: {aspect_ratio:.3f}")
        
        # Check if it's a square or near-square image
        if abs(aspect_ratio - 1.0) < 0.1:
            print(f"🔲 FINAL RESULT: Square image detected (aspect ratio ≈ 1.0)")
            print(f"🔲 Logo will be rendered as {calculated_width}x{target_height} units")
        elif aspect_ratio > 1.5:
            print(f"📐 FINAL RESULT: Wide image detected (aspect ratio = {aspect_ratio:.2f})")
        elif aspect_ratio < 0.7:
            print(f"📐 FINAL RESULT: Tall image detected (aspect ratio = {aspect_ratio:.2f})")
        else:
            print(f"📐 FINAL RESULT: Rectangular image (aspect ratio = {aspect_ratio:.2f})")
        
        # Safety validation - ensure width is reasonable
        if calculated_width <= 0:
            print(f"⚠️  Invalid width calculated, using square fallback")
            calculated_width = target_height
        elif calculated_width > target_height * 10:  # Extremely wide
            print(f"⚠️  Width too large ({calculated_width}), capping at 10x height")
            calculated_width = target_height * 10
        elif calculated_width < target_height * 0.1:  # Extremely narrow
            print(f"⚠️  Width too small ({calculated_width}), setting to 0.1x height")
            calculated_width = int(target_height * 0.1)
        
        return calculated_width
    
    def _try_pil_dimensions(self, logo_file_path: str, target_height: int) -> bool:
        """
        Try to get dimensions using PIL/Pillow.
        
        Args:
            logo_file_path: Path to the logo file
            target_height: Target height in 1/100mm units
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try to import PIL/Pillow
            try:
                from PIL import Image
            except ImportError:
                print("📏 PIL/Pillow not available, trying to install...")
                import subprocess
                import sys
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"], 
                                        capture_output=True, timeout=30)
                    from PIL import Image
                    print("📏 Successfully installed and imported Pillow")
                except Exception as install_error:
                    print(f"📏 Could not install Pillow: {install_error}")
                    return False
            
            # Get image dimensions using PIL/Pillow
            print(f"📏 Reading image dimensions with PIL: {logo_file_path}")
            with Image.open(logo_file_path) as img:
                img_width, img_height = img.size
                
                # Validate dimensions
                if img_width <= 0 or img_height <= 0:
                    print(f"📏 Invalid image dimensions: {img_width}x{img_height}")
                    return False
                
                aspect_ratio = img_width / img_height
                self._pil_calculated_width = int(target_height * aspect_ratio)
                
                print(f"📏 PIL - Image dimensions: {img_width}x{img_height}")
                print(f"📏 PIL - Aspect ratio: {aspect_ratio:.3f}")
                if abs(aspect_ratio - 1.0) < 0.1:
                    print(f"📏 PIL - Detected SQUARE image (aspect ratio ≈ 1.0)")
                print(f"📏 PIL - Calculated width: {self._pil_calculated_width} (for height {target_height})")
                
                return True
                
        except Exception as e:
            print(f"📏 PIL method failed: {e}")
            return False
    
    def _try_libreoffice_dimensions(self, logo_file_path: str, target_height: int) -> Optional[int]:
        """
        Try to get dimensions using LibreOffice's built-in capabilities.
        
        Args:
            logo_file_path: Path to the logo file
            target_height: Target height in 1/100mm units
            
        Returns:
            Calculated width if successful, None otherwise
        """
        try:
            print(f"📏 Trying LibreOffice built-in image reading...")
            
            # Create a temporary graphic object to read dimensions
            temp_graphic = self.doc.createInstance("com.sun.star.text.GraphicObject")
            logo_file_url = to_url(logo_file_path)
            temp_graphic.setPropertyValue("GraphicURL", logo_file_url)
            
            # Try to get the actual size from the graphic
            try:
                # Get size in 1/100mm units
                actual_size = temp_graphic.getPropertyValue("ActualSize")
                if actual_size and hasattr(actual_size, 'Width') and hasattr(actual_size, 'Height'):
                    actual_width = actual_size.Width
                    actual_height = actual_size.Height
                    
                    if actual_width > 0 and actual_height > 0:
                        aspect_ratio = actual_width / actual_height
                        calculated_width = int(target_height * aspect_ratio)
                        
                        print(f"📏 LibreOffice - Actual size: {actual_width}x{actual_height}")
                        print(f"📏 LibreOffice - Aspect ratio: {aspect_ratio:.3f}")
                        if abs(aspect_ratio - 1.0) < 0.1:
                            print(f"📏 LibreOffice - Detected SQUARE image (aspect ratio ≈ 1.0)")
                        print(f"📏 LibreOffice - Calculated width: {calculated_width}")
                        
                        return calculated_width
            except Exception as e:
                print(f"📏 Could not get ActualSize: {e}")
            
            # Alternative: try to get OriginalSize
            try:
                original_size = temp_graphic.getPropertyValue("OriginalSize")
                if original_size and hasattr(original_size, 'Width') and hasattr(original_size, 'Height'):
                    orig_width = original_size.Width
                    orig_height = original_size.Height
                    
                    if orig_width > 0 and orig_height > 0:
                        aspect_ratio = orig_width / orig_height
                        calculated_width = int(target_height * aspect_ratio)
                        
                        print(f"📏 LibreOffice - Original size: {orig_width}x{orig_height}")
                        print(f"📏 LibreOffice - Aspect ratio: {aspect_ratio:.3f}")
                        if abs(aspect_ratio - 1.0) < 0.1:
                            print(f"📏 LibreOffice - Detected SQUARE image (aspect ratio ≈ 1.0)")
                        print(f"📏 LibreOffice - Calculated width: {calculated_width}")
                        
                        return calculated_width
            except Exception as e:
                print(f"📏 Could not get OriginalSize: {e}")
            
        except Exception as e:
            print(f"📏 LibreOffice image reading failed: {e}")
        
        return None
    
    def _try_basic_image_analysis(self, logo_file_path: str, target_height: int) -> Optional[int]:
        """
        Try basic image format analysis for common formats.
        
        Args:
            logo_file_path: Path to the logo file
            target_height: Target height in 1/100mm units
            
        Returns:
            Calculated width if successful, None otherwise
        """
        try:
            print(f"📏 Trying basic image format analysis...")
            
            with open(logo_file_path, 'rb') as f:
                # Read first few bytes to determine format and try to extract dimensions
                header = f.read(24)
                
                if header.startswith(b'\xff\xd8\xff'):
                    # JPEG format
                    return self._analyze_jpeg_dimensions(f, target_height)
                elif header.startswith(b'\x89PNG\r\n\x1a\n'):
                    # PNG format
                    return self._analyze_png_dimensions(f, target_height)
                else:
                    print(f"📏 Unknown image format, header: {header[:8].hex()}")
                    
        except Exception as e:
            print(f"📏 Basic image analysis failed: {e}")
        
        return None
    
    def _analyze_png_dimensions(self, file_obj, target_height: int) -> Optional[int]:
        """Extract dimensions from PNG file header."""
        try:
            # PNG IHDR chunk starts at byte 16
            file_obj.seek(16)
            width_bytes = file_obj.read(4)
            height_bytes = file_obj.read(4)
            
            if len(width_bytes) == 4 and len(height_bytes) == 4:
                width = int.from_bytes(width_bytes, 'big')
                height = int.from_bytes(height_bytes, 'big')
                
                if width > 0 and height > 0:
                    aspect_ratio = width / height
                    calculated_width = int(target_height * aspect_ratio)
                    
                    print(f"📏 PNG analysis - Dimensions: {width}x{height}")
                    print(f"📏 PNG analysis - Aspect ratio: {aspect_ratio:.3f}")
                    if abs(aspect_ratio - 1.0) < 0.1:
                        print(f"📏 PNG analysis - Detected SQUARE image (aspect ratio ≈ 1.0)")
                    print(f"📏 PNG analysis - Calculated width: {calculated_width}")
                    
                    return calculated_width
        except Exception as e:
            print(f"📏 PNG analysis failed: {e}")
        
        return None
    
    def _analyze_jpeg_dimensions(self, file_obj, target_height: int) -> Optional[int]:
        """Extract dimensions from JPEG file header."""
        try:
            # Look for SOF0 or SOF2 markers in JPEG
            file_obj.seek(0)
            data = file_obj.read(1024)  # Read first 1KB to find SOF marker
            
            # Find SOF0 (0xFFC0) or SOF2 (0xFFC2) markers
            for i in range(len(data) - 9):
                if data[i:i+2] in [b'\xff\xc0', b'\xff\xc2']:
                    # Found SOF marker, dimensions are at offset +5 and +7
                    height = int.from_bytes(data[i+5:i+7], 'big')
                    width = int.from_bytes(data[i+7:i+9], 'big')
                    
                    if width > 0 and height > 0:
                        aspect_ratio = width / height
                        calculated_width = int(target_height * aspect_ratio)
                        
                        print(f"📏 JPEG analysis - Dimensions: {width}x{height}")
                        print(f"📏 JPEG analysis - Aspect ratio: {aspect_ratio:.3f}")
                        if abs(aspect_ratio - 1.0) < 0.1:
                            print(f"📏 JPEG analysis - Detected SQUARE image (aspect ratio ≈ 1.0)")
                        print(f"📏 JPEG analysis - Calculated width: {calculated_width}")
                        
                        return calculated_width
                    break
        except Exception as e:
            print(f"📏 JPEG analysis failed: {e}")
        
        return None
    
    def _clear_inherited_highlighting(self, graphic: Any, found_range: Any) -> None:
        """
        Clear any highlighting that might have been inherited during logo insertion.
        This is critical for first page headers where highlighting inheritance can occur.
        
        Args:
            graphic: The inserted graphic object
            found_range: The range where the graphic was inserted
        """
        try:
            print(f"🎨 Clearing inherited highlighting from inserted logo...")
            
            # Method 1: Clear graphic object highlighting properties ONLY
            try:
                # Clear character background color on the graphic itself
                graphic.setPropertyValue("CharBackColor", -1)  # Transparent
                graphic.setPropertyValue("CharBackTransparent", True)
                print(f"🎨 Cleared graphic CharBackColor properties")
            except Exception as e:
                print(f"🎨 Note: Could not clear CharBackColor: {e}")
            
            # Method 2: Clear highlighting ONLY from the graphic's immediate container
            try:
                # Create a cursor that ONLY covers the graphic, not surrounding text
                cursor = found_range.getText().createTextCursorByRange(found_range)
                
                # Clear highlighting ONLY from the graphic's run, not surrounding context
                cursor.setPropertyValue("CharBackColor", -1)
                cursor.setPropertyValue("CharBackTransparent", True)
                print(f"🎨 Cleared highlighting from graphic's immediate container only")
                
            except Exception as e:
                print(f"🎨 Note: Could not clear graphic container highlighting: {e}")
            
            print(f"🎨 Highlighting cleanup completed for inserted logo")
            
        except Exception as e:
            print(f"⚠️ Error during highlighting cleanup: {e}")
            # Don't fail the logo insertion if highlighting cleanup fails
    
    def _set_graphic_highlighting_properties(self, graphic: Any) -> None:
        """
        Set highlighting properties on the graphic BEFORE insertion to prevent inheritance.
        This is more effective than trying to clear highlighting after insertion.
        
        Args:
            graphic: The graphic object to configure
        """
        try:
            print(f"🎨 Setting highlighting properties on graphic before insertion...")
            
            # Set all highlighting properties to transparent/off BEFORE insertion
            graphic.setPropertyValue("CharBackColor", -1)  # Transparent background
            graphic.setPropertyValue("CharBackTransparent", True)  # Force transparency
            graphic.setPropertyValue("CharHighlight", 0)  # No highlighting
            graphic.setPropertyValue("CharShadingValue", 0)  # No shading
            
            # Also try to set any other background-related properties
            try:
                graphic.setPropertyValue("FillColor", -1)  # No fill color
                graphic.setPropertyValue("FillStyle", 0)  # No fill style
            except:
                pass  # These properties might not exist on all graphic types
            
            print(f"🎨 Graphic highlighting properties set to transparent")
            
        except Exception as e:
            print(f"⚠️ Could not set graphic highlighting properties: {e}")
            # Continue anyway - this is not critical for functionality
    
    def _nuclear_highlighting_cleanup(self, found_range: Any) -> None:
        """
        NUCLEAR OPTION: Force clear highlighting at the deepest possible level.
        This targets the XML structure directly to remove any highlighting that
        LibreOffice might have applied during graphic insertion.
        
        Args:
            found_range: The range where the graphic was inserted
        """
        try:
            print(f"☢️  NUCLEAR OPTION: Force clearing highlighting at XML level...")
            
            # Method 1: Try to access the underlying XML and clear highlighting
            try:
                # Get the text cursor and try to access XML properties
                cursor = found_range.getText().createTextCursorByRange(found_range)
                
                # Force clear ALL possible highlighting properties
                cursor.setPropertyValue("CharBackColor", -1)
                cursor.setPropertyValue("CharBackTransparent", True)
                cursor.setPropertyValue("CharHighlight", 0)
                cursor.setPropertyValue("CharShadingValue", 0)
                cursor.setPropertyValue("CharColor", -1)  # Default text color
                
                print(f"☢️  Cleared all character-level highlighting properties")
                
            except Exception as e:
                print(f"☢️  Note: Could not clear character properties: {e}")
            
            # Method 2: Clear paragraph-level properties that might affect the graphic
            try:
                # Get paragraph cursor
                para_cursor = found_range.getText().createTextCursorByRange(found_range)
                para_cursor.gotoStart(False)
                para_cursor.gotoEnd(True)
                
                # Clear paragraph background
                para_cursor.setPropertyValue("ParaBackColor", -1)
                para_cursor.setPropertyValue("ParaBackTransparent", True)
                print(f"☢️  Cleared paragraph background properties")
                
            except Exception as e:
                print(f"☢️  Note: Could not clear paragraph properties: {e}")
            
            # Method 3: Try to clear any inherited section properties
            try:
                # Get the text and try to clear section-level properties
                text = found_range.getText()
                if hasattr(text, 'setPropertyValue'):
                    text.setPropertyValue("BackColor", -1)
                    text.setPropertyValue("BackTransparent", True)
                    print(f"☢️  Cleared text-level background properties")
                    
            except Exception as e:
                print(f"☢️  Note: Could not clear text properties: {e}")
            
            print(f"☢️  NUCLEAR highlighting cleanup completed")
            
        except Exception as e:
            print(f"⚠️  Error during nuclear highlighting cleanup: {e}")
            # Don't fail the logo insertion if this cleanup fails
    
            
        except Exception as e:
            print(f"⚠️ Error during first page header highlighting cleanup: {e}")
            # Don't fail the logo insertion if this cleanup fails
    
    def _estimate_width_from_file_size(self, logo_file_path: str, target_height: int) -> int:
        """
        Intelligent estimation based on file size and file extension.
        This method assumes square images for better aspect ratio preservation.
        """
        try:
            file_size = os.path.getsize(logo_file_path)
            file_ext = os.path.splitext(logo_file_path)[1].lower()
            
            print(f"📏 Logo file size: {file_size} bytes, extension: {file_ext}")
            
            # Default to square aspect ratio (1:1) as a safe assumption
            # This is much better than arbitrary multipliers for unknown images
            calculated_width = target_height
            
            # Adjust based on file size and format for better estimation
            if file_ext in ['.png', '.gif']:
                # PNG/GIF files with transparency or logos tend to be more square
                if file_size > 100000:  # Very large file, might be wide
                    calculated_width = int(target_height * 1.5)
                elif file_size > 50000:  # Medium file, slightly wider
                    calculated_width = int(target_height * 1.2)
                else:
                    calculated_width = target_height  # Assume square
                    
            elif file_ext in ['.jpg', '.jpeg']:
                # JPEG photos can vary more in aspect ratio
                if file_size > 200000:  # Very large JPEG, might be wide photo
                    calculated_width = int(target_height * 1.8)
                elif file_size > 100000:  # Medium JPEG
                    calculated_width = int(target_height * 1.4)
                elif file_size > 30000:   # Small-medium JPEG
                    calculated_width = int(target_height * 1.1)
                else:
                    calculated_width = target_height  # Small JPEG, likely square logo
                    
            else:
                # Unknown format - be conservative and assume square
                calculated_width = target_height
                print(f"📏 Unknown image format - assuming square aspect ratio")
            
            print(f"📏 File-size-based estimate: {calculated_width} (aspect ratio: {calculated_width/target_height:.2f})")
            
            # Safety check: ensure width is reasonable (between 0.5x and 4x height)
            min_width = int(target_height * 0.5)
            max_width = int(target_height * 4.0)
            if calculated_width < min_width:
                calculated_width = min_width
                print(f"📏 Adjusted width to minimum: {calculated_width}")
            elif calculated_width > max_width:
                calculated_width = max_width
                print(f"📏 Adjusted width to maximum: {calculated_width}")
            
            return calculated_width
            
        except Exception as e:
            print(f"📏 Error in file size estimation: {e}")
            # Ultimate fallback - square aspect ratio
            calculated_width = target_height
            print(f"📏 Using safe fallback (square): {calculated_width}")
            return calculated_width
    
    def _set_graphic_size(self, graphic: Any, calculated_width: int, target_height: int) -> None:
        """
        Set graphic size using multiple methods for compatibility.
        
        Args:
            graphic: LibreOffice graphic object
            calculated_width: Width in 1/100mm units
            target_height: Height in 1/100mm units
        """
        try:
            # Method 1: Individual properties
            graphic.setPropertyValue("Height", target_height)
            graphic.setPropertyValue("Width", calculated_width)
            graphic.setPropertyValue("SizeType", 1)   # Absolute size
            
            # Method 2: Try Size object approach
            try:
                import uno
                from com.sun.star.awt import Size
                size_obj = Size()
                size_obj.Width = calculated_width
                size_obj.Height = target_height
                graphic.setPropertyValue("Size", size_obj)
                print(f"📏 Applied Size object: {calculated_width}x{target_height}")
            except Exception as e:
                print(f"📏 Size object method failed: {e}")
            
            # Method 3: Try setting scaling to prevent override
            try:
                graphic.setPropertyValue("RelativeHeight", 100)  # 100% of set height
                graphic.setPropertyValue("RelativeWidth", 100)   # 100% of set width
                graphic.setPropertyValue("IsSizeProtected", True)  # Lock the size
            except Exception as e:
                print(f"📏 Protection method failed: {e}")
            
            # Method 4: NEW - Force aspect ratio preservation
            self._force_aspect_ratio_preservation(graphic, calculated_width, target_height)
            
            print(f"📏 Set logo size to {calculated_width}x{target_height} (width x height in 1/100mm)")
            
        except Exception as e:
            print(f"⚠️  Using default logo size: {e}")
    
    def _force_aspect_ratio_preservation(self, graphic: Any, calculated_width: int, target_height: int) -> None:
        """
        Force LibreOffice to maintain aspect ratio using additional properties.
        
        Args:
            graphic: LibreOffice graphic object
            calculated_width: Width in 1/100mm units
            target_height: Height in 1/100mm units
        """
        try:
            print(f"🔒 Forcing aspect ratio preservation...")
            
            # Method 1: Try to set proportional scaling properties
            try:
                # These properties might exist in some LibreOffice versions
                graphic.setPropertyValue("IsProportional", True)  # Maintain aspect ratio
                print(f"🔒 Set IsProportional = True")
            except Exception as e:
                print(f"🔒 IsProportional property not available: {e}")
            
            # Method 2: Try to set additional size protection
            try:
                # Lock both dimensions independently
                graphic.setPropertyValue("IsHeightProtected", True)
                graphic.setPropertyValue("IsWidthProtected", True)
                print(f"🔒 Set dimension protection flags")
            except Exception as e:
                print(f"🔒 Dimension protection properties not available: {e}")
            
            # Method 3: Try to set scaling mode
            try:
                # Some versions use different scaling mode properties
                graphic.setPropertyValue("ScaleMode", 1)  # 1 = proportional scaling
                print(f"🔒 Set ScaleMode = 1 (proportional)")
            except Exception as e:
                print(f"🔒 ScaleMode property not available: {e}")
            
            # Method 4: Try to set graphic type to prevent auto-resizing
            try:
                # Set as embedded graphic to prevent external scaling
                graphic.setPropertyValue("GraphicType", 1)  # 1 = embedded
                print(f"🔒 Set GraphicType = 1 (embedded)")
            except Exception as e:
                print(f"🔒 GraphicType property not available: {e}")
            
            # Method 5: Try to set additional size constraints
            try:
                # Set minimum and maximum sizes to force exact dimensions
                graphic.setPropertyValue("MinWidth", calculated_width)
                graphic.setPropertyValue("MaxWidth", calculated_width)
                graphic.setPropertyValue("MinHeight", target_height)
                graphic.setPropertyValue("MaxHeight", target_height)
                print(f"🔒 Set size constraints to exact dimensions")
            except Exception as e:
                print(f"🔒 Size constraint properties not available: {e}")
            
            print(f"🔒 Aspect ratio preservation methods applied")
            
        except Exception as e:
            print(f"⚠️  Some aspect ratio preservation methods failed: {e}")
            # Continue anyway - this is not critical for functionality
    
    def _try_alternative_anchor_types(self, graphic: Any) -> None:
        """
        Try alternative anchor types that might preserve dimensions better.
        
        Args:
            graphic: LibreOffice graphic object
        """
        try:
            print(f"🔗 Trying alternative anchor types for better dimension preservation...")
            
            # Try different anchor types that might preserve dimensions better
            anchor_types_to_try = [
                ("AS_CHARACTER", 1),      # As character (inline)
                ("TO_CHARACTER", 2),      # To character
                ("TO_PAGE", 4),           # To page
                ("TO_FRAME", 5),          # To frame
                ("TO_PARAGRAPH", 3),      # To paragraph
            ]
            
            for anchor_name, anchor_value in anchor_types_to_try:
                try:
                    graphic.setPropertyValue("AnchorType", anchor_value)
                    print(f"🔗 Successfully set anchor type to {anchor_name} ({anchor_value})")
                    # Try this anchor type - if it works better, we'll know from the logs
                    break
                except Exception as e:
                    print(f"🔗 Could not set {anchor_name}: {e}")
                    continue
            
            print(f"🔗 Alternative anchor type testing completed")
            
        except Exception as e:
            print(f"⚠️  Alternative anchor type testing failed: {e}")
            # Continue anyway - this is not critical for functionality
    
    def _verify_space_insertion(self, target_text: str, expected_spaces: int) -> None:
        """
        Verify that spaces were successfully inserted before the target text.
        
        Args:
            target_text: The target text to check
            expected_spaces: Number of spaces that should have been added
        """
        try:
            print(f"🔍 Verifying space insertion for '{target_text}'...")
            
            # Search for the target text again to verify spacing
            search_desc = self.doc.createSearchDescriptor()
            search_desc.SearchString = target_text
            search_desc.SearchCaseSensitive = False
            search_desc.SearchWords = False
            
            found_range = self.doc.findFirst(search_desc)
            if found_range:
                # Get text before the target to check for spaces
                cursor = found_range.getText().createTextCursorByRange(found_range)
                cursor.goLeft(expected_spaces + 5, True)  # Go back further than expected
                cursor.gotoRange(found_range.getStart(), True)
                surrounding_text = cursor.getString()
                
                # Count trailing spaces in the surrounding text
                trailing_spaces = len(surrounding_text) - len(surrounding_text.rstrip(' '))
                
                if trailing_spaces >= expected_spaces:
                    print(f"✅ Space insertion verified: found {trailing_spaces} spaces before target")
                else:
                    print(f"⚠️ Space insertion may have failed: found only {trailing_spaces} spaces, expected {expected_spaces}")
                    
            else:
                print(f"⚠️ Could not find target text for verification")
                
        except Exception as e:
            print(f"⚠️ Space insertion verification failed: {e}")
    
    def _alternative_space_insertion(self, found_range: Any, spaces_to_insert: str) -> None:
        """
        Alternative method for inserting spaces, useful for small content scenarios.
        
        Args:
            found_range: The range where the target text was found
            spaces_to_insert: The spaces string to insert
        """
        try:
            print(f"🔄 Trying alternative space insertion method...")
            
            # Method 1: Try to get parent paragraph and insert at beginning
            try:
                cursor = found_range.getText().createTextCursorByRange(found_range)
                cursor.gotoStart(False)  # Go to start of text, don't expand selection
                cursor.getText().insertString(cursor, spaces_to_insert, False)
                print(f"✅ Alternative method 1 (paragraph start) succeeded")
                return
            except Exception as e:
                print(f"⚠️ Alternative method 1 failed: {e}")
            
            # Method 2: Try direct text replacement approach
            try:
                target_text = found_range.getString()
                replacement_text = spaces_to_insert + target_text
                found_range.setString(replacement_text)
                print(f"✅ Alternative method 2 (direct replacement) succeeded")
                return
            except Exception as e:
                print(f"⚠️ Alternative method 2 failed: {e}")
            
            # Method 3: Try cursor positioning with different approach
            try:
                text_obj = found_range.getText()
                cursor = text_obj.createTextCursor()
                cursor.gotoRange(found_range.getStart(), False)
                cursor.getText().insertString(cursor, spaces_to_insert, False)
                print(f"✅ Alternative method 3 (new cursor) succeeded")
                return
            except Exception as e:
                print(f"⚠️ Alternative method 3 failed: {e}")
            
            raise Exception("All alternative space insertion methods failed")
            
        except Exception as e:
            print(f"❌ Alternative space insertion completely failed: {e}")
            raise e
