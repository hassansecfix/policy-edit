#!/usr/bin/env python3
"""
Create DOCX with TRUE tracked changes that show up in Word Review mode.
This version uses LibreOffice's actual tracked changes feature.
"""
import subprocess
import csv
import os
import tempfile
import time
from pathlib import Path

def create_tracked_changes_script(input_docx, csv_file, output_docx):
    """Create a script that will run with LibreOffice and add tracked changes."""
    
    # Read the CSV to get replacements
    replacements = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            find_text = row.get('Find', '').strip()
            replace_text = row.get('Replace', '').strip()
            if find_text:
                replacements.append((find_text, replace_text))
    
    # Create LibreOffice Basic macro
    macro_content = f'''
Sub CreateTrackedChanges

    ' Open the document
    Dim sInputURL As String
    sInputURL = "{Path(input_docx).absolute().as_uri()}"
    
    Dim LoadProps(0) As New com.sun.star.beans.PropertyValue
    LoadProps(0).Name = "Hidden"
    LoadProps(0).Value = False
    
    Dim oDoc As Object
    oDoc = StarDesktop.loadComponentFromURL(sInputURL, "_blank", 0, LoadProps())
    
    If IsNull(oDoc) Then
        Print "Failed to load document"
        Exit Sub
    End If
    
    ' Enable Track Changes
    oDoc.RecordChanges = True
    Print "Track Changes enabled"
    
    ' Apply each replacement with tracking
'''
    
    # Add replacement code for each item
    for i, (find_text, replace_text) in enumerate(replacements):
        find_escaped = find_text.replace('"', '""')
        replace_escaped = replace_text.replace('"', '""')
        
        macro_content += f'''
    ' Replacement {i+1}: {find_text} -> {replace_text}
    Dim oReplace{i} As Object
    oReplace{i} = oDoc.createReplaceDescriptor()
    oReplace{i}.SearchString = "{find_escaped}"
    oReplace{i}.ReplaceString = "{replace_escaped}"
    
    Dim nCount{i} As Long
    nCount{i} = oDoc.replaceAll(oReplace{i})
    Print "Replaced '{find_escaped}' with '{replace_escaped}': " & nCount{i} & " times"
'''
    
    # Complete the macro
    macro_content += f'''
    
    ' Save as DOCX with tracked changes
    Dim sOutputURL As String
    sOutputURL = "{Path(output_docx).absolute().as_uri()}"
    
    Dim SaveProps(0) As New com.sun.star.beans.PropertyValue
    SaveProps(0).Name = "FilterName"
    SaveProps(0).Value = "MS Word 2007 XML"
    
    oDoc.storeToURL(sOutputURL, SaveProps())
    Print "Document saved with tracked changes to: " & sOutputURL
    
    ' Close document
    oDoc.close(True)
    Print "Tracked changes creation completed!"
    
End Sub
'''
    
    return macro_content

def run_libreoffice_macro(macro_content):
    """Run the LibreOffice macro to create tracked changes."""
    
    # Write macro to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.bas', delete=False, encoding='utf-8') as f:
        f.write(macro_content)
        macro_file = f.name
    
    try:
        print("🚀 Running LibreOffice with tracked changes macro...")
        
        # Create a temporary LibreOffice macro directory
        import shutil
        temp_dir = tempfile.mkdtemp()
        macro_dir = os.path.join(temp_dir, 'Standard')
        os.makedirs(macro_dir)
        
        # Copy macro to Standard module
        shutil.copy2(macro_file, os.path.join(macro_dir, 'Module1.bas'))
        
        # Run LibreOffice with the macro
        result = subprocess.run([
            'soffice',
            '--headless',
            '--invisible',
            '--nodefault',
            '--nolockcheck',
            '--nologo',
            '--norestore',
            f'--macro-file={macro_file}',
            '--macro=CreateTrackedChanges'
        ], capture_output=True, text=True, timeout=120)
        
        print(f"LibreOffice output: {result.stdout}")
        if result.stderr:
            print(f"LibreOffice errors: {result.stderr}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ LibreOffice macro timed out")
        return False
    except Exception as e:
        print(f"❌ Error running macro: {e}")
        return False
    finally:
        # Clean up
        try:
            os.unlink(macro_file)
        except:
            pass

def run_simple_approach(input_docx, csv_file, output_docx):
    """Simple approach using LibreOffice command line with a script."""
    
    print("📝 Using simple LibreOffice approach...")
    
    # Create a temporary script that opens LibreOffice with the document
    script_content = f'''#!/bin/bash
# Temporary script to open LibreOffice and apply tracked changes

echo "Opening LibreOffice with document..."
soffice "{input_docx}" &
LOPID=$!

echo "Please follow these steps in LibreOffice:"
echo "1. Go to Edit → Track Changes → Record"
echo "2. Go to Edit → Find & Replace (Ctrl+H)"
'''
    
    # Add instructions for each replacement
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 3):
            find_text = row.get('Find', '').strip()
            replace_text = row.get('Replace', '').strip()
            if find_text:
                script_content += f'echo "{i}. Find: \\"{find_text}\\" → Replace: \\"{replace_text}\\" → Click Replace All"\n'
    
    script_content += f'''
echo "4. Save as: {output_docx}"
echo "5. Close LibreOffice"

read -p "Press Enter when you're done..."
kill $LOPID 2>/dev/null || true
'''
    
    # Write and run the script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write(script_content)
        script_file = f.name
    
    os.chmod(script_file, 0o755)
    
    try:
        subprocess.run(['bash', script_file])
        return os.path.exists(output_docx)
    finally:
        try:
            os.unlink(script_file)
        except:
            pass

def main():
    print("🎯 CREATING TRUE TRACKED CHANGES")
    print("=" * 40)
    
    input_docx = "docs/test_input.docx"
    csv_file = "edits/edits_sample.csv"
    output_docx = "build/tracked_changes_output.docx"
    
    if not os.path.exists(input_docx):
        print(f"❌ Input file not found: {input_docx}")
        return
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    os.makedirs("build", exist_ok=True)
    
    print(f"📁 Input: {input_docx}")
    print(f"📁 Edits: {csv_file}")
    print(f"📁 Output: {output_docx}")
    print()
    
    # Show what changes will be made
    print("📋 Tracked changes to be created:")
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            find_text = row.get('Find', '').strip()
            replace_text = row.get('Replace', '').strip()
            if find_text:
                print(f"   {i}. '{find_text}' → '{replace_text}' (will be a tracked change)")
    print()
    
    # Try to create the macro
    print("🔧 Creating LibreOffice macro for tracked changes...")
    macro_content = create_tracked_changes_script(input_docx, csv_file, output_docx)
    
    if run_libreoffice_macro(macro_content):
        print("✅ SUCCESS! Tracked changes created")
        print(f"📁 Output: {output_docx}")
        print("\n📖 How to view tracked changes:")
        print("1. Open the file in Microsoft Word")
        print("2. Go to Review → Track Changes → All Markup")
        print("3. You'll see all changes as accept/reject suggestions!")
    else:
        print("⚠️ Macro approach failed. Using guided approach...")
        print("This will open LibreOffice and guide you through the process.")
        
        if run_simple_approach(input_docx, csv_file, output_docx):
            print("✅ Guided approach completed")
        else:
            print("❌ Manual guidance needed")
            print("\n📋 Manual steps:")
            print("1. Open docs/test_input.docx in LibreOffice")
            print("2. Edit → Track Changes → Record")
            print("3. Edit → Find & Replace, apply all replacements")
            print("4. Save as build/tracked_changes_output.docx")

if __name__ == "__main__":
    main()
