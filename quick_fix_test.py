#!/usr/bin/env python3
"""
Quick test to verify LibreOffice is working and create a simple solution.
"""
import subprocess
import sys
import os

def test_system_python_with_pyuno():
    """Test if system Python can import uno."""
    print("🔍 Testing system Python with pyuno...")
    try:
        import uno
        print("✅ System Python has UNO support!")
        return sys.executable
    except ImportError:
        print("❌ System Python doesn't have UNO support")
        return None

def test_libreoffice_direct():
    """Test LibreOffice by running a headless instance."""
    print("🔍 Testing LibreOffice headless mode...")
    try:
        # Try to start LibreOffice headless (this should work if LO is properly installed)
        proc = subprocess.Popen([
            "soffice", 
            "--headless", 
            "--nologo", 
            "--nodefault",
            "--accept=socket,host=127.0.0.1,port=2003;urp;"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Give it a moment to start
        import time
        time.sleep(2)
        
        # Try to terminate it
        proc.terminate()
        proc.wait(timeout=5)
        
        print("✅ LibreOffice headless mode works!")
        return True
    except Exception as e:
        print(f"❌ LibreOffice headless test failed: {e}")
        return False

def install_pyuno_homebrew():
    """Try to install pyuno via homebrew."""
    print("📦 Attempting to install pyuno via homebrew...")
    try:
        # Check if brew is available
        subprocess.run(["brew", "--version"], check=True, capture_output=True)
        
        # Try to install python-uno
        result = subprocess.run(["brew", "install", "python-uno"], 
                              capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print("✅ python-uno installed successfully!")
            return True
        else:
            print(f"❌ brew install failed: {result.stderr}")
            return False
    except subprocess.CalledProcessError:
        print("❌ Homebrew not available")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Installation timed out")
        return False

def create_simple_test():
    """Create a simple test that doesn't require UNO import during setup."""
    test_content = '''#!/usr/bin/env python3
"""
Simple test that starts LibreOffice and tests basic functionality.
This script doesn't import UNO until LibreOffice is already running.
"""
import subprocess
import time
import sys
import os

def main():
    print("🚀 Starting LibreOffice test...")
    
    # Start LibreOffice headless
    print("📝 Starting LibreOffice headless listener...")
    proc = subprocess.Popen([
        "soffice", 
        "--headless", 
        "--nologo", 
        "--nodefault",
        "--accept=socket,host=127.0.0.1,port=2002;urp;StarOffice.ServiceManager"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait for it to start
    time.sleep(3)
    
    try:
        # Now try to import and connect
        print("🔌 Attempting to connect...")
        import uno
        from com.sun.star.beans import PropertyValue
        
        local_ctx = uno.getComponentContext()
        resolver = local_ctx.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local_ctx)
        ctx = resolver.resolve("uno:socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext")
        
        print("✅ Successfully connected to LibreOffice!")
        print("🎉 The system is working! You can run the main scripts.")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Try reinstalling LibreOffice or using system Python with pyuno")
    
    finally:
        # Clean up
        print("🧹 Cleaning up...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

if __name__ == "__main__":
    main()
'''
    
    with open("simple_test.py", "w") as f:
        f.write(test_content)
    
    os.chmod("simple_test.py", 0o755)
    print("✅ Created simple_test.py")

def main():
    print("🔧 Quick Fix for LibreOffice Python Issues")
    print("=" * 45)
    
    # Test 1: System Python with UNO
    system_python = test_system_python_with_pyuno()
    if system_python:
        print(f"\n🎉 Great! Use system Python: {system_python}")
        print("You can run the scripts directly with:")
        print(f"  {system_python} scripts/apply_tracked_edits_libre.py --help")
        return
    
    # Test 2: LibreOffice direct
    if test_libreoffice_direct():
        print("\n📝 LibreOffice is working, but Python import issue exists.")
        print("Creating a simple test script...")
        create_simple_test()
        print("\nRun: python3 simple_test.py")
        print("If that works, the main script should work too with LibreOffice Python")
        return
    
    # Test 3: Try to install pyuno
    if install_pyuno_homebrew():
        print("\n🔄 Retesting after pyuno installation...")
        if test_system_python_with_pyuno():
            print("✅ Success! Now you can use system Python")
            return
    
    print("\n💡 Alternative Solutions:")
    print("1. Use Docker with LibreOffice pre-installed")
    print("2. Use the GitHub Actions workflow (it works there)")
    print("3. Reinstall LibreOffice from scratch:")
    print("   brew uninstall --cask libreoffice")
    print("   brew install --cask libreoffice")

if __name__ == "__main__":
    main()
