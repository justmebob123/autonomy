"""
Pattern Detector - Detects 6 types of infinite loops

This module analyzes action history to detect various types of loops:
1. Action Loops - Same action repeated
2. Modification Loops - Same file modified repeatedly
3. Conversation Loops - Same questions/responses
4. Circular Dependencies - A depends on B depends on A
5. State Cycles - System state cycling through same states
6. Pattern Repetition - Complex multi-step patterns repeating
"""

import re
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path

from .action_tracker import ActionTracker, Action
from .error_signature import ErrorSignature


@dataclass
class LoopDetection:
    """Represents a detected loop"""
    loop_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    evidence: List[str]
    suggestion: str
    actions_involved: List[Action]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'loop_type': self.loop_type,
            'severity': self.severity,
            'description': self.description,
            'evidence': self.evidence,
            'suggestion': self.suggestion,
            'action_count': len(self.actions_involved)
        }


class PatternDetector:
    """
    Detects various types of infinite loops in AI behavior.
    
    Uses ActionTracker history to identify patterns that indicate
    the system is stuck in a loop and not making progress.
    """
    
    def __init__(self, action_tracker: ActionTracker):
        """
        Initialize pattern detector.
        
        Args:
            action_tracker: ActionTracker instance to analyze
        """
        self.tracker = action_tracker
        
        # Track current error signature to detect when it changes
        self.current_error_signature: Optional[ErrorSignature] = None
        self.error_signature_changed = False
        
        # Thresholds for detection
        self.thresholds = {
            'action_repeat': 3,           # Same action 3+ times
            'modification_repeat': 4,     # Same file modified 4+ times
            'conversation_repeat': 3,     # Same conversation 3+ times
            'pattern_cycles': 2,          # Pattern repeats 2+ times
            'time_window': 300.0,         # 5 minute window
            'rapid_actions': 10,          # 10+ actions in 60 seconds
        }
    
    def set_current_error(self, error_signature: Optional[ErrorSignature]) -> None:
        """
        Set the current error signature being worked on.
        
        If the error signature changes, this indicates progress (fixing one bug
        and moving to another), so we should reset loop detection.
        
        Args:
            error_signature: Current error being worked on, or None
        """
        if error_signature != self.current_error_signature:
            self.error_signature_changed = True
            self.current_error_signature = error_signature
        else:
            self.error_signature_changed = False
    
    def is_making_progress(self) -> bool:
        """
        Check if we're making progress (error signature changed).
        
        Returns:
            True if error signature changed (indicating progress)
        """
        return self.error_signature_changed
    
    def detect_all_loops(self) -> List[LoopDetection]:
        """
        Run all loop detection algorithms.
        
        Returns:
            List of detected loops, sorted by severity
        """
        # If error signature changed, we're making progress - don't report loops
        if self.error_signature_changed:
            return []
        
        detections = []
        
        # Run all detection methods
        detections.extend(self.detect_action_loops())
        detections.extend(self.detect_modification_loops())
        detections.extend(self.detect_conversation_loops())
        detections.extend(self.detect_circular_dependencies())
        detections.extend(self.detect_state_cycles())
        detections.extend(self.detect_pattern_repetition())
        detections.extend(self.detect_no_progress_loop())
        
        # Filter out false positives based on phase context
        detections = self._filter_phase_aware(detections)
        
        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        detections.sort(key=lambda d: severity_order.get(d.severity, 4))
        
        return detections
    
    def _filter_phase_aware(self, detections: List[LoopDetection]) -> List[LoopDetection]:
        """
        Filter out false positives based on phase context.
        
        Different phases have different expected patterns:
        - QA: Reading multiple files and searching code is NORMAL
        - Investigation: Gathering context from multiple sources is NORMAL
        - Debugging: Trying 2-3 different approaches is NORMAL
        
        Args:
            detections: Raw loop detections
            
        Returns:
            Filtered detections with false positives removed
        """
        filtered = []
        recent_actions = self.tracker.get_recent_actions(20)
        
        # Determine current phase
        current_phase = recent_actions[-1].phase if recent_actions else 'unknown'
        
        for detection in detections:
            # Get actions involved in this detection
            actions = detection.actions_involved if detection.actions_involved else recent_actions
            
            # Check if this is a false positive
            is_false_positive = False
            
            # QA Phase: Reading/searching multiple files is normal
            if current_phase == 'qa' and detection.loop_type in ['conversation_loop', 'pattern_repetition', 'state_cycle']:
                # Check if actions are just reading different files
                tools_used = set(a.tool for a in actions)
                files_accessed = set(a.file_path for a in actions if a.file_path)
                
                # If using read/search tools on different files, it's normal QA work
                if tools_used <= {'read_file', 'search_code', 'list_directory'} and len(files_accessed) > 1:
                    is_false_positive = True
            
            # Investigation Phase: Gathering context is normal
            if current_phase == 'investigation' and detection.loop_type in ['conversation_loop', 'pattern_repetition']:
                tools_used = set(a.tool for a in actions)
                investigation_tools = {'read_file', 'search_code', 'list_directory', 'execute_command', 
                                     'investigate_data_flow', 'investigate_parameter_removal', 'get_function_signature'}
                
                # If using investigation tools, it's normal
                if tools_used <= investigation_tools:
                    is_false_positive = True
            
            # Debugging Phase: Only flag if SAME fix attempted 3+ times
            if current_phase == 'debugging' and detection.loop_type == 'modification_loop':
                # Check if modifications are on SAME code
                modifications = [a for a in actions if a.tool in ['str_replace', 'full_file_rewrite']]
                if modifications:
                    old_strs = [m.args.get('old_str', '')[:100] for m in modifications if 'old_str' in m.args]
                    unique_targets = len(set(old_strs))
                    
                    # If targeting different code each time, it's trying different approaches (good)
                    if unique_targets >= len(modifications) * 0.7:  # 70% unique
                        is_false_positive = True
            
            # Only keep real loops
            if not is_false_positive:
                filtered.append(detection)
        
        return filtered
    
    def detect_action_loops(self) -> List[LoopDetection]:
        """
        Detect Type 1: Action Loops - Same action repeated.
        
        Returns:
            List of detected action loops
        """
        detections = []
        
        # Check for immediate repeats
        repeat = self.tracker.detect_immediate_repeat(
            threshold=self.thresholds['action_repeat']
        )
        
        if repeat:
            signature, count = repeat
            recent = self.tracker.get_recent_actions(count)
            
            # Determine severity based on count
            if count >= 10:
                severity = 'critical'
            elif count >= 7:
                severity = 'high'
            elif count >= 5:
                severity = 'medium'
            else:
                severity = 'low'
            
            detections.append(LoopDetection(
                loop_type='action_loop',
                severity=severity,
                description=f'Same action repeated {count} times consecutively',
                evidence=[
                    f'Action: {signature}',
                    f'Repeated: {count} times',
                    f'Time span: {recent[-1].timestamp - recent[0].timestamp:.1f}s'
                ],
                suggestion='Try a different approach or tool. Consider using ask tool to request user guidance.',
                actions_involved=recent
            ))
        
        # Check for high frequency of same action
        frequency = self.tracker.get_action_frequency(
            time_window=self.thresholds['time_window']
        )
        
        for signature, count in frequency.items():
            if count >= 5:
                detections.append(LoopDetection(
                    loop_type='action_loop',
                    severity='medium',
                    description=f'Action repeated {count} times in 5 minutes',
                    evidence=[
                        f'Action: {signature}',
                        f'Frequency: {count} times in 5 minutes'
                    ],
                    suggestion='This action may not be effective. Consider alternative approaches.',
                    actions_involved=[]
                ))
        
        return detections
    
    def detect_modification_loops(self) -> List[LoopDetection]:
        """
        Detect Type 2: Modification Loops - Same file modified repeatedly.
        
        Returns:
            List of detected modification loops
        """
        detections = []
        
        # Get all files that have been modified
        recent_actions = self.tracker.get_recent_actions(50)
        files_modified = defaultdict(list)
        
        for action in recent_actions:
            if action.file_path and action.tool in ['str_replace', 'full_file_rewrite']:
                files_modified[action.file_path].append(action)
        
        # Check each file
        for file_path, modifications in files_modified.items():
            if len(modifications) >= self.thresholds['modification_repeat']:
                # Check if modifications are in rapid succession
                time_span = modifications[-1].timestamp - modifications[0].timestamp
                
                # Determine severity
                if len(modifications) >= 10:
                    severity = 'critical'
                elif len(modifications) >= 7:
                    severity = 'high'
                elif len(modifications) >= 5:
                    severity = 'medium'
                else:
                    severity = 'low'
                
                # Check if same code is being modified repeatedly
                old_strs = []
                for mod in modifications:
                    if 'old_str' in mod.args:
                        old_strs.append(mod.args['old_str'][:100])
                
                # Count unique vs repeated modifications
                unique_mods = len(set(old_strs))
                total_mods = len(old_strs)
                
                if unique_mods < total_mods * 0.5:
                    # More than 50% are repeats
                    detections.append(LoopDetection(
                        loop_type='modification_loop',
                        severity=severity,
                        description=f'File modified {len(modifications)} times, many targeting same code',
                        evidence=[
                            f'File: {file_path}',
                            f'Modifications: {len(modifications)}',
                            f'Time span: {time_span:.1f}s',
                            f'Unique targets: {unique_mods}/{total_mods}'
                        ],
                        suggestion='The current approach is not working. Consider: 1) Reading the file to see current state, 2) Using full_file_rewrite instead of str_replace, 3) Consulting a specialist, 4) Asking user for guidance.',
                        actions_involved=modifications
                    ))
        
        return detections
    
    def detect_conversation_loops(self) -> List[LoopDetection]:
        """
        Detect Type 3: Conversation Loops - Same questions/responses.
        
        Returns:
            List of detected conversation loops
        """
        detections = []
        
        # Get recent conversation turns
        recent = self.tracker.get_recent_actions(20)
        
        # Extract tool calls that represent "questions" or "analysis"
        analysis_tools = ['read_file', 'search_code', 'list_directory', 'execute_command']
        analysis_actions = [a for a in recent if a.tool in analysis_tools]
        
        if len(analysis_actions) >= 6:
            # Check for repeated analysis of same targets
            targets = defaultdict(int)
            for action in analysis_actions:
                if action.file_path:
                    targets[action.file_path] += 1
                elif 'command' in action.args:
                    targets[action.args['command'][:50]] += 1
            
            for target, count in targets.items():
                if count >= self.thresholds['conversation_repeat']:
                    detections.append(LoopDetection(
                        loop_type='conversation_loop',
                        severity='medium',
                        description=f'Repeatedly analyzing same target {count} times',
                        evidence=[
                            f'Target: {target}',
                            f'Analysis count: {count}'
                        ],
                        suggestion='You have already analyzed this. Use the information you gathered to make a decision and take action.',
                        actions_involved=[a for a in analysis_actions if a.file_path == target or action.args.get('command', '')[:50] == target]
                    ))
        
        return detections
    
    def detect_circular_dependencies(self) -> List[LoopDetection]:
        """
        Detect Type 4: Circular Dependencies - A depends on B depends on A.
        
        Returns:
            List of detected circular dependencies
        """
        detections = []
        
        # Build dependency graph from recent actions
        recent = self.tracker.get_recent_actions(30)
        
        # Track which files reference which other files
        references = defaultdict(set)
        
        for action in recent:
            if action.tool == 'read_file' and action.file_path:
                # Check if result contains imports or references
                if action.result and 'content' in action.result:
                    content = action.result['content']
                    
                    # Extract import statements
                    imports = re.findall(r'from\s+(\S+)\s+import|import\s+(\S+)', content)
                    for imp in imports:
                        module = imp[0] or imp[1]
                        if module:
                            references[action.file_path].add(module)
        
        # Detect cycles in dependency graph
        def find_cycle(node: str, visited: Set[str], path: List[str]) -> Optional[List[str]]:
            if node in path:
                # Found cycle
                cycle_start = path.index(node)
                return path[cycle_start:] + [node]
            
            if node in visited:
                return None
            
            visited.add(node)
            path.append(node)
            
            for neighbor in references.get(node, []):
                cycle = find_cycle(neighbor, visited, path.copy())
                if cycle:
                    return cycle
            
            return None
        
        visited = set()
        for node in references:
            if node not in visited:
                cycle = find_cycle(node, visited, [])
                if cycle:
                    detections.append(LoopDetection(
                        loop_type='circular_dependency',
                        severity='high',
                        description=f'Circular dependency detected: {" -> ".join(cycle)}',
                        evidence=[
                            f'Cycle: {" -> ".join(cycle)}',
                            f'Length: {len(cycle) - 1} files'
                        ],
                        suggestion='Break the circular dependency by refactoring code or using dependency injection.',
                        actions_involved=[]
                    ))
        
        return detections
    
    def detect_state_cycles(self) -> List[LoopDetection]:
        """
        Detect Type 5: State Cycles - System state cycling through same states.
        
        Returns:
            List of detected state cycles
        """
        detections = []
        
        # Track state transitions (phase changes, file states)
        recent = self.tracker.get_recent_actions(30)
        
        # Build state sequence
        states = []
        for action in recent:
            # State = (phase, file_path, tool)
            state = (action.phase, action.file_path or 'none', action.tool)
            states.append(state)
        
        # Detect repeating state sequences
        for pattern_len in range(3, len(states) // 2 + 1):
            pattern = states[:pattern_len]
            
            # Check if pattern repeats
            cycles = 0
            for i in range(0, len(states) - pattern_len + 1, pattern_len):
                if states[i:i+pattern_len] == pattern:
                    cycles += 1
                else:
                    break
            
            if cycles >= 2:
                detections.append(LoopDetection(
                    loop_type='state_cycle',
                    severity='high',
                    description=f'System cycling through same {pattern_len} states {cycles} times',
                    evidence=[
                        f'Pattern length: {pattern_len} states',
                        f'Cycles: {cycles}',
                        f'States: {" -> ".join([f"{s[0]}:{s[2]}" for s in pattern])}'
                    ],
                    suggestion='The system is stuck in a cycle. Try a completely different approach or ask user for guidance.',
                    actions_involved=recent[:pattern_len * cycles]
                ))
                break  # Only report first detected cycle
        
        return detections
    
    def detect_pattern_repetition(self) -> List[LoopDetection]:
        """
        Detect Type 6: Pattern Repetition - Complex multi-step patterns repeating.
        
        Returns:
            List of detected pattern repetitions
        """
        detections = []
        
        # Use ActionTracker's alternating pattern detection
        pattern = self.tracker.detect_alternating_pattern(
            window_size=20,
            min_cycles=self.thresholds['pattern_cycles']
        )
        
        if pattern:
            pattern_seq, cycles = pattern
            
            # Determine severity
            if cycles >= 5:
                severity = 'critical'
            elif cycles >= 4:
                severity = 'high'
            elif cycles >= 3:
                severity = 'medium'
            else:
                severity = 'low'
            
            detections.append(LoopDetection(
                loop_type='pattern_repetition',
                severity=severity,
                description=f'Complex pattern repeated {cycles} times',
                evidence=[
                    f'Pattern: {" -> ".join(pattern_seq)}',
                    f'Cycles: {cycles}',
                    f'Pattern length: {len(pattern_seq)} actions'
                ],
                suggestion='This multi-step pattern is repeating without progress. Break the pattern by: 1) Consulting a specialist, 2) Trying a fundamentally different approach, 3) Asking user for guidance.',
                actions_involved=self.tracker.get_recent_actions(len(pattern_seq) * cycles)
            ))
        
        return detections
    
    def get_loop_summary(self, detections: List[LoopDetection]) -> str:
        """
        Generate human-readable summary of detected loops.
        
        Args:
            detections: List of loop detections
            
        Returns:
            Formatted summary string
        """
        if not detections:
            return "No loops detected. System is making progress."
        
        summary = ["⚠️  LOOP DETECTION ALERT ⚠️\n"]
        summary.append(f"Detected {len(detections)} potential loop(s):\n")
        
        for i, detection in enumerate(detections, 1):
            summary.append(f"\n{i}. {detection.loop_type.upper()} [{detection.severity.upper()}]")
            summary.append(f"   {detection.description}")
            summary.append(f"   Evidence:")
            for evidence in detection.evidence:
                summary.append(f"     - {evidence}")
            summary.append(f"   💡 Suggestion: {detection.suggestion}")
        
        return "\n".join(summary)
    
    def should_intervene(self, detections: List[LoopDetection]) -> bool:
        """
        Determine if intervention is needed based on detections.
        
        Args:
            detections: List of loop detections
            
        Returns:
            True if intervention needed, False otherwise
        """
        if not detections:
            return False
        
        # Intervene if any critical or 2+ high severity
        critical_count = sum(1 for d in detections if d.severity == 'critical')
        high_count = sum(1 for d in detections if d.severity == 'high')
        
        return critical_count > 0 or high_count >= 2
    
    def detect_no_progress_loop(self) -> List[LoopDetection]:
        """
        Detect when system is stuck returning 'no updates needed' repeatedly.
        
        This is a specific type of loop where:
        - Same phase runs multiple times
        - Each time returns "no updates needed" or similar
        - No actual work is being done
        
        Returns:
            List of detected no-progress loops
        """
        detections = []
        
        recent = self.tracker.get_recent_actions(20)
        
        # Group by phase
        phase_actions = defaultdict(list)
        for action in recent:
            phase_actions[action.phase].append(action)
        
        for phase, actions in phase_actions.items():
            if len(actions) >= 5:
                # Check if all actions are "read-only" (no modifications)
                modification_tools = {'str_replace', 'full_file_rewrite', 'create_file', 'delete_file'}
                modifications = [a for a in actions if a.tool in modification_tools]
                
                # If less than 20% are modifications, likely stuck in analysis loop
                if len(modifications) < len(actions) * 0.2:
                    detections.append(LoopDetection(
                        loop_type='no_progress_loop',
                        severity='high',
                        description=f'{phase} phase running repeatedly without making changes',
                        evidence=[
                            f'Phase: {phase}',
                            f'Iterations: {len(actions)}',
                            f'Modifications: {len(modifications)} ({len(modifications)/len(actions)*100:.0f}%)',
                            f'Read-only actions: {len(actions) - len(modifications)}'
                        ],
                        suggestion=f'Phase {phase} is stuck in analysis. Force transition to next phase or ask user for guidance.',
                        actions_involved=actions
                    ))
        
        return detections