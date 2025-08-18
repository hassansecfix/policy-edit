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
import csv
import json
import os
import sys
import time
import subprocess
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser(description="Apply tracked edits to DOCX via LibreOffice (headless UNO).")
    p.add_argument("--in", dest="in_path", required=True, help="Input .docx")
    p.add_argument("--csv", dest="csv_path", required=True, help="CSV with columns: Find,Replace,MatchCase,WholeWord,Wildcards OR JSON with operations format")
    p.add_argument("--out", dest="out_path", required=True, help="Output .docx (will be overwritten)")
    p.add_argument("--launch", action="store_true", help="Launch a headless LibreOffice UNO listener if not already running")
    p.add_argument("--logo", dest="logo_path", help="Optional path to company logo image (png/jpg) to insert in header")
    p.add_argument("--logo-width-mm", dest="logo_width_mm", type=int, help="Optional logo width in millimeters")
    p.add_argument("--logo-height-mm", dest="logo_height_mm", type=int, help="Optional logo height in millimeters")
    p.add_argument("--questionnaire", dest="questionnaire_csv", help="Optional path to questionnaire CSV for logo URL extraction")
    return p.parse_args()

def bool_from_str(s, default=False):
    if s is None: return default
    s = str(s).strip().lower()
    return s in ("1","true","yes","y")

def create_libreoffice_datetime():
    """Create a LibreOffice DateTime object for annotations"""
    try:
        from com.sun.star.util import DateTime
        import datetime
        now = datetime.datetime.now()
        dt = DateTime()
        dt.Year = now.year
        dt.Month = now.month
        dt.Day = now.day
        dt.Hours = now.hour
        dt.Minutes = now.minute
        dt.Seconds = now.second
        dt.NanoSeconds = now.microsecond * 1000
        return dt
    except Exception:
        # Fallback to Unix timestamp
        import time
        return time.time()

def rows_from_file(path):
    """Load edits from either CSV or JSON format"""
    file_ext = Path(path).suffix.lower()
    
    if file_ext == '.json':
        return rows_from_json(path)
    else:
        return rows_from_csv(path)

def rows_from_json(path):
    """Load edits from JSON operations format"""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    operations = data.get('instructions', {}).get('operations', [])
    
    for op in operations:
        action = op.get('action', 'replace')
        target_text = op.get('target_text', '')
        replacement = op.get('replacement', '')
        comment = op.get('comment', '')
        author = op.get('comment_author', 'AI Assistant')
        
        # Handle comment-only operations in main loop, not here
        if action == 'comment':
            continue
            
        # Handle delete operations (empty replacement)
        if action == 'delete':
            replacement = ''
        
        yield {
            "Find": target_text,
            "Replace": replacement,
            "MatchCase": "",  # Default to False
            "WholeWord": "",  # Default to False  
            "Wildcards": "",  # Default to False
            "Comment": comment,
            "Author": author,
        }

def rows_from_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or len(reader.fieldnames) < 2:
            # No header: assume simple CSV
            f.seek(0)
            reader2 = csv.reader(f)
            for row in reader2:
                if not row: continue
                yield {
                    "Find": row[0],
                    "Replace": row[1] if len(row) > 1 else "",
                    "MatchCase": row[2] if len(row) > 2 else "",
                    "WholeWord": row[3] if len(row) > 3 else "",
                    "Wildcards": row[4] if len(row) > 4 else "",
                    "Comment": row[5] if len(row) > 5 else "",
                    "Author": row[6] if len(row) > 6 else "AI Assistant",
                }
        else:
            for rec in reader:
                yield {
                    "Find": (rec.get("Find") or rec.get("find") or rec.get("FIND") or "").strip(),
                    "Replace": rec.get("Replace") or rec.get("replace") or rec.get("REPLACE") or "",
                    "MatchCase": rec.get("MatchCase") or rec.get("matchcase") or rec.get("MATCHCASE") or "",
                    "WholeWord": rec.get("WholeWord") or rec.get("wholeword") or rec.get("WHOLEWORD") or "",
                    "Wildcards": rec.get("Wildcards") or rec.get("wildcards") or rec.get("WILDCARDS") or "",
                    "Comment": rec.get("Comment") or rec.get("comment") or rec.get("COMMENT") or "",
                    "Author": rec.get("Author") or rec.get("author") or rec.get("AUTHOR") or "AI Assistant",
                }

def ensure_listener():
    # Start a headless LibreOffice UNO listener on port 2002 if not already running.
    # Harmless if one is already up.
    try:
        # Kill any existing LibreOffice processes to ensure clean start
        subprocess.run(["pkill", "-f", "soffice"], capture_output=True, timeout=5)
        time.sleep(1)
        
        # Create a temporary user profile with correct author info
        profile_dir = "/tmp/lo_profile_secfix"
        try:
            import shutil
            if os.path.exists(profile_dir):
                shutil.rmtree(profile_dir)
            os.makedirs(profile_dir, exist_ok=True)
            
            # Create a registrymodifications.xcu file to set user info
            registry_content = '''<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <item oor:path="/org.openoffice.UserProfile/Data">
    <prop oor:name="givenname" oor:op="fuse">
      <value>Secfix</value>
    </prop>
    <prop oor:name="sn" oor:op="fuse">
      <value>AI</value>
    </prop>
  </item>
</oor:items>'''
            with open(f"{profile_dir}/registrymodifications.xcu", "w") as f:
                f.write(registry_content)
            print("✅ Created LibreOffice profile with Secfix AI author")
        except Exception as e:
            print(f"Could not create profile: {e}")
        
        # Set environment variables for LibreOffice user info
        os.environ['LO_USER_GIVENNAME'] = 'Secfix'
        os.environ['LO_USER_SURNAME'] = 'AI'
        
        # Start LibreOffice headless listener with custom profile
        process = subprocess.Popen([
            "soffice",
            "--headless",
            "--nologo",
            "--nodefault",
            "--norestore",
            "--invisible",
            f"-env:UserInstallation=file://{profile_dir}",
            '--accept=socket,host=127.0.0.1,port=2002;urp;StarOffice.ServiceManager'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=os.environ)
        
        # Wait longer and test connection
        print("Starting LibreOffice listener...")
        for i in range(30):  # Try for up to 30 seconds
            time.sleep(1)
            try:
                # Test if we can connect
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', 2002))
                sock.close()
                if result == 0:
                    print(f"LibreOffice listener ready after {i+1} seconds")
                    return
            except:
                pass
            print(f"Waiting for LibreOffice... ({i+1}/30)")
        
        print("WARNING: LibreOffice listener may not be ready")
        
    except FileNotFoundError:
        print("ERROR: 'soffice' not found on PATH. Install LibreOffice or add it to PATH.", file=sys.stderr)

def main():
    args = parse_args()
    in_path = os.path.abspath(args.in_path)
    out_path = os.path.abspath(args.out_path)
    csv_path = os.path.abspath(args.csv_path)

    if not os.path.exists(in_path):
        print("Input DOCX not found:", in_path, file=sys.stderr); sys.exit(2)
    if not os.path.exists(csv_path):
        print("CSV not found:", csv_path, file=sys.stderr); sys.exit(2)

    if args.launch:
        ensure_listener()

    try:
        import uno
        from com.sun.star.beans import PropertyValue
    except Exception:
        print("ERROR: UNO bridge not available. Run with LibreOffice's Python (recommended).", file=sys.stderr)
        sys.exit(1)

    # Connect to running LibreOffice with retries
    local_ctx = uno.getComponentContext()
    resolver = local_ctx.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local_ctx)
    
    print("Connecting to LibreOffice...")
    ctx = None
    for attempt in range(10):  # Try 10 times
        try:
            ctx = resolver.resolve("uno:socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext")
            print("Successfully connected to LibreOffice!")
            break
        except Exception as e:
            if attempt < 9:
                print(f"Connection attempt {attempt + 1} failed, retrying in 2 seconds...")
                time.sleep(2)
            else:
                print(f"Could not connect to LibreOffice listener after 10 attempts. Error: {e}", file=sys.stderr)
                print("Make sure LibreOffice is running with --launch flag or start it externally.", file=sys.stderr)
                sys.exit(1)
    
    if not ctx:
        print("Could not establish LibreOffice context.", file=sys.stderr)
        sys.exit(1)

    smgr = ctx.ServiceManager
    desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)

    def mkprop(name, value):
        p = PropertyValue()
        p.Name = name
        p.Value = value
        return p

    def to_url(path):
        return Path(path).absolute().as_uri()

    def get_redline_type(redline):
        """Best-effort detection of a redline's type ("insert" or "delete").
        Returns a lowercase string or empty string if unknown.
        """
        # Common property names observed across LO builds
        candidate_keys = (
            "RedlineType", "Type", "RedLineType", "RedlineKind",
        )
        for key in candidate_keys:
            try:
                value = redline.getPropertyValue(key)
                if isinstance(value, str) and value:
                    return value.strip().lower()
            except Exception:
                pass
        # Boolean flags in some builds
        try:
            if redline.getPropertyValue("IsDeletion"):
                return "delete"
        except Exception:
            pass
        try:
            if redline.getPropertyValue("IsInsertion"):
                return "insert"
        except Exception:
            pass
        return ""

    def mm_to_100th_mm(mm):
        try:
            return int(mm) * 100
        except Exception:
            return None



    # Load hidden
    in_props = (mkprop("Hidden", True),)
    doc = desktop.loadComponentFromURL(to_url(in_path), "_blank", 0, in_props)

    # Set document properties for tracked changes
    try:
        doc_info = doc.getDocumentInfo()
        doc_info.setPropertyValue("Author", "Secfix AI")
        doc_info.setPropertyValue("ModifiedBy", "Secfix AI")
    except Exception as e:
        print(f"Warning: Could not set document author: {e}")

    # Ensure Track Changes on and set author
    try:
        # For Writer documents this should be available:
        doc.RecordChanges = True
        
        # Try multiple ways to set the redline author
        try:
            doc.setPropertyValue("RedlineAuthor", "Secfix AI")
        except Exception:
            pass
            
        try:
            doc.setPropertyValue("rsid", "Secfix AI")
        except Exception:
            pass
            
        # Try to set user data which affects tracked changes
        try:
            from com.sun.star.util import XChangesNotifier
            config_provider = smgr.createInstance("com.sun.star.configuration.ConfigurationProvider")
            config_access = config_provider.createInstanceWithArguments(
                "com.sun.star.configuration.ConfigurationUpdateAccess",
                (mkprop("nodepath", "/org.openoffice.UserProfile/Data"),)
            )
            if config_access:
                config_access.setPropertyValue("givenname", "Secfix")
                config_access.setPropertyValue("sn", "AI")
                config_access.commitChanges()
                print("✅ Set user profile for tracked changes")
        except Exception as e:
            print(f"Could not set user profile: {e}")
            
    except Exception as e:
        print(f"Warning: Could not enable track changes: {e}")

    # Apply replacements, comments, and optional header logo.
    try:
        # Read optional logo parameters from args first
        cli_logo_path = args.logo_path
        cli_logo_w = args.logo_width_mm
        cli_logo_h = args.logo_height_mm

        # FIRST: Handle logo replacement BEFORE any tracking is enabled
        if csv_path.endswith('.json'):
            with open(csv_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            operations = data.get('instructions', {}).get('operations', [])

            # Find logo operations and do them FIRST, before tracking
            logo_operations = [op for op in operations if op.get('action') == 'replace_with_logo']
            if logo_operations:
                print(f"🖼️  Processing {len(logo_operations)} logo operations BEFORE tracking...")
                
                # DISABLE TRACKING COMPLETELY
                doc.RecordChanges = False
                
                for logo_op in logo_operations:
                    target_text = logo_op.get('target_text', '')
                    print(f"🔍 Looking for logo placeholder: '{target_text}'")
                    
                    # Get logo from questionnaire URL
                    questionnaire_logo = None
                    try:
                        questionnaire_path = 'data/questionnaire_responses.csv'
                        if os.path.exists(questionnaire_path):
                            with open(questionnaire_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                import re
                                urls = re.findall(r'https://[^\s,;]+', content)
                                for url in urls:
                                    if 'image' in url or any(ext in url.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                                        questionnaire_logo = url
                                        print(f"🔗 Found logo URL: {url}")
                                        break
                    except Exception as e:
                        print(f"⚠️  Error reading questionnaire: {e}")
                    
                    # Download and replace logo
                    if questionnaire_logo:
                        try:
                            import requests
                            import tempfile
                            print(f"📥 Downloading logo...")
                            
                            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
                            response = requests.get(questionnaire_logo, headers=headers, stream=True, timeout=30)
                            
                            if response.status_code == 200:
                                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                                for chunk in response.iter_content(chunk_size=8192):
                                    temp_file.write(chunk)
                                temp_file.close()
                                
                                # DIRECT REPLACEMENT WITHOUT TRACKING
                                search_desc = doc.createSearchDescriptor()
                                search_desc.SearchString = target_text
                                search_desc.SearchCaseSensitive = False
                                search_desc.SearchWords = False
                                
                                found_range = doc.findFirst(search_desc)
                                replaced_count = 0
                                while found_range:
                                    try:
                                        # Clear the text first
                                        found_range.setString("")
                                        
                                        # Create and insert graphic
                                        graphic = doc.createInstance("com.sun.star.text.GraphicObject")
                                        logo_file_url = to_url(temp_file.name)
                                        graphic.setPropertyValue("GraphicURL", logo_file_url)
                                        
                                        # Set anchor type to ensure proper positioning
                                        try:
                                            from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
                                            graphic.setPropertyValue("AnchorType", AS_CHARACTER)
                                        except:
                                            pass
                                        
                                        # Set size properly - LibreOffice uses 1/100mm units
                                        try:
                                            # Default to 35mm width, auto height to preserve ratio
                                            width_100mm = 35 * 100  # 35mm = 3500 units
                                            graphic.setPropertyValue("Width", width_100mm)
                                            graphic.setPropertyValue("SizeType", 1)  # Fixed size
                                            graphic.setPropertyValue("RelativeWidth", 0)  # Disable relative sizing
                                            graphic.setPropertyValue("KeepRatio", True)  # Preserve aspect ratio
                                            print(f"📏 Set logo size to 35mm width with preserved aspect ratio")
                                        except Exception as e:
                                            print(f"⚠️  Could not set logo size: {e}")
                                            # Fallback: try different size approaches
                                            try:
                                                graphic.setPropertyValue("Width", 3500)  # 35mm
                                                graphic.setPropertyValue("Height", 2000)  # 20mm
                                                print(f"📏 Fallback: Set logo to 35x20mm")
                                            except Exception as e2:
                                                print(f"⚠️  Fallback sizing also failed: {e2}")
                                                # Last resort: try with Size property
                                                try:
                                                    from com.sun.star.awt import Size
                                                    size = Size()
                                                    size.Width = 3500  # 35mm
                                                    size.Height = 2000  # 20mm 
                                                    graphic.setPropertyValue("Size", size)
                                                    print(f"📏 Last resort: Set size using Size object")
                                                except:
                                                    print(f"⚠️  All sizing methods failed - using default size")
                                        
                                        # Insert the graphic
                                        found_range.getText().insertTextContent(found_range, graphic, False)
                                        replaced_count += 1
                                        print(f"✅ Logo inserted successfully!")
                                        
                                    except Exception as e:
                                        print(f"❌ Failed to insert logo: {e}")
                                    
                                    found_range = doc.findNext(found_range, search_desc)
                                
                                # Clean up
                                try:
                                    os.unlink(temp_file.name)
                                except:
                                    pass
                                    
                                if replaced_count > 0:
                                    print(f"🎉 Successfully replaced {replaced_count} logo placeholder(s)")
                                else:
                                    print(f"❌ Could not find '{target_text}' in document")
                            
                        except Exception as e:
                            print(f"❌ Failed to download/insert logo: {e}")
            
            # NOW enable tracking for other operations
            print(f"🔄 Enabling tracking for other operations...")

            # If provided via JSON metadata, prefer it unless CLI overrides are present
            try:
                meta = data.get('metadata', {})
                json_logo_path = (meta.get('logo_path') or meta.get('logo') or '').strip() or None
                json_logo_w = meta.get('logo_width_mm')
                json_logo_h = meta.get('logo_height_mm')
                if cli_logo_path:
                    logo_path_to_use = cli_logo_path
                else:
                    logo_path_to_use = json_logo_path
                logo_w_to_use = cli_logo_w if cli_logo_w is not None else json_logo_w
                logo_h_to_use = cli_logo_h if cli_logo_h is not None else json_logo_h
            except Exception:
                logo_path_to_use = cli_logo_path
                logo_w_to_use = cli_logo_w
                logo_h_to_use = cli_logo_h

            comment_operations = [op for op in operations if op.get('action') == 'comment']
            print(f"📝 Found {len(comment_operations)} comment-only operations to process")
            
            for op in operations:
                action = op.get('action', 'replace')
                if action == 'replace_with_logo':
                    # Skip - already handled above before tracking was enabled
                    continue
                
                elif action == 'comment':
                    target_text = op.get('target_text', '')
                    comment = op.get('comment', '')
                    author = op.get('comment_author', 'AI Assistant')
                    
                    try:
                        # Find the target text to add comment to
                        search_desc = doc.createSearchDescriptor()
                        search_desc.SearchString = target_text
                        search_desc.SearchCaseSensitive = False
                        search_desc.SearchWords = False
                        
                        found_range = doc.findFirst(search_desc)
                        added_count = 0
                        while found_range:
                            try:
                                # Clean up comment content
                                comment_content = comment.replace('\\\n', '\n').replace('\\n', '\n')
                                
                                # Method 1: Try creating annotation field (most compatible)
                                try:
                                    # Create annotation text field
                                    annotation = doc.createInstance("com.sun.star.text.TextField.Annotation")
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
                                    # Don't collapse - keep the full range selected for the comment
                                    cursor.getText().insertTextContent(cursor, annotation, True)
                                    added_count += 1
                                
                                except Exception as e1:
                                    print(f"Annotation method failed: {e1}")
                                    
                                    # Method 2: Try creating postit annotation (Word-compatible)
                                    try:
                                        annotation = doc.createInstance("com.sun.star.text.textfield.PostItField")
                                        annotation.setPropertyValue("Author", author)
                                        annotation.setPropertyValue("Content", comment_content)
                                        
                                        # Set proper timestamp
                                        dt = create_libreoffice_datetime()
                                        try:
                                            annotation.setPropertyValue("Date", dt)
                                        except Exception:
                                            annotation.setPropertyValue("DateTimeValue", dt)
                                        
                                        cursor = found_range.getText().createTextCursorByRange(found_range)
                                        # Keep the full range selected for the comment
                                        cursor.getText().insertTextContent(cursor, annotation, True)
                                        added_count += 1
                                    
                                    except Exception as e2:
                                        print(f"PostIt method failed: {e2}")
                                        
                                        # Method 3: Simple annotation approach
                                        try:
                                            # Create a simple annotation
                                            annotation = doc.createInstance("com.sun.star.text.textfield.Annotation")
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
                                                added_count += 1
                                            else:
                                                raise Exception("Could not create annotation instance")
                                                
                                        except Exception as e3:
                                            print(f"Basic annotation failed: {e3}")
                                            
                                            # Method 4: Fallback - insert as tracked change with comment
                                            try:
                                                # Make a minimal edit to create a tracked change we can comment on
                                                cursor = found_range.getText().createTextCursorByRange(found_range)
                                                cursor.collapseToStart()
                                                
                                                # Insert a space and immediately delete it to create a tracked change
                                                cursor.getText().insertString(cursor, " ", False)
                                                cursor.goRight(1, True)  # Select the space
                                                cursor.getText().insertString(cursor, "", True)  # Delete (replace with nothing)
                                                
                                                # Try to add comment to the last redline
                                                redlines = doc.getPropertyValue("Redlines")
                                                if redlines and redlines.getCount() > 0:
                                                    last_redline = redlines.getByIndex(redlines.getCount() - 1)
                                                    last_redline.setPropertyValue("Comment", f"{author}: {comment_content}")
                                                    added_count += 1
                                                else:
                                                    print(f"❌ No tracked changes available for comment")
                                                    
                                            except Exception as e4:
                                                print(f"❌ All comment methods failed. Last error: {e4}")
                                
                            except Exception as e:
                                print(f"❌ Could not add comment: {e}")
                            
                            # Move to next occurrence
                            found_range = doc.findNext(found_range, search_desc)
                        
                        if added_count > 0:
                            print(f"✅ Added {added_count} comment(s) to occurrences of '{target_text[:50]}...' by {author}")
                        else:
                            print(f"⚠️ Could not find text '{target_text}' for comment operation")
                    except Exception as e:
                        print(f"❌ Failed to process comment-only operation: {e}")
        
        # Now process replacement/delete operations
        for row in rows_from_file(csv_path):
            find = (row.get("Find") or "").strip()
            repl = (row.get("Replace") or "")
            if not find:
                continue
            match_case = bool_from_str(row.get("MatchCase"))
            whole_word = bool_from_str(row.get("WholeWord"))
            wildcards  = bool_from_str(row.get("Wildcards"))
            comment_text = (row.get("Comment") or "").strip()
            author_name = (row.get("Author") or "AI Assistant").strip()

            # Update the document author for this specific change
            try:
                doc.setPropertyValue("RedlineAuthor", author_name)
                
                # Also try to set it on the document info
                doc_info = doc.getDocumentInfo()
                doc_info.setPropertyValue("Author", author_name)
                doc_info.setPropertyValue("ModifiedBy", author_name)
                
                # Try to update user profile temporarily
                config_provider = smgr.createInstance("com.sun.star.configuration.ConfigurationProvider")
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
                print(f"Could not set author for change: {e}")

            # Keep replacement text clean - use exact replacement value
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

            # Capture redlines count before replacement
            prev_redlines_count = 0
            try:
                prev_redlines = doc.getPropertyValue("Redlines")
                if prev_redlines:
                    prev_redlines_count = prev_redlines.getCount()
            except Exception:
                prev_redlines_count = 0

            # Perform the replacement
            count_replaced = doc.replaceAll(rd)
            
            # Add comment if provided and replacements were made
            if comment_text and count_replaced > 0:
                try:
                    # First, try to attach the comment ONLY to NEW DELETION redlines created by this replaceAll
                    added_to_redlines = 0
                    try:
                        redlines = doc.getPropertyValue("Redlines")
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

                    if added_to_redlines > 0:
                        print(f"✅ Added comment to {added_to_redlines} tracked change(s) by {author_name}")
                    else:
                        # Fallback: annotate occurrences directly (previous behavior)
                        search_desc = doc.createSearchDescriptor()
                        search_desc.SearchString = repl if repl else find
                        search_desc.SearchCaseSensitive = match_case
                        search_desc.SearchWords = whole_word
                        
                        found_range = doc.findFirst(search_desc)
                        added_count = 0
                        while found_range:
                            try:
                                # Method 1: Try creating annotation field (most compatible)
                                try:
                                    annotation = doc.createInstance("com.sun.star.text.TextField.Annotation")
                                    annotation.setPropertyValue("Author", author_name)
                                    annotation.setPropertyValue("Content", comment_text)
                                    
                                    # Set proper timestamp
                                    dt = create_libreoffice_datetime()
                                    try:
                                        annotation.setPropertyValue("Date", dt)
                                    except Exception:
                                        annotation.setPropertyValue("DateTimeValue", dt)
                                    
                                    cursor = found_range.getText().createTextCursorByRange(found_range)
                                    # Keep the full range selected for the comment
                                    cursor.getText().insertTextContent(cursor, annotation, True)
                                    
                                    added_count += 1
                                
                                except Exception as e1:
                                    print(f"Annotation method failed: {e1}")
                                    
                                    # Method 2: Try PostIt field
                                    try:
                                        annotation = doc.createInstance("com.sun.star.text.textfield.PostItField")
                                        annotation.setPropertyValue("Author", author_name)
                                        annotation.setPropertyValue("Content", comment_text)
                                        
                                        # Set proper timestamp
                                        dt = create_libreoffice_datetime()
                                        try:
                                            annotation.setPropertyValue("Date", dt)
                                        except Exception:
                                            annotation.setPropertyValue("DateTimeValue", dt)
                                        
                                        cursor = found_range.getText().createTextCursorByRange(found_range)
                                        # Keep the full range selected for the comment
                                        cursor.getText().insertTextContent(cursor, annotation, True)
                                        
                                        added_count += 1
                                    
                                    except Exception as e2:
                                        print(f"PostIt method failed: {e2}")
                                        
                                        # Method 3: Basic annotation
                                        try:
                                            annotation = doc.createInstance("com.sun.star.text.textfield.Annotation")
                                            if annotation:
                                                annotation.Author = author_name
                                                annotation.Content = comment_text
                                                
                                                # Set proper timestamp
                                                dt = create_libreoffice_datetime()
                                                try:
                                                    annotation.Date = dt
                                                except Exception:
                                                    annotation.DateTimeValue = dt
                                                
                                                # Insert to cover the entire found range
                                                found_range.getText().insertTextContent(found_range, annotation, True)
                                                added_count += 1
                                            else:
                                                raise Exception("Could not create annotation instance")
                                                
                                        except Exception as e3:
                                            print(f"Basic annotation failed: {e3}")
                                            
                                            # Method 4: Fallback to tracked change comment (last redline)
                                            try:
                                                redlines = doc.getPropertyValue("Redlines")
                                                if redlines and redlines.getCount() > 0:
                                                    last_redline = redlines.getByIndex(redlines.getCount() - 1)
                                                    last_redline.setPropertyValue("Comment", f"{author_name}: {comment_text}")
                                                    added_count += 1
                                                else:
                                                    print(f"❌ No tracked changes available for comment")
                                            except Exception as e4:
                                                print(f"❌ All comment methods failed for replacement. Last error: {e4}")
                            except Exception as e:
                                print(f"Warning: Could not add comment: {e}")
                            
                            # Move to next occurrence
                            found_range = doc.findNext(found_range, search_desc)
                        
                        if added_count > 0:
                            print(f"✅ Added {added_count} comment(s) to replacements by {author_name}")
                        else:
                            # Fallback: try to attach to the most recent tracked change
                            try:
                                redlines = doc.getPropertyValue("Redlines")
                                if redlines and redlines.getCount() > 0:
                                    last_redline = redlines.getByIndex(redlines.getCount() - 1)
                                    last_redline.setPropertyValue("Comment", f"{author_name}: {comment_text}")
                                    print(f"✅ Added comment to recent tracked change: {comment_text[:80]}...")
                                else:
                                    print(f"❌ Could not find replacement text and no tracked changes available")
                            except Exception as e:
                                print(f"Could not add comment to tracked change: {e}")
                except Exception as e:
                    print(f"Warning: Could not add comment: {e}")
            
            if count_replaced > 0:
                print(f"Replaced {count_replaced} occurrence(s) of '{find}' with '{repl}' by {author_name}")
    finally:
        # Save as DOCX (Word 2007+ XML)
        out_props = (mkprop("FilterName", "MS Word 2007 XML"),)
        doc.storeToURL(to_url(out_path), out_props)
        doc.close(True)

    print("Done. Wrote:", out_path)

if __name__ == "__main__":
    main()