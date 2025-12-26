# debugging.py Refactoring Plan - Reduce Coupling from 22 to <10

## Current State Analysis

### Import Count: 22 unique sources

**Standard Library (3)**:
1. datetime
2. typing
3. time

**Internal - Core (6)**:
4. .base (BasePhase, PhaseResult)
5. ..state.manager (PipelineState, TaskState, TaskStatus, FileStatus)
6. ..state.priority (TaskPriority)
7. ..tools (get_tools_for_phase)
8. ..prompts (get_debug_prompt, get_modification_decision_prompt)
9. ..handlers (ToolCallHandler)

**Internal - Features (13)** ⚠️ HIGH COUPLING:
10. ..conversation_thread (ConversationThread)
11. ..specialist_agents (SpecialistTeam)
12. ..failure_prompts (get_retry_prompt)
13. ..sudo_filter (filter_sudo_from_tool_calls)
14. ..action_tracker (ActionTracker)
15. ..pattern_detector (PatternDetector)
16. ..loop_intervention (LoopInterventionSystem)
17. ..team_orchestrator (TeamOrchestrator)
18. ..error_strategies (get_strategy, enhance_prompt_with_strategy)
19. pipeline.user_proxy (UserProxyAgent)
20. json (for data handling)

**Unused (2)**:
21. pathlib (Path) ❌
22. ..utils (validate_python_syntax) ❌

## Problems Identified

### 1. Duplicate Imports
- get_debug_prompt imported 3 times
- get_retry_prompt imported 2 times
- UserProxyAgent imported 3 times
- json imported 2 times

### 2. Unused Imports
- Path from pathlib
- validate_python_syntax from ..utils
- SYSTEM_PROMPTS from ..prompts

### 3. High Feature Coupling
The debugging phase directly imports 13 feature modules, making it tightly coupled to:
- Loop detection system (3 modules)
- Team orchestration (3 modules)
- Error handling (2 modules)
- Conversation management (1 module)
- Security filtering (1 module)
- User interaction (1 module)

## Refactoring Strategy

### Phase 1: Quick Wins (22 → 20)
**Remove unused imports:**
- ❌ Remove `from pathlib import Path`
- ❌ Remove `from ..utils import validate_python_syntax`
- ❌ Remove `SYSTEM_PROMPTS` from prompts import

**Clean duplicates:**
- Keep only first occurrence of each import
- Remove duplicate import statements

**Result**: 20 import sources

### Phase 2: Consolidation (20 → 15)
**Consolidate related functionality:**

1. **Loop Detection** (3 → 1):
   - Current: ActionTracker, PatternDetector, LoopInterventionSystem
   - Solution: These are already consolidated in BasePhase via LoopDetectionMixin
   - Action: Use inherited methods instead of direct imports
   - Savings: -2 imports

2. **Team/Orchestration** (3 → 1):
   - Current: SpecialistTeam, TeamOrchestrator, ConversationThread
   - Solution: Create a single orchestration facade
   - Action: Use BasePhase orchestration methods
   - Savings: -2 imports

3. **Error Handling** (2 → 1):
   - Current: get_strategy, enhance_prompt_with_strategy, get_retry_prompt
   - Solution: Consolidate into error_strategies module
   - Action: Import only error_strategies module, use methods
   - Savings: -1 import

**Result**: 15 import sources

### Phase 3: Dependency Injection (15 → 9)
**Move feature dependencies to BasePhase:**

The debugging phase shouldn't directly depend on:
- sudo_filter
- user_proxy
- specialist_agents
- team_orchestrator

**Solution**: 
1. Move these to BasePhase as optional capabilities
2. Debugging phase calls BasePhase methods
3. BasePhase handles the feature imports

**Imports to move to BasePhase:**
- filter_sudo_from_tool_calls → BasePhase.filter_sudo()
- UserProxyAgent → BasePhase.get_user_proxy()
- SpecialistTeam → BasePhase.get_specialists()
- TeamOrchestrator → BasePhase.get_orchestrator()

**Result**: 9 import sources ✅

## Final Target Structure

### Remaining Imports (9 total):

**Standard Library (2)**:
1. datetime
2. typing

**Core Dependencies (7)**:
3. .base (BasePhase, PhaseResult)
4. ..state.manager (PipelineState, TaskState, TaskStatus, FileStatus)
5. ..state.priority (TaskPriority)
6. ..tools (get_tools_for_phase)
7. ..prompts (get_debug_prompt, get_modification_decision_prompt)
8. ..handlers (ToolCallHandler)
9. ..error_strategies (consolidated error handling)

## Implementation Steps

### Step 1: Clean Duplicates and Unused
```python
# Remove these lines:
from pathlib import Path  # UNUSED
from ..utils import validate_python_syntax  # UNUSED
from ..prompts import SYSTEM_PROMPTS  # UNUSED (in import)

# Keep only first occurrence:
from ..prompts import get_debug_prompt  # Remove duplicates
from ..failure_prompts import get_retry_prompt  # Remove duplicates
from pipeline.user_proxy import UserProxyAgent  # Remove duplicates
import json  # Remove duplicates
```

### Step 2: Use Inherited Loop Detection
```python
# Instead of:
from ..action_tracker import ActionTracker
from ..pattern_detector import PatternDetector
from ..loop_intervention import LoopInterventionSystem

# Use inherited from LoopDetectionMixin:
self.track_tool_calls(tool_calls, results)
self.check_for_loops()
# These are already available via BasePhase
```

### Step 3: Consolidate Error Handling
```python
# Instead of:
from ..failure_prompts import get_retry_prompt
from ..error_strategies import get_strategy, enhance_prompt_with_strategy

# Use consolidated:
from ..error_strategies import ErrorStrategyManager
# Then: ErrorStrategyManager.get_retry_prompt(), etc.
```

### Step 4: Move Features to BasePhase
```python
# In BasePhase, add:
def filter_sudo(self, tool_calls):
    from ..sudo_filter import filter_sudo_from_tool_calls
    return filter_sudo_from_tool_calls(tool_calls)

def get_user_proxy(self):
    from pipeline.user_proxy import UserProxyAgent
    return UserProxyAgent()

# Then in debugging.py, use:
tool_calls = self.filter_sudo(tool_calls)
proxy = self.get_user_proxy()
```

## Benefits

1. **Reduced Coupling**: 22 → 9 (59% reduction)
2. **Better Separation**: Features isolated in BasePhase
3. **Easier Testing**: Fewer dependencies to mock
4. **Better Maintainability**: Changes to features don't affect debugging.py
5. **Cleaner Code**: Debugging phase focuses on debugging logic

## Risks

1. **Breaking Changes**: Moving code to BasePhase affects all phases
2. **Testing Required**: Need to verify all functionality still works
3. **Performance**: Lazy imports in BasePhase might have slight overhead

## Mitigation

1. **Incremental Approach**: Do Phase 1 first, test, then Phase 2, etc.
2. **Comprehensive Testing**: Run full test suite after each phase
3. **Backward Compatibility**: Keep old methods as deprecated wrappers initially

## Success Criteria

- ✅ Import count < 10
- ✅ All tests pass
- ✅ No functionality lost
- ✅ Code still readable and maintainable