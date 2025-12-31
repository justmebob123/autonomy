# Filename Normalization Analysis

## Problem Statement

The AI created a file with literal placeholder text in the filename:
```
storage/migrations/versions/<version>_projects_table.py
```

This reveals a critical gap in our validation system - we need to detect and prevent erroneous filename conventions before files are created.

## Categories of Problematic Filenames

### 1. **Placeholder Text** (CRITICAL - Current Issue)
- `<version>`, `<timestamp>`, `<name>`, etc.
- **Detection**: Angle brackets `< >`
- **Action**: MUST be replaced with actual values before file creation
- **Examples**:
  - `<version>_migration.py` → `001_migration.py`
  - `<timestamp>_backup.sql` → `20240101_120000_backup.sql`

### 2. **Version Iterators** (COMMON)
- `file (1).py`, `file (2).py`, `file_v2.py`
- **Detection**: Parentheses with numbers, version suffixes
- **Action**: Consolidate or use proper versioning
- **Examples**:
  - `utils (1).py`, `utils (2).py` → Should be one `utils.py`
  - `config_v1.py`, `config_v2.py` → Use git history instead

### 3. **Parenthetical Meaning** (NUANCED)
- `chapter_01_(introduction).md`
- `module_(core_functionality).py`
- **Detection**: Parentheses with descriptive text
- **Action**: May be intentional, needs AI judgment
- **Examples**:
  - `01_(setup).md` - Could be valid chapter structure
  - `test_(edge_cases).py` - Could be valid test organization

### 4. **Special Characters** (VARIES)
- Spaces: `my file.py` → `my_file.py`
- Multiple underscores: `file___name.py` → `file_name.py`
- Mixed separators: `file-name_v2.py` → `file_name_v2.py`

## Detection Strategy

### Phase 1: Pre-Creation Validation (IMMEDIATE)
Before any file is created, validate the filename:

```python
def validate_filename(filepath: str) -> tuple[bool, str, list[str]]:
    """
    Validate filename for common issues.
    
    Returns:
        (is_valid, normalized_path, warnings)
    """
    filename = os.path.basename(filepath)
    warnings = []
    
    # CRITICAL: Detect placeholder text
    if '<' in filename or '>' in filename:
        return (False, filepath, ["CRITICAL: Placeholder text detected in filename. Must be replaced with actual value."])
    
    # Detect version iterators
    if re.search(r'\(\d+\)', filename):
        warnings.append("Version iterator detected - consider consolidation")
    
    # Detect parenthetical meaning
    if '(' in filename and ')' in filename and not re.search(r'\(\d+\)', filename):
        warnings.append("Parenthetical text detected - verify intentional naming")
    
    # Detect spaces
    if ' ' in filename:
        warnings.append("Spaces in filename - should use underscores")
    
    # Detect multiple consecutive underscores
    if '__' in filename:
        warnings.append("Multiple consecutive underscores detected")
    
    return (True, filepath, warnings)
```

### Phase 2: AI Consultation (WHEN NEEDED)
When warnings are detected, consult AI with context:

```python
def consult_ai_on_filename(filepath: str, warnings: list[str], directory_structure: dict) -> str:
    """
    Ask AI to resolve filename issues with full context.
    
    Args:
        filepath: The proposed file path
        warnings: List of detected issues
        directory_structure: Existing files in the directory
    
    Returns:
        Corrected filepath
    """
    prompt = f"""
    Filename Issue Detected:
    
    Proposed file: {filepath}
    Warnings: {', '.join(warnings)}
    
    Existing files in directory:
    {format_directory_structure(directory_structure)}
    
    Please provide the correct filename that:
    1. Follows project naming conventions
    2. Avoids duplication
    3. Uses appropriate separators (underscores preferred)
    4. Replaces any placeholder text with actual values
    5. Maintains semantic meaning
    
    Return ONLY the corrected filename, no explanation.
    """
    
    return call_ai(prompt)
```

### Phase 3: Post-Creation Detection (REFACTORING)
During refactoring phase, detect existing problematic files:

```python
def detect_filename_issues(project_root: str) -> list[dict]:
    """
    Scan project for filename issues.
    
    Returns:
        List of issues with file paths and recommendations
    """
    issues = []
    
    for root, dirs, files in os.walk(project_root):
        for filename in files:
            filepath = os.path.join(root, filename)
            is_valid, _, warnings = validate_filename(filepath)
            
            if not is_valid or warnings:
                issues.append({
                    'filepath': filepath,
                    'is_critical': not is_valid,
                    'warnings': warnings,
                    'recommendation': generate_recommendation(filepath, warnings)
                })
    
    return issues
```

## Implementation Plan

### 1. **Immediate Fix** (Current Issue)
- Add pre-creation validation to `create_python_file` tool
- Block file creation if placeholder text detected
- Force AI to provide actual values

### 2. **Enhanced Validation** (Short Term)
- Add filename validation to all file creation tools
- Implement AI consultation for ambiguous cases
- Add directory structure context to AI prompts

### 3. **Refactoring Integration** (Medium Term)
- Add filename issue detection to refactoring phase
- Create automated normalization for simple cases
- Generate reports for complex cases requiring developer input

### 4. **Prevention** (Long Term)
- Enhance AI prompts to avoid placeholder text
- Add examples of proper filename conventions
- Implement project-specific naming rules

## Specific Rules by Symbol

### Angle Brackets `< >`
- **ALWAYS CRITICAL**: Must be replaced before file creation
- **Never valid** in filenames (filesystem restriction on Windows)
- **Action**: Block creation, force AI to provide actual value

### Parentheses `( )`
- **With numbers**: Likely version iterator → Consolidate
- **With text**: Could be intentional → AI judgment needed
- **Context matters**: Compare with existing files

### Spaces ` `
- **Generally discouraged**: Use underscores instead
- **Action**: Auto-normalize to underscores
- **Exception**: Some documentation systems allow spaces

### Underscores `_`
- **Single**: Preferred separator
- **Multiple consecutive**: Normalize to single
- **Action**: Auto-normalize `__+` to `_`

### Hyphens `-`
- **Valid**: Common in package names
- **Mixed with underscores**: Choose one convention
- **Action**: Normalize to project convention

## Edge Cases

### Migration Files
```
# WRONG: <version>_projects_table.py
# RIGHT: 001_projects_table.py
# OR:    20240101_120000_projects_table.py
```

### Test Files
```
# ACCEPTABLE: test_(edge_cases).py (if project convention)
# PREFERRED:  test_edge_cases.py
```

### Chapter/Section Files
```
# ACCEPTABLE: 01_(introduction).md (if book/docs structure)
# PREFERRED:  01_introduction.md
```

### Backup Files
```
# WRONG: config (1).py
# RIGHT: config.py (use git history)
# OR:    config_backup_20240101.py (if truly needed)
```

## Recommendations

1. **Implement pre-creation validation immediately** - This prevents the current issue
2. **Add AI consultation for ambiguous cases** - Provides context-aware decisions
3. **Create project-specific naming rules** - Define conventions in ARCHITECTURE.md
4. **Enhance refactoring phase** - Detect and fix existing issues
5. **Improve AI prompts** - Include filename examples and rules

## Success Metrics

- **Zero placeholder text** in created filenames
- **< 5% false positives** in filename validation
- **AI consultation rate** < 10% (most cases auto-resolved)
- **Refactoring detection** finds all existing issues