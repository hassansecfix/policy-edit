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

# Configuration constants
LOGO_SPACES_THRESHOLD = -14  # Additional spaces to remove on top of replacement text length for logo positioning

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
    p.add_argument("--fast", action="store_true", help="Enable fast mode: use shorter timeouts, minimal retries, optimized logo downloads")
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

def ensure_listener(fast_mode=False):
    # Start a headless LibreOffice UNO listener on port 2002 if not already running.
    # Harmless if one is already up.
    try:
        # Kill any existing LibreOffice processes to ensure clean start
        subprocess.run(["pkill", "-f", "soffice"], capture_output=True, timeout=2 if fast_mode else 5)
        time.sleep(0.5 if fast_mode else 1)
        
        # Create a temporary user profile with correct author info (skip in fast mode)
        profile_dir = "/tmp/lo_profile_secfix"
        if not fast_mode:
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
        subprocess.Popen([
            "soffice",
            "--headless",
            "--nologo",
            "--nodefault",
            "--norestore",
            "--invisible",
            f"-env:UserInstallation=file://{profile_dir}",
            '--accept=socket,host=127.0.0.1,port=2002;urp;StarOffice.ServiceManager'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=os.environ)
        
        # Wait and test connection (reduced time in fast mode)
        max_wait = 5 if fast_mode else 15
        wait_interval = 0.2 if fast_mode else 0.5
        print("Starting LibreOffice listener...")
        for i in range(max_wait):
            time.sleep(wait_interval)
            try:
                # Test if we can connect
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex(('127.0.0.1', 2002))
                sock.close()
                if result == 0:
                    print(f"LibreOffice listener ready after {(i+1)*wait_interval:.1f} seconds")
                    return
            except:
                pass
            if not fast_mode or i % 5 == 0:  # Reduce log spam in fast mode
                print(f"Waiting for LibreOffice... ({i+1}/{max_wait})")
        
        print("WARNING: LibreOffice listener may not be ready")
        
    except FileNotFoundError:
        print("ERROR: 'soffice' not found on PATH. Install LibreOffice or add it to PATH.", file=sys.stderr)

def main():
    args = parse_args()
    import os
    in_path = os.path.abspath(args.in_path)
    out_path = os.path.abspath(args.out_path)
    csv_path = os.path.abspath(args.csv_path)

    if not os.path.exists(in_path):
        print("Input DOCX not found:", in_path, file=sys.stderr); sys.exit(2)
    if not os.path.exists(csv_path):
        print("CSV not found:", csv_path, file=sys.stderr); sys.exit(2)

    if args.launch:
        ensure_listener(fast_mode=args.fast)

    try:
        import uno
        from com.sun.star.beans import PropertyValue
    except Exception:
        print("ERROR: UNO bridge not available. Run with LibreOffice's Python (recommended).", file=sys.stderr)
        sys.exit(1)

    # Connect to running LibreOffice with retries (fewer retries in fast mode)
    local_ctx = uno.getComponentContext()
    resolver = local_ctx.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local_ctx)
    
    print("Connecting to LibreOffice...")
    ctx = None
    max_attempts = 3 if args.fast else 10
    retry_delay = 0.5 if args.fast else 2
    for attempt in range(max_attempts):
        try:
            ctx = resolver.resolve("uno:socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext")
            print(f"✅ Connected to LibreOffice (attempt {attempt + 1})")
            break
        except Exception as e:
            if attempt < max_attempts - 1:
                if not args.fast or attempt == 0:  # Reduce log spam in fast mode
                    print(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print(f"❌ Could not connect to LibreOffice listener after {max_attempts} attempts. Error: {e}", file=sys.stderr)
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

    # Utility function for unit conversion (currently unused but kept for future use)
    # def mm_to_100th_mm(mm):
    #     try:
    #         return int(mm) * 100
    #     except Exception:
    #         return None



    # Load hidden
    in_props = (mkprop("Hidden", True),)
    doc = desktop.loadComponentFromURL(to_url(in_path), "_blank", 0, in_props)

    # Set document properties for tracked changes (skip in fast mode)
    if not args.fast:
        try:
            doc_info = doc.getDocumentInfo()
            doc_info.setPropertyValue("Author", "Secfix AI")
            doc_info.setPropertyValue("ModifiedBy", "Secfix AI")
        except Exception as e:
            print(f"Warning: Could not set document author: {e}")
    else:
        print("⚡ Fast mode: Skipping document metadata setup")

    # Initially set tracking to False - we'll enable it after logo operations
    # This gets overridden later in the script
    try:
        # For Writer documents this should be available:
        doc.RecordChanges = False  # Start with tracking OFF
        
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
        # Note: CLI logo parameters are available but base64 data is preferred

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
                            dynamic_spaces_to_remove = length_difference + LOGO_SPACES_THRESHOLD
                            print(f"📏 Found company name replacement:")
                            print(f"📏   Target: '{target_text_op}' ({target_length} chars)")
                            print(f"📏   Replacement: '{replacement_text}' ({replacement_length} chars)")
                            print(f"📏   Difference: {replacement_length} - {target_length} = {length_difference}")
                            print(f"📏   Dynamic spaces to remove: {length_difference} + {LOGO_SPACES_THRESHOLD} = {dynamic_spaces_to_remove}")
                            break
                
                for logo_op in logo_operations:
                    target_text = logo_op.get('target_text', '')
                    print(f"🔍 Looking for logo placeholder: '{target_text}'")
                    
                    # Get logo from metadata (preferred) or user's uploaded data (fallback)
                    logo_file_path = None
                    logo_base64_data = None
                    
                    # First, check if logo path is already provided in JSON metadata
                    try:
                        meta = data.get('metadata', {})
                        meta_logo_path = meta.get('logo_path', '').strip()
                        if meta_logo_path and os.path.exists(meta_logo_path):
                            logo_file_path = meta_logo_path
                            print(f"🖼️  Using logo from metadata: {logo_file_path}")
                    except Exception as e:
                        print(f"⚠️  Error reading metadata: {e}")
                    
                    # Fallback 1: Check JSON metadata for base64 logo data
                    if not logo_file_path:
                        try:
                            meta = data.get('metadata', {})
                            # Look for base64 logo data in metadata
                            if 'logo_base64_data' in meta:
                                logo_base64_data = meta['logo_base64_data']
                                print(f"🖼️  Found base64 logo data in JSON metadata")
                        except Exception as e:
                            print(f"⚠️  Error reading metadata: {e}")
                    
                    # Fallback 2: Check if environment has base64 data 
                    if not logo_file_path and not logo_base64_data:
                        import os
                        env_data = os.environ.get('QUESTIONNAIRE_ANSWERS_DATA')
                        if env_data:
                            try:
                                import json
                                json_data = json.loads(env_data)
                                logo_data = json_data.get('_logo_base64_data', {})
                                if isinstance(logo_data, dict) and 'value' in logo_data:
                                    logo_base64_data = logo_data['value']
                                    print(f"🖼️  Found base64 logo data in environment")
                            except Exception as e:
                                print(f"⚠️  Error reading environment logo data: {e}")
                    
                    # Fallback 3: try to get base64 data from questionnaire CSV
                    if not logo_file_path and not logo_base64_data and args.questionnaire_csv and os.path.exists(args.questionnaire_csv):
                        try:
                            with open(args.questionnaire_csv, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                            # Look for embedded base64 logo data first (user upload)
                            for line in content.split('\n'):
                                if line.startswith('99;Logo Base64 Data;_logo_base64_data;'):
                                    parts = line.split(';', 4)
                                    if len(parts) >= 5:
                                        logo_base64_data = parts[4]
                                        print(f"🖼️  Found user's uploaded logo data in questionnaire CSV")
                                        break
                        except Exception as e:
                            print(f"⚠️  Error reading user questionnaire: {e}")
                    
                    # Process logo (either from existing file or convert from base64)
                    if logo_file_path or logo_base64_data:
                        try:
                            temp_file_to_cleanup = None
                            actual_logo_path = None
                            
                            if logo_file_path:
                                # Use existing logo file
                                actual_logo_path = logo_file_path
                                print(f"🖼️  Using existing logo file: {actual_logo_path}")
                            elif logo_base64_data:
                                # Convert base64 directly to LibreOffice graphic without temporary file
                                import base64
                                print(f"🖼️  Processing base64 logo data directly...")
                                
                                # Validate and clean base64 data
                                if ',' in logo_base64_data:
                                    base64_content = logo_base64_data.split(',')[1]
                                    print(f"🔍 Removed data URL prefix, base64 content length: {len(base64_content)}")
                                else:
                                    base64_content = logo_base64_data
                                    print(f"🔍 Using raw base64 content, length: {len(base64_content)}")
                                
                                # Validate base64 content
                                if not base64_content or len(base64_content.strip()) == 0:
                                    print(f"❌ Base64 content is empty after processing")
                                    continue
                                
                                # Clean base64 content (remove whitespace)
                                base64_content = base64_content.strip()
                                
                                # Decode base64 to binary with error handling
                                try:
                                    logo_binary = base64.b64decode(base64_content, validate=True)
                                    if len(logo_binary) == 0:
                                        print(f"❌ Base64 decoded to empty binary data")
                                        continue
                                    print(f"✅ Successfully decoded base64 to {len(logo_binary)} bytes")
                                except Exception as decode_error:
                                    print(f"❌ Base64 decode failed: {decode_error}")
                                    print(f"🔍 Base64 sample (first 100 chars): {base64_content[:100]}...")
                                    continue
                                
                                # Create temporary file for LibreOffice with better error handling
                                try:
                                    # Create a temporary file for LibreOffice to read
                                    import tempfile
                                    import os
                                    
                                    # Determine image format from base64 header
                                    image_suffix = '.png'  # default
                                    if logo_base64_data.startswith('data:image/'):
                                        format_part = logo_base64_data.split(';')[0].split('/')[-1]
                                        if format_part.lower() in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                                            image_suffix = f'.{format_part.lower()}'
                                    
                                    # Create temporary file with proper permissions
                                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=image_suffix)
                                    temp_file.write(logo_binary)
                                    temp_file.flush()  # Ensure data is written
                                    temp_file.close()
                                    
                                    # Verify file was created and has content
                                    if os.path.exists(temp_file.name) and os.path.getsize(temp_file.name) > 0:
                                        actual_logo_path = temp_file.name
                                        temp_file_to_cleanup = temp_file.name
                                        print(f"✅ Logo temporary file created: {temp_file.name} ({len(logo_binary)} bytes, format: {image_suffix})")
                                        
                                        # Set readable permissions
                                        try:
                                            os.chmod(temp_file.name, 0o644)
                                        except Exception:
                                            pass  # Not critical if chmod fails
                                    else:
                                        print(f"❌ Temporary file creation failed or file is empty")
                                        actual_logo_path = None
                                        temp_file_to_cleanup = None
                                        
                                except Exception as e:
                                    print(f"❌ Failed to process base64 logo data: {e}")
                                    import traceback
                                    print(f"🐛 Stack trace: {traceback.format_exc()}")
                                    actual_logo_path = None
                                    temp_file_to_cleanup = None
                            
                            if actual_logo_path and os.path.exists(actual_logo_path):
                                # Handle both space removal (positive) and space addition (negative)
                                if dynamic_spaces_to_remove >= 0:
                                    print(f"🔄 Attempting to remove up to {dynamic_spaces_to_remove} spaces before '{target_text}' using multiple strategies")
                                else:
                                    spaces_to_add = abs(dynamic_spaces_to_remove)
                                    print(f"🔄 Attempting to add {spaces_to_add} spaces before '{target_text}'")
                                    
                                    # Add spaces by finding target and inserting spaces before it
                                    search_desc = doc.createSearchDescriptor()
                                    search_desc.SearchString = target_text
                                    search_desc.SearchCaseSensitive = False
                                    search_desc.SearchWords = False
                                    
                                    found_range = doc.findFirst(search_desc)
                                    if found_range:
                                        # Insert spaces before the target text
                                        cursor = found_range.getText().createTextCursorByRange(found_range)
                                        cursor.collapseToStart()
                                        spaces_to_insert = " " * spaces_to_add
                                        cursor.getText().insertString(cursor, spaces_to_insert, False)
                                        print(f"✅ Added {spaces_to_add} spaces before logo placeholder")
                                    
                                    # For negative difference, directly replace target with logo (no space removal needed)
                                    search_desc = doc.createSearchDescriptor()
                                    search_desc.SearchString = target_text
                                    search_desc.SearchCaseSensitive = False
                                    search_desc.SearchWords = False
                                    
                                    found_range = doc.findFirst(search_desc)
                                    logo_count = 0
                                    
                                    while found_range:
                                        try:
                                            # Clear the target text
                                            found_range.setString("")
                                            
                                            # Create and insert graphic
                                            graphic = doc.createInstance("com.sun.star.text.GraphicObject")
                                            logo_file_url = to_url(actual_logo_path)
                                            graphic.setPropertyValue("GraphicURL", logo_file_url)
                                            
                                            # Set anchor type
                                            try:
                                                from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
                                                graphic.setPropertyValue("AnchorType", AS_CHARACTER)
                                            except:
                                                pass
                                            
                                            # Set size - 35mm x 10mm
                                            try:
                                                graphic.setPropertyValue("Width", 3500)  # 35mm
                                                graphic.setPropertyValue("Height", 1000)  # 10mm
                                                graphic.setPropertyValue("SizeType", 1)
                                                graphic.setPropertyValue("RelativeWidth", 0)
                                                graphic.setPropertyValue("KeepRatio", False)
                                                print(f"📏 Set logo size to 35mm x 10mm")
                                            except Exception as e:
                                                print(f"⚠️  Using default logo size: {e}")
                                            
                                            # Insert the graphic
                                            found_range.getText().insertTextContent(found_range, graphic, False)
                                            logo_count += 1
                                            print(f"✅ Logo #{logo_count} inserted successfully!")
                                            
                                        except Exception as e:
                                            print(f"❌ Failed to insert logo: {e}")
                                        
                                        found_range = doc.findNext(found_range, search_desc)
                                    
                                    print(f"🎉 Successfully replaced {logo_count} logo placeholder(s) with user's logo after adding spaces")
                                
                                # For positive difference, proceed with space removal and logo replacement
                                import re
                                escaped_target = re.escape(target_text)
                                replaced_count = 0
                                
                                if dynamic_spaces_to_remove >= 0:
                                    # Only do space removal strategies when we need to remove spaces
                                    # Strategy 0: Debug - Find what's actually around the target text
                                    try:
                                        search_desc = doc.createSearchDescriptor()
                                        search_desc.SearchString = target_text
                                        search_desc.SearchCaseSensitive = False
                                        search_desc.SearchWords = False
                                        
                                        found_range = doc.findFirst(search_desc)
                                        if found_range:
                                            # Get surrounding text to see what's actually there
                                            cursor = found_range.getText().createTextCursorByRange(found_range)
                                            cursor.goLeft(dynamic_spaces_to_remove + 5, True)  # Expand left to capture preceding chars
                                            cursor.gotoRange(found_range.getEnd(), True)  # Extend to end of original range
                                            surrounding_text = cursor.getString()
                                            
                                            # Show character codes for debugging
                                            char_codes = [f"'{char}'({ord(char)})" for char in surrounding_text[-50:]]
                                            print(f"🔍 Debug: Text around target (last 50 chars): {' '.join(char_codes)}")
                                            print(f"🔍 Debug: Full surrounding text: '{surrounding_text}'")
                                        else:
                                            print(f"🔍 Debug: Could not find target text '{target_text}' for inspection")
                                    except Exception as e:
                                        print(f"🔍 Debug: Could not inspect surrounding text: {e}")
                                    
                                    # Strategy 1: Try comprehensive whitespace regex (spaces, tabs, non-breaking spaces)
                                    try:
                                        # Pattern: up to dynamic_spaces_to_remove whitespace chars (spaces, tabs, non-breaking spaces) followed by target
                                        regex_pattern = f"[\\s\\u00A0\\u2000-\\u200A\\u202F\\u205F\\u3000]{{0,{dynamic_spaces_to_remove}}}{escaped_target}"
                                        
                                        rd1 = doc.createReplaceDescriptor()
                                        rd1.SearchString = regex_pattern
                                        rd1.ReplaceString = "__LOGO_PLACEHOLDER__"
                                        rd1.SearchCaseSensitive = False
                                        rd1.SearchWords = False
                                        rd1.setPropertyValue("RegularExpressions", True)
                                        
                                        replaced_count = doc.replaceAll(rd1)
                                        print(f"🔍 Strategy 1 (comprehensive whitespace regex): replaced {replaced_count} instances")
                                        
                                        if replaced_count == 0:
                                            # Strategy 2: Try simpler space-only regex
                                            regex_pattern2 = f" {{0,{dynamic_spaces_to_remove}}}{escaped_target}"
                                            rd2 = doc.createReplaceDescriptor()
                                            rd2.SearchString = regex_pattern2
                                            rd2.ReplaceString = "__LOGO_PLACEHOLDER__"
                                            rd2.SearchCaseSensitive = False
                                            rd2.SearchWords = False
                                            rd2.setPropertyValue("RegularExpressions", True)
                                            
                                            replaced_count = doc.replaceAll(rd2)
                                            print(f"🔍 Strategy 2 (simple space regex): replaced {replaced_count} instances")
                                            
                                    except Exception as e:
                                        print(f"⚠️  Regex strategies failed: {e}")
                                        replaced_count = 0
                                
                                # Strategy 3: Try tab characters and mixed whitespace if regex failed AND spaces are allowed
                                if replaced_count == 0 and dynamic_spaces_to_remove > 0:
                                    print(f"🔄 Strategy 3: Trying tabs and mixed whitespace patterns (since dynamic_spaces_to_remove = {dynamic_spaces_to_remove})")
                                    
                                    # Generate whitespace patterns dynamically based on dynamic_spaces_to_remove
                                    whitespace_patterns = []
                                    
                                    # Add tab patterns only if we allow space removal
                                    max_tabs = min(5, dynamic_spaces_to_remove)  # Limit tabs to reasonable number
                                    for num_tabs in range(max_tabs, 0, -1):
                                        tabs = "\t" * num_tabs
                                        whitespace_patterns.append(f"{tabs}{target_text}")
                                    
                                    # Add mixed tab/space patterns
                                    if dynamic_spaces_to_remove >= 2:
                                        whitespace_patterns.extend([
                                            f"\t {target_text}",           # Tab + space
                                            f" \t{target_text}",           # Space + tab
                                        ])
                                    
                                    # Add non-breaking space patterns
                                    max_nbsp = min(4, dynamic_spaces_to_remove)
                                    for num_nbsp in range(max_nbsp, 0, -1):
                                        nbsp = "\u00A0" * num_nbsp
                                        whitespace_patterns.append(f"{nbsp}{target_text}")
                                    
                                    print(f"🔍 Generated {len(whitespace_patterns)} whitespace patterns for dynamic_spaces_to_remove={dynamic_spaces_to_remove}")
                                    
                                    for pattern in whitespace_patterns:
                                        rd_ws = doc.createReplaceDescriptor()
                                        rd_ws.SearchString = pattern
                                        rd_ws.ReplaceString = "__LOGO_PLACEHOLDER__"
                                        rd_ws.SearchCaseSensitive = False
                                        rd_ws.SearchWords = False
                                        
                                        count = doc.replaceAll(rd_ws)
                                        if count > 0:
                                            replaced_count += count
                                            print(f"🎯 Found and replaced {count} instance(s) with special whitespace")
                                            break
                                elif replaced_count == 0 and dynamic_spaces_to_remove == 0:
                                    print(f"🔄 Strategy 3: SKIPPED (dynamic_spaces_to_remove = 0, no whitespace removal allowed)")
                                
                                # Strategy 4: Manual space removal if all other strategies failed
                                if replaced_count == 0:
                                    print(f"🔄 Strategy 4: Manual space removal approach")
                                    
                                    # Try different space combinations manually - generate dynamically based on dynamic_spaces_to_remove
                                    space_patterns = []
                                    for num_spaces in range(dynamic_spaces_to_remove, -1, -1):  # From dynamic_spaces_to_remove down to 0
                                        spaces = " " * num_spaces
                                        space_patterns.append(f"{spaces}{target_text}")
                                    
                                    print(f"🔍 Trying {len(space_patterns)} different space combinations (from {dynamic_spaces_to_remove} down to 0 spaces)")
                                    
                                    for pattern in space_patterns:
                                        rd3 = doc.createReplaceDescriptor()
                                        rd3.SearchString = pattern
                                        rd3.ReplaceString = "__LOGO_PLACEHOLDER__"
                                        rd3.SearchCaseSensitive = False
                                        rd3.SearchWords = False
                                        
                                        count = doc.replaceAll(rd3)
                                        if count > 0:
                                            replaced_count += count
                                            spaces_count = len(pattern) - len(target_text)
                                            print(f"🎯 Found and replaced {count} instance(s) with {spaces_count} spaces")
                                            break  # Stop after first successful replacement pattern
                                    
                                    if replaced_count == 0:
                                        print(f"⚠️  Could not find '{target_text}' with any space combination")
                                
                                print(f"🔄 Total replaced: {replaced_count} instances with temp placeholder")
                                
                                if replaced_count > 0:
                                    # Now find and replace the temp placeholder with actual logo
                                    search_desc = doc.createSearchDescriptor()
                                    search_desc.SearchString = "__LOGO_PLACEHOLDER__"
                                    search_desc.SearchCaseSensitive = True
                                    search_desc.SearchWords = False
                                    
                                    found_range = doc.findFirst(search_desc)
                                    logo_count = 0
                                    
                                    while found_range:
                                        try:
                                            # Clear the temp placeholder
                                            found_range.setString("")
                                            
                                            # Create and insert graphic
                                            graphic = doc.createInstance("com.sun.star.text.GraphicObject")
                                            logo_file_url = to_url(actual_logo_path)
                                            graphic.setPropertyValue("GraphicURL", logo_file_url)
                                            
                                            # Set anchor type
                                            try:
                                                from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
                                                graphic.setPropertyValue("AnchorType", AS_CHARACTER)
                                            except:
                                                pass
                                            
                                            # Set size - 35mm x 10mm
                                            try:
                                                graphic.setPropertyValue("Width", 3500)  # 35mm
                                                graphic.setPropertyValue("Height", 1000)  # 10mm
                                                graphic.setPropertyValue("SizeType", 1)
                                                graphic.setPropertyValue("RelativeWidth", 0)
                                                graphic.setPropertyValue("KeepRatio", False)
                                                print(f"📏 Set logo size to 35mm x 10mm")
                                            except Exception as e:
                                                print(f"⚠️  Using default logo size: {e}")
                                            
                                            # Insert the graphic
                                            found_range.getText().insertTextContent(found_range, graphic, False)
                                            logo_count += 1
                                            print(f"✅ Logo #{logo_count} inserted successfully!")
                                            
                                        except Exception as e:
                                            print(f"❌ Failed to insert logo: {e}")
                                        
                                        found_range = doc.findNext(found_range, search_desc)
                                    
                                    replaced_count = logo_count
                                
                                # Clean up temporary file if created
                                if temp_file_to_cleanup:
                                    try:
                                        os.unlink(temp_file_to_cleanup)
                                        print(f"🧹 Cleaned up temporary logo file: {temp_file_to_cleanup}")
                                    except Exception as e:
                                        print(f"⚠️  Could not clean up temporary file: {e}")
                                        
                                if replaced_count > 0:
                                    print(f"🎉 Successfully replaced {replaced_count} logo placeholder(s) with user's logo")
                                else:
                                    print(f"❌ Could not find '{target_text}' in document")
                            else:
                                print(f"❌ Logo file not found: {actual_logo_path}")
                                    
                        except Exception as e:
                            print(f"❌ Failed to process user's logo: {e}")
                    else:
                        print(f"⚠️  No user logo data found - skipping logo replacement")
            
        # ALWAYS enable tracking for other operations (whether we had logo operations or not)
        print(f"🔄 Enabling tracking for text replacements and other changes...")
        doc.RecordChanges = True
        print(f"✅ Tracking enabled - all subsequent changes will be tracked")

        # Process comment-only operations from JSON data

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
            else:
                print(f"❌ Unknown action: {action}")
        
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
                if args.fast and count_replaced > 10:
                    print(f"⚡ Replaced {count_replaced} occurrences by {author_name} (fast mode)")
                else:
                    print(f"Replaced {count_replaced} occurrence(s) of '{find}' with '{repl}' by {author_name}")
    finally:
        # Save as DOCX (Word 2007+ XML)
        out_props = (mkprop("FilterName", "MS Word 2007 XML"),)
        doc.storeToURL(to_url(out_path), out_props)
        doc.close(True)

    print("Done. Wrote:", out_path)

if __name__ == "__main__":
    main()