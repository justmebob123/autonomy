#!/bin/bash

# QA Phase Tuple Error Fix Script
# This script fixes the AttributeError: 'tuple' object has no attribute 'get'

set -e  # Exit on error

echo "=================================================="
echo "QA Phase Tuple Error - Automated Fix"
echo "=================================================="
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Working directory: $(pwd)"
echo ""

# Step 1: Clean Python cache
echo "Step 1: Cleaning Python bytecode cache..."
find . -type d -name __pycache__ -print0 | xargs -0 rm -rf 2>/dev/null || true
find . -type f -name "*.pyc" -print0 | xargs -0 rm -f 2>/dev/null || true
find . -type f -name "*.pyo" -print0 | xargs -0 rm -f 2>/dev/null || true
echo "✓ Cache cleaned"
echo ""

# Step 2: Check git status
echo "Step 2: Checking git status..."
git status --short
echo ""

# Step 3: Pull latest changes
echo "Step 3: Pulling latest changes from repository..."
git fetch origin
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" = "main" ]; then
    git pull origin main
else
    echo "⚠️  Warning: Not on main branch. Skipping pull."
fi
echo ""

# Step 4: Verify the fix
echo "Step 4: Verifying the fix..."
echo "Checking line 600 in pipeline/phases/base.py:"
sed -n '600p' pipeline/phases/base.py
echo ""

echo "Checking lines 603-605 in pipeline/phases/base.py:"
sed -n '603,605p' pipeline/phases/base.py
echo ""

# Step 5: Search for problematic patterns
echo "Step 5: Searching for problematic patterns..."
if grep -rn "parsed\.get" --include="*.py" pipeline/ 2>/dev/null; then
    echo "❌ Found problematic patterns!"
    exit 1
else
    echo "✓ No problematic patterns found"
fi
echo ""

# Step 6: Display current commit
echo "Step 6: Current commit information..."
git log -1 --oneline
echo ""

# Step 7: Final verification
echo "Step 7: Final verification..."
if [ -f "pipeline/phases/base.py" ]; then
    if grep -q "tool_calls_parsed, _ = self.parser.parse_response" pipeline/phases/base.py; then
        echo "✓ Code is correct - tuple unpacking is present"
    else
        echo "❌ Code verification failed - tuple unpacking not found"
        exit 1
    fi
else
    echo "❌ File not found: pipeline/phases/base.py"
    exit 1
fi
echo ""

echo "=================================================="
echo "✓ Fix Applied Successfully!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Restart your pipeline"
echo "2. Monitor the logs for any errors"
echo "3. If the error persists, check that you're running from the correct directory"
echo ""
echo "If you continue to see errors, please run:"
echo "  python -B main.py"
echo ""
echo "The -B flag prevents Python from creating bytecode files."
echo ""