# Filename Validation AI Engagement Enhancement

## Problem

The initial implementation of filename validation was too rigid - it simply **blocked** file creation when placeholder text was detected, returning an error without engaging the AI to resolve the issue.

This approach was incorrect because:
1. It didn't give the AI a chance to determine the correct filename
2. It didn't provide context about existing files
3. It treated the AI as passive rather than active in problem-solving

## Solution

Enhanced the filename validation system to **engage the AI** in resolving filename issues:

### 1. Contextual Validation

**Before:**
```python
# Just validate and block
is_valid, issues = validator.validate(filepath)
if issues:
    return error  # Dead end
```

**After:**
```python
# Validate with context about existing files
context = self._build_validation_context(filepath)
is_valid, issues = validator.validate(filepath, context)
if issues:
    # Build detailed context for AI to resolve
    issue_context = self._build_filename_issue_context(issues, task)
    # Add to error context so AI sees it in next iteration
    # Return with requires_ai_resolution flag
```

### 2. Enhanced Suggestions

**Before:**
```
Suggestion: NEEDS_AI_CONSULTATION: <version>_projects_table.py
```

**After:**
```
Suggestion: 003_projects_table.py (existing versions: 001, 002)
```

The validator now:
- Scans the target directory for existing files
- Extracts version numbers from existing migration files
- Suggests the next sequential version number
- Provides context about what already exists

### 3. Detailed Error Context

When validation fails, the AI receives:

```
🚨 FILENAME VALIDATION FAILED

You attempted to create files with problematic filenames.
Please provide corrected filenames and try again.

## Issue 1: storage/migrations/versions/<version>_projects_table.py

**Problem**: Placeholder text detected in filename
**Tool**: create_python_file
**Pattern Detected**: `<[^>]+>`

**Existing files in directory**:
  - 001_initial.py
  - 002_users.py

**Suggested correction**: `003_projects_table.py (existing versions: 001, 002)`

## How to Fix

For migration files:
- Use actual version numbers: `001_projects_table.py`, `002_users_table.py`
- Check existing files to determine next version number

For timestamped files:
- Use actual timestamps: `backup_20240101_120000.sql`
- Format: YYYYMMDD_HHMMSS

For general files:
- Use descriptive names: `user_authentication.py`
- Use underscores, not spaces: `my_file.py` not `my file.py`
- Avoid version suffixes: `config.py` not `config_v2.py`

**IMPORTANT**: Replace ALL placeholder text with actual values before retrying.
```

### 4. AI Workflow

**Old workflow (blocking):**
1. AI creates tool call with `<version>` in filename
2. Validation fails
3. Error returned
4. Task fails ❌

**New workflow (engaging):**
1. AI creates tool call with `<version>` in filename
2. Validation fails
3. Detailed context provided to AI showing:
   - What's wrong
   - Existing files in directory
   - Suggested correction (e.g., "003_projects_table.py")
   - How to fix it
4. AI sees error context in next iteration
5. AI determines correct filename based on context
6. AI retries with corrected filename
7. Validation passes
8. File created successfully ✅

## Implementation Details

### New Methods in `coding.py`

#### `_build_validation_context(filepath: str) -> Dict`
Builds context for filename validation including:
- Target directory path
- List of existing files in directory
- Used by validator to suggest version numbers

#### `_build_filename_issue_context(issues: List[Dict], task: TaskState) -> str`
Builds detailed context about filename issues for AI including:
- What's wrong with each filename
- Existing files in the directory
- Suggested corrections
- Examples of correct filenames
- Step-by-step fix instructions

### Enhanced Validator Methods

#### `_suggest_placeholder_replacement(filename: str, context: Optional[Dict]) -> str`
Now provides intelligent suggestions:
- For migrations: "003_projects_table.py (existing versions: 001, 002)"
- For empty directories: "001_projects_table.py (no existing versions, starting with 001)"
- For timestamps: Actual current timestamp
- For other placeholders: Descriptive examples

### Updated Prompts

Enhanced `get_coding_prompt()` with clearer guidance:
```
IF VALIDATION FAILS:
- You will receive detailed error context
- Check existing files in the directory
- Determine the correct filename based on context
- Retry with the corrected filename
- DO NOT ask for clarification - determine the correct name yourself
```

## Testing

### Test Case 1: Migration with Existing Files
```python
context = {
    'directory': 'storage/migrations/versions',
    'existing_files': ['001_initial.py', '002_users.py']
}

is_valid, issues = validator.validate(
    'storage/migrations/versions/<version>_projects_table.py', 
    context
)

# Result:
# Valid: False
# Suggestion: 003_projects_table.py (existing versions: 001, 002)
```

### Test Case 2: Migration with No Existing Files
```python
context = {
    'directory': 'storage/migrations/versions',
    'existing_files': []
}

is_valid, issues = validator.validate(
    'storage/migrations/versions/<version>_projects_table.py', 
    context
)

# Result:
# Valid: False
# Suggestion: 001_projects_table.py (no existing versions, starting with 001)
```

## Benefits

1. **AI Autonomy**: AI can resolve filename issues without human intervention
2. **Context-Aware**: Suggestions based on actual project state
3. **Educational**: AI learns correct patterns through detailed feedback
4. **Efficient**: No blocking - AI iterates to solution
5. **Intelligent**: Suggestions consider existing files and conventions

## Example Scenario

**User Task**: "Create database schema and migrations for projects table"

**AI First Attempt**:
```python
create_python_file(
    filepath="storage/migrations/versions/<version>_projects_table.py",
    code="..."
)
```

**System Response**:
```
❌ Filename validation failed

Problem: Placeholder text detected in filename
Existing files: 001_initial.py, 002_users.py
Suggested correction: 003_projects_table.py (existing versions: 001, 002)

Please retry with the corrected filename.
```

**AI Second Attempt**:
```python
create_python_file(
    filepath="storage/migrations/versions/003_projects_table.py",
    code="..."
)
```

**System Response**:
```
✅ File created successfully
```

## Conclusion

The enhanced filename validation system now **engages the AI** as an active problem-solver rather than passively blocking operations. The AI receives rich context, intelligent suggestions, and clear guidance to determine the correct filename and retry successfully.

This aligns with the autonomous agent philosophy - the AI should be empowered to resolve issues independently with appropriate context and guidance.