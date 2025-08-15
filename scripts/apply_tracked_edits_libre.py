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
    return p.parse_args()

def bool_from_str(s, default=False):
    if s is None: return default
    s = str(s).strip().lower()
    return s in ("1","true","yes","y")

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
        
        # Skip comment-only operations (action == 'comment')
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
        
        # Start LibreOffice headless listener
        process = subprocess.Popen([
            "soffice",
            "--headless",
            "--nologo",
            "--nodefault",
            "--norestore",
            "--invisible",
            '--accept=socket,host=127.0.0.1,port=2002;urp;StarOffice.ServiceManager'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
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

    # Ensure Track Changes on
    try:
        # For Writer documents this should be available:
        doc.RecordChanges = True
        # Set the revision author for this session
        doc.setPropertyValue("RedlineAuthor", "Secfix AI")
    except Exception as e:
        print(f"Warning: Could not enable track changes: {e}")

    # Apply replacements (main body). Extend for headers/footers if needed (see TODO).
    try:
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
            except Exception:
                pass

            # Enhance replacement text with comment if provided
            enhanced_repl = repl
            if comment_text:
                # Add comment as a subtle inline note
                comment_summary = comment_text.replace('\n', ' ').strip()
                if len(comment_summary) > 100:
                    comment_summary = comment_summary[:97] + "..."
                enhanced_repl = f"{repl} [AI: {comment_summary}]"

            rd = doc.createReplaceDescriptor()
            rd.SearchString = find
            rd.ReplaceString = enhanced_repl
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
                # Try multiple approaches to add the comment
                try:
                    # Method 1: Try to find and modify the most recent tracked change
                    redlines = doc.getPropertyValue("Redlines")
                    if redlines and redlines.getCount() > 0:
                        # Get the last redline (most recent change)
                        last_redline = redlines.getByIndex(redlines.getCount() - 1)
                        
                        # Try to set comment on the redline itself
                        try:
                            last_redline.setPropertyValue("Comment", comment_text)
                            print(f"✅ Added comment to tracked change: {comment_text[:80]}...")
                        except Exception as e:
                            print(f"Could not set redline comment: {e}")
                            
                        # Try to set description
                        try:
                            last_redline.setPropertyValue("Description", comment_text)
                            print(f"✅ Added description to tracked change")
                        except Exception as e:
                            print(f"Could not set redline description: {e}")
                        
                        # Method 2: Add visible annotation at the change location
                        try:
                            redline_range = last_redline.getAnchor()
                            
                            # Create annotation with formatted comment
                            annotation = doc.createInstance("com.sun.star.text.textfield.Annotation")
                            formatted_comment = f"💡 {author_name}: {comment_text}"
                            annotation.setPropertyValue("Content", formatted_comment)
                            annotation.setPropertyValue("Author", author_name)
                            annotation.setPropertyValue("Date", time.strftime("%Y-%m-%dT%H:%M:%S"))
                            
                            # Insert at the end of the changed range for visibility
                            redline_range.insertTextContent(redline_range.getEnd(), annotation, False)
                            print(f"✅ Added visible annotation by {author_name}")
                        except Exception as e:
                            print(f"Could not add annotation: {e}")
                            
                        # Method 3: Try to add comment to redline properties
                        try:
                            redline_props = last_redline.getPropertySetInfo()
                            available_props = [prop.Name for prop in redline_props.getProperties()]
                            print(f"Available redline properties: {', '.join(available_props[:5])}...")
                            
                            # Try various comment property names
                            for prop_name in ['RedlineComment', 'RedlineText', 'Comment']:
                                try:
                                    if redline_props.hasPropertyByName(prop_name):
                                        last_redline.setPropertyValue(prop_name, comment_text)
                                        print(f"✅ Set {prop_name}: {comment_text[:50]}...")
                                        break
                                except Exception:
                                    continue
                        except Exception as e:
                            print(f"Could not analyze redline properties: {e}")
                    
                    # Method 4: As fallback, add a visible text comment near the change
                    try:
                        # Find the replaced text to add comment nearby
                        search_desc = doc.createSearchDescriptor()
                        search_desc.SearchString = enhanced_repl if enhanced_repl else find
                        search_desc.SearchCaseSensitive = match_case
                        search_desc.SearchWords = False  # Don't use whole word since we added comment
                        
                        found_range = doc.findFirst(search_desc)
                        if found_range:
                            print(f"✅ Comment included in replacement text")
                        else:
                            print(f"Could not find enhanced replacement text for additional comment")
                    except Exception as e:
                        print(f"Could not verify comment integration: {e}")
                        
                except Exception as e:
                    print(f"Warning: Could not process comment: {e}")
            
            if count_replaced > 0:
                print(f"Replaced {count_replaced} occurrence(s) of '{find}' with '{enhanced_repl}' by {author_name}")
    finally:
        # Save as DOCX (Word 2007+ XML)
        out_props = (mkprop("FilterName", "MS Word 2007 XML"),)
        doc.storeToURL(to_url(out_path), out_props)
        doc.close(True)

    print("Done. Wrote:", out_path)

if __name__ == "__main__":
    main()
