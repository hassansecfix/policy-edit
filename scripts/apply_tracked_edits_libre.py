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
import datetime
import subprocess
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser(description="Apply tracked edits to DOCX via LibreOffice (headless UNO).")
    p.add_argument("--in", dest="in_path", required=True, help="Input .docx")
    p.add_argument("--csv", dest="csv_path", required=True, help="CSV with columns: Find,Replace,MatchCase,WholeWord,Wildcards OR JSON with operations format")
    p.add_argument("--out", dest="out_path", required=True, help="Output .docx (will be overwritten)")
    p.add_argument("--launch", action="store_true", help="Launch a headless LibreOffice UNO listener if not already running")
    return p.parse_args()

def bool_from_str(s, default=False):
    if s is None: return default
    s = str(s).strip().lower()
    return s in ("1","true","yes","y")

def create_libreoffice_datetime():
    """Create a proper LibreOffice DateTime object for current time"""
    try:
        from com.sun.star.util import DateTime
        now = datetime.datetime.now()
        
        # Create LibreOffice DateTime object
        dt = DateTime()
        dt.Year = now.year
        dt.Month = now.month
        dt.Day = now.day
        dt.Hours = now.hour
        dt.Minutes = now.minute
        dt.Seconds = now.second
        dt.NanoSeconds = now.microsecond * 1000
        
        return dt
    except Exception as e:
        # Fallback to string format if DateTime fails
        print(f"DateTime creation failed: {e}, using string fallback")
        return time.strftime("%Y-%m-%d %H:%M:%S")

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

    # Apply replacements and comments (main body). Extend for headers/footers if needed (see TODO).
    try:
        # First, process comment-only operations directly from JSON
        if csv_path.endswith('.json'):
            with open(csv_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            operations = data.get('instructions', {}).get('operations', [])
            
            comment_operations = [op for op in operations if op.get('action') == 'comment']
            print(f"📝 Found {len(comment_operations)} comment-only operations to process")
            
            for op in operations:
                action = op.get('action', 'replace')
                if action == 'comment':
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
                        if found_range:
                            try:
                                # Clean up comment content
                                comment_content = comment.replace('\\\\n', '\n').replace('\\n', '\n')
                                
                                # Create a simple DOCX comment/annotation
                                annotation = doc.createInstance("com.sun.star.text.textfield.Annotation")
                                annotation.setPropertyValue("Author", author)
                                annotation.setPropertyValue("Content", comment_content)
                                annotation.setPropertyValue("Date", create_libreoffice_datetime())
                                
                                # Insert the comment at the found text location covering the entire range
                                cursor = found_range.getText().createTextCursorByRange(found_range)
                                cursor.getText().insertTextContent(cursor, annotation, True)
                                
                                print(f"✅ Added comment to '{target_text[:50]}...' by {author}")
                                
                            except Exception as e:
                                print(f"❌ Could not add comment: {e}")
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

            # Perform the replacement first
            count_replaced = doc.replaceAll(rd)
            
            # Add comment if provided and replacements were made
            if comment_text and count_replaced > 0:
                try:
                    # Simpler approach: Find the replaced text and add annotation
                    search_desc = doc.createSearchDescriptor()
                    search_desc.SearchString = repl if repl else find
                    search_desc.SearchCaseSensitive = match_case
                    search_desc.SearchWords = whole_word
                    
                    found_range = doc.findFirst(search_desc)
                    if found_range:
                        # Add Word-compatible comment
                        try:
                            # Create Word-style annotation for compatibility
                            annotation = doc.createInstance("com.sun.star.text.textfield.Annotation")
                            annotation.setPropertyValue("Author", author_name)
                            annotation.setPropertyValue("Content", comment_text)
                            annotation.setPropertyValue("Date", create_libreoffice_datetime())
                            
                            # Insert covering the entire found range
                            cursor = found_range.getText().createTextCursorByRange(found_range)
                            cursor.getText().insertTextContent(cursor, annotation, True)
                            print(f"✅ Added comment to replacement by {author_name}")
                            print(f"   Comment: {comment_text[:100]}...")
                            
                        except Exception as e1:
                            print(f"Could not add annotation: {e1}")
                    else:
                        # Fallback: try to attach to tracked change
                        try:
                            redlines = doc.getPropertyValue("Redlines")
                            if redlines and redlines.getCount() > 0:
                                last_redline = redlines.getByIndex(redlines.getCount() - 1)
                                last_redline.setPropertyValue("Comment", comment_text)
                                print(f"✅ Added comment to tracked change: {comment_text[:80]}...")
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
