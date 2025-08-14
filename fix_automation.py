#!/usr/bin/env python3
"""
AUTOMATED solution that actually works.
This bypasses the LibreOffice Python wrapper issues by using a different approach.
"""
import subprocess
import sys
import os
import time
import tempfile
from pathlib import Path

def create_working_script(input_docx, csv_file, output_docx):
    """Create a Python script that will run with LibreOffice Python."""
    
    script_content = f'''
import sys
import os
import time

# Add LibreOffice Python paths
sys.path.insert(0, '/Applications/LibreOffice.app/Contents/Resources')
sys.path.insert(0, '/Applications/LibreOffice.app/Contents/Frameworks')

try:
    import uno
    from com.sun.star.beans import PropertyValue
    print("✅ UNO module imported successfully")
except Exception as e:
    print(f"❌ Failed to import UNO: {{e}}")
    sys.exit(1)

def mkprop(name, value):
    p = PropertyValue()
    p.Name = name
    p.Value = value
    return p

def main():
    print("🚀 Starting automated tracked edits...")
    
    # Connect to LibreOffice
    try:
        local_ctx = uno.getComponentContext()
        resolver = local_ctx.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local_ctx)
        ctx = resolver.resolve("uno:socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext")
        print("✅ Connected to LibreOffice")
    except Exception as e:
        print(f"❌ Connection failed: {{e}}")
        sys.exit(1)
    
    smgr = ctx.ServiceManager
    desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
    
    # Load document
    input_url = "{Path(input_docx).absolute().as_uri()}"
    load_props = (mkprop("Hidden", True),)
    
    try:
        doc = desktop.loadComponentFromURL(input_url, "_blank", 0, load_props)
        print("✅ Document loaded")
    except Exception as e:
        print(f"❌ Failed to load document: {{e}}")
        sys.exit(1)
    
    # Enable track changes
    doc.RecordChanges = True
    print("✅ Track changes enabled")
    
    # Apply replacements from CSV
    import csv
    with open("{csv_file}", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            find_text = row.get('Find', '').strip()
            replace_text = row.get('Replace', '').strip()
            
            if not find_text:
                continue
            
            print(f"🔄 Replacement {{i}}: '{{find_text}}' → '{{replace_text}}'")
            
            rd = doc.createReplaceDescriptor()
            rd.SearchString = find_text
            rd.ReplaceString = replace_text
            
            # Apply options
            match_case = row.get('MatchCase', '').strip().upper() == 'TRUE'
            whole_word = row.get('WholeWord', '').strip().upper() == 'TRUE'
            wildcards = row.get('Wildcards', '').strip().upper() == 'TRUE'
            
            rd.SearchCaseSensitive = match_case
            rd.SearchWords = whole_word
            
            if wildcards:
                rd.setPropertyValue("RegularExpressions", True)
            
            count = doc.replaceAll(rd)
            print(f"   ✅ Replaced {{count}} occurrences")
    
    # Save as DOCX
    output_url = "{Path(output_docx).absolute().as_uri()}"
    save_props = (mkprop("FilterName", "MS Word 2007 XML"),)
    
    try:
        doc.storeToURL(output_url, save_props)
        print(f"✅ Saved to: {output_docx}")
    except Exception as e:
        print(f"❌ Failed to save: {{e}}")
    
    doc.close(True)
    print("🎉 Automation completed successfully!")

if __name__ == "__main__":
    main()
'''
    
    return script_content

def run_automated_process(input_docx, csv_file, output_docx):
    """Run the automated process."""
    
    print("🔧 Setting up automated tracked edits...")
    
    # Create the script
    script_content = create_working_script(input_docx, csv_file, output_docx)
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(script_content)
        script_file = f.name
    
    try:
        # Start LibreOffice listener
        print("🚀 Starting LibreOffice listener...")
        lo_proc = subprocess.Popen([
            'soffice',
            '--headless',
            '--nologo', 
            '--nodefault',
            '--accept=socket,host=127.0.0.1,port=2002;urp;StarOffice.ServiceManager'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for LibreOffice to start
        time.sleep(3)
        print("✅ LibreOffice listener started")
        
        # Run the script with direct Python executable
        lo_python = "/Applications/LibreOffice.app/Contents/Frameworks/LibreOfficePython.framework/Versions/3.10/bin/python3.10"
        
        print("🐍 Running automation script...")
        print(f"Using: {lo_python}")
        
        # Set up environment
        env = os.environ.copy()
        env['PYTHONPATH'] = '/Applications/LibreOffice.app/Contents/Resources:/Applications/LibreOffice.app/Contents/Frameworks:' + env.get('PYTHONPATH', '')
        env['UNO_PATH'] = '/Applications/LibreOffice.app/Contents/MacOS'
        env['URE_BOOTSTRAP'] = 'vnd.sun.star.pathname:/Applications/LibreOffice.app/Contents/Resources/fundamentalrc'
        
        result = subprocess.run([lo_python, script_file], 
                              capture_output=True, text=True, 
                              timeout=60, env=env)
        
        print("📤 Script output:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ Script errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            if os.path.exists(output_docx):
                print(f"🎉 SUCCESS! Output created: {output_docx}")
                return True
            else:
                print("❌ Script completed but no output file found")
                return False
        else:
            print(f"❌ Script failed with return code: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Script timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Clean up
        try:
            lo_proc.terminate()
            lo_proc.wait(timeout=5)
        except:
            try:
                lo_proc.kill()
            except:
                pass
        
        try:
            os.unlink(script_file)
        except:
            pass

def main():
    print("🎯 AUTOMATED TRACKED EDITS - FIXED VERSION")
    print("=" * 50)
    
    # Default files
    input_docx = "docs/test_input.docx"
    csv_file = "edits/edits_sample.csv"
    output_docx = "build/automated_output.docx"
    
    # Check if files exist
    if not os.path.exists(input_docx):
        print(f"❌ Input file not found: {input_docx}")
        print("📝 Create it by copying content from docs/test_input_content.txt to Word")
        return
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    # Create output directory
    os.makedirs("build", exist_ok=True)
    
    print(f"📁 Input: {input_docx}")
    print(f"📁 Edits: {csv_file}")
    print(f"📁 Output: {output_docx}")
    
    success = run_automated_process(input_docx, csv_file, output_docx)
    
    if success:
        print("\n🎉 AUTOMATION WORKED!")
        print(f"✅ Open {output_docx} in Microsoft Word")
        print("✅ Go to Review → All Markup to see tracked changes")
        print("✅ Accept or reject changes as needed")
    else:
        print("\n❌ Automation failed. Check the output above for details.")

if __name__ == "__main__":
    main()
