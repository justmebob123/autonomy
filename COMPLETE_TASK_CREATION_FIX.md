# Complete Task Creation Fix - All Missing analysis_data

## Issues Found

### 1. Dead Code Tasks (Line 861) - ❌ MISSING analysis_data
```python
task = manager.create_task(
    issue_type=RefactoringIssueType.DEAD_CODE,
    title=f"Remove dead code: {item.get('name', 'unknown')}",
    description=f"Dead code: {item.get('name', 'unknown')}",
    # NO analysis_data!
)
```

### 2. Architecture Violation Tasks (Line 896) - ❌ MISSING analysis_data
```python
task = manager.create_task(
    issue_type=issue_type_map.get(violation['type'], RefactoringIssueType.ARCHITECTURE),
    title=f"Architecture violation: {violation['type']}",
    description=violation['description'],
    # NO analysis_data!
)
```

### 3. Anti-pattern Tasks (Line 1011) - ❌ MISSING analysis_data
```python
task = manager.create_task(
    issue_type=RefactoringIssueType.ARCHITECTURE,
    title=f"Anti-pattern: {pattern.get('name', 'Unknown')}",
    description=f"Anti-pattern: {pattern.get('name', 'Unknown')}",
    # NO analysis_data!
)
```

### 4. Circular Import Tasks (Line 1141) - ❌ MISSING analysis_data
```python
task = manager.create_task(
    issue_type=RefactoringIssueType.ARCHITECTURE,
    title=f"Circular import detected",
    description=f"Circular import: {' → '.join(cycle.get('cycle', []))}",
    # NO analysis_data!
)
```

## Solution

Add analysis_data to ALL four task types with proper formatting.

### Fix 1: Dead Code
```python
analysis_data={
    'type': 'dead_code',
    'name': item.get('name', 'unknown'),
    'file': item.get('file', ''),
    'reason': item.get('reason', 'unused'),
    'action': 'cleanup_redundant_files'
}
```

### Fix 2: Architecture Violations
```python
analysis_data={
    'type': 'architecture_violation',
    'violation_type': violation['type'],
    'file': violation['file'],
    'description': violation['description'],
    'severity': violation.get('severity', 'medium'),
    'action': 'move_file or create_issue_report'
}
```

### Fix 3: Anti-patterns
```python
analysis_data={
    'type': 'antipattern',
    'pattern_name': pattern.get('name', 'Unknown'),
    'file': pattern.get('file', ''),
    'description': pattern.get('description', ''),
    'severity': pattern.get('severity', 'medium'),
    'suggestion': pattern.get('suggestion', ''),
    'action': 'create_issue_report'
}
```

### Fix 4: Circular Imports
```python
analysis_data={
    'type': 'circular_import',
    'cycle': cycle.get('cycle', []),
    'files': cycle.get('files', []),
    'description': f"Circular import: {' → '.join(cycle.get('cycle', []))}",
    'action': 'move_file or restructure_directory'
}
```

## Enhanced _format_analysis_data()

Need to add handlers for these new types:
- DEAD_CODE
- ARCHITECTURE (violations, anti-patterns, circular imports)

## Expected Impact

After fix:
- ✅ All tasks have structured analysis_data
- ✅ AI knows exactly what to do
- ✅ Clear action guidance
- ✅ No more "Unknown" titles
- ✅ No more requesting developer review for simple issues