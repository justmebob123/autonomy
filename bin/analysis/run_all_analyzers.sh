#!/bin/bash

# Run All Analysis Scripts
# This script runs all analysis tools in sequence and generates a comprehensive report

echo "=========================================="
echo "Running Complete Analysis Suite"
echo "=========================================="
echo ""

# Set working directory
cd /workspace

# Create output directory
mkdir -p analysis_output
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="analysis_output/${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"

echo "Output directory: $OUTPUT_DIR"
echo ""

# Step 1: Enhanced Analyzer
echo "Step 1/6: Running Enhanced Depth-61 Analyzer..."
python scripts/analysis/ENHANCED_DEPTH_61_ANALYZER.py > "$OUTPUT_DIR/enhanced_analyzer.log" 2>&1
if [ -f "analysis_enhanced.txt" ]; then
    mv analysis_enhanced.txt "$OUTPUT_DIR/"
fi
echo "✓ Complete"
echo ""

# Step 2: Improved Analyzer
echo "Step 2/6: Running Improved Depth-61 Analyzer..."
python scripts/analysis/IMPROVED_DEPTH_61_ANALYZER.py > "$OUTPUT_DIR/improved_analyzer.log" 2>&1
if [ -f "improved_analysis.txt" ]; then
    mv improved_analysis.txt "$OUTPUT_DIR/"
fi
echo "✓ Complete"
echo ""

# Step 3: Dead Code Detector
echo "Step 3/6: Running Dead Code Detector..."
python scripts/analysis/DEAD_CODE_DETECTOR.py > "$OUTPUT_DIR/dead_code.log" 2>&1
if [ -f "DEAD_CODE_REPORT.txt" ]; then
    mv DEAD_CODE_REPORT.txt "$OUTPUT_DIR/"
fi
echo "✓ Complete"
echo ""

# Step 4: Complexity Analyzer
echo "Step 4/6: Running Complexity Analyzer..."
python scripts/analysis/COMPLEXITY_ANALYZER.py > "$OUTPUT_DIR/complexity.log" 2>&1
if [ -f "COMPLEXITY_REPORT.txt" ]; then
    mv COMPLEXITY_REPORT.txt "$OUTPUT_DIR/"
fi
echo "✓ Complete"
echo ""

# Step 5: Integration Gap Finder
echo "Step 5/6: Running Integration Gap Finder..."
python scripts/analysis/INTEGRATION_GAP_FINDER.py > "$OUTPUT_DIR/integration_gaps.log" 2>&1
if [ -f "INTEGRATION_GAP_REPORT.txt" ]; then
    mv INTEGRATION_GAP_REPORT.txt "$OUTPUT_DIR/"
fi
echo "✓ Complete"
echo ""

# Step 6: Call Graph Generator
echo "Step 6/6: Running Call Graph Generator..."
python scripts/analysis/CALL_GRAPH_GENERATOR.py > "$OUTPUT_DIR/call_graph.log" 2>&1
if [ -f "CALL_GRAPH_REPORT.txt" ]; then
    mv CALL_GRAPH_REPORT.txt "$OUTPUT_DIR/"
fi
if [ -f "call_graph.dot" ]; then
    mv call_graph.dot "$OUTPUT_DIR/"
fi
echo "✓ Complete"
echo ""

# Generate summary report
echo "Generating summary report..."
cat > "$OUTPUT_DIR/ANALYSIS_SUMMARY.txt" << EOF
========================================
COMPREHENSIVE ANALYSIS SUMMARY
========================================
Generated: $(date)
Output Directory: $OUTPUT_DIR

REPORTS GENERATED:
1. Enhanced Analyzer Report (analysis_enhanced.txt)
2. Improved Analyzer Report (improved_analysis.txt)
3. Dead Code Report (DEAD_CODE_REPORT.txt)
4. Complexity Report (COMPLEXITY_REPORT.txt)
5. Integration Gap Report (INTEGRATION_GAP_REPORT.txt)
6. Call Graph Report (CALL_GRAPH_REPORT.txt)
7. Call Graph DOT File (call_graph.dot)

LOGS:
- enhanced_analyzer.log
- improved_analyzer.log
- dead_code.log
- complexity.log
- integration_gaps.log
- call_graph.log

TO VISUALIZE CALL GRAPH:
cd $OUTPUT_DIR
dot -Tpng call_graph.dot -o call_graph.png

NEXT STEPS:
1. Review all reports in $OUTPUT_DIR
2. Prioritize findings by severity
3. Create action plan for improvements
4. Execute refactoring as needed
5. Re-run analysis to verify improvements

========================================
EOF

echo ""
echo "=========================================="
echo "Analysis Complete!"
echo "=========================================="
echo ""
echo "All reports saved to: $OUTPUT_DIR"
echo ""
echo "Summary:"
ls -lh "$OUTPUT_DIR"/*.txt "$OUTPUT_DIR"/*.dot 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo "To view summary: cat $OUTPUT_DIR/ANALYSIS_SUMMARY.txt"
echo ""