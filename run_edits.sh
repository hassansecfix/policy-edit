#!/bin/bash
# Simple wrapper script for running tracked edits

PYTHON_CMD="/Applications/LibreOffice.app/Contents/Resources/python"

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
