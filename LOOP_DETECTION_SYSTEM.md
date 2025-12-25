# Loop Detection System

## Overview

The Loop Detection System is a comprehensive framework that monitors AI agent behavior to detect and prevent infinite loops. It tracks all actions, identifies 6 types of loops, and provides intelligent interventions to break cycles.

## Architecture

### Components

1. **ActionTracker** (`pipeline/action_tracker.py`)
   - Tracks every AI action with timestamps
   - Maintains action history in JSONL format
   - Provides query methods for pattern analysis
   - Calculates action frequencies and statistics

2. **PatternDetector** (`pipeline/pattern_detector.py`)
   - Analyzes action history for loop patterns
   - Detects 6 types of loops (see below)
   - Assigns severity levels (low, medium, high, critical)
   - Generates evidence and suggestions

3. **LoopInterventionSystem** (`pipeline/loop_intervention.py`)
   - Checks for loops after each action
   - Provides targeted interventions based on loop type
   - Escalates to user after multiple failed interventions
   - Tracks intervention count to prevent intervention loops

## Six Types of Loops Detected

### 1. Action Loops
**Description:** Same action repeated consecutively

**Detection:**
- Threshold: 3+ identical actions in a row
- Checks action signatures (tool + key arguments)

**Example:**
```
str_replace(file:main.py, old:curses.cbreak())
str_replace(file:main.py, old:curses.cbreak())
str_replace(file:main.py, old:curses.cbreak())
```

**Intervention:**
- Stop using the current tool
- Read file to see current state
- Try a different approach (e.g., full_file_rewrite instead of str_replace)
- Consult specialist or ask user

### 2. Modification Loops
**Description:** Same file modified repeatedly without progress

**Detection:**
- Threshold: 4+ modifications to same file
- Checks if same code is being targeted repeatedly
- Analyzes uniqueness of modifications

**Example:**
```
Attempt 1: str_replace in main.py line 100
Attempt 2: str_replace in main.py line 100 (same target)
Attempt 3: str_replace in main.py line 100 (same target)
Attempt 4: str_replace in main.py line 100 (same target)
```

**Intervention:**
- Read file to see CURRENT state
- Verify code to replace actually exists
- Check exact indentation
- Consider full_file_rewrite
- Consult Whitespace or Syntax Analyst

### 3. Conversation Loops
**Description:** Repeatedly analyzing same thing without taking action

**Detection:**
- Threshold: 3+ analyses of same target
- Tracks read_file, search_code, list_directory, execute_command
- Identifies analysis paralysis

**Example:**
```
read_file(main.py)
search_code("curses")
read_file(main.py)  # Same file again
search_code("curses")  # Same search again
```

**Intervention:**
- Stop gathering more information
- Review what you've already learned
- Make a decision and take action
- Block analysis tools temporarily

### 4. Circular Dependencies
**Description:** A depends on B depends on A

**Detection:**
- Builds dependency graph from imports
- Detects cycles using graph traversal
- Identifies circular import chains

**Example:**
```
module_a.py imports module_b
module_b.py imports module_c
module_c.py imports module_a  # Cycle!
```

**Intervention:**
- Identify the circular dependency chain
- Break cycle by:
  - Moving shared code to separate module
  - Using dependency injection
  - Refactoring to remove circular reference
- Consult Pattern Analyst

### 5. State Cycles
**Description:** System cycling through same states

**Detection:**
- Tracks state transitions (phase, file, tool)
- Detects repeating state sequences
- Minimum 2 complete cycles

**Example:**
```
State sequence: (debug, main.py, str_replace) → (debug, main.py, read_file) → (debug, main.py, str_replace)
Pattern repeats 3 times
```

**Intervention:**
- Break cycle with fundamentally different approach
- Consult specialist for fresh perspective
- Consider if current strategy is viable
- Reset and try different strategy

### 6. Pattern Repetition
**Description:** Complex multi-step patterns repeating

**Detection:**
- Detects alternating patterns (A-B-A-B or A-B-C-A-B-C)
- Minimum 2 complete cycles
- Pattern length 2-10 actions

**Example:**
```
Pattern: read_file → str_replace → read_file → str_replace
Repeats 3 times without progress
```

**Intervention:**
- Stop the current sequence
- Analyze why pattern isn't working
- Consult specialist for different perspective
- Try completely different approach

## Severity Levels

### Low
- Early warning
- 3-4 repetitions
- No immediate action required
- Logged for awareness

### Medium
- Concerning pattern
- 5-6 repetitions
- Intervention recommended
- Guidance provided to AI

### High
- Serious loop detected
- 7-9 repetitions
- Intervention required
- Specific actions mandated

### Critical
- Severe infinite loop
- 10+ repetitions or escalation needed
- Immediate intervention
- May require user input

## Intervention Strategy

### Stage 1: Guidance
- Provide specific suggestions based on loop type
- Suggest alternative tools or approaches
- Recommend specialist consultation

### Stage 2: Tool Blocking
- Temporarily block problematic tools
- Force AI to try different approaches
- Suggest specific alternative tools

### Stage 3: Escalation
- After 3 failed interventions
- Require user input via 'ask' tool
- Block all modification tools
- Provide comprehensive context to user

## Integration Points

### Debugging Phase
Loop detection is integrated at 3 points:

1. **Main Fix Attempt** (line ~270)
   - After initial tool execution
   - Agent: "main"

2. **Retry Attempt** (line ~470)
   - After retry tool execution
   - Agent: "retry"

3. **Conversation Thread** (line ~670)
   - After each conversation turn
   - Agent: "conversation"

### Action Tracking
Every tool call is tracked with:
- Timestamp
- Phase (debug, coding, qa, etc.)
- Agent (main, retry, conversation, specialist)
- Tool name
- Arguments
- Result
- File path (if applicable)
- Success status

## Usage

### Automatic Operation
Loop detection runs automatically in the debugging phase. No configuration needed.

### Manual Checking
```python
from pipeline.action_tracker import ActionTracker
from pipeline.pattern_detector import PatternDetector
from pipeline.loop_intervention import LoopInterventionSystem

# Initialize
tracker = ActionTracker(history_file=Path("action_history.jsonl"))
detector = PatternDetector(tracker)
intervention = LoopInterventionSystem(tracker, detector, logger)

# Check for loops
result = intervention.check_and_intervene()
if result:
    print(result['guidance'])
```

### Viewing Action History
```python
# Get recent actions
recent = tracker.get_recent_actions(count=20)

# Get file modifications
mods = tracker.get_file_modifications("main.py", time_window=300)

# Get statistics
stats = tracker.get_statistics()
print(f"Total actions: {stats['total_actions']}")
print(f"Success rate: {stats['success_rate']:.1%}")
```

## Configuration

### Thresholds
Configurable in `PatternDetector.__init__`:

```python
self.thresholds = {
    'action_repeat': 3,           # Same action 3+ times
    'modification_repeat': 4,     # Same file modified 4+ times
    'conversation_repeat': 3,     # Same conversation 3+ times
    'pattern_cycles': 2,          # Pattern repeats 2+ times
    'time_window': 300.0,         # 5 minute window
    'rapid_actions': 10,          # 10+ actions in 60 seconds
}
```

### Intervention Limits
Configurable in `LoopInterventionSystem.__init__`:

```python
self.max_interventions = 3  # Escalate after 3 interventions
```

## Files

### Created Files
- `autonomy/pipeline/action_tracker.py` (300 lines)
- `autonomy/pipeline/pattern_detector.py` (400 lines)
- `autonomy/pipeline/loop_intervention.py` (400 lines)

### Modified Files
- `autonomy/pipeline/phases/debugging.py`
  - Added imports
  - Added initialization in `__init__`
  - Added `_track_tool_calls()` method
  - Added `_check_for_loops()` method
  - Integrated at 3 execution points

### Log Files
- `.autonomous_logs/action_history.jsonl` - Complete action history
- `ai_activity.log` - AI activity log (existing)

## Benefits

1. **Prevents Infinite Loops**
   - Detects loops before they consume excessive resources
   - Breaks cycles automatically with intelligent guidance

2. **Improves AI Effectiveness**
   - Forces AI to try different approaches
   - Prevents repetitive failed attempts
   - Encourages strategic thinking

3. **Reduces Wasted Time**
   - Stops unproductive patterns early
   - Escalates to user when stuck
   - Provides actionable guidance

4. **Comprehensive Monitoring**
   - Tracks all AI actions
   - Provides detailed statistics
   - Enables post-mortem analysis

5. **Intelligent Interventions**
   - Tailored guidance for each loop type
   - Progressive escalation strategy
   - Preserves AI autonomy when possible

## Example Scenarios

### Scenario 1: Indentation Loop
```
Action 1: str_replace(main.py, old="curses.cbreak()")
Result: Code not found (indentation mismatch)

Action 2: str_replace(main.py, old="curses.cbreak()")
Result: Code not found (same issue)

Action 3: str_replace(main.py, old="curses.cbreak()")
Result: Code not found (same issue)

🛑 LOOP DETECTED: Action Loop (Medium Severity)
Intervention: Read file to see exact indentation, use larger code block
```

### Scenario 2: Analysis Paralysis
```
Action 1: read_file(main.py)
Action 2: search_code("error")
Action 3: read_file(main.py)  # Same file
Action 4: search_code("error")  # Same search

🛑 LOOP DETECTED: Conversation Loop (Medium Severity)
Intervention: Stop analyzing, make a decision, take action
```

### Scenario 3: Escalation
```
Intervention 1: Try different approach → AI continues same pattern
Intervention 2: Block str_replace, use full_file_rewrite → AI still stuck
Intervention 3: Consult specialist → Still no progress

🚨 ESCALATION: User intervention required
Action: Must use 'ask' tool to request user guidance
```

## Future Enhancements

1. **Machine Learning**
   - Learn from successful interventions
   - Predict loops before they occur
   - Personalize thresholds based on patterns

2. **Cross-Session Learning**
   - Track patterns across multiple runs
   - Build knowledge base of common loops
   - Share learnings between projects

3. **Visualization**
   - Action flow diagrams
   - Loop pattern visualization
   - Real-time monitoring dashboard

4. **Advanced Detection**
   - Semantic similarity (not just exact matches)
   - Context-aware loop detection
   - Multi-agent coordination loops

## Troubleshooting

### False Positives
If legitimate repeated actions are flagged:
- Increase thresholds in `PatternDetector`
- Add exceptions for specific tools
- Adjust time windows

### Missed Loops
If loops aren't detected:
- Decrease thresholds
- Add new loop types
- Improve action signatures

### Performance Impact
Action tracking is lightweight:
- ~1ms per action tracked
- JSONL format for efficient appending
- In-memory analysis with file persistence

## Conclusion

The Loop Detection System provides comprehensive protection against infinite loops while maintaining AI autonomy. It detects 6 types of loops, provides intelligent interventions, and escalates to users when necessary. This ensures the debugging phase makes consistent progress and doesn't waste time on unproductive patterns.