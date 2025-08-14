#!/usr/bin/env python3
"""
Test script for the automated tracked edits system.
This script will help you verify that everything is working correctly.
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

def get_libreoffice_python():
    """Get the path to LibreOffice's bundled Python based on the platform."""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        path = "/Applications/LibreOffice.app/Contents/Resources/python"
    elif system == "Linux":
        path = "/usr/lib/libreoffice/program/python"
    elif system == "Windows":
        path = "C:\\Program Files\\LibreOffice\\program\\python.exe"
    else:
        print(f"Unsupported platform: {system}")
        return None
    
    if os.path.exists(path):
        return path
    else:
        print(f"LibreOffice Python not found at: {path}")
        return None

def test_libreoffice_installation():
    """Test if LibreOffice is properly installed."""
    print("🔍 Testing LibreOffice installation...")
    
    # Test soffice command
    try:
        result = subprocess.run(["soffice", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ LibreOffice found: {result.stdout.strip()}")
        else:
            print("❌ LibreOffice 'soffice' command failed")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ LibreOffice 'soffice' command not found")
        return False
    
    # Test LibreOffice Python and UNO
    lo_python = get_libreoffice_python()
    if not lo_python:
        return False
    
    try:
        result = subprocess.run([lo_python, "-c", "import uno; print('UNO module available')"],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ LibreOffice Python with UNO: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ UNO import failed: {result.stderr}")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f"❌ LibreOffice Python not executable: {lo_python}")
        return False

def test_converter_script():
    """Test the find_replace_list_to_csv.py script."""
    print("\n🔍 Testing converter script...")
    
    lo_python = get_libreoffice_python()
    if not lo_python:
        return False
    
    script_path = "scripts/find_replace_list_to_csv.py"
    input_file = "edits/edits_example.txt"
    output_file = "edits/test_converted.csv"
    
    try:
        result = subprocess.run([lo_python, script_path, input_file, output_file],
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ Converter script: {result.stdout.strip()}")
            # Verify output file exists
            if os.path.exists(output_file):
                print(f"✅ Output file created: {output_file}")
                return True
            else:
                print(f"❌ Output file not created: {output_file}")
                return False
        else:
            print(f"❌ Converter script failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Converter script timed out")
        return False

def check_requirements():
    """Check if all required files and directories exist."""
    print("\n🔍 Checking project structure...")
    
    required_files = [
        "scripts/apply_tracked_edits_libre.py",
        "scripts/find_replace_list_to_csv.py",
        "edits/edits_sample.csv",
        "edits/edits_example.txt",
        ".github/workflows/redline-docx.yml"
    ]
    
    required_dirs = [
        "scripts/",
        "edits/", 
        "docs/",
        "build/",
        ".github/workflows/"
    ]
    
    all_good = True
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
            all_good = False
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path}")
        else:
            print(f"❌ Missing directory: {dir_path}")
            all_good = False
    
    return all_good

def provide_next_steps():
    """Provide instructions for next steps."""
    print("\n📋 Next Steps:")
    print("1. Create a test DOCX file:")
    print("   - Open docs/test_input_content.txt")
    print("   - Copy the content to a new Word document")
    print("   - Save as 'docs/test_input.docx'")
    print()
    print("2. Run the main script:")
    lo_python = get_libreoffice_python()
    if lo_python:
        print(f"   {lo_python} scripts/apply_tracked_edits_libre.py \\")
        print("     --in docs/test_input.docx \\")
        print("     --csv edits/edits_sample.csv \\")
        print("     --out build/test_output.docx \\")
        print("     --launch")
    print()
    print("3. Open build/test_output.docx in Microsoft Word")
    print("4. Go to Review → All Markup to see tracked changes")

def main():
    print("🚀 Testing Automated Tracked Edits System")
    print("=" * 50)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    if check_requirements():
        tests_passed += 1
    
    if test_libreoffice_installation():
        tests_passed += 1
    
    if test_converter_script():
        tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! System is ready to use.")
        provide_next_steps()
    else:
        print("⚠️  Some tests failed. Please check the installation.")
        print("\nCommon issues:")
        print("- LibreOffice not installed or not in PATH")
        print("- Using system Python instead of LibreOffice Python")
        print("- Missing required files or directories")

if __name__ == "__main__":
    main()
