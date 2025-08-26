"""
Comment and Annotation Utilities

This module provides utilities for adding comments and annotations to LibreOffice documents,
including multiple fallback methods for maximum compatibility.
"""

from typing import Any, List, Dict
from libre_office_utils import create_libreoffice_datetime, get_redline_type


class CommentManager:
    """
    Manages comments and annotations in LibreOffice documents.
    """
    
    def __init__(self, doc: Any, smgr: Any):
        """
        Initialize comment manager.
        
        Args:
            doc: LibreOffice document object
            smgr: LibreOffice service manager
        """
        self.doc = doc
        self.smgr = smgr
    
    def process_comment_operations(self, operations: List[Dict[str, Any]]) -> None:
        """
        Process comment-only operations from JSON data.
        
        Args:
            operations: List of comment operations to process
        """
        comment_operations = [op for op in operations if op.get('action') == 'comment']
        print(f"📝 Found {len(comment_operations)} comment-only operations to process")
        
        for op in comment_operations:
            target_text = op.get('target_text', '')
            comment = op.get('comment', '')
            author = op.get('comment_author', 'Secfix AI')
            
            # SAFETY: Ensure author is always Secfix AI (override any other values)
            if author != "Secfix AI":
                print(f"⚠️ Comment author was '{author}', overriding to 'Secfix AI'")
                author = "Secfix AI"
            
            self.add_comment_to_text(target_text, comment, author)
    
    def add_comment_to_text(self, target_text: str, comment: str, author: str) -> int:
        """
        Add comment to all occurrences of target text.
        
        Args:
            target_text: Text to find and comment on
            comment: Comment content
            author: Comment author
            
        Returns:
            Number of comments added
        """
        try:
            # Find the target text to add comment to
            search_desc = self.doc.createSearchDescriptor()
            search_desc.SearchString = target_text
            search_desc.SearchCaseSensitive = False
            search_desc.SearchWords = False
            
            found_range = self.doc.findFirst(search_desc)
            added_count = 0
            
            while found_range:
                try:
                    # Clean up comment content
                    comment_content = comment.replace('\\\\n', '\n').replace('\\n', '\n')
                    
                    # Try multiple annotation methods for compatibility
                    if self._try_annotation_field(found_range, author, comment_content):
                        added_count += 1
                    elif self._try_postit_field(found_range, author, comment_content):
                        added_count += 1
                    elif self._try_basic_annotation(found_range, author, comment_content):
                        added_count += 1
                    elif self._try_tracked_change_comment(author, comment_content):
                        added_count += 1
                    else:
                        print(f"❌ All comment methods failed for '{target_text[:50]}...'")
                    
                except Exception as e:
                    print(f"❌ Could not add comment: {e}")
                
                # Move to next occurrence
                found_range = self.doc.findNext(found_range, search_desc)
            
            if added_count > 0:
                print(f"✅ Added {added_count} comment(s) to occurrences of '{target_text[:50]}...' by {author}")
            else:
                print(f"⚠️ Could not find text '{target_text}' for comment operation")
            
            return added_count
            
        except Exception as e:
            print(f"❌ Failed to process comment-only operation: {e}")
            return 0
    
    def _try_annotation_field(self, found_range: Any, author: str, comment_content: str) -> bool:
        """Try creating annotation text field (most compatible)."""
        try:
            annotation = self.doc.createInstance("com.sun.star.text.TextField.Annotation")
            annotation.setPropertyValue("Author", author)
            annotation.setPropertyValue("Content", comment_content)
            
            # Set proper timestamp
            dt = create_libreoffice_datetime()
            try:
                annotation.setPropertyValue("Date", dt)
            except Exception:
                annotation.setPropertyValue("DateTimeValue", dt)
            
            # Insert annotation to cover the entire found range
            cursor = found_range.getText().createTextCursorByRange(found_range)
            cursor.getText().insertTextContent(cursor, annotation, True)
            return True
            
        except Exception as e:
            print(f"Annotation method failed: {e}")
            return False
    
    def _try_postit_field(self, found_range: Any, author: str, comment_content: str) -> bool:
        """Try creating postit annotation (Word-compatible)."""
        try:
            annotation = self.doc.createInstance("com.sun.star.text.textfield.PostItField")
            annotation.setPropertyValue("Author", author)
            annotation.setPropertyValue("Content", comment_content)
            
            # Set proper timestamp
            dt = create_libreoffice_datetime()
            try:
                annotation.setPropertyValue("Date", dt)
            except Exception:
                annotation.setPropertyValue("DateTimeValue", dt)
            
            cursor = found_range.getText().createTextCursorByRange(found_range)
            cursor.getText().insertTextContent(cursor, annotation, True)
            return True
            
        except Exception as e:
            print(f"PostIt method failed: {e}")
            return False
    
    def _try_basic_annotation(self, found_range: Any, author: str, comment_content: str) -> bool:
        """Try simple annotation approach."""
        try:
            annotation = self.doc.createInstance("com.sun.star.text.textfield.Annotation")
            if annotation:
                annotation.Author = author
                annotation.Content = comment_content
                
                # Set proper timestamp
                dt = create_libreoffice_datetime()
                try:
                    annotation.Date = dt
                except Exception:
                    annotation.DateTimeValue = dt
                
                # Insert to cover the entire found range
                found_range.getText().insertTextContent(found_range, annotation, True)
                return True
            else:
                raise Exception("Could not create annotation instance")
                
        except Exception as e:
            print(f"Basic annotation failed: {e}")
            return False
    
    def _try_tracked_change_comment(self, author: str, comment_content: str) -> bool:
        """Fallback - insert as tracked change with comment."""
        try:
            # Try to add comment to the last redline
            redlines = self.doc.getPropertyValue("Redlines")
            if redlines and redlines.getCount() > 0:
                last_redline = redlines.getByIndex(redlines.getCount() - 1)
                last_redline.setPropertyValue("Comment", f"{author}: {comment_content}")
                return True
            else:
                print(f"❌ No tracked changes available for comment")
                return False
                
        except Exception as e:
            print(f"❌ Tracked change comment failed: {e}")
            return False
    
    def add_comment_to_replacements(self, find_text: str, replace_text: str, 
                                   comment_text: str, author_name: str, 
                                   match_case: bool, whole_word: bool,
                                   prev_redlines_count: int) -> None:
        """
        Add comment to text replacements.
        
        Args:
            find_text: Original text that was found
            replace_text: Replacement text
            comment_text: Comment to add
            author_name: Author of the comment
            match_case: Whether search was case sensitive
            whole_word: Whether search was whole word
            prev_redlines_count: Number of redlines before the replacement
        """
        if not comment_text:
            return
        
        # First, try to attach the comment ONLY to NEW DELETION redlines
        added_to_redlines = self._add_comment_to_new_redlines(
            comment_text, author_name, prev_redlines_count)
        
        if added_to_redlines > 0:
            print(f"✅ Added comment to {added_to_redlines} tracked change(s) by {author_name}")
        else:
            # Fallback: annotate occurrences directly
            added_count = self._add_comment_to_text_occurrences(
                replace_text if replace_text else find_text, 
                comment_text, author_name, match_case, whole_word)
            
            if added_count > 0:
                print(f"✅ Added {added_count} comment(s) to replacements by {author_name}")
            else:
                # Final fallback: attach to most recent tracked change
                self._add_comment_to_latest_redline(comment_text, author_name)
    
    def _add_comment_to_new_redlines(self, comment_text: str, author_name: str, 
                                   prev_redlines_count: int) -> int:
        """Add comment to newly created redlines."""
        added_to_redlines = 0
        try:
            redlines = self.doc.getPropertyValue("Redlines")
            if redlines:
                total_after = redlines.getCount()
                for i in range(prev_redlines_count, total_after):
                    try:
                        rl = redlines.getByIndex(i)
                        rl_type = get_redline_type(rl)
                        if rl_type == "delete":
                            rl.setPropertyValue("Comment", f"{author_name}: {comment_text}")
                            added_to_redlines += 1
                    except Exception as e_rl:
                        print(f"Could not set comment on redline {i}: {e_rl}")
        except Exception as e_red:
            print(f"Could not access redlines: {e_red}")
        
        return added_to_redlines
    
    def _add_comment_to_text_occurrences(self, search_text: str, comment_text: str, 
                                       author_name: str, match_case: bool, 
                                       whole_word: bool) -> int:
        """Add comment to text occurrences directly."""
        search_desc = self.doc.createSearchDescriptor()
        search_desc.SearchString = search_text
        search_desc.SearchCaseSensitive = match_case
        search_desc.SearchWords = whole_word
        
        found_range = self.doc.findFirst(search_desc)
        added_count = 0
        
        while found_range:
            try:
                # Try multiple annotation methods
                if self._try_annotation_field(found_range, author_name, comment_text):
                    added_count += 1
                elif self._try_postit_field(found_range, author_name, comment_text):
                    added_count += 1
                elif self._try_basic_annotation(found_range, author_name, comment_text):
                    added_count += 1
                elif self._try_tracked_change_comment(author_name, comment_text):
                    added_count += 1
                else:
                    print(f"❌ All comment methods failed for replacement")
                    
            except Exception as e:
                print(f"Warning: Could not add comment: {e}")
            
            # Move to next occurrence
            found_range = self.doc.findNext(found_range, search_desc)
        
        return added_count
    
    def _add_comment_to_latest_redline(self, comment_text: str, author_name: str) -> None:
        """Add comment to the most recent tracked change."""
        try:
            redlines = self.doc.getPropertyValue("Redlines")
            if redlines and redlines.getCount() > 0:
                last_redline = redlines.getByIndex(redlines.getCount() - 1)
                last_redline.setPropertyValue("Comment", f"{author_name}: {comment_text}")
                print(f"✅ Added comment to recent tracked change: {comment_text[:80]}...")
            else:
                print(f"❌ Could not find replacement text and no tracked changes available")
        except Exception as e:
            print(f"Could not add comment to tracked change: {e}")
    
    def update_document_author(self, author_name: str) -> None:
        """
        Update document author for tracked changes.
        
        Args:
            author_name: Author name to set
        """
        try:
            print(f"🚨 AGGRESSIVELY SETTING AUTHOR TO '{author_name}' FOR TRACKED CHANGES...")
            
            # Method 1: Set redline author (MOST IMPORTANT)
            try:
                self.doc.setPropertyValue("RedlineAuthor", author_name)
                print(f"✅ Set RedlineAuthor to '{author_name}'")
            except Exception as e:
                print(f"❌ Failed to set RedlineAuthor: {e}")
            
            # Method 2: Document info properties
            try:
                doc_info = self.doc.getDocumentInfo()
                doc_info.setPropertyValue("Author", author_name)
                doc_info.setPropertyValue("ModifiedBy", author_name)
                doc_info.setPropertyValue("Creator", author_name)
                print(f"✅ Set document info authors to '{author_name}'")
            except Exception as e:
                print(f"❌ Failed to set document info: {e}")
            
            # Method 3: Try ALL possible author properties
            try:
                for prop_name in ["Author", "LastAuthor", "ModifiedBy", "Creator", "RedlineAuthor"]:
                    try:
                        self.doc.setPropertyValue(prop_name, author_name)
                        print(f"✅ Set {prop_name} to '{author_name}'")
                    except Exception:
                        pass
            except Exception as e:
                print(f"❌ Failed additional properties: {e}")
            
            # Method 4: Update user profile
            try:
                self._update_user_profile(author_name)
                print(f"✅ Updated user profile to '{author_name}'")
            except Exception as e:
                print(f"❌ Failed to update user profile: {e}")
            
            print(f"🎯 AUTHOR UPDATE COMPLETE - SHOULD NOW BE '{author_name}'")
            
        except Exception as e:
            print(f"❌ CRITICAL: Could not set author for change: {e}")
            # Emergency fallback
            try:
                self.doc.setPropertyValue("RedlineAuthor", author_name)
                print(f"🆘 Emergency: Set RedlineAuthor to '{author_name}'")
            except Exception:
                print(f"🆘 EMERGENCY FALLBACK FAILED!")
    
    def _update_user_profile(self, author_name: str) -> None:
        """Update user profile for the current change."""
        try:
            from libre_office_utils import mkprop
            
            config_provider = self.smgr.createInstance("com.sun.star.configuration.ConfigurationProvider")
            config_access = config_provider.createInstanceWithArguments(
                "com.sun.star.configuration.ConfigurationUpdateAccess",
                (mkprop("nodepath", "/org.openoffice.UserProfile/Data"),)
            )
            if config_access:
                # Split author name if it contains spaces
                name_parts = author_name.split(' ', 1)
                given_name = name_parts[0] if name_parts else author_name
                surname = name_parts[1] if len(name_parts) > 1 else ""
                
                config_access.setPropertyValue("givenname", given_name)
                config_access.setPropertyValue("sn", surname)
                config_access.commitChanges()
                
        except Exception as e:
            print(f"Could not update user profile: {e}")
