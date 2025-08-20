#!/bin/bash

# Fix Git Sync Issues in Production
echo "🔧 Git Sync Fix Tool for Production"
echo "=" * 50

# Check current git status
echo "📊 Current git status:"
git status

echo ""
echo "🔍 Checking remote commits..."
git fetch origin

echo ""
echo "📈 Commits ahead/behind:"
git status -uno

echo ""
echo "🔄 Attempting to sync with remote..."

# Option 1: Try standard pull
echo "Trying: git pull origin main"
if git pull origin main; then
    echo "✅ Standard pull successful"
    echo "🚀 You can now run your automation again"
    exit 0
fi

echo ""
echo "⚠️  Standard pull failed, trying rebase..."

# Option 2: Try pull with rebase
echo "Trying: git pull --rebase origin main"
if git pull --rebase origin main; then
    echo "✅ Rebase pull successful"
    echo "🚀 You can now run your automation again"
    exit 0
fi

echo ""
echo "❌ Both standard pull and rebase failed"
echo ""
echo "🆘 Manual intervention required:"
echo "1. Check what files are conflicting:"
echo "   git status"
echo ""
echo "2. If you want to keep all remote changes and discard local:"
echo "   git reset --hard origin/main"
echo ""
echo "3. If you want to keep local changes:"
echo "   - Resolve conflicts manually"
echo "   - git add ."
echo "   - git commit -m 'Resolve merge conflicts'"
echo "   - git push origin main"
echo ""
echo "4. Nuclear option (reset everything to remote):"
echo "   git fetch origin"
echo "   git reset --hard origin/main"
echo "   git clean -fd"

echo ""
echo "💡 Common causes in production:"
echo "- Multiple automation processes running simultaneously"
echo "- Manual commits made directly to GitHub"
echo "- Automated workflows committing changes"
echo "- Repository being modified by other systems"
