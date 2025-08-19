#!/bin/bash
# Switch back to the original workflow

echo "🔄 Switching back to original GitHub Actions workflow..."

if [ -f ".github/workflows/redline-docx-original.yml" ]; then
    cp .github/workflows/redline-docx-original.yml .github/workflows/redline-docx.yml
    echo "✅ Restored original workflow"
    echo "⚠️  Note: This will be slower but includes all features"
else
    echo "❌ No backup found - original workflow not available"
    exit 1
fi