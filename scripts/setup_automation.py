#!/usr/bin/env python3
"""
Setup Script for AI Policy Automation

This script helps set up the environment and dependencies for the complete automation flow.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is adequate."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def install_python_packages():
    """Install required Python packages."""
    packages = [
        "anthropic",
        "requests", 
        "pandas",
        "openpyxl",
        "python-docx"
    ]
    
    print("📦 Installing Python packages...")
    for package in packages:
        # Try normal install first
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True, check=True)
            print(f"✅ {package}")
            continue
        except subprocess.CalledProcessError:
            pass
        
        # Try with --break-system-packages (for macOS externally-managed Python)
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "--break-system-packages", package
            ], capture_output=True, text=True, check=True)
            print(f"✅ {package} (with --break-system-packages)")
            continue
        except subprocess.CalledProcessError:
            pass
        
        # Try with --user flag
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "--user", package
            ], capture_output=True, text=True, check=True)
            print(f"✅ {package} (with --user)")
            continue
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package} with all methods")
            print(f"   Error: {e}")
            print(f"💡 Manual install: pip3 install --break-system-packages {package}")
            return False
    return True

def check_git_repository():
    """Check if we're in a git repository."""
    try:
        result = subprocess.run(['git', 'status'], capture_output=True, text=True, check=True)
        print("✅ Git repository detected")
        return True
    except subprocess.CalledProcessError:
        print("❌ Not in a git repository")
        print("💡 Initialize with: git init && git remote add origin YOUR_REPO_URL")
        return False

def setup_environment_file():
    """Create environment setup file."""
    env_file = Path("env_setup.example")
    if env_file.exists():
        print("✅ Environment template exists")
        print(f"💡 Copy and edit: cp {env_file} .env")
        return True
    else:
        print("❌ Environment template missing")
        return False

def check_files_exist():
    """Check if required files exist."""
    required_files = [
        "data/updated_policy_instructions_v4.0.md",
        "scripts/ai_policy_processor.py",
        "scripts/complete_automation.py",
        "scripts/xlsx_to_csv_converter.py",
        ".github/workflows/redline-docx.yml"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def main():
    print("🚀 AI Policy Automation Setup")
    print("=" * 40)
    
    checks = [
        ("Python Version", check_python_version()),
        ("Python Packages", install_python_packages()),
        ("Git Repository", check_git_repository()),
        ("Required Files", check_files_exist()),
        ("Environment Setup", setup_environment_file())
    ]
    
    print("\n📋 Setup Summary:")
    print("=" * 40)
    
    all_passed = True
    for name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 Setup Complete!")
        print("\n🔑 Next Steps:")
        print("1. Get Claude API key: https://console.anthropic.com/")
        print("2. Copy environment file: cp env_setup.example .env")
        print("3. Edit .env with your API key")
        print("4. Run automation: python3 scripts/complete_automation.py --help")
        print("\n🚀 Ready for fully automated policy processing!")
    else:
        print("\n❌ Setup incomplete. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
