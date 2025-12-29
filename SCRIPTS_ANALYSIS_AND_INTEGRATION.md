# Scripts Analysis and Integration Plan

## Executive Summary

The `scripts/` directory contains powerful analysis tools that are currently underutilized. This document analyzes all available scripts and provides a detailed integration plan.

## Current State Analysis

### Issue 1: Custom Tools Limited Scope
**Problem**: Custom tools only look in `scripts/custom_tools/tools/`
**Impact**: Missing valuable analysis tools in `scripts/analysis/`
**Root Cause**: Hardcoded path in registry.py and handler.py

### Issue 2: Scripts Not Integrated as Primary Tools
**Problem**: Analysis scripts are external utilities, not first-class pipeline tools
**Impact**: Phases cannot leverage powerful analysis capabilities
**Root Cause**: No integration layer between scripts and pipeline tools

### Issue 3: No Module Import Support
**Problem**: Scripts only executable via subprocess
**Impact**: Slower execution, no direct function access
**Root Cause**: No Python module import mechanism

## Available Scripts Inventory

### Category 1: Deep Analysis Framework (scripts/analysis/)

#### 1. ENHANCED_DEPTH_61_ANALYZER.py
**Capabilities**:
- Full AST analysis with variable tracing
- Function and class discovery
- Variable flow tracking
- Import analysis
- Call graph generation
- Complexity metrics
- Dependency mapping

**Input**: Directory path
**Output**: analysis_enhanced.txt
**Runtime**: ~2-3 minutes
**Use Cases**:
- Initial codebase analysis
- Understanding code structure
- Identifying dependencies
- Baseline complexity assessment

**Integration Priority**: HIGH
**Best Phases**: Planning, Project Planning, Debugging

#### 2. IMPROVED_DEPTH_61_ANALYZER.py
**Capabilities**:
- Template method pattern detection
- Inheritance chain analysis
- Polymorphic call detection
- False positive reduction
- Cross-file relationship mapping

**Input**: Directory path
**Output**: improved_analysis.txt
**Runtime**: ~2-3 minutes
**Use Cases**:
- Verifying dead code findings
- Understanding design patterns
- Reducing false positives

**Integration Priority**: HIGH
**Best Phases**: QA, Debugging, Project Planning

#### 3. DEAD_CODE_DETECTOR.py
**Capabilities**:
- Unused function detection
- Unused method detection (pattern-aware)
- Unused import detection
- Template method exclusion
- Comprehensive reporting

**Input**: Directory path
**Output**: DEAD_CODE_REPORT.txt
**Runtime**: ~1-2 minutes
**Use Cases**:
- Code cleanup initiatives
- Before refactoring
- Reducing codebase size
- Identifying incomplete features

**Integration Priority**: CRITICAL
**Best Phases**: QA, Debugging, Project Planning

#### 4. COMPLEXITY_ANALYZER.py
**Capabilities**:
- Per-function complexity calculation
- Complexity distribution analysis
- Refactoring priority ranking
- Effort estimation
- Top 20 most complex functions

**Input**: Directory path
**Output**: COMPLEXITY_REPORT.txt
**Runtime**: ~1-2 minutes
**Use Cases**:
- Planning refactoring efforts
- Identifying technical debt
- Prioritizing code improvements
- Estimating development time

**Complexity Thresholds**:
- CRITICAL: >= 50 (7-10 days effort)
- URGENT: 30-49 (5-7 days effort)
- HIGH: 20-29 (2-3 days effort)
- MEDIUM: 10-19 (1-2 days effort)
- LOW: < 10 (<1 day effort)

**Integration Priority**: CRITICAL
**Best Phases**: QA, Planning, Project Planning, Debugging

#### 5. INTEGRATION_GAP_FINDER.py
**Capabilities**:
- Unused class detection
- Classes with many unused methods
- Imported but unused classes
- Integration point analysis
- Architectural gap identification

**Input**: Directory path
**Output**: INTEGRATION_GAP_REPORT.txt
**Runtime**: ~1-2 minutes
**Use Cases**:
- Identifying incomplete features
- Finding over-engineered code
- Cleaning up unused dependencies
- Understanding system architecture

**Integration Priority**: HIGH
**Best Phases**: Project Planning, QA, Debugging

#### 6. CALL_GRAPH_GENERATOR.py
**Capabilities**:
- Function/method call tracking
- Inheritance-aware analysis
- Call chain generation
- DOT format graph generation
- Most called/calling functions

**Input**: Directory path
**Output**: CALL_GRAPH_REPORT.txt, call_graph.dot
**Runtime**: ~2-3 minutes
**Use Cases**:
- Understanding code flow
- Identifying critical functions
- Visualizing dependencies
- Planning refactoring

**Integration Priority**: MEDIUM
**Best Phases**: Project Planning, Debugging

#### 7. deep_analyze.py (CLI Tool)
**Capabilities**:
- Unified interface to all analyzers
- Multiple output formats (markdown, JSON)
- Recursive directory analysis
- Selective check execution

**Input**: File or directory path
**Output**: Configurable (markdown, JSON, console)
**Runtime**: Varies by checks
**Use Cases**:
- Comprehensive analysis
- Report generation
- CI/CD integration

**Integration Priority**: HIGH
**Best Phases**: All phases (as unified analysis tool)

### Category 2: Custom Tools Framework (scripts/custom_tools/)

#### Current Custom Tools:
1. **analyze_imports.py** - Import analysis
2. **code_complexity.py** - Complexity metrics
3. **find_todos.py** - TODO/FIXME finder
4. **test_tool.py** - Testing tool

**Integration Status**: Partially integrated
**Issue**: Limited to custom_tools/tools/ directory

## Integration Architecture

### Strategy: Three-Tier Integration

#### Tier 1: Direct Module Import (FASTEST)
```python
# Import scripts as Python modules
import sys
from pathlib import Path

scripts_dir = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

# Import analysis modules
from analysis.core.analyzer import DeepCodeAnalyzer
from analysis.core.complexity import ComplexityAnalyzer
# etc.
```

**Advantages**:
- Fast execution (no subprocess overhead)
- Direct function access
- Type safety
- Better error handling
- Can return structured data

**Disadvantages**:
- Requires refactoring scripts to be importable
- Potential namespace conflicts

#### Tier 2: Executable Wrapper (FALLBACK)
```python
# Run scripts as executables
def run_analysis_script(script_name: str, *args):
    script_path = scripts_dir / 'analysis' / f"{script_name}.py"
    result = subprocess.run(
        [sys.executable, str(script_path), *args],
        capture_output=True,
        text=True,
        cwd=project_dir
    )
    return parse_output(result.stdout)
```

**Advantages**:
- Works with any script
- Process isolation
- No import issues

**Disadvantages**:
- Slower (subprocess overhead)
- Output parsing required
- Less structured data

#### Tier 3: Hybrid Approach (OPTIMAL)
```python
# Try module import first, fallback to executable
def execute_analysis_tool(tool_name: str, **kwargs):
    try:
        # Try direct import
        module = import_analysis_module(tool_name)
        return module.analyze(**kwargs)
    except ImportError:
        # Fallback to executable
        return run_analysis_script(tool_name, **kwargs)
```

## Phase-Specific Integration Plan

### Planning Phase
**Current Tools**: create_task_plan, read_file, write_file
**Add Analysis Tools**:
1. **deep_analyze** - Comprehensive project analysis
2. **complexity_analyzer** - Identify complex areas
3. **integration_gap_finder** - Find incomplete features

**Use Cases**:
- Before creating task plan, analyze project structure
- Identify high-complexity areas needing attention
- Find integration gaps to plan completion

**Integration**:
```python
# In planning phase
def create_task_plan(self, ...):
    # 1. Run deep analysis
    analysis = self.tools.deep_analyze(project_dir)
    
    # 2. Check complexity
    complexity = self.tools.analyze_complexity(project_dir)
    
    # 3. Find gaps
    gaps = self.tools.find_integration_gaps(project_dir)
    
    # 4. Create informed task plan
    tasks = self._generate_tasks(analysis, complexity, gaps)
```

### Coding Phase
**Current Tools**: create_file, read_file, write_file, str_replace
**Add Analysis Tools**:
1. **complexity_analyzer** - Check code complexity before/after
2. **dead_code_detector** - Ensure no dead code introduced

**Use Cases**:
- Verify new code doesn't exceed complexity thresholds
- Check for unused imports
- Ensure code follows patterns

**Integration**:
```python
# In coding phase
def after_code_creation(self, filepath):
    # 1. Check complexity
    complexity = self.tools.analyze_file_complexity(filepath)
    if complexity > 20:
        self.logger.warning(f"High complexity: {complexity}")
    
    # 2. Check for dead code
    dead_code = self.tools.check_dead_code(filepath)
    if dead_code:
        self.logger.warning(f"Potential dead code: {dead_code}")
```

### QA Phase
**Current Tools**: approve_code, report_issue, read_file
**Add Analysis Tools**:
1. **complexity_analyzer** - Verify complexity thresholds
2. **dead_code_detector** - Find unused code
3. **improved_depth_61_analyzer** - Pattern verification
4. **integration_gap_finder** - Check integration completeness

**Use Cases**:
- Comprehensive code quality checks
- Architectural consistency verification
- Pattern compliance checking
- Integration completeness validation

**Integration**:
```python
# In QA phase
def review_code(self, filepath):
    issues = []
    
    # 1. Check complexity
    complexity = self.tools.analyze_complexity(filepath)
    if complexity['critical_functions']:
        issues.append({
            'type': 'complexity',
            'severity': 'high',
            'details': complexity['critical_functions']
        })
    
    # 2. Check dead code
    dead_code = self.tools.detect_dead_code(filepath)
    if dead_code['unused_functions']:
        issues.append({
            'type': 'dead_code',
            'severity': 'medium',
            'details': dead_code['unused_functions']
        })
    
    # 3. Check patterns
    patterns = self.tools.analyze_patterns(filepath)
    if patterns['violations']:
        issues.append({
            'type': 'pattern_violation',
            'severity': 'medium',
            'details': patterns['violations']
        })
    
    return issues
```

**CRITICAL FIX**: QA Phase Logic
```python
# WRONG (current):
if issues_found:
    mark_qa_phase_as_failed()

# CORRECT (should be):
if issues_found:
    mark_code_as_needs_fix()
    mark_qa_phase_as_succeeded()  # QA succeeded in finding issues!
```

### Debugging Phase
**Current Tools**: read_file, write_file, str_replace, run_command
**Add Analysis Tools**:
1. **call_graph_generator** - Trace execution paths
2. **enhanced_depth_61_analyzer** - Understand code structure
3. **complexity_analyzer** - Identify complex areas
4. **integration_gap_finder** - Find missing integrations

**Use Cases**:
- Trace bug through call graph
- Understand complex code structure
- Find integration issues
- Identify architectural problems

**Integration**:
```python
# In debugging phase
def debug_issue(self, issue_description):
    # 1. Generate call graph
    call_graph = self.tools.generate_call_graph(project_dir)
    
    # 2. Analyze structure
    structure = self.tools.analyze_structure(project_dir)
    
    # 3. Find related code
    related = self._find_related_code(issue_description, call_graph, structure)
    
    # 4. Analyze complexity
    complexity = self.tools.analyze_complexity(related['files'])
    
    return {
        'call_graph': call_graph,
        'structure': structure,
        'related_code': related,
        'complexity': complexity
    }
```

### Project Planning Phase
**Current Tools**: read_file, write_file
**Add Analysis Tools**:
1. **ALL ANALYSIS TOOLS** - Comprehensive project understanding
2. **deep_analyze** - Unified analysis interface

**Use Cases**:
- Comprehensive project analysis
- Architecture documentation
- Dependency mapping
- Complexity assessment
- Integration gap identification
- Update MASTER_PLAN, PRIMARY_OBJECTIVES, ARCHITECTURE, etc.

**Integration**:
```python
# In project planning phase
def update_project_documents(self):
    # 1. Run comprehensive analysis
    analysis = self.tools.deep_analyze(
        project_dir,
        checks=['all'],
        format='structured'
    )
    
    # 2. Update ARCHITECTURE.md
    self.tools.update_section(
        'ARCHITECTURE.md',
        'System Structure',
        analysis['structure']
    )
    
    # 3. Update MASTER_PLAN.md
    self.tools.update_section(
        'MASTER_PLAN.md',
        'Technical Debt',
        analysis['complexity']['high_priority']
    )
    
    # 4. Update PRIMARY_OBJECTIVES.md
    self.tools.append_to_file(
        'PRIMARY_OBJECTIVES.md',
        f"\n## New Objectives from Analysis\n{analysis['gaps']}"
    )
```

## Implementation Roadmap

### Phase 1: Core Infrastructure (IMMEDIATE)
1. Create `pipeline/tools/analysis_tools.py`
2. Implement module import mechanism
3. Implement executable fallback
4. Create tool wrappers for each script
5. Add tool definitions

### Phase 2: File Update Tools (IMMEDIATE)
1. Create `pipeline/tools/file_updates.py`
2. Implement `append_to_file`
3. Implement `update_section`
4. Implement `insert_after`
5. Add to planning and project_planning phases

### Phase 3: Phase Integration (HIGH PRIORITY)
1. Update `pipeline/tools.py` get_tools_for_phase()
2. Add analysis tools to each phase
3. Update phase prompts with tool guidance
4. Test tool availability

### Phase 4: QA Phase Fix (CRITICAL)
1. Update `pipeline/phases/qa.py` logic
2. Fix issue attribution (code issues, not QA failure)
3. Update task status handling
4. Test with intentionally buggy code

### Phase 5: Testing (CRITICAL)
1. Test each tool in each phase
2. Test module import mode
3. Test executable fallback mode
4. Test file update tools
5. Run full pipeline test

### Phase 6: Documentation (HIGH PRIORITY)
1. Document new tools
2. Update phase documentation
3. Create usage examples
4. Update README

## Success Metrics

### Integration Success
- ✅ All scripts/ tools available in appropriate phases
- ✅ Module import working for all scripts
- ✅ Executable fallback working
- ✅ File update tools working
- ✅ Planning phase can expand objectives
- ✅ QA phase correctly attributes issues

### Performance Metrics
- Tool discovery: < 10ms
- Module import: < 50ms
- Executable fallback: < 500ms
- Analysis execution: < 5 minutes
- File updates: < 100ms

### Quality Metrics
- No false positives in dead code detection
- Accurate complexity calculations
- Correct pattern detection
- Proper issue attribution in QA

## Risk Mitigation

### Risk 1: Import Conflicts
**Mitigation**: Use isolated namespaces, careful import management

### Risk 2: Performance Degradation
**Mitigation**: Cache analysis results, use incremental analysis

### Risk 3: Breaking Changes
**Mitigation**: Maintain backward compatibility, comprehensive testing

### Risk 4: False Positives
**Mitigation**: Use improved analyzer, pattern-aware detection

## Conclusion

Integrating the scripts/ directory tools as first-class pipeline tools will dramatically enhance the pipeline's capabilities. The analysis tools provide deep insights that can guide planning, improve code quality, aid debugging, and maintain architectural consistency.

The three-tier integration strategy (module import → executable fallback → hybrid) ensures maximum performance while maintaining flexibility and reliability.