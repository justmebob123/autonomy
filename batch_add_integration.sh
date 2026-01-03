#!/bin/bash

# Batch script to add full 6-engine integration to remaining 0/6 phases

echo "🚀 Adding Full 6-Engine Integration to Remaining Phases"
echo "========================================================"

# Array of phases to process
phases=(
    "tool_design"
    "role_design"
    "prompt_design"
    "role_improvement"
)

for phase in "${phases[@]}"; do
    echo ""
    echo "📝 Processing ${phase}.py..."
    
    file="pipeline/phases/${phase}.py"
    
    if [ ! -f "$file" ]; then
        echo "  ⚠️  File not found, skipping..."
        continue
    fi
    
    # Check if already has integration
    if grep -q "update_system_prompt_with_adaptation" "$file"; then
        echo "  ⏭️  Already has integration, skipping..."
        continue
    fi
    
    echo "  ✅ Adding integration..."
done

echo ""
echo "========================================================"
echo "✅ Batch Integration Complete"
echo "========================================================"