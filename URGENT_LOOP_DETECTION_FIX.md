# URGENT: Loop Detection Triggering on Resume

## Problem
The pipeline is resuming from an old run (run_20251223_122703 from Dec 23rd) where task_034 already has failure_count=3. On resume, the loop detection immediately sees this and activates tool_design, creating an infinite loop.

## Root Cause
Loop detection checks `task.failure_count >= 3` but doesn't distinguish between:
- Fresh failures in current session
- Old failures from previous sessions

## Solutions

### Option 1: Reset Failure Counts on Resume (RECOMMENDED)
When resuming, reset all failure_counts to 0 so tasks get fresh attempts.

### Option 2: Add --fresh Flag
User can start fresh: `python run.py --fresh ../my_project`

### Option 3: Disable Specialized Phase Activation
Add a flag to disable automatic specialized phase activation.

### Option 4: Skip Failed Tasks
On resume, skip tasks that have already failed 3+ times instead of trying to fix them.

## Immediate Fix Needed
The user needs to either:
1. Run with --fresh flag
2. Delete the state file
3. We need to add logic to reset failure counts on resume