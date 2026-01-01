# URGENT: File Recovery Guide

## What Happened

The `merge_file_implementations` tool was **destroying files** instead of merging them. Every time it ran, it replaced the entire file content with just a comment.

## Files That Need Recovery

Based on your report, these files were destroyed:
- `timeline/resource_estimation.py` - Now just a comment
- `resources/resource_estimator.py` - Now 83 bytes (just a comment)
- `chat/ollama_integration.py` - Destroyed
- Potentially many more files

## How to Recover

### Step 1: Find Your Backups

```bash
cd /home/ai/AI/web
ls -la .autonomy/backups/ | tail -20
```

You should see directories like:
- `merge_20251231_200020/`
- `merge_20251231_200509/`
- `merge_20251231_195528/`
- `merge_20251231_144356/`

### Step 2: Check What's in the Backups

```bash
# List files in a backup
ls -la .autonomy/backups/merge_20251231_200509/

# Check file size to see if it has content
ls -lh .autonomy/backups/merge_20251231_200509/resource_estimation.py
```

### Step 3: Restore Files

For each destroyed file, find the most recent backup with actual content:

```bash
# Example: Restore resource_estimation.py
# Find the backup with the largest file (most content)
ls -lh .autonomy/backups/*/resource_estimation.py

# Copy the best one back
cp .autonomy/backups/merge_20251231_200509/resource_estimation.py timeline/

# Verify it has content
wc -l timeline/resource_estimation.py
cat timeline/resource_estimation.py | head -20
```

### Step 4: Restore All Destroyed Files

```bash
cd /home/ai/AI/web

# Find all files that are just comments (very small)
find . -name "*.py" -size -200c -type f | grep -v __pycache__ | grep -v .autonomy

# For each small file, check if it's just a comment
for file in $(find . -name "*.py" -size -200c -type f | grep -v __pycache__ | grep -v .autonomy); do
    echo "=== $file ==="
    head -3 "$file"
    echo ""
done

# Restore from backups
# (You'll need to identify which backup has the correct version)
```

## Quick Recovery Script

```bash
#!/bin/bash
cd /home/ai/AI/web

# Function to restore a file from backups
restore_file() {
    local filename=$1
    local target_path=$2
    
    echo "Looking for backups of $filename..."
    
    # Find all backups of this file, sorted by size (largest first)
    backup=$(find .autonomy/backups -name "$filename" -type f -exec ls -lh {} \; | sort -k5 -hr | head -1 | awk '{print $NF}')
    
    if [ -n "$backup" ]; then
        echo "Found backup: $backup"
        size=$(stat -f%z "$backup" 2>/dev/null || stat -c%s "$backup" 2>/dev/null)
        if [ "$size" -gt 200 ]; then
            echo "Restoring $backup -> $target_path"
            cp "$backup" "$target_path"
            echo "✅ Restored"
        else
            echo "⚠️  Backup is too small ($size bytes), skipping"
        fi
    else
        echo "❌ No backup found"
    fi
    echo ""
}

# Restore known destroyed files
restore_file "resource_estimation.py" "timeline/resource_estimation.py"
restore_file "resource_estimator.py" "resources/resource_estimator.py"
restore_file "ollama_integration.py" "chat/ollama_integration.py"

echo "Recovery complete. Verify files have content:"
wc -l timeline/resource_estimation.py resources/resource_estimator.py chat/ollama_integration.py
```

## Verification

After restoring, verify each file:

```bash
# Check file has content (not just a comment)
wc -l timeline/resource_estimation.py

# Check it's valid Python
python3 -m py_compile timeline/resource_estimation.py

# View first 20 lines to verify it's real code
head -20 timeline/resource_estimation.py
```

## Prevention

The merge tool is now **FIXED** (commit abb5949). To prevent this from happening again:

1. **Pull latest changes**:
   ```bash
   cd /home/ai/AI/autonomy
   git pull origin main
   ```

2. **The fix includes**:
   - Proper AST-based file merging
   - Automatic backups before merging
   - Deduplication of imports
   - Preservation of all classes and functions
   - Error handling for syntax errors

3. **Test before using**:
   ```bash
   # Create test files
   echo "import os\ndef foo(): pass" > test1.py
   echo "import sys\ndef bar(): pass" > test2.py
   
   # Run pipeline on test project first
   # Verify merge works correctly
   ```

## If Backups Are Missing

If you can't find backups, you may need to:

1. **Check git history** (if the project is in git):
   ```bash
   cd /home/ai/AI/web
   git log --all --full-history -- timeline/resource_estimation.py
   git show <commit>:timeline/resource_estimation.py
   ```

2. **Reconstruct from scratch**:
   - Look at MASTER_PLAN.md for requirements
   - Look at other similar files for patterns
   - Implement based on what the file should do

3. **Check other backup locations**:
   - System backups
   - Cloud backups
   - Previous project copies

## Summary

1. ✅ **Tool is now fixed** (commit abb5949)
2. ⚠️  **Files need recovery** from `.autonomy/backups/`
3. 📋 **Follow steps above** to restore destroyed files
4. 🔄 **Pull latest changes** before running again
5. ✅ **Test with simple files** before production use

## Need Help?

If you can't recover files or need assistance:
1. List all backup directories: `ls -la .autonomy/backups/`
2. Show file sizes: `ls -lh .autonomy/backups/*/resource_estimation.py`
3. Check what's in the files: `head -20 .autonomy/backups/merge_*/resource_estimation.py`

The backups should have your original code - the tool created backups before destroying the files.