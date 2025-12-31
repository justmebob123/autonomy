# Result Structure Normalization Analysis

## Goal
Normalize ALL analysis tool result structures to be consistent across the entire pipeline.

## Current Analysis Tools

### 1. Architecture Validation
**Handler**: `_handle_validate_architecture`
**Returns**:
```python
{
    "tool": "validate_architecture",
    "success": True,
    "result": {
        "violations": [
            {
                'type': 'location',
                'severity': 'high',
                'file': 'path/to/file.py',
                'description': '...',
                'expected': '...',
                'actual': '...',
                'recommendation': '...'
            }
        ],
        "total_violations": 5,
        "by_severity": {'critical': 1, 'high': 2, 'medium': 1, 'low': 1}
    },
    "report": "...",
    "report_file": "ARCHITECTURE_VALIDATION_REPORT.md"
}
```
**Status**: ✅ GOOD - Uses consistent structure

---

### 2. Duplicate Detection
**Handler**: `_handle_detect_duplicate_implementations`
**Returns**:
```python
{
    "tool": "detect_duplicate_implementations",
    "success": True,
    "result": {
        "duplicate_sets": [
            {
                'files': ['file1.py', 'file2.py'],
                'similarity': 0.85,
                'common_lines': 31,
                ...
            }
        ],
        "total_duplicates": 1,
        "estimated_reduction": 31
    }
}
```
**Status**: ✅ GOOD - Uses consistent structure

---

### 3. Complexity Analysis
**Handler**: `_handle_analyze_complexity`
**Returns**:
```python
{
    "tool": "analyze_complexity",
    "success": True,
    "result": {
        "functions": [...],
        "critical_functions": [...],
        "high_complexity_functions": [...],
        "total_functions": 356,
        "average_complexity": 2.21,
        "critical_count": 0,
        "high_count": 5,
        ...
    },
    "report": "...",
    "report_file": "COMPLEXITY_REPORT.txt"
}
```
**Status**: ✅ GOOD - Uses consistent structure

---

### 4. Dead Code Detection
**Handler**: `_handle_detect_dead_code`
**Returns**:
```python
{
    "tool": "detect_dead_code",
    "success": True,
    "result": {
        "unused_functions": [
            {'name': 'func_name', 'file': 'path.py', 'line': 123}
        ],
        "unused_methods": [
            {'name': 'method_name', 'file': 'path.py', 'line': 456}
        ],
        "unused_imports": {...},
        "summary": {
            "total_unused_functions": 32,
            "total_unused_methods": 87,
            "total_unused_imports": 300
        }
    },
    "report": "...",
    "report_file": "DEAD_CODE_REPORT.txt"
}
```
**Status**: ✅ GOOD - Uses consistent structure with summary

---

### 5. Integration Gaps
**Handler**: `_handle_find_integration_gaps`
**Returns**:
```python
{
    "tool": "find_integration_gaps",
    "success": True,
    "result": {
        "unused_classes": [
            {'name': 'ClassName', 'file': 'path.py', 'line': 123}
        ],
        "classes_with_unused_methods": {
            'ClassName': ['method1', 'method2']
        },
        "imported_but_unused": {...},
        "summary": {
            "total_unused_classes": 36,
            "total_classes_with_gaps": 29,
            "total_unused_imports": 300
        }
    },
    "report": "...",
    "report_file": "INTEGRATION_GAP_REPORT.txt"
}
```
**Status**: ✅ GOOD - Uses consistent structure with summary

---

### 6. Integration Conflicts
**Handler**: `_handle_detect_integration_conflicts` (CUSTOM)
**Returns**:
```python
{
    "tool": "detect_integration_conflicts",
    "success": True,
    "result": {
        "conflicts": [
            IntegrationConflict(  # ← DATACLASS!
                conflict_type='duplicate_implementation',
                severity='high',
                files=['file1.py', 'file2.py'],
                description='...',
                recommendation='...',
                details={}
            )
        ],
        "total_conflicts": 114
    }
}
```
**Status**: ⚠️ INCONSISTENT - Returns dataclasses instead of dicts
**Fix Needed**: Convert dataclasses to dicts in handler

---

### 7. Call Graph
**Handler**: `_handle_generate_call_graph`
**Returns**:
```python
{
    "tool": "generate_call_graph",
    "success": True,
    "result": {
        "functions": [...],
        "calls": [...],
        "total_functions": 328,
        "total_calls": 1093,
        ...
    },
    "report": "...",
    "report_file": "CALL_GRAPH_REPORT.txt",
    "graph_file": "call_graph.dot"
}
```
**Status**: ✅ GOOD - Uses consistent structure

---

### 8. Bug Detection
**Handler**: `_handle_find_bugs`
**Returns**:
```python
{
    "tool": "find_bugs",
    "success": True,
    "result": {
        "bugs": [
            {
                'type': 'use_before_def',
                'severity': 'high',
                'file': 'path.py',
                'line': 123,
                'description': '...',
                'recommendation': '...'
            }
        ],
        "total_bugs": 15,
        "by_severity": {'critical': 2, 'high': 5, 'medium': 8}
    },
    "report": "...",
    "report_file": "BUG_DETECTION_REPORT.txt"
}
```
**Status**: ✅ GOOD - Uses consistent structure

---

### 9. Anti-pattern Detection
**Handler**: `_handle_detect_antipatterns`
**Returns**:
```python
{
    "tool": "detect_antipatterns",
    "success": True,
    "result": {
        "antipatterns": [
            {
                'name': 'god_class',
                'severity': 'medium',
                'file': 'path.py',
                'line': 123,
                'description': '...',
                'recommendation': '...'
            }
        ],
        "total_antipatterns": 8,
        "by_type": {'god_class': 2, 'long_method': 3, ...}
    },
    "report": "...",
    "report_file": "ANTIPATTERN_REPORT.txt"
}
```
**Status**: ✅ GOOD - Uses consistent structure

---

## Normalization Standard

### Standard Result Structure:
```python
{
    "tool": "tool_name",
    "success": True/False,
    "result": {
        "items": [  # Main list of issues/findings
            {
                'type': '...',  # Type of issue
                'severity': 'critical/high/medium/low',  # Severity level
                'file': 'path/to/file.py',  # Affected file
                'line': 123,  # Line number (optional)
                'name': '...',  # Name of item (optional)
                'description': '...',  # Human-readable description
                'recommendation': '...',  # How to fix (optional)
                'details': {}  # Additional details (optional)
            }
        ],
        "summary": {  # Summary statistics
            "total_items": 10,
            "by_severity": {'critical': 1, 'high': 3, 'medium': 4, 'low': 2},
            "by_type": {...}
        }
    },
    "report": "...",  # Human-readable report text
    "report_file": "REPORT_FILE.txt"  # Report file path
}
```

---

## Issues Found

### Issue 1: Integration Conflicts Returns Dataclasses
**Problem**: Handler returns `IntegrationConflict` dataclass objects instead of dicts
**Impact**: Code must use `asdict()` to convert, inconsistent with other tools
**Fix**: Convert dataclasses to dicts in the handler itself

### Issue 2: Inconsistent Key Names
**Problem**: Different tools use different key names for similar data
- Some use `items`, some use specific names (`bugs`, `antipatterns`, `conflicts`)
- Some use `total_items`, some use `total_bugs`, `total_conflicts`, etc.

**Fix Options**:
1. **Keep specific names** (current approach) - More descriptive but inconsistent
2. **Normalize to generic names** - Consistent but less descriptive

**Recommendation**: Keep specific names but ensure ALL return dicts, not dataclasses

---

## Action Plan

### Priority 1: Fix Integration Conflicts Handler
Convert dataclasses to dicts in the handler:
```python
def _handle_detect_integration_conflicts(self, args: Dict) -> Dict:
    ...
    from dataclasses import asdict
    
    return {
        "tool": "detect_integration_conflicts",
        "success": True,
        "result": {
            "conflicts": [asdict(c) for c in conflict_analysis.conflicts],  # ← Convert here!
            "total_conflicts": len(conflict_analysis.conflicts)
        }
    }
```

### Priority 2: Verify All Handlers Return Dicts
Check every handler to ensure they return plain dicts, not dataclasses or custom objects

### Priority 3: Document Standard Structure
Create clear documentation of expected result structure for each tool

---

## Status

- ✅ 8/9 tools return consistent dict structures
- ⚠️ 1/9 tools (integration conflicts) returns dataclasses
- 🔧 Fix needed: Convert dataclasses in handler