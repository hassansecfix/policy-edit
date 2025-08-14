#!/usr/bin/env python3
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
