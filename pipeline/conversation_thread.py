"""
Conversation Thread Manager

Maintains persistent conversation context across multiple debugging attempts,
allowing specialists to build on previous analysis and attempts.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json


@dataclass
class Message:
    """A single message in the conversation"""
    role: str  # system, user, assistant, specialist
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    agent_name: Optional[str] = None  # Which specialist sent this
    tool_calls: List[Dict] = field(default_factory=list)
    tool_results: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "agent_name": self.agent_name,
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "metadata": self.metadata
        }


@dataclass
class AttemptRecord:
    """Record of a single fix attempt"""
    attempt_number: int
    timestamp: datetime
    agent_name: str
    original_code: str
    replacement_code: str
    success: bool
    error_message: Optional[str] = None
    tool_calls: List[Dict] = field(default_factory=list)
    tool_results: List[Dict] = field(default_factory=list)
    analysis: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            "attempt_number": self.attempt_number,
            "timestamp": self.timestamp.isoformat(),
            "agent_name": self.agent_name,
            "original_code": self.original_code,
            "replacement_code": self.replacement_code,
            "success": self.success,
            "error_message": self.error_message,
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "analysis": self.analysis
        }


class ConversationThread:
    """
    Manages a persistent conversation thread for debugging a single issue.
    
    Maintains:
    - Full message history
    - All attempt records
    - File state snapshots
    - Specialist consultations
    - Tool call history
    """
    
    def __init__(self, issue: Dict, project_dir: Path):
        self.issue = issue
        self.project_dir = project_dir
        # Sanitize filepath for use in filename (replace slashes with underscores)
        sanitized_filepath = issue['filepath'].replace('/', '_').replace('\\', '_')
        self.thread_id = f"{sanitized_filepath}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Conversation history
        self.messages: List[Message] = []
        
        # Attempt tracking
        self.attempts: List[AttemptRecord] = []
        self.current_attempt = 0
        
        # File state tracking
        self.file_snapshots: Dict[int, str] = {}  # attempt_number -> file_content
        self.patches: Dict[int, str] = {}  # attempt_number -> patch
        
        # Specialist consultations
        self.specialists_consulted: List[str] = []
        self.specialist_analyses: Dict[str, Dict] = {}
        
        # Context data
        self.context_data: Dict[str, Any] = {
            "whitespace_analysis": None,
            "syntax_analysis": None,
            "indentation_analysis": None,
            "similar_code_blocks": [],
            "file_history": []
        }
        
        # Initialize with issue context
        self._initialize_thread()
    
    def _initialize_thread(self):
        """Initialize the conversation thread with issue context"""
        
        # Read current file state
        filepath = self.issue.get("filepath")
        if filepath:
            full_path = self.project_dir / filepath
            if full_path.exists():
                self.file_snapshots[0] = full_path.read_text()
        
        # Add initial system message
        self.add_message(
            role="system",
            content=self._generate_initial_context(),
            metadata={"type": "initialization"}
        )
    
    def _generate_initial_context(self) -> str:
        """Generate comprehensive initial context"""
        
        context = f"""# Debugging Session Initialized

## Issue Details
- **File:** {self.issue.get('filepath')}
- **Type:** {self.issue.get('type')}
- **Message:** {self.issue.get('message')}
- **Line:** {self.issue.get('line', 'N/A')}

## Current File State
```python
{self.file_snapshots.get(0, 'File not found')}
```

## Objective
Fix this issue through collaborative analysis and iterative attempts.
All specialists have access to the full conversation history and can build on previous analysis.
"""
        return context
    
    def add_message(self, role: str, content: str, 
                   agent_name: Optional[str] = None,
                   tool_calls: List[Dict] = None,
                   tool_results: List[Dict] = None,
                   metadata: Dict = None) -> Message:
        """Add a message to the conversation thread"""
        
        message = Message(
            role=role,
            content=content,
            agent_name=agent_name,
            tool_calls=tool_calls or [],
            tool_results=tool_results or [],
            metadata=metadata or {}
        )
        
        self.messages.append(message)
        return message
    
    def record_attempt(self, agent_name: str, original_code: str, 
                      replacement_code: str, success: bool,
                      error_message: Optional[str] = None,
                      tool_calls: List[Dict] = None,
                      tool_results: List[Dict] = None,
                      analysis: Optional[Dict] = None) -> AttemptRecord:
        """Record a fix attempt"""
        
        self.current_attempt += 1
        
        # Snapshot file state after attempt
        filepath = self.issue.get("filepath")
        if filepath:
            full_path = self.project_dir / filepath
            if full_path.exists():
                self.file_snapshots[self.current_attempt] = full_path.read_text()
        
        attempt = AttemptRecord(
            attempt_number=self.current_attempt,
            timestamp=datetime.now(),
            agent_name=agent_name,
            original_code=original_code,
            replacement_code=replacement_code,
            success=success,
            error_message=error_message,
            tool_calls=tool_calls or [],
            tool_results=tool_results or [],
            analysis=analysis
        )
        
        self.attempts.append(attempt)
        
        # Add to conversation
        status = "✅ SUCCESS" if success else "❌ FAILED"
        self.add_message(
            role="assistant",
            content=f"## Attempt #{self.current_attempt} - {status}\n\n{error_message or 'Fix applied successfully'}",
            agent_name=agent_name,
            tool_calls=tool_calls or [],
            tool_results=tool_results or [],
            metadata={"attempt_number": self.current_attempt, "success": success}
        )
        
        return attempt
    
    def add_specialist_analysis(self, specialist_name: str, analysis: Dict):
        """Add analysis from a specialist"""
        
        if specialist_name not in self.specialists_consulted:
            self.specialists_consulted.append(specialist_name)
        
        self.specialist_analyses[specialist_name] = analysis
        
        # Add to conversation
        self.add_message(
            role="specialist",
            content=f"## Analysis from {specialist_name}\n\n{json.dumps(analysis, indent=2)}",
            agent_name=specialist_name,
            metadata={"type": "specialist_analysis"}
        )
    
    def add_patch(self, attempt_number: int, patch: str):
        """Add a patch for an attempt"""
        self.patches[attempt_number] = patch
    
    def update_context_data(self, key: str, value: Any):
        """Update context data"""
        self.context_data[key] = value
    
    def get_conversation_history(self, include_tool_calls: bool = True) -> List[Dict]:
        """Get conversation history in format suitable for LLM"""
        
        history = []
        for msg in self.messages:
            message_dict = {
                "role": msg.role if msg.role != "specialist" else "assistant",
                "content": msg.content
            }
            
            if include_tool_calls and msg.tool_calls:
                message_dict["tool_calls"] = msg.tool_calls
            
            if msg.agent_name:
                message_dict["content"] = f"[{msg.agent_name}] {msg.content}"
            
            history.append(message_dict)
        
        return history
    
    def get_attempt_summary(self) -> str:
        """Get a summary of all attempts"""
        
        if not self.attempts:
            return "No attempts made yet."
        
        summary = f"## Attempt History ({len(self.attempts)} attempts)\n\n"
        
        for attempt in self.attempts:
            status = "✅" if attempt.success else "❌"
            summary += f"### Attempt #{attempt.attempt_number} {status}\n"
            summary += f"- **Agent:** {attempt.agent_name}\n"
            summary += f"- **Time:** {attempt.timestamp.strftime('%H:%M:%S')}\n"
            
            if not attempt.success:
                summary += f"- **Error:** {attempt.error_message}\n"
            
            summary += f"\n**Original Code:**\n```python\n{attempt.original_code[:200]}...\n```\n\n"
            summary += f"**Replacement Code:**\n```python\n{attempt.replacement_code[:200]}...\n```\n\n"
            
            if attempt.analysis:
                summary += f"**Analysis:** {attempt.analysis.get('failure_type', 'N/A')}\n\n"
        
        return summary
    
    def get_file_diff(self, from_attempt: int = 0, to_attempt: int = None) -> str:
        """Get diff between file states"""
        
        if to_attempt is None:
            to_attempt = self.current_attempt
        
        from_content = self.file_snapshots.get(from_attempt, "")
        to_content = self.file_snapshots.get(to_attempt, "")
        
        if not from_content or not to_content:
            return "File snapshots not available"
        
        import difflib
        diff = difflib.unified_diff(
            from_content.splitlines(keepends=True),
            to_content.splitlines(keepends=True),
            fromfile=f"Attempt {from_attempt}",
            tofile=f"Attempt {to_attempt}"
        )
        
        return ''.join(diff)
    
    def get_comprehensive_context(self) -> str:
        """Get comprehensive context for specialists"""
        
        context = f"""# Comprehensive Debugging Context

## Thread ID: {self.thread_id}

## Issue
{json.dumps(self.issue, indent=2)}

## Attempt Summary
{self.get_attempt_summary()}

## File State Evolution
- **Initial State:** {len(self.file_snapshots.get(0, ''))} characters
- **Current State:** {len(self.file_snapshots.get(self.current_attempt, ''))} characters
- **Changes:** {self.current_attempt} attempts made

## Specialists Consulted
{', '.join(self.specialists_consulted) if self.specialists_consulted else 'None yet'}

## Context Data
"""
        
        for key, value in self.context_data.items():
            if value:
                context += f"\n### {key}\n{json.dumps(value, indent=2)}\n"
        
        return context
    
    def save_thread(self, output_dir: Path):
        """Save the complete conversation thread"""
        
        output_dir.mkdir(exist_ok=True)
        thread_file = output_dir / f"thread_{self.thread_id}.json"
        
        thread_data = {
            "thread_id": self.thread_id,
            "issue": self.issue,
            "messages": [msg.to_dict() for msg in self.messages],
            "attempts": [att.to_dict() for att in self.attempts],
            "file_snapshots": self.file_snapshots,
            "patches": self.patches,
            "specialists_consulted": self.specialists_consulted,
            "specialist_analyses": self.specialist_analyses,
            "context_data": self.context_data
        }
        
        thread_file.write_text(json.dumps(thread_data, indent=2))
        return thread_file
    
    def should_continue(self, max_attempts: int = 999999) -> bool:  # UNLIMITED attempts
        """Determine if we should continue trying"""
        
        # Stop if we succeeded
        if self.attempts and self.attempts[-1].success:
            return False
        
        # Stop if we hit max attempts
        if self.current_attempt >= max_attempts:
            return False
        
        # Continue if we have new information from specialists
        if len(self.specialists_consulted) < 3:  # Can consult up to 3 specialists
            return True
        
        return True