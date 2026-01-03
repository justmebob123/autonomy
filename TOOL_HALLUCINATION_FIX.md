# 🔍 TOOL HALLUCINATION PROBLEM - ROOT CAUSE ANALYSIS

## The Problem

The AI is hallucinating tools that don't exist:
- `relationship` - SQLAlchemy ORM relationship
- `run` - Flask app.run() method  
- `_make_request` - HTTP request method
- `plot` - Matplotlib plotting function

## Root Cause

The AI is **CONFUSING PYTHON CODE WITH TOOL CALLS**.

### Example 1: `relationship` Hallucination
```python
# What the AI WANTS to write (correct):
from sqlalchemy.orm import relationship
posts = relationship("Post", back_populates="author")

# What the AI ACTUALLY does (wrong):
{
  "name": "relationship",
  "arguments": {
    "back_populates": "author"
  }
}
```

### Example 2: `run` Hallucination
```python
# What the AI WANTS to write (correct):
app.run(host="0.0.0.0", port=5000)

# What the AI ACTUALLY does (wrong):
{
  "name": "run",
  "arguments": {
    "host": "0.0.0.0"
  }
}
```

## Why This Happens

### 1. Tool Extraction is Too Aggressive
**Location**: `pipeline/client.py` line 500-600

The `_extract_all_json_blocks()` method extracts **ANY** JSON-like structure, including:
- Python function calls with keyword arguments
- Dictionary literals in code
- SQLAlchemy relationship definitions
- Flask method calls

### 2. AI is in "Tool Calling Mode"
The AI sees EVERYTHING as a potential tool call because:
- The prompt emphasizes tool calling
- The model is trained to call tools
- The extraction system validates ANY JSON as a tool

### 3. No Distinction Between Code and Tools
The system doesn't differentiate between:
- **File operation tools** (create_python_file, modify_python_file)
- **Python code constructs** (relationship(), app.run(), etc.)

## The Real Issue

**The AI is trying to write CODE CONTENT as TOOL CALLS.**

When creating a file with SQLAlchemy models, the AI should:
1. Call `create_python_file` tool
2. Put ALL Python code (including `relationship()`) INSIDE the `content` argument

Instead, the AI is:
1. Trying to call `relationship` as a separate tool
2. Treating Python code as tool calls

## Solutions

### Solution 1: Fix Tool Extraction (CRITICAL)
**Location**: `pipeline/client.py`

Add validation to ONLY extract known tools:

```python
def _extract_all_json_blocks(self, text: str) -> Optional[Dict]:
    # ... existing extraction code ...
    
    # CRITICAL: Validate tool name against known tools
    tool_name = data.get("name")
    if tool_name not in KNOWN_TOOLS:
        self.logger.debug(f"    ✗ Rejecting unknown tool: {tool_name}")
        continue
    
    # Only return if tool is known
    return result
```

### Solution 2: Enhance Coding Prompt (HIGH PRIORITY)
**Location**: `pipeline/prompts.py`

Add explicit guidance:

```python
CRITICAL: TOOLS vs CODE
========================
TOOLS are for FILE OPERATIONS:
✅ create_python_file - Create a new Python file
✅ modify_python_file - Modify existing Python file
✅ read_file - Read file content

CODE goes INSIDE the file content:
✅ relationship() - SQLAlchemy relationship (IN CODE)
✅ app.run() - Flask run method (IN CODE)
✅ requests.get() - HTTP request (IN CODE)

NEVER call Python code as tools!
NEVER call relationship(), run(), plot(), etc. as tools!
ALL Python code goes in the 'content' argument of create_python_file!

Example CORRECT usage:
{
  "name": "create_python_file",
  "arguments": {
    "filepath": "models/user.py",
    "content": "from sqlalchemy.orm import relationship\n\nclass User:\n    posts = relationship('Post', back_populates='author')"
  }
}

Example WRONG usage (DO NOT DO THIS):
{
  "name": "relationship",  ← WRONG! This is not a tool!
  "arguments": {"back_populates": "author"}
}
```

### Solution 3: Add Tool Whitelist (IMMEDIATE)
**Location**: `pipeline/client.py`

Create a whitelist of valid tools:

```python
# At top of file
VALID_CODING_TOOLS = {
    "create_python_file",
    "modify_python_file", 
    "full_file_rewrite",
    "read_file",
    "list_directory",
    "search_code",
    # ... all valid tools
}

def _extract_tool_call_from_text(self, text: str) -> Optional[Dict]:
    result = self._extract_all_json_blocks(text)
    
    if result:
        tool_name = result.get("function", {}).get("name")
        if tool_name not in VALID_CODING_TOOLS:
            self.logger.warning(f"🚫 Rejecting hallucinated tool: {tool_name}")
            return None
    
    return result
```

### Solution 4: Add Error Message for Hallucinated Tools
**Location**: `pipeline/handlers.py`

When unknown tool is detected, provide helpful error:

```python
if tool_name not in known_tools:
    error_msg = (
        f"Tool '{tool_name}' does not exist. "
        f"Did you mean to write Python code instead? "
        f"Python code like relationship(), run(), plot() should go "
        f"INSIDE the 'content' argument of create_python_file, "
        f"NOT as separate tool calls."
    )
    return {"success": False, "error": error_msg}
```

## Implementation Priority

1. **IMMEDIATE**: Add tool whitelist validation (Solution 3)
2. **HIGH**: Enhance coding prompt (Solution 2)
3. **MEDIUM**: Fix tool extraction (Solution 1)
4. **LOW**: Add helpful error messages (Solution 4)

## Expected Behavior After Fix

### Before Fix (Current - WRONG):
```
AI: Calling tool 'relationship' with args {"back_populates": "author"}
System: ERROR - Unknown tool 'relationship'
Task: FAILED
```

### After Fix (Expected - CORRECT):
```
AI: Calling tool 'create_python_file' with content containing relationship()
System: ✓ File created successfully
Task: COMPLETED
```

## Testing

After implementing fixes:
1. Run coding phase on database model task
2. Verify AI calls `create_python_file` (not `relationship`)
3. Verify Python code is in `content` argument
4. Verify no hallucinated tool errors

---

**Status**: IDENTIFIED - Ready for implementation
**Severity**: CRITICAL - Blocking all coding tasks
**Impact**: 100% of coding tasks failing due to hallucinated tools