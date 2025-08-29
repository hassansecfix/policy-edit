# User Isolation Guide for Policy Automation

## Overview

This document explains the user isolation system implemented in the Policy Automation platform to ensure multiple users can run operations simultaneously without interfering with each other.

## Key Features

### 1. User-Specific Git Branches

- Each user operation creates a unique branch: `user-{user_id}`
- Users work in isolated branches, preventing merge conflicts
- Automatic cleanup after successful completion

### 2. GitHub Actions Isolation

- Workflows run on user-specific branches
- Unique artifact names per user: `redlined-docx-{user_id}-{run_id}-{run_number}`
- User context passed through workflow parameters

### 3. File Path Isolation

- User-prefixed file names for all generated files
- Separate logo files per user when uploaded
- Isolated output directories

## How It Works

### Git Operations Flow

1. **Branch Creation**: When a user starts an operation:

   ```
   main branch → user-{user_id} branch
   ```

2. **Isolated Work**: All commits happen on the user branch:

   ```
   user-{user_id}: file1.json, file2.docx, logo.png
   ```

3. **GitHub Actions**: Workflow runs on user branch:

   ```
   Trigger: ref = user-{user_id}
   Inputs: user_id, branch, files...
   ```

4. **Cleanup**: After successful completion:
   ```
   Delete user-{user_id} branch (local + remote)
   ```

### User ID Generation

- **Automatic**: `user-{timestamp}-{random}`
- **Manual**: Can be provided via `--user-id` parameter
- **Web UI**: Generated automatically per session

## Implementation Details

### GitManager Class Updates

```python
class GitManager:
    def __init__(self, repo_path: str = ".", user_id: Optional[str] = None):
        self.user_id = user_id
        self.user_branch = f"user-{user_id}" if user_id else None

    def create_user_branch(self) -> Tuple[bool, str]:
        # Creates isolated branch from main

    def cleanup_user_branch(self) -> Tuple[bool, str]:
        # Cleans up branch after completion
```

### GitHub Actions Updates

**Workflow Inputs**:

```yaml
user_id:
  description: 'User ID for isolation (optional)'
  required: false
  default: ''
branch:
  description: 'Branch to checkout (optional)'
  required: false
  default: 'main'
```

**Checkout Step**:

```yaml
- name: Checkout user-specific branch
  uses: actions/checkout@v4
  with:
    ref: ${{ github.event.inputs.branch }}
    fetch-depth: 0
```

**Artifact Naming**:

```yaml
name: redlined-docx-${{ github.event.inputs.user_id }}-${{ github.run_id }}-${{ github.run_number }}
```

## Usage Examples

### Command Line

```bash
# With automatic user ID
python3 scripts/complete_automation.py \
  --policy data/policy.docx \
  --questionnaire data/answers.json \
  --output-name "my_policy"

# With custom user ID
python3 scripts/complete_automation.py \
  --policy data/policy.docx \
  --questionnaire data/answers.json \
  --output-name "my_policy" \
  --user-id "alice-session-1"
```

### Web UI

User isolation is automatic - each browser session gets a unique user ID.

## Parallel Execution Example

**Before (Single Branch)**:

```
User A: commits to main → conflict with User B
User B: commits to main → overwrites User A's work
```

**After (User Branches)**:

```
User A: commits to user-alice → isolated work
User B: commits to user-bob   → isolated work
Both workflows run independently with different artifacts
```

## Cleanup Process

### Automatic Cleanup

1. **On Success**: User branch is automatically deleted
2. **On Failure**: User branch remains for debugging
3. **Manual Cleanup**: `cleanup_user_git_operations(user_id)`

### Manual Cleanup

```bash
# Clean up specific user branch
git branch -D user-alice-123
git push origin --delete user-alice-123
```

## Troubleshooting

### Common Issues

1. **Branch Already Exists**:

   - Solution: Existing branch is reset to main automatically

2. **Push Conflicts**:

   - Solution: User branches don't conflict since they're isolated

3. **Cleanup Failures**:
   - Solution: Manual cleanup commands provided in logs

### Debugging

**Check User Branches**:

```bash
git branch -a | grep user-
```

**Check GitHub Actions**:

- Look for user ID in workflow run names
- Check artifact names for user identification

## Benefits

1. **Zero Conflicts**: Users can't interfere with each other
2. **Parallel Processing**: Multiple workflows run simultaneously
3. **Easy Debugging**: Each user's work is isolated and traceable
4. **Automatic Cleanup**: No manual intervention required
5. **Scalable**: Supports unlimited concurrent users

## Backward Compatibility

- **No User ID**: Falls back to main branch (legacy behavior)
- **Existing Scripts**: Work without modification
- **Environment Variables**: All existing configs still work

## Security Considerations

- User branches are temporary and cleaned up automatically
- No sensitive data persists in user branches
- Branch names don't contain sensitive information
- GitHub token permissions apply to all branches

## Performance Impact

- **Minimal**: Branch creation/deletion is fast
- **Scalable**: Git handles many branches efficiently
- **Cleanup**: Prevents branch proliferation
- **Caching**: GitHub Actions cache still works effectively
