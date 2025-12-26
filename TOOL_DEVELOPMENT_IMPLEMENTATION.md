# Tool Development Auto-Trigger Implementation

## Current State Analysis

### ✅ What's Already Implemented
1. **ToolCallHandler** - Returns error for unknown tools (line 266):
   ```python
   return {"tool": name, "success": False, "error": f"Unknown tool: {name}"}
   ```

2. **Tool Design Phase** - Fully implemented and integrated
   - Creates tool specifications
   - Generates Python implementations
   - Registers with ToolRegistry

3. **Tool Evaluation Phase** - Fully implemented
   - Tests new tools
   - Validates safety
   - Confirms functionality

4. **ToolRegistry** - Functional
   - `register_tool()` - Adds new tools
   - `get_tool()` - Retrieves tools
   - Dynamic loading without restart

5. **Polytopic Adjacency** - Defined
   - Any Phase → tool_design (when unknown tool)
   - tool_design → tool_evaluation
   - tool_evaluation → original_phase (retry)

### ⚠️ What's Missing
1. **PhaseCoordinator** - No unknown tool detection
   - Doesn't check tool call results for unknown tool errors
   - Doesn't route to tool_design when unknown tool detected
   - Doesn't retry original phase after tool creation

2. **Phase Error Propagation** - Incomplete
   - Phases don't propagate unknown tool errors to PhaseResult
   - PhaseResult.data doesn't include tool error details

## Implementation Plan

### Step 1: Enhance ToolCallHandler Error Return
**File**: `pipeline/handlers.py`

Current:
```python
return {"tool": name, "success": False, "error": f"Unknown tool: {name}"}
```

Enhanced:
```python
return {
    "tool": name, 
    "success": False, 
    "error": "unknown_tool",
    "error_type": "unknown_tool",
    "tool_name": name,
    "message": f"Unknown tool: {name}",
    "args": args  # Include for context
}
```

### Step 2: Enhance Phase Error Handling
**Files**: All phase files that use ToolCallHandler

Add after `results = handler.process_tool_calls(tool_calls)`:
```python
# Check for unknown tool errors
unknown_tools = [r for r in results if r.get('error_type') == 'unknown_tool']
if unknown_tools:
    return PhaseResult(
        success=False,
        phase=self.phase_name,
        message=f"Unknown tools detected: {[t['tool_name'] for t in unknown_tools]}",
        data={
            'unknown_tools': unknown_tools,
            'requires_tool_development': True,
            'original_tool_calls': tool_calls
        }
    )
```

### Step 3: Enhance PhaseCoordinator
**File**: `pipeline/coordinator.py`

Add to `execute_phase()` or `run()` method:
```python
def execute_phase(self, phase_name: str, state: PipelineState, **kwargs) -> PhaseResult:
    """Execute a phase with unknown tool detection and routing"""
    
    # Execute the phase
    result = self.phases[phase_name].execute(state, **kwargs)
    
    # Check for unknown tool errors
    if not result.success and result.data.get('requires_tool_development'):
        self.logger.info(f"🔧 Unknown tools detected, routing to tool_design")
        
        unknown_tools = result.data.get('unknown_tools', [])
        
        for unknown_tool in unknown_tools:
            # Route to tool_design phase
            tool_design_result = self._develop_tool(
                tool_name=unknown_tool['tool_name'],
                tool_args=unknown_tool.get('args', {}),
                usage_context={
                    'phase': phase_name,
                    'original_tool_calls': result.data.get('original_tool_calls')
                },
                state=state
            )
            
            if not tool_design_result.success:
                self.logger.error(f"Failed to develop tool: {unknown_tool['tool_name']}")
                return result  # Return original error
        
        # Retry original phase with new tools available
        self.logger.info(f"🔄 Retrying {phase_name} with new tools")
        result = self.phases[phase_name].execute(state, **kwargs)
    
    return result

def _develop_tool(self, tool_name: str, tool_args: dict, usage_context: dict, 
                  state: PipelineState) -> PhaseResult:
    """Develop a new tool through tool_design and tool_evaluation phases"""
    
    # Step 1: Design the tool
    self.logger.info(f"📐 Designing tool: {tool_name}")
    design_result = self.phases['tool_design'].execute(
        state,
        tool_name=tool_name,
        tool_args=tool_args,
        usage_context=usage_context
    )
    
    if not design_result.success:
        return design_result
    
    # Step 2: Evaluate the tool
    self.logger.info(f"🧪 Evaluating tool: {tool_name}")
    eval_result = self.phases['tool_evaluation'].execute(
        state,
        tool_name=tool_name,
        tool_spec=design_result.data.get('tool_spec')
    )
    
    return eval_result
```

### Step 4: Update Tool Design Phase
**File**: `pipeline/phases/tool_design.py`

Ensure it accepts the new parameters:
```python
def execute(self, state: PipelineState, tool_name: str = None, 
            tool_args: dict = None, usage_context: dict = None, **kwargs) -> PhaseResult:
    """
    Design a new tool based on requirements.
    
    Args:
        tool_name: Name of the tool to create
        tool_args: Arguments that were passed to the unknown tool
        usage_context: Context about how/where the tool was used
    """
    # Use provided context or extract from kwargs
    if not tool_name:
        tool_name = kwargs.get('tool_name')
    
    # Generate tool specification using LLM
    # ... existing implementation ...
```

### Step 5: Update Tool Evaluation Phase
**File**: `pipeline/phases/tool_evaluation.py`

Ensure it accepts tool specifications:
```python
def execute(self, state: PipelineState, tool_name: str = None,
            tool_spec: dict = None, **kwargs) -> PhaseResult:
    """
    Evaluate a newly created tool.
    
    Args:
        tool_name: Name of the tool to evaluate
        tool_spec: Tool specification from tool_design phase
    """
    # Load the tool from registry
    # Test with sample inputs
    # Validate safety
    # ... existing implementation ...
```

## Implementation Priority

### Phase 1: Core Functionality (HIGH PRIORITY)
1. ✅ Enhance ToolCallHandler error return (Step 1)
2. ✅ Add unknown tool detection to phases (Step 2)
3. ✅ Implement PhaseCoordinator routing (Step 3)

### Phase 2: Refinement (MEDIUM PRIORITY)
4. Update tool_design phase parameters (Step 4)
5. Update tool_evaluation phase parameters (Step 5)
6. Add logging and monitoring

### Phase 3: Optimization (LOW PRIORITY)
7. Cache tool development attempts
8. Batch multiple unknown tools
9. Learn from successful tool patterns

## Testing Strategy

### Test Case 1: Single Unknown Tool
```python
# Phase calls: analyze_documentation_needs(project_dir="/path")
# Expected: Tool created, phase retries, succeeds
```

### Test Case 2: Multiple Unknown Tools
```python
# Phase calls: tool_a(), tool_b(), tool_c()
# Expected: All tools created, phase retries once, succeeds
```

### Test Case 3: Tool Development Failure
```python
# Tool design fails (invalid spec)
# Expected: Original error returned, no infinite loop
```

### Test Case 4: Tool Evaluation Failure
```python
# Tool created but fails validation
# Expected: Tool not registered, original error returned
```

## Success Metrics

1. **Auto-Detection**: Unknown tool errors automatically trigger tool_design
2. **Success Rate**: >90% of tool development attempts succeed
3. **No Loops**: System never enters infinite tool development loop
4. **Performance**: Tool development adds <30s to phase execution
5. **Safety**: All tools validated before deployment

## Rollout Plan

1. **Week 1**: Implement Steps 1-3 (core functionality)
2. **Week 2**: Test with real unknown tool scenarios
3. **Week 3**: Refine based on test results
4. **Week 4**: Deploy to production with monitoring

## Monitoring & Observability

### Metrics to Track
- `tool_development_triggered`: Count of unknown tool detections
- `tool_development_success`: Count of successful tool creations
- `tool_development_duration`: Time taken for tool development
- `tool_retry_success`: Count of successful phase retries

### Logs to Capture
- Unknown tool detection events
- Tool design phase executions
- Tool evaluation results
- Phase retry attempts

## Risk Mitigation

### Risk 1: Infinite Loop
**Mitigation**: Track tool development attempts per tool name, max 3 attempts

### Risk 2: Malicious Tool Creation
**Mitigation**: Tool evaluation phase validates safety, sandboxed execution

### Risk 3: Performance Impact
**Mitigation**: Async tool development, cache results, timeout limits

### Risk 4: Tool Conflicts
**Mitigation**: Version tools, namespace isolation, conflict detection

## Future Enhancements

1. **Tool Learning**: Learn from successful tools to improve future designs
2. **Tool Composition**: Combine existing tools to create new ones
3. **Tool Optimization**: Refine tools based on usage patterns
4. **Tool Sharing**: Share tools across projects/teams
5. **Tool Marketplace**: Community-contributed tools

---

**Status**: Ready for Implementation
**Priority**: HIGH - Enables true self-expansion capability
**Estimated Effort**: 2-3 days for core functionality