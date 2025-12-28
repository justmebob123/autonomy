# Actual Usage Analysis - What's Really Used

## Entry Point: run.py

### Direct Imports from run.py
```python
from pipeline import PhaseCoordinator, PipelineConfig
from pipeline.error_signature import ErrorSignature, ProgressTracker
from pipeline.progress_display import print_bug_transition, print_progress_stats, print_refining_fix
from pipeline.command_detector import CommandDetector
```

### Imports Inside Functions (run_debug_qa_mode)
```python
from pipeline.config import ServerConfig
from pipeline.phases.qa import QAPhase
from pipeline.phases.debugging import DebuggingPhase
from pipeline.state.manager import StateManager, TaskState, TaskStatus
from pipeline.state.priority import TaskPriority
from pipeline.client import OllamaClient
from pipeline.phases.investigation import InvestigationPhase
from pipeline.user_proxy import UserProxyAgent
from pipeline.code_search import detect_refactoring_context, format_refactoring_context
from pipeline.debug_context import build_comprehensive_context, format_context_for_prompt
from pipeline.line_fixer import get_line_context, fix_line_directly
from pipeline.runtime_tester import RuntimeTester
from pipeline.error_dedup import deduplicate_errors, format_deduplicated_summary, group_errors_by_file
```

## Files That ARE Used (Need to verify each)

1. **pipeline/__init__.py** - Exports PhaseCoordinator, PipelineConfig
2. **pipeline/coordinator.py** - PhaseCoordinator class
3. **pipeline/config.py** - PipelineConfig, ServerConfig
4. **pipeline/client.py** - OllamaClient
5. **pipeline/error_signature.py** - ErrorSignature, ProgressTracker
6. **pipeline/progress_display.py** - print functions
7. **pipeline/command_detector.py** - CommandDetector
8. **pipeline/user_proxy.py** - UserProxyAgent
9. **pipeline/code_search.py** - refactoring detection
10. **pipeline/debug_context.py** - context building
11. **pipeline/line_fixer.py** - line fixing
12. **pipeline/runtime_tester.py** - RuntimeTester
13. **pipeline/error_dedup.py** - error deduplication
14. **pipeline/state/manager.py** - StateManager, TaskState, TaskStatus
15. **pipeline/state/priority.py** - TaskPriority
16. **pipeline/phases/qa.py** - QAPhase
17. **pipeline/phases/debugging.py** - DebuggingPhase
18. **pipeline/phases/investigation.py** - InvestigationPhase

## Next Steps

For EACH file above, I need to:
1. Open it
2. Check what IT imports
3. Verify those imports are actually used
4. Build the complete dependency tree
5. Mark everything NOT in the tree as dead code

This is the ONLY way to know what's really used.