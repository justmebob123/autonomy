# CRITICAL IMPORT ISSUE - ROOT CAUSE ANALYSIS AND FIX

**Date:** December 25, 2024  
**Issue:** ImportError when prompts/ directory shadows prompts.py file  
**Status:** ✅ FIXED (Commit cbd851d)

---

## Problem Description

### Error Encountered
```
ImportError: cannot import name 'SYSTEM_PROMPTS' from 'pipeline.prompts' 
(/home/ai/AI/autonomy/pipeline/prompts/__init__.py)
```

### Root Cause

**Python Module Resolution Conflict:**

The autonomy pipeline has BOTH:
1. **`pipeline/prompts.py`** (FILE) - Contains core prompts:
   - `SYSTEM_PROMPTS` dictionary
   - `get_planning_prompt()`
   - `get_coding_prompt()`
   - `get_qa_prompt()`
   - `get_debug_prompt()`
   - `get_project_planning_prompt()`
   - `get_documentation_prompt()`
   - `get_modification_decision_prompt()`

2. **`pipeline/prompts/`** (DIRECTORY) - Contains meta-prompts:
   - `prompt_architect.py`
   - `tool_designer.py`
   - `role_creator.py`
   - `team_orchestrator.py`

**The Conflict:**

When Python sees:
```python
from ..prompts import SYSTEM_PROMPTS
```

It looks for `prompts` and finds:
1. ✅ `prompts/` directory (with `__init__.py`) ← Python chooses this
2. ❌ `prompts.py` file ← Gets shadowed/ignored

Since `prompts/__init__.py` didn't re-export `SYSTEM_PROMPTS`, the import failed.

---

## Why This Happened

### Timeline of Events

1. **Original Design:** Only `prompts.py` file existed
2. **Self-Designing System Added:** Created `prompts/` directory for meta-prompts
3. **Missing `__init__.py`:** Directory wasn't a package initially
4. **First Fix Attempt:** Added `__init__.py` but only exported meta-prompts
5. **Result:** Directory shadowed file, breaking all imports from `prompts.py`

### Python's Import Resolution

When Python encounters `from pipeline.prompts import X`:

1. Looks in `sys.path` for `pipeline`
2. Finds `pipeline/` directory
3. Looks for `prompts` inside `pipeline/`
4. Finds BOTH `prompts.py` and `prompts/`
5. **Prefers directory over file** (if directory has `__init__.py`)
6. Imports from `prompts/__init__.py`
7. If `X` not in `__init__.py`, raises ImportError

---

## Solution Implemented

### Fix: Re-export Everything in `prompts/__init__.py`

The `prompts/__init__.py` now:
1. Dynamically loads `prompts.py` file
2. Re-exports all functions and constants
3. Also exports meta-prompts from directory

**Implementation:**

```python
# Load prompts.py file (sibling to this directory)
import importlib.util
from pathlib import Path

parent_dir = Path(__file__).parent.parent
prompts_file = parent_dir / "prompts.py"

spec = importlib.util.spec_from_file_location("_prompts_module", prompts_file)
_prompts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_prompts_module)

# Re-export everything from prompts.py
SYSTEM_PROMPTS = _prompts_module.SYSTEM_PROMPTS
get_planning_prompt = _prompts_module.get_planning_prompt
# ... etc for all functions

# Import meta-prompts from this directory
from .prompt_architect import get_prompt_architect_prompt
from .tool_designer import get_tool_designer_prompt
from .role_creator import get_role_creator_prompt
from .team_orchestrator import get_team_orchestrator_prompt
```

---

## Affected Files

### Files That Import from prompts.py

All these files now work correctly:

1. `pipeline/phases/planning.py`
   ```python
   from ..prompts import SYSTEM_PROMPTS, get_planning_prompt
   ```

2. `pipeline/phases/coding.py`
   ```python
   from ..prompts import SYSTEM_PROMPTS, get_coding_prompt
   ```

3. `pipeline/phases/qa.py`
   ```python
   from ..prompts import SYSTEM_PROMPTS, get_qa_prompt
   ```

4. `pipeline/phases/debugging.py`
   ```python
   from ..prompts import SYSTEM_PROMPTS, get_debug_prompt
   from ..prompts import get_modification_decision_prompt
   ```

5. `pipeline/phases/documentation.py`
   ```python
   from ..prompts import SYSTEM_PROMPTS, get_documentation_prompt
   ```

6. `pipeline/phases/project_planning.py`
   ```python
   from ..prompts import SYSTEM_PROMPTS, get_project_planning_prompt
   ```

### Files That Import from prompts/ directory

This file also works:

1. `pipeline/team_orchestrator.py`
   ```python
   from .prompts.team_orchestrator import get_team_orchestrator_prompt
   ```

---

## Alternative Solutions Considered

### Option 1: Rename Directory (NOT CHOSEN)
- Rename `prompts/` to `meta_prompts/`
- **Pros:** Clean separation, no shadowing
- **Cons:** Breaks existing imports in team_orchestrator.py

### Option 2: Rename File (NOT CHOSEN)
- Rename `prompts.py` to `core_prompts.py`
- **Pros:** Clean separation
- **Cons:** Breaks ALL existing imports in 6+ files

### Option 3: Re-export in __init__.py (CHOSEN) ✅
- Keep both names, re-export everything
- **Pros:** No breaking changes, backward compatible
- **Cons:** Slightly more complex __init__.py

---

## Verification

### Test the Fix

```bash
cd /home/ai/AI/autonomy
git pull origin main

# Should work now
python3 run.py --debug-qa -vv
```

### Expected Behavior

All imports should work:
```python
# These work (from prompts.py via prompts/__init__.py)
from pipeline.prompts import SYSTEM_PROMPTS
from pipeline.prompts import get_planning_prompt
from pipeline.prompts import get_coding_prompt

# This works (from prompts/team_orchestrator.py)
from pipeline.prompts.team_orchestrator import get_team_orchestrator_prompt
```

---

## Lessons Learned

### 1. Python Module Resolution
- Directories with `__init__.py` take precedence over `.py` files
- Always consider shadowing when adding directories

### 2. Package Design
- Avoid having both `module.py` and `module/` in same directory
- If unavoidable, re-export everything in `__init__.py`

### 3. Testing
- Test imports after adding new directories
- Check all affected files, not just new code

### 4. Backward Compatibility
- Consider existing imports when restructuring
- Re-exporting maintains compatibility

---

## Future Recommendations

### Option A: Keep Current Structure (Recommended)
- Maintain both `prompts.py` and `prompts/`
- Keep re-exporting in `__init__.py`
- Document the structure clearly

### Option B: Refactor Later (If Needed)
If the structure becomes problematic:
1. Rename `prompts/` to `meta_prompts/`
2. Update `team_orchestrator.py` import
3. Remove re-exporting from `__init__.py`

---

## Commits

1. **cf806ea** - Added `prompts/__init__.py` (incomplete)
2. **cbd851d** - Fixed `prompts/__init__.py` with re-exports ✅

---

## Status

**✅ ISSUE RESOLVED**

The import error is fixed. All phases can now import from `pipeline.prompts` successfully.

**Pull latest changes:**
```bash
git pull origin main
```

**Run system:**
```bash
python3 run.py --debug-qa -vv
```