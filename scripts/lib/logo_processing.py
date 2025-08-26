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
            metadata: Metadata dictionary
            
        Returns:
            Path to logo file or None if not found
        """
        try:
            meta_logo_path = metadata.get('logo_path', '').strip()
            if meta_logo_path and os.path.exists(meta_logo_path):
                print(f"🖼️  Using logo from metadata: {meta_logo_path}")
                return meta_logo_path
        except Exception as e:
            print(f"⚠️  Error reading metadata: {e}")
        
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
        # Add spaces by finding target and inserting spaces before it
        search_desc = self.doc.createSearchDescriptor()
        search_desc.SearchString = target_text
        search_desc.SearchCaseSensitive = False
        search_desc.SearchWords = False
        
        found_range = self.doc.findFirst(search_desc)
        if found_range:
            # Insert spaces before the target text
            cursor = found_range.getText().createTextCursorByRange(found_range)
            cursor.collapseToStart()
            spaces_to_insert = " " * spaces_to_add
            cursor.getText().insertString(cursor, spaces_to_insert, False)
            print(f"✅ Added {spaces_to_add} spaces before logo placeholder")
        
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
                target_height = 600  # 6mm in 1/100mm units
                
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
            target_height = 600  # 6mm in 1/100mm units
            
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
        Calculate logo width based on aspect ratio.
        
        Args:
            logo_file_path: Path to the logo file
            
        Returns:
            Calculated width in 1/100mm units
        """
        target_height = 600  # 6mm in 1/100mm units
        calculated_width = target_height  # Default fallback
        
        try:
            # Try to use PIL/Pillow for accurate dimensions
            try:
                from PIL import Image
            except ImportError:
                print("📏 Installing Pillow for image processing...")
                import subprocess
                import sys
                subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
                from PIL import Image
            
            # Get image dimensions using PIL/Pillow
            print(f"📏 Reading image file: {logo_file_path}")
            with Image.open(logo_file_path) as img:
                img_width, img_height = img.size
                aspect_ratio = img_width / img_height
                calculated_width = int(target_height * aspect_ratio)
                print(f"📏 Image dimensions: {img_width}x{img_height}, aspect ratio: {aspect_ratio:.2f}")
                print(f"📏 Calculated width: {calculated_width} (for height {target_height})")
                
        except ImportError as ie:
            print(f"📏 PIL not available: {ie}")
            # Fallback to file size estimation
            calculated_width = self._estimate_width_from_file_size(logo_file_path, target_height)
            
        except Exception as e:
            print(f"📏 Could not read image dimensions: {e}")
            calculated_width = int(target_height * 2.5)  # Default fallback
            print(f"📏 Using fallback width: {calculated_width}")
        
        return calculated_width
    
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
        """Estimate width based on file size (rough approximation)."""
        try:
            file_size = os.path.getsize(logo_file_path)
            print(f"📏 Logo file size: {file_size} bytes")
            if file_size > 50000:  # Larger file, probably wider
                calculated_width = int(target_height * 3.0)
            elif file_size > 20000:
                calculated_width = int(target_height * 2.5)
            else:
                calculated_width = int(target_height * 2.0)
            print(f"📏 Using file-size-based width estimate: {calculated_width}")
            return calculated_width
        except Exception:
            calculated_width = int(target_height * 2.5)  # Default fallback
            print(f"📏 Using default width estimate: {calculated_width}")
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

    def _try_alternative_text_insertion(self, found_range: Any, logo_file_path: str) -> bool:
        """
        Try alternative text layer insertion approach.
        
        Args:
            found_range: LibreOffice text range where to insert
            logo_file_path: Path to the logo file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"📝 Trying alternative text insertion...")
            
            # Method 1: Try using a different graphic service
            try:
                # Try using the text field service instead
                graphic_field = self.doc.createInstance("com.sun.star.text.textfield.Graphic")
                if graphic_field:
                    print(f"📝 Created Graphic text field successfully")
                    
                    # Set the graphic URL
                    logo_file_url = to_url(logo_file_path)
                    graphic_field.setPropertyValue("GraphicURL", logo_file_url)
                    
                    # Set dimensions
                    calculated_width = self._calculate_logo_dimensions(logo_file_path)
                    target_height = 600
                    
                    graphic_field.setPropertyValue("Width", calculated_width)
                    graphic_field.setPropertyValue("Height", target_height)
                    
                    # Insert the graphic field
                    found_range.getText().insertTextContent(found_range, graphic_field, False)
                    print(f"📝 Graphic text field insertion successful!")
                    return True
                    
            except Exception as e:
                print(f"⚠️ Graphic text field failed: {e}")
            
            # Method 2: Try using the alternative approach from before
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
                target_height = 600  # 6mm in 1/100mm units
                
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
            
            print(f"❌ Alternative text insertion failed")
            return False
            
        except Exception as e:
            print(f"❌ Alternative text insertion error: {e}")
            return False
    
    def _try_preprocessed_image_insertion(self, found_range: Any, logo_file_path: str) -> bool:
        """
        Try inserting a pre-processed image with exact dimensions.
        
        Args:
            found_range: LibreOffice text range where to insert
            logo_file_path: Path to the logo file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"🖼️ Trying pre-processed image insertion...")
            
            # Create a new image with exact dimensions
            processed_logo_path = self._create_resized_logo(logo_file_path)
            if not processed_logo_path:
                print(f"⚠️ Could not create resized logo")
                return False
            
            try:
                # Now insert the pre-processed image
                graphic = self.doc.createInstance("com.sun.star.text.GraphicObject")
                processed_logo_url = to_url(processed_logo_path)
                graphic.setPropertyValue("GraphicURL", processed_logo_url)
                
                # Set anchor type
                try:
                    from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
                    graphic.setPropertyValue("AnchorType", AS_CHARACTER)
                except:
                    pass
                
                # Insert the graphic
                found_range.getText().insertTextContent(found_range, graphic, False)
                
                # The image should already be the right size, but try to set it anyway
                calculated_width = self._calculate_logo_dimensions(logo_file_path)
                target_height = 600
                
                graphic.setPropertyValue("Height", target_height)
                graphic.setPropertyValue("Width", calculated_width)
                
                print(f"🖼️ Pre-processed image insertion successful!")
                return True
                
            finally:
                # Clean up the temporary file
                try:
                    if os.path.exists(processed_logo_path):
                        os.remove(processed_logo_path)
                        print(f"🧹 Cleaned up temporary processed logo")
                except Exception as e:
                    print(f"⚠️ Could not clean up temporary file: {e}")
            
        except Exception as e:
            print(f"❌ Pre-processed image insertion error: {e}")
            return False
    
    def _create_resized_logo(self, logo_file_path: str) -> Optional[str]:
        """
        Create a new logo image with exact dimensions.
        
        Args:
            logo_file_path: Path to the original logo file
            
        Returns:
            Path to the resized logo file or None if failed
        """
        try:
            print(f"🖼️ Creating resized logo with exact dimensions...")
            
            # Try to use PIL/Pillow for image processing
            try:
                from PIL import Image
            except ImportError:
                print(f"📏 PIL not available, cannot resize image")
                return None
            
            # Calculate target dimensions
            calculated_width = self._calculate_logo_dimensions(logo_file_path)
            target_height = 600
            
            # Open and resize the image
            with Image.open(logo_file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Resize to exact dimensions
                resized_img = img.resize((calculated_width, target_height), Image.Resampling.LANCZOS)
                
                # Create temporary file path
                import tempfile
                temp_dir = tempfile.gettempdir()
                temp_filename = f"resized_logo_{os.path.basename(logo_file_path)}"
                temp_path = os.path.join(temp_dir, temp_filename)
                
                # Save the resized image
                resized_img.save(temp_path, 'PNG', optimize=True)
                print(f"🖼️ Created resized logo: {temp_path} ({calculated_width}x{target_height})")
                
                return temp_path
                
        except Exception as e:
            print(f"❌ Failed to create resized logo: {e}")
            return None
