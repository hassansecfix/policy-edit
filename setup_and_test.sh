#!/bin/bash
# Setup and test script for Automated Tracked Edits system

echo "🚀 Setting up Automated Tracked Edits for DOCX"
echo "=============================================="

# Detect platform
case "$(uname -s)" in
    Darwin*)    PLATFORM="macOS";;
    Linux*)     PLATFORM="Linux";;
    CYGWIN*|MINGW*|MSYS*) PLATFORM="Windows";;
    *)          PLATFORM="Unknown";;
esac

echo "Platform detected: $PLATFORM"

# Set LibreOffice Python path based on platform
case $PLATFORM in
    "macOS")
        LO_PYTHON="/Applications/LibreOffice.app/Contents/Resources/python"
        ;;
    "Linux")
        LO_PYTHON="/usr/lib/libreoffice/program/python"
        ;;
    "Windows")
        LO_PYTHON="C:/Program Files/LibreOffice/program/python.exe"
        ;;
    *)
        echo "❌ Unsupported platform"
        exit 1
        ;;
esac

echo "LibreOffice Python path: $LO_PYTHON"

# Check if LibreOffice is installed
echo ""
echo "🔍 Checking LibreOffice installation..."
if command -v soffice &> /dev/null; then
    echo "✅ LibreOffice found: $(soffice --version)"
else
    echo "❌ LibreOffice not found. Please install LibreOffice:"
    case $PLATFORM in
        "macOS")
            echo "   brew install --cask libreoffice"
            echo "   or download from https://www.libreoffice.org/download/download/"
            ;;
        "Linux")
            echo "   sudo apt-get install libreoffice  # Ubuntu/Debian"
            echo "   sudo yum install libreoffice      # RHEL/CentOS"
            echo "   or download from https://www.libreoffice.org/download/download/"
            ;;
        "Windows")
            echo "   Download from https://www.libreoffice.org/download/download/"
            ;;
    esac
    exit 1
fi

# Check if LibreOffice Python exists
echo ""
echo "🔍 Checking LibreOffice Python..."
if [ -x "$LO_PYTHON" ]; then
    echo "✅ LibreOffice Python found: $LO_PYTHON"
else
    echo "❌ LibreOffice Python not found at: $LO_PYTHON"
    echo "   Please verify LibreOffice installation"
    exit 1
fi

# Test UNO module
echo ""
echo "🔍 Testing UNO module..."
if "$LO_PYTHON" -c "import uno; print('UNO module available')" 2>/dev/null; then
    echo "✅ UNO module is available"
else
    echo "❌ UNO module not available"
    echo "   This usually means LibreOffice Python is not properly configured"
    exit 1
fi

# Make scripts executable
echo ""
echo "🔧 Making scripts executable..."
chmod +x scripts/*.py
chmod +x test_system.py
echo "✅ Scripts are now executable"

# Test the converter
echo ""
echo "🧪 Testing converter script..."
if "$LO_PYTHON" scripts/find_replace_list_to_csv.py edits/edits_example.txt edits/test_converted.csv; then
    echo "✅ Converter script works"
    echo "   Generated: edits/test_converted.csv"
else
    echo "❌ Converter script failed"
    exit 1
fi

# Run comprehensive test
echo ""
echo "🧪 Running comprehensive test suite..."
"$LO_PYTHON" test_system.py

echo ""
echo "📋 Quick Start Instructions:"
echo "============================"
echo ""
echo "1. Create a test DOCX file:"
echo "   - Open docs/test_input_content.txt"
echo "   - Copy content to a new Word document"  
echo "   - Save as 'docs/test_input.docx'"
echo ""
echo "2. Run the pipeline:"
echo "   $LO_PYTHON scripts/apply_tracked_edits_libre.py \\"
echo "     --in docs/test_input.docx \\"
echo "     --csv edits/edits_sample.csv \\"
echo "     --out build/test_output.docx \\"
echo "     --launch"
echo ""
echo "3. Open build/test_output.docx in Microsoft Word"
echo "4. Go to Review → All Markup to see tracked changes"
echo ""
echo "🎉 Setup complete! System is ready to use."
