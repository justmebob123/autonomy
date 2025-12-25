# Failure Analysis System

## Overview

The Failure Analysis System provides intelligent diagnosis of why code modifications fail, along with detailed feedback to help the AI understand and correct its mistakes.

## Key Features

### 1. **Comprehensive Failure Capture**
When a modification fails, the system captures:
- Original file content
- Modified file content (if any)
- Intended original code to replace
- Intended replacement code
- Error message
- Generated patch (if available)
- Timestamp

### 2. **Intelligent Failure Classification**
Failures are automatically classified into categories:
- `CODE_NOT_FOUND` - Original code wasn't found in the file
- `SYNTAX_ERROR` - Replacement code has syntax errors
- `INDENTATION_ERROR` - Indentation mismatch
- `VERIFICATION_FAILURE` - Post-modification checks failed
- `IMPORT_ERROR` - Import-related issues
- `UNKNOWN` - Other failures

### 3. **Root Cause Analysis**
For each failure type, the system performs specific analysis:

#### CODE_NOT_FOUND Analysis
- Finds similar code blocks in the file (with similarity scores)
- Analyzes whitespace differences (tabs vs spaces, indentation levels)
- Checks for line ending differences (CRLF vs LF)
- Provides context before and after similar matches

#### SYNTAX_ERROR Analysis
- Identifies specific syntax issues:
  - Missing colons
  - Unmatched brackets/parentheses
  - Unmatched quotes
  - Invalid Python syntax
- Shows the problematic replacement code

#### INDENTATION_ERROR Analysis
- Detects indentation style in original vs replacement
- Identifies tab/space mismatches
- Calculates indentation levels

#### VERIFICATION_FAILURE Analysis
- Compares intended changes vs actual changes
- Shows diffs of what was expected vs what happened
- Identifies discrepancies

### 4. **AI Feedback Generation**
The system generates comprehensive feedback for the AI including:
- Summary of what went wrong
- Root cause explanation
- What the AI tried to do (original and replacement code)
- Current file content with context
- Similar code matches (if found)
- Intended changes (patch format)
- Specific suggestions for fixing the issue
- Step-by-step guidance based on failure type

### 5. **Automatic Retry with Feedback**
When a modification fails:
1. Failure is analyzed and detailed report is generated
2. Report is saved to `failures/` directory
3. AI feedback is provided to the debugging phase
4. System automatically retries with the enhanced context
5. If retry fails, falls back to alternative approaches

## Usage

### Automatic Usage
The system is automatically integrated into the modification workflow. When any modification fails, failure analysis is performed automatically.

### Manual Analysis
You can also manually analyze failures:

```python
from pipeline.failure_analyzer import FailureAnalyzer, ModificationFailure

analyzer = FailureAnalyzer()

failure = ModificationFailure(
    filepath="src/main.py",
    original_content=file_content,
    modified_content=None,
    intended_original="old code",
    intended_replacement="new code",
    error_message="Original code not found"
)

analysis = analyzer.analyze_modification_failure(failure)
print(analysis["ai_feedback"])
```

## Failure Reports

### Location
All failure reports are saved to: `<project_dir>/failures/`

### Naming Convention
`failure_<timestamp>_<filename>.md`

Example: `failure_20240115_143022_main.md`

### Report Contents
Each report contains:
- Summary of the failure
- Root cause analysis
- What the AI tried to do
- Current file context
- Similar code matches (if found)
- Intended changes (patch)
- Specific suggestions
- Step-by-step guidance

## Integration Points

### 1. handlers.py
The `ToolCallHandler` class integrates failure analysis in three places:
- When original code is not found
- When replacement code has syntax errors
- When post-modification verification fails

### 2. debugging.py
The `DebuggingPhase` class:
- Receives failure analysis in tool results
- Automatically retries with AI feedback
- Uses the `retry_with_feedback()` method

### 3. run.py
The debug/QA mode:
- Checks for retry recommendations
- Calls retry method with failure feedback
- Falls back to alternative approaches if retry fails

## Example Workflow

### Scenario: Code Not Found

1. **Initial Attempt**
   ```python
   # AI tries to replace:
   curses.cbreak()
   
   # But file actually has:
               curses.cbreak()  # (with 12 spaces indentation)
   ```

2. **Failure Detection**
   - System detects exact match failed
   - Tries flexible whitespace matching
   - Still fails due to indentation mismatch

3. **Failure Analysis**
   - Classifies as `CODE_NOT_FOUND`
   - Finds similar code with correct indentation
   - Analyzes whitespace: "File uses 12 spaces, target uses 0"
   - Generates detailed feedback

4. **AI Feedback**
   ```markdown
   # MODIFICATION FAILURE ANALYSIS
   
   ## Root Cause
   The code you're trying to replace was not found in the file.
   Possible reasons:
     - Whitespace mismatch: File uses 12 spaces, target uses 0
   
   ## Similar Code Found in File
   ### Match 1 (Line 1018, 95% similar):
   ```python
               self.stdscr.keypad(True)
               curses.cbreak()
               curses.noecho()
   ```
   
   ## Suggestions
   1. Copy the EXACT code from the file, including all whitespace
   2. Use a larger code block that includes surrounding context
   ...
   ```

5. **Automatic Retry**
   - System calls `retry_with_feedback()`
   - Provides enhanced prompt with failure analysis
   - AI makes corrected attempt with proper indentation
   - Success!

## Benefits

### For AI
- Understands exactly why modifications failed
- Gets concrete examples of correct code
- Learns from mistakes
- Receives actionable suggestions

### For Developers
- Detailed failure reports for debugging
- Visibility into AI decision-making
- Historical record of failures
- Insights for improving prompts

### For System
- Automatic recovery from common failures
- Reduced manual intervention
- Better success rates
- Continuous improvement

## Configuration

### Failure Report Directory
Default: `<project_dir>/failures/`

To change:
```python
handler = ToolCallHandler(project_dir)
handler.failures_dir = Path("/custom/path")
```

### Similarity Threshold
Default: 0.6 (60% similarity)

To adjust:
```python
analyzer = FailureAnalyzer()
similar = analyzer._find_similar_code_blocks(content, target, threshold=0.7)
```

## Future Enhancements

Potential improvements:
1. Machine learning from failure patterns
2. Automatic prompt refinement based on failures
3. Cross-file failure correlation
4. Failure prediction before attempting modifications
5. Interactive failure resolution with user input
6. Failure statistics and analytics dashboard

## Troubleshooting

### Issue: Too many failure reports
**Solution**: Failure reports are only created when modifications fail. If you're seeing many reports, the AI may need better prompts or examples.

### Issue: Retry not working
**Solution**: Check that `should_retry` is set in the PhaseResult data. Ensure the debugging phase has the `retry_with_feedback()` method.

### Issue: AI not learning from feedback
**Solution**: Verify the AI feedback is being included in the retry prompt. Check the activity log for the full prompt sent to the AI.

## Related Documentation

- `ENHANCED_DEBUGGING.md` - Overall debugging system
- `CRITICAL_FIXES_APPLIED.md` - Recent bug fixes
- `SMART_WHITESPACE_HANDLING.md` - Whitespace matching system
- `MULTI_FORMAT_PARSER.md` - Response parsing system