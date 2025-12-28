# Fix for Empty Tool Names in QA Phase

## Problem
The QA phase is stuck in an infinite loop because the model is returning tool calls with empty names:

```json
{
  "function": {
    "name": "",  // Empty!
    "arguments": {"filepath": "..."}
  }
}
```

## Root Cause
The model (qwen2.5:14b) is not properly formatting tool calls. It's providing arguments but leaving the name field empty.

## Solution Options

### Option 1: Infer Tool Name from Arguments (RECOMMENDED)
When tool name is empty, infer it from the arguments:
- If has `issue_type`, `description`, `line_number` → `report_issue`
- If has only `filepath` and `notes` → `approve_code`
- If has only `filepath` → `approve_code`

### Option 2: Force Approval on Empty Tool Name
Treat empty tool names as implicit approval to break the loop.

### Option 3: Better Model Prompting
Enhance the QA phase prompt to be more explicit about tool calling format.

### Option 4: Use FunctionGemma for Tool Name Extraction
Use the FunctionGemma mediator to extract the correct tool name from malformed calls.

## Recommended Fix

Implement Option 1 with fallback to Option 2:

```python
def _infer_tool_name_from_args(self, args: Dict) -> str:
    """Infer tool name from arguments when name is empty"""
    
    # Check for report_issue indicators
    if any(key in args for key in ['issue_type', 'description', 'line_number', 'suggested_fix']):
        return 'report_issue'
    
    # Check for approve_code indicators  
    if 'filepath' in args and ('notes' in args or len(args) <= 2):
        return 'approve_code'
    
    # Default to approve_code to break the loop
    return 'approve_code'
```

This allows the QA phase to continue even when the model provides malformed tool calls.