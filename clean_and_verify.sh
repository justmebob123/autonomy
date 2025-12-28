#!/bin/bash

echo "=== Cleaning Python Cache ==="
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
echo "✓ Cache cleaned"

echo ""
echo "=== Verifying base.py code ==="
echo "Checking line 600 (should show tuple unpacking):"
sed -n '600p' pipeline/phases/base.py

echo ""
echo "Checking lines 603-605 (should show correct usage):"
sed -n '603,605p' pipeline/phases/base.py

echo ""
echo "=== Searching for problematic patterns ==="
echo "Searching for 'parsed.get' in Python files:"
grep -rn "parsed\.get" --include="*.py" pipeline/ || echo "✓ No problematic patterns found"

echo ""
echo "=== Git Status ==="
git status --short

echo ""
echo "=== Current Commit ==="
git log -1 --oneline

echo ""
echo "✓ Verification complete"