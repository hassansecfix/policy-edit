#!/usr/bin/env python3
"""
Simple approach using LibreOffice command line without UNO Python.
This creates an ODT with tracked changes, then converts to DOCX.
"""
import argparse
import csv
import os
import sys
import subprocess
import tempfile
import time
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser(description="Apply tracked edits using LibreOffice command line.")
    p.add_argument("--in", dest="in_path", required=True, help="Input .docx")
    p.add_argument("--csv", dest="csv_path", required=True, help="CSV with Find/Replace rules")
    p.add_argument("--out", dest="out_path", required=True, help="Output .docx")
    return p.parse_args()

def create_libreoffice_basic_macro(csv_path, input_path, output_path):
    """Create a LibreOffice Basic macro to handle find/replace with track changes."""
    
    # Read CSV and create find/replace commands
    commands = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            find_text = row.get('Find', '').strip()
            replace_text = row.get('Replace', '').strip()
            
            if not find_text:
                continue
            
            # Escape quotes for Basic string literals
            find_escaped = find_text.replace('"', '""')
            replace_escaped = replace_text.replace('"', '""')
            
            commands.append(f'''
    ' Replace {i+1}: {find_text} -> {replace_text}
    oReplace = oDoc.createReplaceDescriptor()
    oReplace.SearchString = "{find_escaped}"
    oReplace.ReplaceString = "{replace_escaped}"
    nCount = oDoc.replaceAll(oReplace)
    Print "Replaced '{find_escaped}' with '{replace_escaped}': " & nCount & " occurrences"''')
    
    # Create the complete macro
    macro = f'''
REM ***** BASIC *****

Sub ApplyTrackedEdits
    Dim oDoc As Object
    Dim oReplace As Object
    Dim nCount As Long
    
    On Error Resume Next
    
    ' Load the document
    Dim sInputURL As String
    sInputURL = "{Path(input_path).absolute().as_uri()}"
    
    Dim LoadProps(0) As New com.sun.star.beans.PropertyValue
    LoadProps(0).Name = "Hidden"
    LoadProps(0).Value = True
    
    oDoc = StarDesktop.loadComponentFromURL(sInputURL, "_blank", 0, LoadProps())
    
    If IsNull(oDoc) Then
        Print "Error: Could not load document"
        Exit Sub
    End If
    
    ' Enable track changes
    oDoc.RecordChanges = True
    Print "Track changes enabled"
    
    ' Apply all find/replace operations
{"".join(commands)}
    
    ' Save as DOCX
    Dim sOutputURL As String
    sOutputURL = "{Path(output_path).absolute().as_uri()}"
    
    Dim SaveProps(0) As New com.sun.star.beans.PropertyValue
    SaveProps(0).Name = "FilterName"
    SaveProps(0).Value = "MS Word 2007 XML"
    
    oDoc.storeToURL(sOutputURL, SaveProps())
    Print "Document saved to: " & sOutputURL
    
    ' Close document
    oDoc.close(True)
    
    Print "Process completed successfully"
End Sub

Sub Main
    ApplyTrackedEdits
End Sub
'''
    
    return macro

def run_with_libreoffice_macro(input_path, csv_path, output_path):
    """Run the process using LibreOffice Basic macro."""
    
    # Create macro content
    macro_content = create_libreoffice_basic_macro(csv_path, input_path, output_path)
    
    # Create temporary macro file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.bas', delete=False, encoding='utf-8') as f:
        f.write(macro_content)
        macro_file = f.name
    
    try:
        print(f"📝 Created macro: {macro_file}")
        print("🚀 Running LibreOffice with macro...")
        
        # Run LibreOffice with the macro
        cmd = [
            'soffice',
            '--headless',
            '--invisible',
            '--nodefault',
            '--nolockcheck',
            '--nologo',
            '--norestore',
            f'macro:///{macro_file}$ApplyTrackedEdits'
        ]
        
        # Alternative approach: use --calc to run macro
        cmd_alt = [
            'soffice',
            '--headless',
            '--invisible',
            '--calc',
            f'--macro-file={macro_file}',
            '--macro=ApplyTrackedEdits'
        ]
        
        print(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ LibreOffice macro completed")
            if os.path.exists(output_path):
                print(f"✅ Output file created: {output_path}")
                return True
            else:
                print("❌ Output file not created")
                return False
        else:
            print(f"❌ LibreOffice macro failed:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ LibreOffice macro timed out")
        return False
    except Exception as e:
        print(f"❌ Error running LibreOffice macro: {e}")
        return False
    finally:
        # Clean up
        try:
            os.unlink(macro_file)
            print(f"🧹 Cleaned up macro file")
        except:
            pass

def fallback_manual_process(input_path, csv_path, output_path):
    """Fallback: Create instructions for manual processing."""
    
    print("\n🔄 Creating manual processing instructions...")
    
    instructions_file = "manual_processing_instructions.txt"
    
    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write("MANUAL PROCESSING INSTRUCTIONS\n")
        f.write("="*50 + "\n\n")
        f.write(f"Input file: {input_path}\n")
        f.write(f"Output file: {output_path}\n\n")
        f.write("Steps:\n")
        f.write("1. Open the input file in LibreOffice Writer\n")
        f.write("2. Enable Track Changes: Edit → Track Changes → Record\n")
        f.write("3. Apply these find/replace operations (Edit → Find & Replace):\n\n")
        
        with open(csv_path, 'r', encoding='utf-8') as csv_f:
            reader = csv.DictReader(csv_f)
            for i, row in enumerate(reader, 1):
                find_text = row.get('Find', '').strip()
                replace_text = row.get('Replace', '').strip()
                if find_text:
                    f.write(f"   {i}. Find: '{find_text}' → Replace: '{replace_text}'\n")
        
        f.write("\n4. Save as DOCX format\n")
        f.write("5. All changes will be tracked and visible in Microsoft Word\n")
    
    print(f"📋 Instructions saved to: {instructions_file}")
    return instructions_file

def main():
    args = parse_args()
    
    input_path = os.path.abspath(args.in_path)
    output_path = os.path.abspath(args.out_path)
    csv_path = os.path.abspath(args.csv_path)
    
    # Validate inputs
    if not os.path.exists(input_path):
        print(f"❌ Input file not found: {input_path}")
        sys.exit(1)
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        sys.exit(1)
    
    # Try the macro approach
    print("🔧 Attempting LibreOffice macro approach...")
    success = run_with_libreoffice_macro(input_path, csv_path, output_path)
    
    if not success:
        print("\n⚠️  Macro approach failed. Creating manual instructions...")
        instructions_file = fallback_manual_process(input_path, csv_path, output_path)
        print(f"\n📖 Please follow the instructions in: {instructions_file}")
        print("\nAlternatively, you can:")
        print("1. Use the GitHub Actions workflow (it works in Linux environment)")
        print("2. Run this on a Linux system where LibreOffice Python works better")
    else:
        print(f"\n🎉 Success! Tracked changes applied to: {output_path}")
        print("💡 Open the file in Microsoft Word and go to Review → All Markup to see changes")

if __name__ == "__main__":
    main()
