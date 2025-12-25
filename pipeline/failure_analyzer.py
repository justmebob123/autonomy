"""
Failure Analysis System for Code Modifications

This module provides intelligent analysis of why code modifications fail,
including detailed diagnostics and AI feedback generation.
"""

import difflib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging


class ModificationFailure:
    """Represents a failed modification attempt with full context"""
    
    def __init__(self, 
                 filepath: str,
                 original_content: str,
                 modified_content: Optional[str],
                 intended_original: str,
                 intended_replacement: str,
                 error_message: str,
                 patch: Optional[str] = None):
        self.filepath = filepath
        self.original_content = original_content
        self.modified_content = modified_content
        self.intended_original = intended_original
        self.intended_replacement = intended_replacement
        self.error_message = error_message
        self.patch = patch
        self.timestamp = datetime.now()
        
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "filepath": self.filepath,
            "original_content": self.original_content,
            "modified_content": self.modified_content,
            "intended_original": self.intended_original,
            "intended_replacement": self.intended_replacement,
            "error_message": self.error_message,
            "patch": self.patch,
            "timestamp": self.timestamp.isoformat()
        }


class FailureAnalyzer:
    """Analyzes why code modifications fail and provides detailed feedback"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
    def analyze_modification_failure(self, failure: ModificationFailure) -> Dict:
        """
        Comprehensive analysis of why a modification failed.
        
        Returns a dictionary with:
        - failure_type: Category of failure
        - root_cause: Detailed explanation
        - suggestions: List of alternative approaches
        - context: Relevant code snippets and diffs
        - ai_feedback: Formatted feedback for the AI
        """
        
        analysis = {
            "failure_type": self._classify_failure(failure),
            "root_cause": "",
            "suggestions": [],
            "context": {},
            "ai_feedback": ""
        }
        
        # Perform specific analysis based on failure type
        if "not found" in failure.error_message.lower():
            self._analyze_not_found(failure, analysis)
        elif "syntax" in failure.error_message.lower():
            self._analyze_syntax_error(failure, analysis)
        elif "indentation" in failure.error_message.lower():
            self._analyze_indentation_error(failure, analysis)
        elif "verification failed" in failure.error_message.lower():
            self._analyze_verification_failure(failure, analysis)
        else:
            self._analyze_generic_failure(failure, analysis)
        
        # Generate AI feedback
        analysis["ai_feedback"] = self._generate_ai_feedback(failure, analysis)
        
        return analysis
    
    def _classify_failure(self, failure: ModificationFailure) -> str:
        """Classify the type of failure"""
        error = failure.error_message.lower()
        
        if "not found" in error:
            return "CODE_NOT_FOUND"
        elif "syntax" in error:
            return "SYNTAX_ERROR"
        elif "indentation" in error:
            return "INDENTATION_ERROR"
        elif "verification failed" in error:
            return "VERIFICATION_FAILURE"
        elif "import" in error:
            return "IMPORT_ERROR"
        else:
            return "UNKNOWN"
    
    def _analyze_not_found(self, failure: ModificationFailure, analysis: Dict):
        """Analyze why the original code wasn't found"""
        
        # Find similar code in the file
        similar_matches = self._find_similar_code_blocks(
            failure.original_content,
            failure.intended_original
        )
        
        # Check for whitespace differences
        whitespace_diff = self._analyze_whitespace_differences(
            failure.original_content,
            failure.intended_original
        )
        
        # Check for line ending differences
        line_ending_diff = self._check_line_endings(
            failure.original_content,
            failure.intended_original
        )
        
        analysis["root_cause"] = "The code you're trying to replace was not found in the file."
        
        reasons = []
        if whitespace_diff:
            reasons.append(f"Whitespace mismatch: {whitespace_diff}")
        if line_ending_diff:
            reasons.append(f"Line ending mismatch: {line_ending_diff}")
        if similar_matches:
            reasons.append(f"Found {len(similar_matches)} similar code blocks")
        
        if reasons:
            analysis["root_cause"] += " Possible reasons:\n" + "\n".join(f"  - {r}" for r in reasons)
        
        # Add context
        analysis["context"]["similar_matches"] = similar_matches[:3]  # Top 3 matches
        analysis["context"]["whitespace_analysis"] = whitespace_diff
        
        # Suggestions
        analysis["suggestions"] = [
            "Copy the exact code from the file, including all whitespace",
            "Use a larger code block that includes surrounding context",
            "Check if the code has already been modified",
            "Verify you're looking at the correct file"
        ]
        
        if similar_matches:
            analysis["suggestions"].insert(0, 
                f"Try using this similar code instead:\n{similar_matches[0]['code']}"
            )
    
    def _analyze_syntax_error(self, failure: ModificationFailure, analysis: Dict):
        """Analyze syntax errors in the replacement code"""
        
        analysis["root_cause"] = "The replacement code has a syntax error."
        
        # Try to parse and identify the specific syntax issue
        if failure.modified_content:
            syntax_issues = self._identify_syntax_issues(failure.intended_replacement)
            if syntax_issues:
                analysis["root_cause"] += f"\n\nSpecific issues:\n" + "\n".join(
                    f"  - {issue}" for issue in syntax_issues
                )
        
        analysis["context"]["replacement_code"] = failure.intended_replacement
        
        analysis["suggestions"] = [
            "Check for missing colons, parentheses, or brackets",
            "Verify indentation is consistent",
            "Ensure all strings are properly quoted",
            "Check for invalid Python syntax",
            "Test the code in isolation before applying"
        ]
    
    def _analyze_indentation_error(self, failure: ModificationFailure, analysis: Dict):
        """Analyze indentation-related failures"""
        
        # Detect indentation in original vs replacement
        orig_indent = self._detect_indentation(failure.intended_original)
        repl_indent = self._detect_indentation(failure.intended_replacement)
        
        analysis["root_cause"] = "Indentation mismatch between original and replacement code."
        analysis["root_cause"] += f"\n  Original uses: {orig_indent}"
        analysis["root_cause"] += f"\n  Replacement uses: {repl_indent}"
        
        analysis["context"]["original_indentation"] = orig_indent
        analysis["context"]["replacement_indentation"] = repl_indent
        
        analysis["suggestions"] = [
            f"Ensure replacement code uses {orig_indent} for indentation",
            "Match the indentation level of surrounding code",
            "Use consistent indentation (all spaces or all tabs)",
            "Let the system auto-detect and apply indentation"
        ]
    
    def _analyze_verification_failure(self, failure: ModificationFailure, analysis: Dict):
        """Analyze post-modification verification failures"""
        
        analysis["root_cause"] = "The modification was applied but failed verification checks."
        
        # Compare what was intended vs what actually happened
        if failure.modified_content and failure.original_content:
            actual_diff = self._generate_diff(
                failure.original_content,
                failure.modified_content
            )
            intended_diff = self._generate_diff(
                failure.original_content,
                failure.original_content.replace(
                    failure.intended_original,
                    failure.intended_replacement,
                    1
                )
            )
            
            analysis["context"]["actual_changes"] = actual_diff
            analysis["context"]["intended_changes"] = intended_diff
            
            if actual_diff != intended_diff:
                analysis["root_cause"] += "\n\nThe actual changes differ from intended changes."
        
        analysis["suggestions"] = [
            "Review the actual changes made to the file",
            "Check if the replacement code is correct",
            "Verify all imports and dependencies are present",
            "Ensure the change doesn't break existing functionality"
        ]
    
    def _analyze_generic_failure(self, failure: ModificationFailure, analysis: Dict):
        """Analyze failures that don't fit other categories"""
        
        analysis["root_cause"] = f"Modification failed: {failure.error_message}"
        
        analysis["suggestions"] = [
            "Review the error message carefully",
            "Check if the file exists and is accessible",
            "Verify you have the correct file path",
            "Try a different approach to making the change"
        ]
    
    def _find_similar_code_blocks(self, content: str, target: str, 
                                  threshold: float = 0.6) -> List[Dict]:
        """Find code blocks similar to the target"""
        
        target_lines = [l.strip() for l in target.strip().split('\n') if l.strip()]
        content_lines = content.split('\n')
        
        matches = []
        window_size = len(target_lines)
        
        for i in range(len(content_lines) - window_size + 1):
            window_lines = content_lines[i:i + window_size]
            window = '\n'.join(window_lines)
            
            # Calculate similarity
            ratio = difflib.SequenceMatcher(None, target, window).ratio()
            
            if ratio >= threshold:
                matches.append({
                    "line_number": i + 1,
                    "similarity": ratio,
                    "code": window,
                    "context_before": '\n'.join(content_lines[max(0, i-2):i]),
                    "context_after": '\n'.join(content_lines[i+window_size:i+window_size+2])
                })
        
        # Sort by similarity
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        return matches
    
    def _analyze_whitespace_differences(self, content: str, target: str) -> Optional[str]:
        """Analyze whitespace differences between content and target"""
        
        # Check for leading/trailing whitespace
        target_stripped = target.strip()
        
        # Check if target exists when stripped
        if target_stripped in content:
            return "Target code exists but with different leading/trailing whitespace"
        
        # Check for tab vs space differences
        target_spaces = target.replace('\t', '    ')
        target_tabs = target.replace('    ', '\t')
        
        if target_spaces in content:
            return "Target uses tabs but file uses spaces"
        if target_tabs in content:
            return "Target uses spaces but file uses tabs"
        
        # Check for different amounts of indentation
        target_lines = target.split('\n')
        for line in content.split('\n'):
            if line.strip() == target_lines[0].strip():
                file_indent = len(line) - len(line.lstrip())
                target_indent = len(target_lines[0]) - len(target_lines[0].lstrip())
                if file_indent != target_indent:
                    return f"Indentation mismatch: file uses {file_indent} spaces, target uses {target_indent}"
        
        return None
    
    def _check_line_endings(self, content: str, target: str) -> Optional[str]:
        """Check for line ending differences"""
        
        has_crlf_content = '\r\n' in content
        has_crlf_target = '\r\n' in target
        
        if has_crlf_content != has_crlf_target:
            content_type = "CRLF (Windows)" if has_crlf_content else "LF (Unix)"
            target_type = "CRLF (Windows)" if has_crlf_target else "LF (Unix)"
            return f"File uses {content_type}, target uses {target_type}"
        
        return None
    
    def _identify_syntax_issues(self, code: str) -> List[str]:
        """Identify specific syntax issues in code"""
        
        issues = []
        
        # Check for common syntax issues
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for missing colons
            if stripped.startswith(('if ', 'elif ', 'else', 'for ', 'while ', 
                                   'def ', 'class ', 'try', 'except', 'finally')):
                if not stripped.endswith(':'):
                    issues.append(f"Line {i}: Missing colon at end of statement")
            
            # Check for unmatched brackets
            open_brackets = line.count('(') + line.count('[') + line.count('{')
            close_brackets = line.count(')') + line.count(']') + line.count('}')
            if open_brackets != close_brackets:
                issues.append(f"Line {i}: Unmatched brackets")
            
            # Check for unmatched quotes
            single_quotes = line.count("'") - line.count("\\'")
            double_quotes = line.count('"') - line.count('\&quot;')
            if single_quotes % 2 != 0:
                issues.append(f"Line {i}: Unmatched single quotes")
            if double_quotes % 2 != 0:
                issues.append(f"Line {i}: Unmatched double quotes")
        
        return issues
    
    def _detect_indentation(self, code: str) -> str:
        """Detect the indentation style used in code"""
        
        lines = [l for l in code.split('\n') if l.strip()]
        if not lines:
            return "No indentation"
        
        # Check first indented line
        for line in lines:
            if line.startswith(' ') or line.startswith('\t'):
                if line.startswith('\t'):
                    return "Tabs"
                else:
                    spaces = len(line) - len(line.lstrip())
                    return f"{spaces} spaces"
        
        return "No indentation"
    
    def _generate_diff(self, original: str, modified: str) -> str:
        """Generate a unified diff"""
        
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            lineterm=''
        )
        return ''.join(diff)
    
    def _generate_ai_feedback(self, failure: ModificationFailure, analysis: Dict) -> str:
        """Generate comprehensive feedback for the AI"""
        
        feedback = f"""
# MODIFICATION FAILURE ANALYSIS

## Summary
Your attempt to modify `{failure.filepath}` failed.

**Failure Type:** {analysis['failure_type']}
**Error:** {failure.error_message}

## Root Cause
{analysis['root_cause']}

## What You Tried to Do

### Original Code You Tried to Replace:
```python
{failure.intended_original}
```

### Replacement Code You Provided:
```python
{failure.intended_replacement}
```

## File Context

### Current File Content (relevant section):
"""
        
        # Add relevant file section
        if failure.original_content:
            # Find the area around where the change was supposed to happen
            lines = failure.original_content.split('\n')
            if len(lines) > 20:
                # Show first 10 and last 10 lines
                feedback += "```python\n"
                feedback += '\n'.join(lines[:10])
                feedback += "\n... (content truncated) ...\n"
                feedback += '\n'.join(lines[-10:])
                feedback += "\n```\n"
            else:
                feedback += f"```python\n{failure.original_content}\n```\n"
        
        # Add similar matches if found
        if "similar_matches" in analysis["context"] and analysis["context"]["similar_matches"]:
            feedback += "\n## Similar Code Found in File\n\n"
            for i, match in enumerate(analysis["context"]["similar_matches"][:2], 1):
                feedback += f"### Match {i} (Line {match['line_number']}, {match['similarity']:.1%} similar):\n"
                feedback += "```python\n"
                if match.get('context_before'):
                    feedback += f"{match['context_before']}\n"
                feedback += f"{match['code']}\n"
                if match.get('context_after'):
                    feedback += f"{match['context_after']}\n"
                feedback += "```\n\n"
        
        # Add patch if available
        if failure.patch:
            feedback += "\n## Intended Changes (Patch)\n"
            feedback += f"```diff\n{failure.patch}\n```\n"
        
        # Add suggestions
        feedback += "\n## Suggestions for Next Attempt\n\n"
        for i, suggestion in enumerate(analysis['suggestions'], 1):
            feedback += f"{i}. {suggestion}\n"
        
        # Add specific guidance based on failure type
        if analysis['failure_type'] == "CODE_NOT_FOUND":
            feedback += """
## How to Fix This

1. **Read the file again** using `read_file` to see the current content
2. **Copy the EXACT code** from the file, including all whitespace
3. **Use a larger code block** that includes surrounding lines for context
4. **Verify the code hasn't already been changed** by checking recent modifications

Example of correct approach:
```python
# Instead of trying to replace just one line:
curses.cbreak()

# Replace a larger block with context:
try:
    self.stdscr.keypad(True)
    curses.cbreak()
    curses.noecho()
```
"""
        elif analysis['failure_type'] == "SYNTAX_ERROR":
            feedback += """
## How to Fix This

1. **Test your replacement code** in isolation first
2. **Check for missing colons** after if/for/while/def/class statements
3. **Verify all brackets match** - (), [], {}
4. **Ensure proper indentation** - use consistent spaces or tabs
5. **Check string quotes** - make sure all strings are properly closed
"""
        
        feedback += "\n## Next Steps\n\n"
        feedback += "Please try again with the corrections suggested above.\n"
        
        return feedback


def create_failure_report(failure: ModificationFailure, 
                         analysis: Dict,
                         output_dir: Path) -> Path:
    """Create a detailed failure report file"""
    
    timestamp = failure.timestamp.strftime("%Y%m%d_%H%M%S")
    filename = f"failure_{timestamp}_{Path(failure.filepath).stem}.md"
    report_path = output_dir / filename
    
    # Write the AI feedback as the report
    report_path.write_text(analysis["ai_feedback"])
    
    return report_path