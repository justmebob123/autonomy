# Conversation Reset Fix

## Problem
The coding phase maintains conversation history across multiple tasks, causing the AI model to get confused and respond to previous tasks instead of the current one.

**Symptoms:**
- Model validates/creates wrong files (e.g., validates `core/architecture.py` when asked to create `models/objective_model.py`)
- Infinite loop where model keeps calling analysis tools without creating the target file
- Model appears to be responding to old context from conversation history

**Root Cause:**
The `AutoPruningConversationThread` maintains conversation history across task attempts. When a new task starts, the conversation still contains context from previous tasks, causing the model to get confused about which file it should be working on.

## Solution
Reset or clear conversation history when starting a new task in the coding phase.

### Implementation Options

#### Option 1: Clear conversation on new task (Recommended)
```python
# In coding.py, at the start of execute()
if task.attempts == 0:  # First attempt at this task
    self.conversation.thread.messages = []
    # Re-add system prompt
    system_prompt = self._get_system_prompt()
    self.conversation.add_message("system", system_prompt)
```

#### Option 2: Add strong task context marker
```python
# Add a clear separator and task context at the start of user message
user_message = f"""
{'='*70}
NEW TASK - IGNORE ALL PREVIOUS CONTEXT
{'='*70}

TARGET FILE: {task.target_file}
TASK: {task.description}

{user_message}
"""
```

#### Option 3: Prune conversation more aggressively
```python
# In conversation_pruning.py, reduce max_messages threshold
def should_prune(self, messages: List[Dict]) -> bool:
    return len(messages) > 5  # Instead of default 10
```

## Recommended Fix
Implement Option 1 (clear conversation on new task) combined with Option 2 (strong task context marker) for maximum clarity.

## Testing
After implementing the fix:
1. Run the pipeline
2. Verify that the model creates the correct target file
3. Verify that the model doesn't reference previous tasks
4. Check that conversation history is reset between tasks