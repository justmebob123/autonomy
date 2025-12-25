# FunctionGemma Integration Plan

## Current State
FunctionGemma is only used as a "last resort" fallback when JSON parsing fails.

## Problem
From the user's output, the AI IS calling `modify_python_file`, but:
1. The tool call structure is malformed (showing as "unknown")
2. The `original_code` doesn't match the file exactly
3. The modification fails with "Original code not found"

## Solution: Use FunctionGemma Proactively

### Option 1: Pre-validate Tool Calls
Before executing ANY tool call, pass it through FunctionGemma to:
- Validate the structure
- Fix malformed JSON
- Ensure all required parameters are present

### Option 2: Use FunctionGemma for Tool Call Generation
Instead of asking the main model to generate tool calls directly:
1. Main model describes what it wants to do in natural language
2. FunctionGemma converts that description into a proper tool call
3. Execute the validated tool call

### Option 3: Post-process Failed Tool Calls
When a tool call fails (like "Original code not found"):
1. Use FunctionGemma to analyze the failure
2. Generate a corrected tool call
3. Retry with the corrected version

## Recommended Approach

**Hybrid: Pre-validate + Post-process**

1. **After parsing response:**
   ```python
   tool_calls, text = parser.parse_response(response)
   
   # Validate each tool call with FunctionGemma
   for i, call in enumerate(tool_calls):
       validated = gemma_formatter.validate_tool_call(call, available_tools)
       if validated:
           tool_calls[i] = validated
   ```

2. **After tool execution failure:**
   ```python
   if result['success'] == False:
       # Use FunctionGemma to fix the tool call
       fixed_call = gemma_formatter.fix_tool_call(
           original_call=call,
           error_message=result['error'],
           file_content=file_content
       )
       if fixed_call:
           # Retry with fixed call
           result = handler.execute(fixed_call)
   ```

## Implementation

### 1. Add validate_tool_call method to FunctionGemmaFormatter
```python
def validate_tool_call(self, tool_call: Dict, available_tools: List[Dict]) -> Optional[Dict]:
    """
    Validate and potentially fix a tool call using FunctionGemma.
    
    Returns corrected tool call or None if validation fails.
    """
    # Extract function details
    func = tool_call.get('function', {})
    name = func.get('name')
    args = func.get('arguments', {})
    
    # Build validation prompt
    prompt = f"""
    Validate this tool call and fix any issues:
    
    Tool: {name}
    Arguments: {json.dumps(args, indent=2)}
    
    Available tools: {self._format_tools(available_tools)}
    
    If the tool call is valid, output it as-is.
    If there are issues, fix them and output the corrected version.
    
    Output ONLY valid JSON: {{"name": "...", "arguments": {{...}}}}
    """
    
    # Call FunctionGemma
    response = self._call_gemma(prompt)
    
    # Parse and return
    return self._parse_gemma_response(response)
```

### 2. Add fix_tool_call method
```python
def fix_tool_call(self, original_call: Dict, error_message: str, 
                  file_content: str = None) -> Optional[Dict]:
    """
    Fix a failed tool call using FunctionGemma.
    
    Especially useful for modify_python_file when original_code doesn't match.
    """
    func = original_call.get('function', {})
    name = func.get('name')
    args = func.get('arguments', {})
    
    prompt = f"""
    This tool call failed. Fix it:
    
    Tool: {name}
    Arguments: {json.dumps(args, indent=2)}
    Error: {error_message}
    
    {f"File content:\n{file_content[:2000]}" if file_content else ""}
    
    Analyze the error and provide a corrected tool call.
    Output ONLY valid JSON: {{"name": "...", "arguments": {{...}}}}
    """
    
    response = self._call_gemma(prompt)
    return self._parse_gemma_response(response)
```

### 3. Integrate into debugging phase
```python
# In debugging.py, after parsing response:
if tool_calls:
    # Validate with FunctionGemma
    validated_calls = []
    for call in tool_calls:
        validated = self.gemma_formatter.validate_tool_call(call, tools)
        if validated:
            validated_calls.append(validated)
        else:
            self.logger.warning(f"Tool call validation failed: {call}")
    
    tool_calls = validated_calls

# After tool execution failure:
if not result['success'] and 'Original code not found' in result.get('error', ''):
    # Try to fix with FunctionGemma
    fixed_call = self.gemma_formatter.fix_tool_call(
        original_call=call,
        error_message=result['error'],
        file_content=self.read_file(filepath)
    )
    
    if fixed_call:
        self.logger.info("  🔧 FunctionGemma fixed the tool call, retrying...")
        result = handler.execute(fixed_call)
```

## Benefits

1. **Catches malformed tool calls** before execution
2. **Fixes whitespace/indentation issues** in modify_python_file
3. **Provides better error recovery** when tool calls fail
4. **Leverages FunctionGemma's strength** in tool calling

## Next Steps

1. Implement validate_tool_call method
2. Implement fix_tool_call method
3. Integrate into debugging phase
4. Test with the UnboundLocalError case

This should dramatically improve tool call success rate.