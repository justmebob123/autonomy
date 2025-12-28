# Depth-61 Analysis Scripts Collection

This directory contains specialized scripts created for comprehensive depth-61 recursive analysis of the autonomy codebase.

## Scripts Overview

### 1. ENHANCED_DEPTH_61_ANALYZER.py
**Purpose**: Original enhanced analyzer with variable tracing
**Features**:
- AST-based static analysis
- Variable flow tracking
- Function call graph generation
- Complexity metrics
- Import analysis

**Usage**:
```bash
python scripts/analysis/ENHANCED_DEPTH_61_ANALYZER.py
```

### 2. IMPROVED_DEPTH_61_ANALYZER.py
**Purpose**: Enhanced analyzer with inheritance pattern detection
**Features**:
- Template method pattern detection
- Inheritance chain analysis
- Polymorphic call detection
- False positive reduction
- Cross-file call graph

**Usage**:
```bash
python scripts/analysis/IMPROVED_DEPTH_61_ANALYZER.py
```

### 3. DEAD_CODE_DETECTOR.py
**Purpose**: Specialized dead code detection with pattern awareness
**Features**:
- Unused function detection
- Unused import detection
- Template method pattern handling
- Dynamic call detection
- Comprehensive reporting

**Usage**:
```bash
python scripts/analysis/DEAD_CODE_DETECTOR.py
```

### 4. COMPLEXITY_ANALYZER.py
**Purpose**: Cyclomatic complexity analysis
**Features**:
- Per-function complexity calculation
- Complexity hotspot identification
- Refactoring priority ranking
- Effort estimation

**Usage**:
```bash
python scripts/analysis/COMPLEXITY_ANALYZER.py
```

### 5. INTEGRATION_GAP_FINDER.py
**Purpose**: Find integration gaps and incomplete features
**Features**:
- Unused class detection
- Incomplete feature identification
- Integration point analysis
- Architectural gap detection

**Usage**:
```bash
python scripts/analysis/INTEGRATION_GAP_FINDER.py
```

### 6. CALL_GRAPH_GENERATOR.py
**Purpose**: Generate comprehensive call graphs
**Features**:
- Cross-file call tracking
- Inheritance-aware analysis
- Dynamic call detection
- Visual graph generation

**Usage**:
```bash
python scripts/analysis/CALL_GRAPH_GENERATOR.py
```

## Analysis Workflow

### Step 1: Initial Analysis
```bash
python scripts/analysis/ENHANCED_DEPTH_61_ANALYZER.py
```

### Step 2: Inheritance Analysis
```bash
python scripts/analysis/IMPROVED_DEPTH_61_ANALYZER.py
```

### Step 3: Dead Code Detection
```bash
python scripts/analysis/DEAD_CODE_DETECTOR.py
```

### Step 4: Complexity Analysis
```bash
python scripts/analysis/COMPLEXITY_ANALYZER.py
```

### Step 5: Integration Gap Analysis
```bash
python scripts/analysis/INTEGRATION_GAP_FINDER.py
```

### Step 6: Call Graph Generation
```bash
python scripts/analysis/CALL_GRAPH_GENERATOR.py
```

## Output Files

All scripts generate detailed reports in the workspace root:
- `analysis_*.txt` - Raw analysis output
- `DEPTH_61_*_ANALYSIS.md` - Formatted analysis reports
- `*_REPORT.md` - Summary reports
- `call_graph.png` - Visual call graph (if graphviz installed)

## Notes

- All scripts are designed to be run from the workspace root
- Scripts analyze the `autonomy/` directory by default
- Some scripts may take several minutes to complete
- Ensure sufficient memory for large codebases (>1GB recommended)

## Future Enhancements

- Runtime instrumentation for dynamic call detection
- Test coverage integration
- Performance profiling integration
- Automated refactoring suggestions
- CI/CD integration