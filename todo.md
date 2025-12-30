# Critical Bug Fix: QA_FAILED Tasks Not Being Reactivated

## Problem
- Pipeline has 69-79 tasks stuck in QA_FAILED status
- Coordinator tries to reactivate them but the check only looks for SKIPPED and FAILED
- QA_FAILED is not included in the reactivation check
- Result: "Reactivated 0 tasks" even though there are many QA_FAILED tasks
- Pipeline keeps looping between planning and coding without making progress

## Solution
Add QA_FAILED to the reactivation status check in coordinator.py

## Tasks
- [x] Identify the bug in coordinator.py
- [x] Fix the reactivation logic to include QA_FAILED
- [ ] Test the fix
- [ ] Commit and push