# Integration Fix Plan - Week 2 Components

## Overview

This document provides a step-by-step plan to fix the critical integration gaps identified in the Week 2 implementation. The fixes are organized by priority and estimated time.

## Priority 1: Critical Fixes (MUST FIX)

### Fix 1.1: ToolCallHandler Integration (2 hours)

**Problem:** Custom tools are never registered with ToolCallHandler

**Solution:** Modify ToolCallHandler to accept and use tool_registry

#### Step 1: Update ToolCallHandler.__init__

**File:** `pipeline/handlers.py`

**Change:**
```python
# BEFORE (line 20)
def __init__(self, project_dir: Path, verbose: int = 0, activity_log_file: str = None):
    self.project_dir = Path(project_dir)
    self.logger = get_logger()
    self.verbose = verbose
    # ... rest of init

# AFTER
def __init__(self, project_dir: Path, verbose: int = 0, activity_log_file: str = None, tool_registry=None):
    self.project_dir = Path(project_dir)
    self.logger = get_logger()
    self.verbose = verbose
    # ... rest of init
    
    # Register custom tools from registry
    if tool_registry:
        tool_registry.set_handler(self)
        self.logger.info(f"Registered {len(tool_registry.tools)} custom tools")
```

#### Step 2: Update All ToolCallHandler Instantiations

**Files to Update:** (11 locations)

1. **pipeline/phases/debugging.py** (4 locations: lines 275, 471, 655, 671)
```python
# BEFORE
handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log))

# AFTER
handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log), tool_registry=self.tool_registry)
```

2. **pipeline/phases/coding.py** (line 117)
```python
# BEFORE
handler = ToolCallHandler(self.project_dir)

# AFTER
handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry)
```

3. **pipeline/phases/qa.py** (line 117)
```python
# BEFORE
handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log))

# AFTER
handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log), tool_registry=self.tool_registry)
```

4. **pipeline/phases/planning.py** (line 75)
```python
# BEFORE
handler = ToolCallHandler(self.project_dir)

# AFTER
handler = ToolCallHandler(self.project_dir, tool_registry=self.tool_registry)
```

5. **pipeline/phases/investigation.py** (line 96)
```python
# BEFORE
handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log))

# AFTER
handler = ToolCallHandler(self.project_dir, verbose=verbose, activity_log_file=str(activity_log), tool_registry=self.tool_registry)
```

6. **pipeline/phases/prompt_design.py** (line 130)
```python
# BEFORE
handler = ToolCallHandler(self.project_dir, verbose=self.config.verbose)

# AFTER
handler = ToolCallHandler(self.project_dir, verbose=self.config.verbose, tool_registry=self.tool_registry)
```

7. **pipeline/phases/tool_design.py** (line 131)
```python
# BEFORE
handler = ToolCallHandler(self.project_dir, verbose=self.config.verbose)

# AFTER
handler = ToolCallHandler(self.project_dir, verbose=self.config.verbose, tool_registry=self.tool_registry)
```

8. **pipeline/phases/role_design.py** (line 132)
```python
# BEFORE
handler = ToolCallHandler(self.project_dir, verbose=self.config.verbose)

# AFTER
handler = ToolCallHandler(self.project_dir, verbose=self.config.verbose, tool_registry=self.tool_registry)
```

#### Step 3: Test Custom Tool Execution

**Test Script:**
```python
# test_custom_tools.py
from pathlib import Path
from pipeline.tool_registry import ToolRegistry
from pipeline.handlers import ToolCallHandler

# Create test tool
project_dir = Path("test_project")
registry = ToolRegistry(project_dir)

# Create handler with registry
handler = ToolCallHandler(project_dir, tool_registry=registry)

# Verify custom tools are registered
print(f"Registered tools: {list(handler._handlers.keys())}")
assert 'custom_tool_name' in handler._handlers  # Replace with actual custom tool
```

### Fix 1.2: Loop Detection in All Phases (2 hours)

**Problem:** Loop detection only in debugging phase

**Solution:** Add loop detection to coding, qa, and planning phases

#### Step 1: Create Shared Loop Detection Mixin

**File:** `pipeline/phases/loop_detection_mixin.py` (NEW)

```python
"""
Loop Detection Mixin

Provides loop detection capabilities to any phase.
"""

from typing import List, Dict, Optional
from pathlib import Path

from ..action_tracker import ActionTracker
from ..pattern_detector import PatternDetector
from ..loop_intervention import LoopInterventionSystem


class LoopDetectionMixin:
    """
    Mixin to add loop detection to any phase.
    
    Usage:
        class MyPhase(BasePhase, LoopDetectionMixin):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.init_loop_detection()
    """
    
    def init_loop_detection(self):
        """Initialize loop detection components"""
        logs_dir = self.project_dir / ".autonomous_logs"
        logs_dir.mkdir(exist_ok=True)
        
        self.action_tracker = ActionTracker(
            history_file=logs_dir / "action_history.jsonl"
        )
        self.pattern_detector = PatternDetector(self.action_tracker)
        self.loop_intervention = LoopInterventionSystem(
            self.action_tracker,
            self.pattern_detector,
            self.logger
        )
    
    def track_tool_calls(self, tool_calls: List[Dict], results: List[Dict], agent: str = "main"):
        """Track tool calls for loop detection"""
        for tool_call, result in zip(tool_calls, results):
            tool_name = tool_call.get('tool', 'unknown')
            args = tool_call.get('args', {})
            
            # Extract file path if present
            file_path = None
            if 'file_path' in args:
                file_path = args['file_path']
            elif 'filepath' in args:
                file_path = args['filepath']
            
            # Track the action
            self.action_tracker.track_action(
                phase=self.phase_name,
                agent=agent,
                tool=tool_name,
                args=args,
                result=result,
                file_path=file_path,
                success=result.get('success', False)
            )
    
    def check_for_loops(self) -> Optional[Dict]:
        """Check for loops and intervene if necessary"""
        intervention = self.loop_intervention.check_and_intervene()
        
        if intervention:
            # Log the intervention
            self.logger.warning("=" * 80)
            self.logger.warning("LOOP DETECTED - INTERVENTION REQUIRED")
            self.logger.warning("=" * 80)
            self.logger.warning(intervention['guidance'])
            self.logger.warning("=" * 80)
            
            # Return intervention for AI to see
            return intervention
        
        return None
```

#### Step 2: Integrate into Coding Phase

**File:** `pipeline/phases/coding.py`

```python
# Add import
from .loop_detection_mixin import LoopDetectionMixin

# Modify class definition
class CodingPhase(BasePhase, LoopDetectionMixin):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_loop_detection()  # Add this line
    
    # In execute method, after tool execution:
    def execute(self, state, task, **kwargs):
        # ... existing code ...
        
        # After: results = handler.process_tool_calls(tool_calls)
        # Add:
        self.track_tool_calls(tool_calls, results, agent="coding")
        intervention = self.check_for_loops()
        if intervention and intervention.get('requires_user_input'):
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Loop detected - user intervention required",
                data={'intervention': intervention}
            )
```

#### Step 3: Integrate into QA Phase

**File:** `pipeline/phases/qa.py`

```python
# Add import
from .loop_detection_mixin import LoopDetectionMixin

# Modify class definition
class QAPhase(BasePhase, LoopDetectionMixin):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_loop_detection()  # Add this line
    
    # In execute method, after tool execution:
    def execute(self, state, task, **kwargs):
        # ... existing code ...
        
        # After: results = handler.process_tool_calls(tool_calls)
        # Add:
        self.track_tool_calls(tool_calls, results, agent="qa")
        intervention = self.check_for_loops()
        if intervention and intervention.get('requires_user_input'):
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Loop detected - user intervention required",
                data={'intervention': intervention}
            )
```

#### Step 4: Integrate into Planning Phase

**File:** `pipeline/phases/planning.py`

```python
# Add import
from .loop_detection_mixin import LoopDetectionMixin

# Modify class definition
class PlanningPhase(BasePhase, LoopDetectionMixin):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_loop_detection()  # Add this line
    
    # In execute method, after tool execution:
    def execute(self, state, **kwargs):
        # ... existing code ...
        
        # After: results = handler.process_tool_calls(tool_calls)
        # Add:
        self.track_tool_calls(tool_calls, results, agent="planning")
        intervention = self.check_for_loops()
        if intervention and intervention.get('requires_user_input'):
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Loop detected - user intervention required",
                data={'intervention': intervention}
            )
```

## Priority 2: Important Fixes (SHOULD FIX)

### Fix 2.1: Team Orchestrator Integration (1.5 hours)

**Problem:** TeamOrchestrator is initialized but never invoked

**Solution:** Add logic to invoke team orchestration for complex errors

#### Step 1: Add Complexity Assessment

**File:** `pipeline/phases/debugging.py`

```python
def _assess_error_complexity(self, issue: Dict, thread: ConversationThread) -> str:
    """
    Assess error complexity to determine if team orchestration is needed.
    
    Returns:
        'simple' - Direct fix
        'complex' - Team orchestration
        'novel' - Self-designing
    """
    # Check number of issues
    if len(thread.attempts) >= 3:
        return 'complex'  # Multiple failed attempts
    
    # Check error type
    error_type = issue.get('type', '')
    if error_type in ['SyntaxError', 'IndentationError']:
        return 'simple'
    
    # Check if multiple files involved
    if 'multiple_files' in issue.get('context', {}):
        return 'complex'
    
    # Check if circular dependencies
    if 'circular' in issue.get('message', '').lower():
        return 'complex'
    
    # Default to simple
    return 'simple'
```

#### Step 2: Invoke Team Orchestration

**File:** `pipeline/phases/debugging.py`

```python
def execute(self, state, issue, task, **kwargs):
    # ... existing code ...
    
    # After creating thread, assess complexity
    complexity = self._assess_error_complexity(issue, thread)
    
    if complexity == 'complex':
        self.logger.info("🎭 Complex error detected - using team orchestration")
        
        # Create orchestration plan
        plan = self.team_orchestrator.create_orchestration_plan(
            problem=f"Fix {issue['type']}: {issue['message']}",
            context={
                'file': filepath,
                'error': issue,
                'thread': thread,
                'attempts': len(thread.attempts)
            }
        )
        
        # Execute plan
        orchestration_results = self.team_orchestrator.execute_plan(plan, thread)
        
        # Use synthesis for fix
        if orchestration_results['success']:
            synthesis = orchestration_results['synthesis']
            # Apply synthesized fix
            # ... implementation ...
    
    # ... rest of existing code ...
```

### Fix 2.2: Custom Prompt Integration (1 hour)

**Problem:** Custom prompts are never retrieved or used

**Solution:** Check prompt_registry before using hardcoded prompts

#### Implementation

**File:** `pipeline/phases/debugging.py`

```python
def _get_prompt(self, prompt_type: str, **variables) -> str:
    """
    Get prompt from registry or fall back to hardcoded.
    
    Args:
        prompt_type: Type of prompt (e.g., 'debugging', 'retry')
        **variables: Variables to substitute in prompt
        
    Returns:
        Formatted prompt string
    """
    # Try custom prompt first
    custom_prompt = self.prompt_registry.get_prompt(
        f"{self.phase_name}_{prompt_type}",
        variables=variables
    )
    
    if custom_prompt:
        self.logger.debug(f"Using custom prompt: {self.phase_name}_{prompt_type}")
        return custom_prompt
    
    # Fall back to hardcoded
    if prompt_type == 'debugging':
        return get_debugging_prompt(**variables)
    elif prompt_type == 'retry':
        return get_retry_prompt(**variables)
    else:
        return get_debugging_prompt(**variables)

# Then use in execute:
prompt = self._get_prompt('debugging', error=issue, context=context)
response = self.client.generate(prompt=prompt, ...)
```

### Fix 2.3: Custom Role Integration (1 hour)

**Problem:** Custom specialists are never consulted

**Solution:** Check role_registry before using hardcoded specialists

#### Implementation

**File:** `pipeline/phases/debugging.py`

```python
def _consult_specialist(self, specialist_type: str, thread: ConversationThread, tools: List) -> Dict:
    """
    Consult specialist from registry or fall back to hardcoded.
    
    Args:
        specialist_type: Type of specialist needed
        thread: Conversation thread
        tools: Available tools
        
    Returns:
        Specialist analysis results
    """
    # Try custom specialist first
    custom_specialist = self.role_registry.get_specialist(specialist_type)
    
    if custom_specialist:
        self.logger.debug(f"Using custom specialist: {specialist_type}")
        return self.role_registry.consult_specialist(
            specialist_type,
            thread=thread,
            tools=tools
        )
    
    # Fall back to hardcoded
    return self.specialist_team.consult_specialist(
        specialist_type,
        thread=thread,
        tools=tools
    )

# Then use in execute:
analysis = self._consult_specialist('Whitespace Analyst', thread, tools)
```

## Priority 3: Testing & Validation (2 hours)

### Test 3.1: Custom Tool Execution Test

```python
def test_custom_tool_execution():
    """Test that custom tools are properly registered and executed"""
    # Create custom tool
    tool_spec = {
        'name': 'test_custom_tool',
        'description': 'Test tool',
        'parameters': {}
    }
    
    # Register tool
    registry = ToolRegistry(project_dir)
    registry.register_tool('test_custom_tool', tool_spec, lambda args: {'success': True})
    
    # Create handler with registry
    handler = ToolCallHandler(project_dir, tool_registry=registry)
    
    # Execute custom tool
    result = handler.process_tool_calls([{
        'function': {
            'name': 'test_custom_tool',
            'arguments': {}
        }
    }])
    
    assert result[0]['success'] == True
```

### Test 3.2: Loop Detection Test

```python
def test_loop_detection_all_phases():
    """Test that loop detection works in all phases"""
    phases = ['coding', 'qa', 'planning', 'debugging']
    
    for phase_name in phases:
        phase = get_phase(phase_name)
        
        # Simulate repeated actions
        for i in range(5):
            phase.track_tool_calls([{'tool': 'str_replace', 'args': {}}], [{'success': False}])
        
        # Check for loop
        intervention = phase.check_for_loops()
        
        assert intervention is not None
        assert intervention['loop_type'] == 'action_loop'
```

### Test 3.3: Team Orchestration Test

```python
def test_team_orchestration():
    """Test that team orchestration is invoked for complex errors"""
    phase = DebuggingPhase(...)
    
    # Create complex error
    issue = {
        'type': 'RuntimeError',
        'message': 'Complex error with multiple issues',
        'context': {'multiple_files': True}
    }
    
    # Execute
    result = phase.execute(state, issue=issue)
    
    # Verify orchestration was used
    assert 'orchestration_results' in result.data
    assert result.data['orchestration_results']['success']
```

## Implementation Timeline

### Day 1 (4 hours)
- ✅ Fix 1.1: ToolCallHandler Integration (2 hours)
- ✅ Fix 1.2: Loop Detection in All Phases (2 hours)

### Day 2 (3.5 hours)
- ✅ Fix 2.1: Team Orchestrator Integration (1.5 hours)
- ✅ Fix 2.2: Custom Prompt Integration (1 hour)
- ✅ Fix 2.3: Custom Role Integration (1 hour)

### Day 3 (2 hours)
- ✅ Test 3.1: Custom Tool Execution Test (0.5 hours)
- ✅ Test 3.2: Loop Detection Test (0.5 hours)
- ✅ Test 3.3: Team Orchestration Test (0.5 hours)
- ✅ Integration Testing (0.5 hours)

**Total Time: 9.5 hours**

## Success Criteria

### Must Have (Critical)
- ✅ Custom tools are registered and executable
- ✅ Loop detection works in all 4 main phases
- ✅ All tests pass

### Should Have (Important)
- ✅ Team orchestration is invoked for complex errors
- ✅ Custom prompts are used when available
- ✅ Custom specialists are consulted when available

### Nice to Have (Optional)
- ✅ Performance metrics validate claimed benefits
- ✅ Documentation updated to reflect actual state
- ✅ Additional integration tests

## Rollback Plan

If fixes cause issues:

1. **Revert ToolCallHandler changes**
   ```bash
   git revert <commit_hash>
   ```

2. **Disable loop detection in new phases**
   ```python
   # Comment out init_loop_detection() calls
   ```

3. **Disable team orchestration**
   ```python
   # Set complexity to always return 'simple'
   ```

## Conclusion

This fix plan addresses all critical integration gaps identified in the analysis. Following this plan will result in a fully functional self-designing AI system that delivers the claimed benefits.

**Estimated Total Time:** 9.5 hours
**Priority:** 🔴 CRITICAL
**Status:** Ready for implementation