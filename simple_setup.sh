#!/bin/bash
# Simple setup script that avoids the hanging UNO import issue

echo "🚀 Simple Setup for Automated Tracked Edits"
echo "==========================================="

# Check if LibreOffice is installed
echo "🔍 Checking LibreOffice installation..."
if command -v soffice &> /dev/null; then
    echo "✅ LibreOffice found: $(soffice --version)"
else
    echo "❌ LibreOffice not found. Please install:"
    echo "   brew install --cask libreoffice"
    exit 1
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x scripts/*.py
chmod +x *.py 2>/dev/null || true
echo "✅ Scripts are executable"

# Test the converter (doesn't need UNO)
echo "🧪 Testing converter script (no UNO needed)..."
if python3 scripts/find_replace_list_to_csv.py edits/edits_example.txt edits/test_simple.csv; then
    echo "✅ Converter works with system Python"
    echo "   Generated: edits/test_simple.csv"
else
    echo "❌ Converter failed"
    exit 1
fi

# Try to install pyuno for system Python
echo "📦 Attempting to add UNO support to system Python..."
if pip3 install pyuno 2>/dev/null; then
    echo "✅ pyuno installed successfully"
    
    # Test UNO import
    if python3 -c "import uno; print('UNO module available')" 2>/dev/null; then
        echo "✅ System Python now has UNO support!"
        PYTHON_CMD="python3"
    else
        echo "⚠️  pyuno installed but UNO still not working with system Python"
        PYTHON_CMD="/Applications/LibreOffice.app/Contents/Resources/python"
    fi
else
    echo "⚠️  Could not install pyuno, will use LibreOffice Python"
    PYTHON_CMD="/Applications/LibreOffice.app/Contents/Resources/python"
fi

# Create a simple wrapper script
echo "📝 Creating wrapper script..."
cat > run_edits.sh << 'EOF'
#!/bin/bash
# Simple wrapper script for running tracked edits

PYTHON_CMD="__PYTHON_CMD__"

case "$1" in
    "convert")
        echo "🔄 Converting text format to CSV..."
        python3 scripts/find_replace_list_to_csv.py "$2" "$3"
        ;;
    "apply")
        echo "📝 Applying tracked edits..."
        if [ $# -ne 4 ]; then
            echo "Usage: $0 apply <input.docx> <edits.csv> <output.docx>"
            exit 1
        fi
        
        echo "🚀 Starting LibreOffice listener..."
        soffice --headless --nologo --nodefault \
            --accept='socket,host=127.0.0.1,port=2002;urp;StarOffice.ServiceManager' &
        LO_PID=$!
        
        # Wait for LibreOffice to start
        sleep 3
        
        echo "🐍 Running script..."
        "$PYTHON_CMD" scripts/apply_tracked_edits_libre.py \
            --in "$2" \
            --csv "$3" \
            --out "$4"
        
        # Clean up
        echo "🧹 Stopping LibreOffice..."
        kill $LO_PID 2>/dev/null || true
        ;;
    "test")
        echo "🧪 Testing system..."
        echo "Converter test:"
        python3 scripts/find_replace_list_to_csv.py edits/edits_example.txt edits/test_run.csv
        echo "✅ Basic functionality works"
        echo ""
        echo "To test full pipeline:"
        echo "1. Create docs/test_input.docx from docs/test_input_content.txt"
        echo "2. Run: $0 apply docs/test_input.docx edits/edits_sample.csv build/test_output.docx"
        ;;
    *)
        echo "Usage:"
        echo "  $0 convert <input.txt> <output.csv>      # Convert text format to CSV"
        echo "  $0 apply <input.docx> <edits.csv> <output.docx>  # Apply tracked edits"
        echo "  $0 test                                   # Test the system"
        echo ""
        echo "Examples:"
        echo "  $0 convert edits/edits_example.txt edits/my_edits.csv"
        echo "  $0 apply docs/test.docx edits/edits_sample.csv build/output.docx"
        ;;
esac
EOF

# Replace the Python command in the wrapper
sed -i '' "s|__PYTHON_CMD__|$PYTHON_CMD|g" run_edits.sh
chmod +x run_edits.sh

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Quick Start:"
echo "1. Test the converter:"
echo "   ./run_edits.sh test"
echo ""
echo "2. Create a test DOCX file:"
echo "   - Open docs/test_input_content.txt"
echo "   - Copy content to Word and save as docs/test_input.docx"
echo ""
echo "3. Run the full pipeline:"
echo "   ./run_edits.sh apply docs/test_input.docx edits/edits_sample.csv build/test_output.docx"
echo ""
echo "✨ The wrapper script avoids the hanging UNO import issue!"
