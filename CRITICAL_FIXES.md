# Critical Fixes Needed

## Issue 1: ERROR Types Have No File Location

**Problem**: LogMonitor returns two types:
- ERROR: Immediate errors with `context: []` (no traceback)
- EXCEPTION: Full tracebacks with context

ERROR types get `file: 'unknown'` because they have no traceback to parse.

**Solution**: Skip ERROR types entirely, only process EXCEPTION types which have full tracebacks.

## Issue 2: System Exits After 3 Failed Attempts

**Problem**: `max_no_progress = 3` causes exit after 3 iterations with no fixes.

**Solution**: Increase to 10 or remove the limit entirely. The system should keep trying.

## Issue 3: AI Not Applying Fixes

**Problem**: AI returns "No fix was applied" every time.

**Possible causes**:
1. Prompt not clear enough
2. Tool calling not working
3. Response parsing broken
4. AI doesn't understand what to do

**Solution**: Need to add verbose logging to see:
- What prompt the AI receives
- What the AI responds
- Whether tool calls are made
- Why fixes aren't being applied

## Issue 4: Need Better Error Messages

When AI fails to fix, we need to know WHY. Add detailed logging.