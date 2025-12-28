"""
Conversation History Pruning

Implements intelligent pruning strategies to prevent unbounded memory growth
while preserving important context.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from pathlib import Path

from ..logging_setup import get_logger


@dataclass
class PruningConfig:
    """Configuration for conversation pruning"""
    max_messages: int = 50  # Maximum messages to keep
    preserve_first_n: int = 5  # Always keep first N messages (context)
    preserve_last_n: int = 20  # Always keep last N messages (recent)
    preserve_errors: bool = True  # Always keep error messages
    preserve_decisions: bool = True  # Always keep decision points
    summarize_pruned: bool = True  # Create summary of pruned messages
    min_prune_age_minutes: int = 30  # Only prune messages older than this


class ConversationPruner:
    """
    Intelligent conversation history pruning.
    
    Strategies:
    1. Sliding window: Keep first N + last N messages
    2. Importance-based: Preserve errors, decisions, tool calls
    3. Summarization: Create summaries of pruned sections
    4. Age-based: Only prune old messages
    """
    
    def __init__(self, config: Optional[PruningConfig] = None):
        """
        Initialize pruner.
        
        Args:
            config: Pruning configuration
        """
        self.config = config or PruningConfig()
        self.logger = get_logger()
        self.pruning_stats = {
            "total_pruned": 0,
            "summaries_created": 0,
            "errors_preserved": 0,
            "decisions_preserved": 0
        }
    
    def should_prune(self, messages: List[Dict]) -> bool:
        """
        Check if pruning is needed.
        
        Args:
            messages: List of messages
            
        Returns:
            True if pruning needed
        """
        return len(messages) > self.config.max_messages
    
    def prune_messages(self, messages: List[Dict]) -> Tuple[List[Dict], Optional[str]]:
        """
        Prune messages using intelligent strategy.
        
        Args:
            messages: List of messages to prune
            
        Returns:
            Tuple of (pruned_messages, summary_of_pruned)
        """
        if not self.should_prune(messages):
            return messages, None
        
        self.logger.info(f"Pruning conversation: {len(messages)} messages -> {self.config.max_messages}")
        
        # Identify important messages
        important_indices = self._identify_important_messages(messages)
        
        # Calculate which messages to keep
        keep_indices = self._calculate_keep_indices(messages, important_indices)
        
        # Separate kept and pruned messages
        kept_messages = []
        pruned_messages = []
        
        for i, msg in enumerate(messages):
            if i in keep_indices:
                kept_messages.append(msg)
            else:
                pruned_messages.append(msg)
        
        # Create summary of pruned messages
        summary = None
        if self.config.summarize_pruned and pruned_messages:
            summary = self._create_summary(pruned_messages)
            self.pruning_stats["summaries_created"] += 1
        
        self.pruning_stats["total_pruned"] += len(pruned_messages)
        
        self.logger.info(f"Pruned {len(pruned_messages)} messages, kept {len(kept_messages)}")
        
        return kept_messages, summary
    
    def _identify_important_messages(self, messages: List[Dict]) -> set:
        """
        Identify messages that should be preserved.
        
        Args:
            messages: List of messages
            
        Returns:
            Set of indices to preserve
        """
        important = set()
        
        for i, msg in enumerate(messages):
            # Always preserve first N messages (initial context)
            if i < self.config.preserve_first_n:
                important.add(i)
                continue
            
            # Always preserve last N messages (recent context)
            if i >= len(messages) - self.config.preserve_last_n:
                important.add(i)
                continue
            
            # Preserve error messages
            if self.config.preserve_errors:
                content = msg.get("content", "").lower()
                if any(keyword in content for keyword in ["error", "exception", "failed", "traceback"]):
                    important.add(i)
                    self.pruning_stats["errors_preserved"] += 1
                    continue
            
            # Preserve decision points
            if self.config.preserve_decisions:
                content = msg.get("content", "").lower()
                if any(keyword in content for keyword in ["decided", "choosing", "selected", "strategy"]):
                    important.add(i)
                    self.pruning_stats["decisions_preserved"] += 1
                    continue
            
            # Preserve messages with tool calls
            if msg.get("tool_calls") or msg.get("metadata", {}).get("has_tool_calls"):
                important.add(i)
                continue
            
            # Check age - don't prune recent messages
            if "timestamp" in msg:
                try:
                    msg_time = datetime.fromisoformat(msg["timestamp"])
                    age_minutes = (datetime.now() - msg_time).total_seconds() / 60
                    if age_minutes < self.config.min_prune_age_minutes:
                        important.add(i)
                        continue
                except (ValueError, TypeError):
                    pass
        
        return important
    
    def _calculate_keep_indices(self, messages: List[Dict], important_indices: set) -> set:
        """
        Calculate which message indices to keep.
        
        Args:
            messages: List of messages
            important_indices: Indices marked as important
            
        Returns:
            Set of indices to keep
        """
        # Start with important indices
        keep = important_indices.copy()
        
        # If we're still over the limit, we need to be more aggressive
        if len(keep) > self.config.max_messages:
            # Keep only first N and last N, plus critical errors
            keep = set()
            
            # First N
            for i in range(min(self.config.preserve_first_n, len(messages))):
                keep.add(i)
            
            # Last N
            for i in range(max(0, len(messages) - self.config.preserve_last_n), len(messages)):
                keep.add(i)
            
            # Add back critical errors only
            for i in important_indices:
                if i not in keep:
                    msg = messages[i]
                    content = msg.get("content", "").lower()
                    if "error" in content or "exception" in content:
                        keep.add(i)
                        if len(keep) >= self.config.max_messages:
                            break
        
        # If still too many, trim from middle
        if len(keep) > self.config.max_messages:
            # Sort indices
            sorted_keep = sorted(keep)
            
            # Keep first N and last N
            final_keep = set()
            for i in range(min(self.config.preserve_first_n, len(sorted_keep))):
                final_keep.add(sorted_keep[i])
            for i in range(max(0, len(sorted_keep) - self.config.preserve_last_n), len(sorted_keep)):
                final_keep.add(sorted_keep[i])
            
            keep = final_keep
        
        return keep
    
    def _create_summary(self, pruned_messages: List[Dict]) -> str:
        """
        Create a summary of pruned messages.
        
        Args:
            pruned_messages: Messages that were pruned
            
        Returns:
            Summary text
        """
        if not pruned_messages:
            return ""
        
        summary_parts = [
            f"[Pruned {len(pruned_messages)} messages from conversation history]",
            ""
        ]
        
        # Count by role
        role_counts = {}
        for msg in pruned_messages:
            role = msg.get("role", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1
        
        summary_parts.append("Message breakdown:")
        for role, count in sorted(role_counts.items()):
            summary_parts.append(f"  - {role}: {count}")
        
        # Extract key topics/actions
        actions = []
        errors = []
        
        for msg in pruned_messages:
            content = msg.get("content", "")
            
            # Extract errors
            if "error" in content.lower() or "exception" in content.lower():
                # Get first line of error
                first_line = content.split("\n")[0][:100]
                errors.append(first_line)
            
            # Extract tool calls
            if msg.get("tool_calls"):
                for tool_call in msg["tool_calls"]:
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get("name", "unknown")
                        actions.append(f"Called {tool_name}")
        
        if actions:
            summary_parts.append("")
            summary_parts.append("Key actions:")
            for action in actions[:5]:  # Limit to 5
                summary_parts.append(f"  - {action}")
        
        if errors:
            summary_parts.append("")
            summary_parts.append("Errors encountered:")
            for error in errors[:3]:  # Limit to 3
                summary_parts.append(f"  - {error}")
        
        # Time range
        timestamps = [msg.get("timestamp") for msg in pruned_messages if msg.get("timestamp")]
        if timestamps:
            try:
                times = [datetime.fromisoformat(ts) for ts in timestamps]
                earliest = min(times)
                latest = max(times)
                duration = (latest - earliest).total_seconds() / 60
                summary_parts.append("")
                summary_parts.append(f"Time range: {earliest.strftime('%H:%M')} - {latest.strftime('%H:%M')} ({duration:.1f} minutes)")
            except (ValueError, TypeError):
                pass
        
        return "\n".join(summary_parts)
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get pruning statistics.
        
        Returns:
            Dict with stats
        """
        return self.pruning_stats.copy()
    
    def reset_stats(self):
        """Reset pruning statistics."""
        self.pruning_stats = {
            "total_pruned": 0,
            "summaries_created": 0,
            "errors_preserved": 0,
            "decisions_preserved": 0
        }


class AutoPruningConversationThread:
    """
    Conversation thread with automatic pruning.
    
    Wraps a standard ConversationThread and automatically prunes
    when message count exceeds threshold.
    """
    
    def __init__(self, thread, pruner: Optional[ConversationPruner] = None):
        """
        Initialize auto-pruning thread.
        
        Args:
            thread: ConversationThread to wrap
            pruner: ConversationPruner instance
        """
        self.thread = thread
        self.pruner = pruner or ConversationPruner()
        self.logger = get_logger()
        self.prune_summaries: List[str] = []
    
    def add_message(self, *args, **kwargs):
        """Add message and auto-prune if needed."""
        # Add message to thread
        self.thread.add_message(*args, **kwargs)
        
        # Check if pruning needed
        if self.pruner.should_prune(self.thread.messages):
            self._auto_prune()
    
    def _auto_prune(self):
        """Automatically prune conversation."""
        self.logger.info("Auto-pruning conversation thread")
        
        # Prune messages
        pruned_messages, summary = self.pruner.prune_messages(self.thread.messages)
        
        # Update thread
        self.thread.messages = pruned_messages
        
        # Store summary
        if summary:
            self.prune_summaries.append(summary)
            
            # Add summary as system message
            self.thread.add_message(
                role="system",
                content=summary,
                metadata={"type": "prune_summary"}
            )
        
        # Update metadata
        self.thread.metadata["message_count"] = len(pruned_messages)
        self.thread.metadata["pruned_count"] = self.thread.metadata.get("pruned_count", 0) + 1
    
    def get_context(self, *args, **kwargs):
        """Get context from wrapped thread."""
        return self.thread.get_context(*args, **kwargs)
    
    def get_full_history(self):
        """Get full history from wrapped thread."""
        return self.thread.get_full_history()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get combined stats."""
        thread_stats = self.thread.get_stats()
        pruner_stats = self.pruner.get_stats()
        
        return {
            **thread_stats,
            "pruning": pruner_stats,
            "prune_summaries_count": len(self.prune_summaries)
        }
    
    def __getattr__(self, name):
        """Delegate other attributes to wrapped thread."""
        return getattr(self.thread, name)