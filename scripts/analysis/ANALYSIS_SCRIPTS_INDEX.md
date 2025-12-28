# Analysis Scripts Index

This document provides a comprehensive index of all specialized analysis scripts created for the depth-61 examination of the autonomy codebase.

## Quick Reference

| Script | Purpose | Output | Runtime |
|--------|---------|--------|---------|
| ENHANCED_DEPTH_61_ANALYZER.py | Full AST analysis with variable tracing | analysis_enhanced.txt | ~2-3 min |
| IMPROVED_DEPTH_61_ANALYZER.py | Inheritance-aware analysis | improved_analysis.txt | ~2-3 min |
| DEAD_CODE_DETECTOR.py | Find unused functions/imports | DEAD_CODE_REPORT.txt | ~1-2 min |
| COMPLEXITY_ANALYZER.py | Calculate cyclomatic complexity | COMPLEXITY_REPORT.txt | ~1-2 min |
| INTEGRATION_GAP_FINDER.py | Find incomplete features | INTEGRATION_GAP_REPORT.txt | ~1-2 min |
| CALL_GRAPH_GENERATOR.py | Generate call graphs | CALL_GRAPH_REPORT.txt, call_graph.dot | ~2-3 min |

## Detailed Descriptions

### 1. ENHANCED_DEPTH_61_ANALYZER.py

**Purpose**: Comprehensive AST-based static analysis with variable flow tracking

**Features**:
- Function and class discovery
- Variable flow tracking
- Import analysis
- Call graph generation
- Complexity metrics
- Dependency mapping

**Output Files**:
- `analysis_enhanced.txt` - Raw analysis data
- Console output with statistics

**Usage**:
```bash
cd /workspace
python scripts/analysis/ENHANCED_DEPTH_61_ANALYZER.py
```

**When to Use**:
- Initial codebase analysis
- Understanding code structure
- Identifying dependencies
- Baseline complexity assessment

---

### 2. IMPROVED_DEPTH_61_ANALYZER.py

**Purpose**: Enhanced analyzer with design pattern awareness

**Features**:
- Template method pattern detection
- Inheritance chain analysis
- Polymorphic call detection
- False positive reduction
- Cross-file relationship mapping

**Output Files**:
- `improved_analysis.txt` - Enhanced analysis data
- Console output with pattern detection

**Usage**:
```bash
cd /workspace
python scripts/analysis/IMPROVED_DEPTH_61_ANALYZER.py
```

**When to Use**:
- After initial analysis
- Verifying dead code findings
- Understanding design patterns
- Reducing false positives

---

### 3. DEAD_CODE_DETECTOR.py

**Purpose**: Identify unused functions, methods, and imports

**Features**:
- Unused function detection
- Unused method detection (pattern-aware)
- Unused import detection
- Template method exclusion
- Comprehensive reporting

**Output Files**:
- `DEAD_CODE_REPORT.txt` - Detailed dead code report

**Usage**:
```bash
cd /workspace
python scripts/analysis/DEAD_CODE_DETECTOR.py
```

**When to Use**:
- Code cleanup initiatives
- Before refactoring
- Reducing codebase size
- Identifying incomplete features

**Report Sections**:
1. Unused Functions
2. Unused Methods
3. Unused Imports
4. Summary Statistics

---

### 4. COMPLEXITY_ANALYZER.py

**Purpose**: Calculate cyclomatic complexity and identify refactoring priorities

**Features**:
- Per-function complexity calculation
- Complexity distribution analysis
- Refactoring priority ranking
- Effort estimation
- Top 20 most complex functions

**Output Files**:
- `COMPLEXITY_REPORT.txt` - Comprehensive complexity report

**Usage**:
```bash
cd /workspace
python scripts/analysis/COMPLEXITY_ANALYZER.py
```

**When to Use**:
- Planning refactoring efforts
- Identifying technical debt
- Prioritizing code improvements
- Estimating development time

**Complexity Thresholds**:
- **CRITICAL**: >= 50 (7-10 days effort)
- **URGENT**: 30-49 (5-7 days effort)
- **HIGH**: 20-29 (2-3 days effort)
- **MEDIUM**: 10-19 (1-2 days effort)
- **LOW**: < 10 (<1 day effort)

**Report Sections**:
1. Top 20 Most Complex Functions
2. Complexity Distribution
3. Refactoring Priorities
4. Effort Estimation
5. Summary Statistics

---

### 5. INTEGRATION_GAP_FINDER.py

**Purpose**: Identify incomplete features and architectural gaps

**Features**:
- Unused class detection
- Classes with many unused methods
- Imported but unused classes
- Integration point analysis
- Architectural gap identification

**Output Files**:
- `INTEGRATION_GAP_REPORT.txt` - Integration gap analysis

**Usage**:
```bash
cd /workspace
python scripts/analysis/INTEGRATION_GAP_FINDER.py
```

**When to Use**:
- Identifying incomplete features
- Finding over-engineered code
- Cleaning up unused dependencies
- Understanding system architecture

**Report Sections**:
1. Unused Classes
2. Classes with Many Unused Methods (>50%)
3. Imported but Unused Classes
4. Summary
5. Recommendations

---

### 6. CALL_GRAPH_GENERATOR.py

**Purpose**: Generate comprehensive call graphs for visualization

**Features**:
- Function/method call tracking
- Inheritance-aware analysis
- Call chain generation
- DOT format graph generation
- Most called/calling functions

**Output Files**:
- `CALL_GRAPH_REPORT.txt` - Call graph statistics
- `call_graph.dot` - DOT format graph for visualization

**Usage**:
```bash
cd /workspace
python scripts/analysis/CALL_GRAPH_GENERATOR.py

# To visualize (requires graphviz):
dot -Tpng call_graph.dot -o call_graph.png
```

**When to Use**:
- Understanding code flow
- Identifying critical functions
- Visualizing dependencies
- Planning refactoring

**Report Sections**:
1. Statistics
2. Top 20 Most Called Functions
3. Top 20 Functions with Most Calls
4. Inheritance Hierarchy
5. Summary

---

## Recommended Analysis Workflow

### Phase 1: Initial Discovery
```bash
# Step 1: Run enhanced analyzer for baseline
python scripts/analysis/ENHANCED_DEPTH_61_ANALYZER.py

# Step 2: Run improved analyzer for pattern detection
python scripts/analysis/IMPROVED_DEPTH_61_ANALYZER.py
```

### Phase 2: Issue Identification
```bash
# Step 3: Find dead code
python scripts/analysis/DEAD_CODE_DETECTOR.py

# Step 4: Analyze complexity
python scripts/analysis/COMPLEXITY_ANALYZER.py

# Step 5: Find integration gaps
python scripts/analysis/INTEGRATION_GAP_FINDER.py
```

### Phase 3: Visualization
```bash
# Step 6: Generate call graph
python scripts/analysis/CALL_GRAPH_GENERATOR.py
dot -Tpng call_graph.dot -o call_graph.png
```

### Phase 4: Review and Action
1. Review all generated reports
2. Prioritize findings by severity
3. Create action plan
4. Execute refactoring
5. Re-run analysis to verify improvements

---

## Integration with Development Workflow

### Pre-Commit Analysis
```bash
# Quick check before committing
python scripts/analysis/DEAD_CODE_DETECTOR.py
python scripts/analysis/COMPLEXITY_ANALYZER.py
```

### Weekly Code Review
```bash
# Comprehensive weekly analysis
./scripts/analysis/run_all_analyzers.sh
```

### Before Major Refactoring
```bash
# Full analysis suite
python scripts/analysis/ENHANCED_DEPTH_61_ANALYZER.py
python scripts/analysis/IMPROVED_DEPTH_61_ANALYZER.py
python scripts/analysis/DEAD_CODE_DETECTOR.py
python scripts/analysis/COMPLEXITY_ANALYZER.py
python scripts/analysis/INTEGRATION_GAP_FINDER.py
python scripts/analysis/CALL_GRAPH_GENERATOR.py
```

---

## Output File Reference

| File | Generated By | Purpose |
|------|--------------|---------|
| analysis_enhanced.txt | ENHANCED_DEPTH_61_ANALYZER.py | Raw AST analysis data |
| improved_analysis.txt | IMPROVED_DEPTH_61_ANALYZER.py | Pattern-aware analysis |
| DEAD_CODE_REPORT.txt | DEAD_CODE_DETECTOR.py | Unused code listing |
| COMPLEXITY_REPORT.txt | COMPLEXITY_ANALYZER.py | Complexity metrics |
| INTEGRATION_GAP_REPORT.txt | INTEGRATION_GAP_FINDER.py | Architectural gaps |
| CALL_GRAPH_REPORT.txt | CALL_GRAPH_GENERATOR.py | Call statistics |
| call_graph.dot | CALL_GRAPH_GENERATOR.py | Graph visualization |
| call_graph.png | dot (manual) | Visual call graph |

---

## Script Maintenance

### Adding New Scripts
1. Create script in `scripts/analysis/`
2. Add execute permissions: `chmod +x scripts/analysis/SCRIPT_NAME.py`
3. Update this index
4. Update README.md
5. Test thoroughly

### Modifying Existing Scripts
1. Document changes in script header
2. Update this index if behavior changes
3. Update README.md if usage changes
4. Re-run tests

### Testing Scripts
```bash
# Test on small subset first
cd /workspace
python scripts/analysis/SCRIPT_NAME.py

# Verify output
cat OUTPUT_FILE.txt
```

---

## Troubleshooting

### Common Issues

**Issue**: Script fails with syntax error
**Solution**: Check Python version (requires 3.8+)

**Issue**: Script runs slowly
**Solution**: Reduce scope or optimize AST traversal

**Issue**: False positives in dead code detection
**Solution**: Use IMPROVED_DEPTH_61_ANALYZER.py for pattern-aware analysis

**Issue**: Call graph too large to visualize
**Solution**: Filter by complexity or specific modules

---

## Performance Characteristics

| Script | Files/Second | Memory Usage | Scalability |
|--------|--------------|--------------|-------------|
| ENHANCED_DEPTH_61_ANALYZER.py | ~30 | ~200MB | Good |
| IMPROVED_DEPTH_61_ANALYZER.py | ~25 | ~250MB | Good |
| DEAD_CODE_DETECTOR.py | ~40 | ~150MB | Excellent |
| COMPLEXITY_ANALYZER.py | ~50 | ~100MB | Excellent |
| INTEGRATION_GAP_FINDER.py | ~35 | ~180MB | Good |
| CALL_GRAPH_GENERATOR.py | ~30 | ~300MB | Fair |

---

## Future Enhancements

### Planned Features
- [ ] Runtime instrumentation for dynamic call detection
- [ ] Test coverage integration
- [ ] Performance profiling integration
- [ ] Automated refactoring suggestions
- [ ] CI/CD integration
- [ ] Interactive visualization
- [ ] Incremental analysis (only changed files)
- [ ] Machine learning for pattern detection

### Contribution Guidelines
1. Follow existing code style
2. Add comprehensive docstrings
3. Include usage examples
4. Update this index
5. Test on real codebase
6. Submit PR with description

---

## Contact and Support

For questions or issues with these scripts:
1. Check this documentation first
2. Review script docstrings
3. Check output files for error messages
4. Consult README.md for general guidance

---

**Last Updated**: December 28, 2024
**Version**: 1.0
**Maintainer**: SuperNinja AI Agent