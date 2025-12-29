# CRITICAL FIX: Planning Loop Issue

## Problem
Planning phase keeps saying "all 78 tasks already exist" but doesn't activate them.
Tasks are stuck in non-active statuses (likely SKIPPED or FAILED).

## Root Cause
1. Planning creates tasks but they get marked as SKIPPED/FAILED
2. Planning sees they exist and says "no new work"
3. Coordinator has 0 pending tasks, so goes back to planning
4. INFINITE LOOP

## Solution
Planning phase needs to:
1. Check for tasks in SKIPPED/FAILED status
2. REACTIVATE them by setting status to NEW
3. Add them to the queue

## Files to Fix
- `pipeline/phases/planning.py` - Add task reactivation logic