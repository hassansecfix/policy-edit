#!/usr/bin/env python3
"""
Alternative approach using LibreOffice macros to apply tracked changes.
This bypasses the UNO Python import issues.
"""
import argparse
import csv
import os
import sys
import subprocess
import tempfile
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser(description="Apply tracked edits to DOCX via LibreOffice macros.")
    p.add_argument("--in", dest="in_path", required=True, help="Input .docx")
    p.add_argument("--csv", dest="csv_path", required=True, help="CSV with Find/Replace rules")
    p.add_argument("--out", dest="out_path", required=True, help="Output .docx")
    return p.parse_args()

def csv_to_macro_commands(csv_path):
    """Convert CSV to LibreOffice Basic macro commands."""
    commands = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            find_text = row.get('Find', '').strip()
            replace_text = row.get('Replace', '').strip()
            
            if not find_text:
                continue
                
            # Escape quotes for Basic
            find_escaped = find_text.replace('"', '""')
            replace_escaped = replace_text.replace('"', '""')
            
            # Create Basic command for find/replace with track changes
            command = f'''
    oDoc.RecordChanges = True
    oReplace = oDoc.createReplaceDescriptor()
    oReplace.SearchString = "{find_escaped}"
    oReplace.ReplaceString = "{replace_escaped}"
    oDoc.replaceAll(oReplace)'''
            
            commands.append(command)
    
    return '\n'.join(commands)

def create_macro(input_path, output_path, replace_commands):
    """Create a LibreOffice Basic macro to apply changes."""
    
    macro_content = f'''
Sub ApplyTrackedEdits
    Dim oDoc As Object
    Dim oReplace As Object
    
    ' Open document
    oDoc = StarDesktop.loadComponentFromURL("{Path(input_path).absolute().as_uri()}", "_blank", 0, Array())
    
    ' Enable track changes
    oDoc.RecordChanges = True
    
    ' Apply all replacements
{replace_commands}
    
    ' Save as DOCX
    Dim SaveParams(0) As New com.sun.star.beans.PropertyValue
    SaveParams(0).Name = "FilterName"
    SaveParams(0).Value = "MS Word 2007 XML"
    
    oDoc.storeToURL("{Path(output_path).absolute().as_uri()}", SaveParams())
    
    ' Close document
    oDoc.close(True)
    
    ' Exit LibreOffice
    StarDesktop.terminate()
End Sub
'''
    
    return macro_content

def run_macro_with_libreoffice(macro_content):
    """Run the macro using LibreOffice."""
    
    # Create temporary macro file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.bas', delete=False, encoding='utf-8') as f:
        f.write(macro_content)
        macro_file = f.name
    
    try:
        # Run LibreOffice with the macro
        cmd = [
            'soffice',
            '--headless',
            '--invisible',
            '--nodefault',
            '--nolockcheck',
            '--nologo',
            '--norestore',
            f'--macro-file={macro_file}',
            '--macro=ApplyTrackedEdits'
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Macro executed successfully")
            return True
        else:
            print(f"❌ Macro failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Macro execution timed out")
        return False
    except Exception as e:
        print(f"❌ Error running macro: {e}")
        return False
    finally:
        # Clean up temporary file
        try:
            os.unlink(macro_file)
        except:
            pass

def main():
    args = parse_args()
    
    in_path = os.path.abspath(args.in_path)
    out_path = os.path.abspath(args.out_path)
    csv_path = os.path.abspath(args.csv_path)
    
    # Validate inputs
    if not os.path.exists(in_path):
        print(f"❌ Input file not found: {in_path}")
        sys.exit(1)
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        sys.exit(1)
    
    # Convert CSV to macro commands
    print("📝 Converting CSV to macro commands...")
    replace_commands = csv_to_macro_commands(csv_path)
    
    # Create macro
    print("🔧 Creating LibreOffice macro...")
    macro_content = create_macro(in_path, out_path, replace_commands)
    
    # Run macro
    print("🚀 Running macro with LibreOffice...")
    success = run_macro_with_libreoffice(macro_content)
    
    if success and os.path.exists(out_path):
        print(f"✅ Success! Output written to: {out_path}")
    else:
        print("❌ Failed to create output file")
        sys.exit(1)

if __name__ == "__main__":
    main()
