"""
Pattern Feedback System

Tracks AI behavior patterns, detects workflow violations, and dynamically
adapts system prompts based on learned patterns.

This system enables self-correcting behavior by:
1. Tracking when AI violates workflow steps
2. Identifying repeat violation patterns
3. Dynamically adding prompt reminders
4. Learning from successful adaptations
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json
from pathlib import Path


@dataclass
class ViolationRecord:
    """Record of a workflow violation"""
    phase: str
    violation_type: str
    timestamp: datetime
    context: Dict
    severity: str  # "low", "medium", "high"
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None


@dataclass
class PatternStats:
    """Statistics for a violation pattern"""
    violation_type: str
    phase: str
    count: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    resolution_rate: float = 0.0
    avg_time_to_resolution: float = 0.0
    prompt_additions_applied: int = 0
    effectiveness_score: float = 0.0


class PromptFeedbackSystem:
    """
    System for tracking AI behavior patterns and adapting prompts.
    
    Workflow:
    1. Phases report violations via track_workflow_violation()
    2. System detects patterns in violations
    3. System generates dynamic prompt additions
    4. Phases request additions via get_prompt_additions()
    5. System tracks effectiveness of additions
    6. System learns which additions work best
    """
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.violations: List[ViolationRecord] = []
        self.patterns: Dict[str, PatternStats] = {}
        self.active_additions: Dict[str, List[str]] = defaultdict(list)
        self.addition_effectiveness: Dict[str, float] = {}
        
        # Violation type definitions
        self.violation_types = {
            # Coding phase violations
            "skipped_discovery": {
                "phase": "coding",
                "severity": "high",
                "description": "AI skipped find_similar_files step",
                "prompt_addition": """
⚠️ CRITICAL REMINDER - RECENT VIOLATION DETECTED:
You have been skipping the DISCOVERY step (find_similar_files).
This is a MANDATORY step that MUST be performed FIRST.

ENFORCEMENT:
- STEP 1 is NOT optional
- You MUST call find_similar_files BEFORE any other action
- Skipping this step is a CRITICAL ERROR
- This violation has been detected multiple times

IMMEDIATE ACTION REQUIRED:
Before proceeding, call find_similar_files with the target filename.
"""
            },
            "skipped_validation": {
                "phase": "coding",
                "severity": "high",
                "description": "AI skipped validate_filename step",
                "prompt_addition": """
⚠️ CRITICAL REMINDER - RECENT VIOLATION DETECTED:
You have been skipping the VALIDATION step (validate_filename).
This is a MANDATORY step that MUST be performed SECOND.

ENFORCEMENT:
- STEP 2 is NOT optional
- You MUST call validate_filename BEFORE creating files
- Skipping this step is a CRITICAL ERROR
- This violation has been detected multiple times

IMMEDIATE ACTION REQUIRED:
Before creating any file, call validate_filename with the filename.
"""
            },
            "created_duplicate": {
                "phase": "coding",
                "severity": "high",
                "description": "AI created duplicate file despite similar files existing",
                "prompt_addition": """
⚠️ CRITICAL REMINDER - RECENT VIOLATION DETECTED:
You have been creating DUPLICATE files when similar files already exist.
This is a CRITICAL ERROR that wastes resources and creates confusion.

ENFORCEMENT:
- If similarity > 80%, you MUST modify existing file
- If similarity > 60%, you SHOULD modify existing file
- Creating duplicates is a CRITICAL ERROR
- This violation has been detected multiple times

IMMEDIATE ACTION REQUIRED:
Review find_similar_files results carefully before creating new files.
"""
            },
            "stopped_refactoring_early": {
                "phase": "refactoring",
                "severity": "high",
                "description": "AI stopped refactoring with conflicts remaining",
                "prompt_addition": """
⚠️ CRITICAL REMINDER - RECENT VIOLATION DETECTED:
You have been stopping refactoring with conflicts still remaining.
Refactoring is ITERATIVE and MUST continue until NO conflicts remain.

ENFORCEMENT:
- You MUST call find_all_conflicts after each change
- If conflicts remain, you MUST continue iterating
- Stopping early is a CRITICAL ERROR
- This violation has been detected multiple times

IMMEDIATE ACTION REQUIRED:
After each merge/rename, call find_all_conflicts to verify completion.
"""
            },
            "missing_tool_call": {
                "phase": "qa",
                "severity": "high",
                "description": "AI provided text description without tool call",
                "prompt_addition": """
⚠️ CRITICAL REMINDER - RECENT VIOLATION DETECTED:
You have been providing text descriptions without using required tools.
EVERY finding MUST be reported via tool calls.

ENFORCEMENT:
- Text descriptions are INVALID
- You MUST use report_issue or approve_code
- The "name" field is MANDATORY
- This violation has been detected multiple times

IMMEDIATE ACTION REQUIRED:
Use proper tool calls with "name" field for ALL findings.
"""
            },
            "skipped_validation_debug": {
                "phase": "debugging",
                "severity": "high",
                "description": "AI modified code without validation",
                "prompt_addition": """
⚠️ CRITICAL REMINDER - RECENT VIOLATION DETECTED:
You have been modifying code without proper validation.
You MUST validate before fixing (get_function_signature, read_file).

ENFORCEMENT:
- STEP 2 (validation) is MANDATORY
- You MUST check function signatures before modifying calls
- You MUST verify indentation before replacing code
- This violation has been detected multiple times

IMMEDIATE ACTION REQUIRED:
Call get_function_signature or read_file BEFORE modifying code.
"""
            },
            "small_code_block": {
                "phase": "debugging",
                "severity": "medium",
                "description": "AI used single-line replacement instead of large block",
                "prompt_addition": """
⚠️ REMINDER - RECENT ISSUE DETECTED:
You have been using single-line code replacements.
You MUST use LARGER code blocks (5-10 lines) with context.

BEST PRACTICE:
- Include 2-3 lines before the error
- Include the error line
- Include 2-3 lines after the error
- Match indentation exactly

IMMEDIATE ACTION REQUIRED:
Use larger code blocks for all replacements.
"""
            },
            "no_step_tracking": {
                "phase": "all",
                "severity": "medium",
                "description": "AI didn't state which step being executed",
                "prompt_addition": """
⚠️ REMINDER - RECENT ISSUE DETECTED:
You have not been stating which step you're executing.
Step tracking is REQUIRED for all phases.

REQUIREMENT:
- State "STEP X: [action]" before each action
- Confirm "✅ STEP X COMPLETE: [result]" after each action
- Explain transitions between steps

IMMEDIATE ACTION REQUIRED:
State your current step before proceeding.
"""
            },
        }
        
        # Load existing data if available
        self._load_data()
    
    def track_workflow_violation(
        self,
        phase: str,
        violation_type: str,
        context: Optional[Dict] = None,
        severity: Optional[str] = None
    ) -> None:
        """
        Track a workflow violation.
        
        Args:
            phase: Phase where violation occurred
            violation_type: Type of violation (from violation_types)
            context: Additional context about the violation
            severity: Override default severity
        """
        if violation_type not in self.violation_types:
            # Unknown violation type - add as generic
            violation_def = {
                "phase": phase,
                "severity": severity or "medium",
                "description": f"Unknown violation: {violation_type}",
                "prompt_addition": f"⚠️ Issue detected: {violation_type}"
            }
        else:
            violation_def = self.violation_types[violation_type]
        
        # Create violation record
        record = ViolationRecord(
            phase=phase,
            violation_type=violation_type,
            timestamp=datetime.now(),
            context=context or {},
            severity=severity or violation_def["severity"]
        )
        
        self.violations.append(record)
        
        # Update pattern statistics
        pattern_key = f"{phase}:{violation_type}"
        if pattern_key not in self.patterns:
            self.patterns[pattern_key] = PatternStats(
                violation_type=violation_type,
                phase=phase,
                first_seen=record.timestamp
            )
        
        pattern = self.patterns[pattern_key]
        pattern.count += 1
        pattern.last_seen = record.timestamp
        
        # If this is a repeat violation (count > 2), add prompt reminder
        if pattern.count >= 2 and pattern_key not in self.active_additions[phase]:
            self.active_additions[phase].append(violation_type)
            pattern.prompt_additions_applied += 1
        
        # Save data
        self._save_data()
    
    def mark_violation_resolved(
        self,
        phase: str,
        violation_type: str
    ) -> None:
        """
        Mark a violation as resolved (AI followed workflow correctly).
        
        Args:
            phase: Phase where violation was resolved
            violation_type: Type of violation that was resolved
        """
        # Find most recent unresolved violation of this type
        for record in reversed(self.violations):
            if (record.phase == phase and 
                record.violation_type == violation_type and 
                not record.resolved):
                record.resolved = True
                record.resolution_timestamp = datetime.now()
                
                # Update pattern statistics
                pattern_key = f"{phase}:{violation_type}"
                if pattern_key in self.patterns:
                    pattern = self.patterns[pattern_key]
                    
                    # Calculate resolution rate
                    resolved_count = sum(
                        1 for v in self.violations 
                        if v.phase == phase and 
                           v.violation_type == violation_type and 
                           v.resolved
                    )
                    pattern.resolution_rate = resolved_count / pattern.count
                    
                    # Calculate average time to resolution
                    resolution_times = [
                        (v.resolution_timestamp - v.timestamp).total_seconds()
                        for v in self.violations
                        if v.phase == phase and
                           v.violation_type == violation_type and
                           v.resolved and
                           v.resolution_timestamp
                    ]
                    if resolution_times:
                        pattern.avg_time_to_resolution = sum(resolution_times) / len(resolution_times)
                    
                    # Calculate effectiveness score
                    # Higher score = better resolution rate + faster resolution
                    if pattern.prompt_additions_applied > 0:
                        pattern.effectiveness_score = (
                            pattern.resolution_rate * 0.7 +
                            (1.0 / (1.0 + pattern.avg_time_to_resolution / 3600)) * 0.3
                        )
                
                break
        
        # Save data
        self._save_data()
    
    def get_prompt_additions(self, phase: str) -> str:
        """
        Get dynamic prompt additions for a phase based on violation patterns.
        
        Args:
            phase: Phase to get additions for
            
        Returns:
            String with prompt additions (empty if none)
        """
        if phase not in self.active_additions:
            return ""
        
        additions = []
        for violation_type in self.active_additions[phase]:
            if violation_type in self.violation_types:
                addition = self.violation_types[violation_type]["prompt_addition"]
                additions.append(addition)
        
        if not additions:
            return ""
        
        return "\n\n" + "\n\n".join(additions)
    
    def get_pattern_summary(self, phase: Optional[str] = None) -> Dict:
        """
        Get summary of violation patterns.
        
        Args:
            phase: Optional phase to filter by
            
        Returns:
            Dictionary with pattern statistics
        """
        summary = {
            "total_violations": len(self.violations),
            "resolved_violations": sum(1 for v in self.violations if v.resolved),
            "active_patterns": len(self.patterns),
            "patterns": []
        }
        
        for pattern_key, pattern in self.patterns.items():
            if phase and pattern.phase != phase:
                continue
            
            summary["patterns"].append({
                "phase": pattern.phase,
                "violation_type": pattern.violation_type,
                "count": pattern.count,
                "resolution_rate": f"{pattern.resolution_rate:.1%}",
                "effectiveness_score": f"{pattern.effectiveness_score:.2f}",
                "prompt_additions_applied": pattern.prompt_additions_applied,
                "first_seen": pattern.first_seen.isoformat() if pattern.first_seen else None,
                "last_seen": pattern.last_seen.isoformat() if pattern.last_seen else None
            })
        
        # Sort by count (most frequent first)
        summary["patterns"].sort(key=lambda x: x["count"], reverse=True)
        
        return summary
    
    def clear_resolved_patterns(self, threshold: float = 0.8) -> int:
        """
        Clear prompt additions for patterns that are consistently resolved.
        
        Args:
            threshold: Resolution rate threshold (0.0-1.0)
            
        Returns:
            Number of patterns cleared
        """
        cleared = 0
        
        for pattern_key, pattern in list(self.patterns.items()):
            if pattern.resolution_rate >= threshold and pattern.count >= 5:
                # Pattern is consistently resolved - remove prompt addition
                if pattern.violation_type in self.active_additions[pattern.phase]:
                    self.active_additions[pattern.phase].remove(pattern.violation_type)
                    cleared += 1
        
        self._save_data()
        return cleared
    
    def _load_data(self) -> None:
        """Load violation data from file"""
        data_file = self.project_dir / ".autonomy" / "pattern_feedback.json"
        if not data_file.exists():
            return
        
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            # Load violations
            self.violations = [
                ViolationRecord(
                    phase=v["phase"],
                    violation_type=v["violation_type"],
                    timestamp=datetime.fromisoformat(v["timestamp"]),
                    context=v["context"],
                    severity=v["severity"],
                    resolved=v["resolved"],
                    resolution_timestamp=datetime.fromisoformat(v["resolution_timestamp"]) if v.get("resolution_timestamp") else None
                )
                for v in data.get("violations", [])
            ]
            
            # Load patterns
            for p in data.get("patterns", []):
                pattern = PatternStats(
                    violation_type=p["violation_type"],
                    phase=p["phase"],
                    count=p["count"],
                    first_seen=datetime.fromisoformat(p["first_seen"]) if p.get("first_seen") else None,
                    last_seen=datetime.fromisoformat(p["last_seen"]) if p.get("last_seen") else None,
                    resolution_rate=p["resolution_rate"],
                    avg_time_to_resolution=p["avg_time_to_resolution"],
                    prompt_additions_applied=p["prompt_additions_applied"],
                    effectiveness_score=p["effectiveness_score"]
                )
                pattern_key = f"{p['phase']}:{p['violation_type']}"
                self.patterns[pattern_key] = pattern
            
            # Load active additions
            self.active_additions = defaultdict(list, data.get("active_additions", {}))
            
        except Exception as e:
            print(f"Warning: Could not load pattern feedback data: {e}")
    
    def _save_data(self) -> None:
        """Save violation data to file"""
        data_dir = self.project_dir / ".autonomy"
        data_dir.mkdir(exist_ok=True)
        data_file = data_dir / "pattern_feedback.json"
        
        try:
            data = {
                "violations": [
                    {
                        "phase": v.phase,
                        "violation_type": v.violation_type,
                        "timestamp": v.timestamp.isoformat(),
                        "context": v.context,
                        "severity": v.severity,
                        "resolved": v.resolved,
                        "resolution_timestamp": v.resolution_timestamp.isoformat() if v.resolution_timestamp else None
                    }
                    for v in self.violations
                ],
                "patterns": [
                    {
                        "phase": p.phase,
                        "violation_type": p.violation_type,
                        "count": p.count,
                        "first_seen": p.first_seen.isoformat() if p.first_seen else None,
                        "last_seen": p.last_seen.isoformat() if p.last_seen else None,
                        "resolution_rate": p.resolution_rate,
                        "avg_time_to_resolution": p.avg_time_to_resolution,
                        "prompt_additions_applied": p.prompt_additions_applied,
                        "effectiveness_score": p.effectiveness_score
                    }
                    for p in self.patterns.values()
                ],
                "active_additions": dict(self.active_additions)
            }
            
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save pattern feedback data: {e}")