#!/usr/bin/env python3
"""
Create tracked changes specifically for LibreOffice Writer.
This opens LibreOffice and guides you through creating tracked changes.
"""
import subprocess
import csv
import os
import time

def create_libreoffice_instructions(csv_file):
    """Create step-by-step instructions for LibreOffice."""
    
    print("\n📋 LIBREOFFICE TRACKED CHANGES INSTRUCTIONS")
    print("=" * 50)
    
    print("\n1. LibreOffice should now be open with your document")
    print("2. In LibreOffice Writer, follow these steps:")
    print()
    print("   🔴 ENABLE TRACKING:")
    print("   • Go to Edit → Track Changes → Record")
    print("   • You should see a red recording icon appear")
    print()
    print("   🔍 APPLY CHANGES:")
    print("   • Go to Edit → Find & Replace (Ctrl+H)")
    print("   • Apply each replacement below:")
    print()
    
    # Read CSV and show replacements
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            find_text = row.get('Find', '').strip()
            replace_text = row.get('Replace', '').strip()
            if find_text:
                print(f"   {i}. Find: '{find_text}'")
                print(f"      Replace: '{replace_text}'")
                print(f"      Click 'Replace All'")
                print()
    
    print("   💾 SAVE:")
    print("   • File → Save As → 'build/libreoffice_tracked_changes.docx'")
    print("   • Make sure to save as DOCX format")
    print()
    print("   👀 VIEW CHANGES:")
    print("   • Go to Edit → Track Changes → Manage")
    print("   • You'll see all changes with Accept/Reject buttons")
    print()
    
    return True

def check_for_changes(output_file):
    """Check if the output file was created."""
    if os.path.exists(output_file):
        print(f"✅ SUCCESS! File created: {output_file}")
        print("\n📖 To view tracked changes:")
        print("1. Open the file in LibreOffice Writer")
        print("2. Go to Edit → Track Changes → Manage")
        print("3. Accept or reject individual changes")
        print("4. Or use 'Accept All' / 'Reject All' buttons")
        return True
    else:
        print("⚠️ File not created yet. Follow the instructions above.")
        return False

def main():
    print("🎯 LIBREOFFICE TRACKED CHANGES CREATOR")
    print("=" * 45)
    
    input_docx = "docs/test_input.docx"
    csv_file = "edits/edits_sample.csv"
    output_docx = "build/libreoffice_tracked_changes.docx"
    
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
    
    # Open LibreOffice with the document
    print("\n🚀 Opening LibreOffice with your document...")
    
    try:
        # Open LibreOffice with the document (not headless)
        subprocess.Popen(['soffice', input_docx])
        time.sleep(2)  # Give it time to open
        
        # Show instructions
        create_libreoffice_instructions(csv_file)
        
        # Wait for user to complete
        input("\n⏸️  Press Enter when you've completed all the steps above...")
        
        # Check if file was created
        check_for_changes(output_docx)
        
    except Exception as e:
        print(f"❌ Error opening LibreOffice: {e}")
        print("\n📋 Manual steps:")
        print("1. Open docs/test_input.docx in LibreOffice Writer")
        print("2. Follow the instructions above")

if __name__ == "__main__":
    main()
