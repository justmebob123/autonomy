# TODO: Fix Refactoring Phase Infinite Loop

## Problem
- [x] AI stuck calling `analyze_architecture_consistency` repeatedly
- [x] Tasks have "Anti-pattern: Unknown" with no data
- [x] Tasks created BEFORE recent fixes lack proper analysis_data
- [x] Infinite loop: task fails → same task selected → fails again

## Root Cause Analysis
- [x] Identified: Old tasks have empty analysis_data
- [x] Identified: Tasks created before commits dd11f57, 6eb20a7, eb02d6c
- [x] Identified: AI has zero information to work with
- [x] Documented in CRITICAL_REFACTORING_ANALYSIS.md

## Solution Implementation
- [x] Add `_cleanup_broken_tasks()` method to RefactoringPhase
- [x] Call cleanup at start of `execute()` method
- [x] Delete tasks with "Unknown" or empty analysis_data
- [x] Let phase re-detect issues with proper data
- [x] Add `delete_task()` method to RefactoringTaskManager

## Files Modified
- [x] `pipeline/phases/refactoring.py` - Added cleanup method
- [x] `pipeline/state/refactoring_task.py` - Added delete_task method

## Testing
- [ ] Verify broken tasks are deleted
- [ ] Verify new tasks have proper analysis_data
- [ ] Verify AI can actually fix issues
- [ ] Verify no infinite loop

## Next Steps
1. Commit and push changes
2. User runs pipeline again
3. Broken tasks will be deleted on first iteration
4. New tasks will be created with proper analysis_data
5. AI should be able to fix issues

## Alternative Solution (if needed)
User can manually reset:
```bash
cd /home/ai/AI/web
rm -rf .pipeline_state/
python3 /home/ai/AI/autonomy/run.py -vv .
```