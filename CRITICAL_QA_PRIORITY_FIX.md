# CRITICAL: QA Priority Fix

## Problem

QA is being checked TOO EARLY in the tactical decision tree:

```
Current Order:
1. Debugging (needs_fixes)
2. QA (qa_pending)          ← TOO EARLY!
3. Pending tasks (coding/refactoring/documentation)
```

This means QA runs even when:
- Refactoring is needed
- Integration work is pending
- More coding should happen first

## Correct Order

QA should come AFTER coding-related structures:

```
Correct Order:
1. Debugging (needs_fixes)
2. Pending tasks check
   a. Documentation tasks → documentation
   b. Refactoring check → refactoring
   c. Regular coding → coding
3. QA (qa_pending)          ← AFTER coding structures
```

## Rationale

- **Refactoring** is a coding-related structure that improves code quality
- **Integration** work connects components (coding-related)
- **QA** validates completed work, not work-in-progress
- QA should only run when there's nothing more urgent to code

## Implementation

Move QA check to AFTER pending tasks check in `_determine_next_action_tactical()`.

This ensures:
- Refactoring happens before QA
- Integration work happens before QA
- Coding continues before QA
- QA only runs when coding work is done