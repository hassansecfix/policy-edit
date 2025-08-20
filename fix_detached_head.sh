#!/bin/bash

# Fix Detached HEAD State on Render
echo "🔧 Detached HEAD Fix Tool"
echo "=" * 50

# Check current git status
echo "📊 Current git status:"
git status

# Check if we're in detached HEAD state
if git status | grep -q "HEAD detached"; then
    echo "🚨 Confirmed: Repository is in detached HEAD state"
    
    # Get current commit
    CURRENT_COMMIT=$(git rev-parse HEAD)
    echo "📝 Current commit: $CURRENT_COMMIT"
    
    # Show recent commits
    echo "📜 Recent commits:"
    git log --oneline -3
    
    echo ""
    echo "🔄 Attempting to fix detached HEAD..."
    
    # Try to checkout main
    if git checkout main; then
        echo "✅ Successfully switched to main branch"
        
        # Check if our commit is already in main
        if git merge-base --is-ancestor $CURRENT_COMMIT main; then
            echo "✅ Commit is already in main branch"
        else
            echo "🔄 Applying commit to main branch..."
            if git cherry-pick $CURRENT_COMMIT; then
                echo "✅ Successfully applied commit to main"
                
                # Push to GitHub
                echo "🚀 Pushing to GitHub..."
                if git push origin main; then
                    echo "✅ Successfully pushed to GitHub"
                    echo "🎉 Detached HEAD fixed and changes pushed!"
                else
                    echo "❌ Failed to push - check credentials and network"
                fi
            else
                echo "❌ Cherry-pick failed - may need manual intervention"
            fi
        fi
    else
        echo "❌ Could not checkout main branch"
        echo "💡 Trying to create main branch..."
        if git checkout -b main; then
            echo "✅ Created and switched to main branch"
            echo "🚀 Pushing new main branch..."
            git push -u origin main
        else
            echo "❌ Could not create main branch"
        fi
    fi
else
    echo "✅ Repository is not in detached HEAD state"
    echo "📍 Current branch: $(git branch --show-current)"
fi

echo ""
echo "📊 Final status:"
git status --porcelain
git branch -v
