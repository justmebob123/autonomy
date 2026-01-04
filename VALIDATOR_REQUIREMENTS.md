# Validator Requirements to Catch All Runtime Errors

## Error 1: UnboundLocalError - Variable Used Before Definition

**Error:** `task` used at line 172 but not defined until line 245

**What's Needed:**
- Track variable definitions (assignments) in each function
- Track variable usages (reads) in each function
- For each usage, verify there's a definition before it in execution order
- Handle control flow (if/else, loops, try/except)

**Current Gap:** No validator tracks variable initialization order

---

## Error 2: NameError - Missing Imports

**Error:** `Message` and `MessagePriority` used but not imported

**What's Needed:**
- Track ALL name usages in each file
- Track ALL imports in each file
- For each name usage, verify it's either:
  1. Imported
  2. Defined locally (function, class, variable)
  3. A builtin
- Handle conditional imports (inside if blocks)

**Current Gap:** Import validator only checks if imported names exist, not if all used names are imported

---

## Error 3: TypeError - Non-Serializable Objects

**Error:** Path objects in dictionary that gets JSON serialized

**What's Needed:**
- Identify all dictionaries that get serialized (passed to json.dumps, to_dict, etc.)
- Track what gets stored in these dictionaries
- Verify all values are JSON-serializable types:
  - str, int, float, bool, None
  - list, dict (recursively)
  - NOT: Path, datetime, custom objects
- Warn about type mismatches

**Current Gap:** No validator checks serialization compatibility

---

## Implementation Plan

### 1. Variable Initialization Validator (NEW)
**File:** `autonomy/pipeline/analysis/variable_initialization_validator.py`

**Features:**
- Build control flow graph for each function
- Track variable definitions and usages
- Detect use-before-definition
- Handle conditional assignments

### 2. Enhanced Import Validator (UPGRADE)
**File:** `autonomy/pipeline/analysis/import_validator.py`

**Features:**
- Track ALL name usages (not just imports)
- Verify all used names are imported or defined
- Handle builtin names
- Handle conditional imports

### 3. Serialization Validator (NEW)
**File:** `autonomy/pipeline/analysis/serialization_validator.py`

**Features:**
- Identify serialization points (json.dumps, to_dict, etc.)
- Track data flow to these points
- Verify all values are JSON-serializable
- Warn about Path, datetime, custom objects

---

## Success Criteria

After implementation, running these validators should produce:

### Error 1: UnboundLocalError
```
❌ pipeline/phases/refactoring.py:172
   Variable 'task' used before definition
   Used at line 172, first defined at line 245
```

### Error 2: NameError
```
❌ pipeline/phases/refactoring.py:431
   Name 'Message' is not defined
   Not imported and not defined locally

❌ pipeline/phases/refactoring.py:431
   Name 'MessagePriority' is not defined
   Not imported and not defined locally
```

### Error 3: TypeError
```
❌ pipeline/phases/refactoring.py:595
   Non-serializable value in analysis_data
   'affected_files' may contain Path objects
   Recommend: [str(f) for f in impact.affected_files]
```

---

## Timeline

1. **Variable Initialization Validator** - 2-3 hours
2. **Enhanced Import Validator** - 1-2 hours  
3. **Serialization Validator** - 2-3 hours

**Total:** 5-8 hours of focused development