# Depth-61 Analysis: Model Selection Architecture Issue

## Root Cause Identified

The planning phase fails because of **TWO separate issues**:

### Issue #1: Wrong Server in Config ✅ FIXED
**Location:** `pipeline/config.py` line 78
**Problem:** Planning configured to use ollama01, but qwen2.5-coder:32b only on ollama02
**Fix Applied:** Changed to ollama02

### Issue #2: Fallback Logic Bypassed 🔴 CRITICAL
**Location:** `pipeline/phases/base.py` lines 563-573
**Problem:** `chat_with_history()` bypasses `get_model_for_task()` fallback logic

## The Architecture Problem

```python
# In base.py chat_with_history():
model_name = self.conversation.thread.model  # Gets model name
_, host = self.config.model_assignments[self.phase_name]  # Gets host
response = self.client.chat(host=host, model=model_name, ...)  # Direct call
```

This **bypasses** the intelligent model selection in `client.get_model_for_task()` which:
- Checks if model exists on preferred host
- Falls back to other hosts if not found
- Uses fallback models if needed
- Provides detailed logging

## Call Stack Analysis

### Current (Broken) Flow:
```
1. PlanningPhase.execute()
2. → chat_with_history()
3. → Gets model from conversation.thread.model
4. → Gets host from config.model_assignments
5. → Directly calls client.chat(host, model)
6. → If model not on host: FAILS (no fallback)
```

### Should Be:
```
1. PlanningPhase.execute()
2. → chat_with_history()
3. → Calls client.get_model_for_task(phase_name)
4. → Intelligent selection with fallbacks
5. → Returns (host, model) that actually exists
6. → Calls client.chat(host, model)
7. → SUCCESS
```

## Why This Matters

Even though we fixed the config, the architecture is fragile:
- If a model becomes unavailable, no automatic fallback
- If server goes down, no automatic failover
- Manual config changes required for every model issue
- Fallback logic exists but is never used

## Recommended Fix

### Option 1: Use get_model_for_task (RECOMMENDED)

```python
# In pipeline/phases/base.py, chat_with_history():

# BEFORE:
model_name = self.conversation.thread.model
if self.phase_name in self.config.model_assignments:
    _, host = self.config.model_assignments[self.phase_name]
else:
    host = self.config.servers[0].host if self.config.servers else "localhost"

# AFTER:
result = self.client.get_model_for_task(self.phase_name)
if result:
    host, model_name = result
else:
    # Fallback to conversation model
    model_name = self.conversation.thread.model
    host = self.config.servers[0].host if self.config.servers else "localhost"
```

### Option 2: Add Fallback in chat() Method

Keep current architecture but add fallback logic in `client.chat()`:
- If model not found on specified host
- Try other hosts automatically
- Use fallback models if needed

## Impact Assessment

**Current State:**
- ✅ Config fixed - planning will work now
- ❌ Architecture fragile - will break again if models change
- ❌ Fallback logic unused - wasted code
- ❌ No automatic recovery - requires manual intervention

**After Fix:**
- ✅ Automatic fallback to other hosts
- ✅ Automatic fallback to alternative models
- ✅ Resilient to server/model availability changes
- ✅ Existing fallback logic actually used

## Testing Plan

1. Test with correct config (current fix)
2. Test with wrong config (should auto-fallback)
3. Test with server down (should use other server)
4. Test with model unavailable (should use fallback model)

## Recommendation

**Implement Option 1** - Use `get_model_for_task()` in `chat_with_history()`

This makes the system resilient and uses the existing intelligent selection logic.

---

**Priority:** HIGH
**Complexity:** LOW (simple change)
**Risk:** LOW (improves reliability)
**Benefit:** HIGH (automatic recovery from model/server issues)