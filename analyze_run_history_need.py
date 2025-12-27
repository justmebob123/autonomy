#!/usr/bin/env python3
"""
Deep analysis of run history tracking needs.

This script examines:
1. Current state tracking capabilities
2. What information is lost without run history
3. Whether run history is needed for better loop detection
4. Impact on polytopic structure analysis
"""

import json
from pathlib import Path
from typing import Dict, List, Any

def analyze_current_state_tracking():
    """Analyze what PhaseState currently tracks"""
    
    print("=" * 80)
    print("CURRENT STATE TRACKING ANALYSIS")
    print("=" * 80)
    print()
    
    current_tracking = {
        "PhaseState": {
            "last_run": "timestamp of last run",
            "runs": "total run count",
            "successes": "total success count",
            "failures": "total failure count"
        },
        "Derived Metrics": {
            "success_rate": "successes / runs",
            "failure_rate": "failures / runs"
        }
    }
    
    print("✅ Currently Tracked:")
    for category, items in current_tracking.items():
        print(f"\n{category}:")
        for key, desc in items.items():
            print(f"  • {key}: {desc}")
    
    print("\n" + "=" * 80)
    print("INFORMATION LOST WITHOUT RUN HISTORY")
    print("=" * 80)
    print()
    
    lost_info = {
        "Temporal Patterns": [
            "Cannot detect if failures are clustered or distributed",
            "Cannot see if success rate is improving or degrading",
            "Cannot identify recent vs historical patterns",
            "Cannot detect oscillating behavior (success-fail-success-fail)"
        ],
        "Consecutive Analysis": [
            "Cannot count consecutive successes",
            "Cannot count consecutive failures",
            "Cannot detect streaks or patterns",
            "Cannot identify when pattern started"
        ],
        "Detailed Diagnostics": [
            "Cannot see exact sequence of events",
            "Cannot correlate failures with specific tasks",
            "Cannot identify which attempt succeeded",
            "Cannot replay execution history"
        ],
        "Loop Detection Precision": [
            "Cannot distinguish: SSSSS (5 success) from SFSFS (alternating)",
            "Cannot detect: FFFSS (improving) vs SSFFF (degrading)",
            "Cannot identify: FFFFF (stuck) vs FSFFF (occasional success)",
            "Cannot measure: time between successes"
        ]
    }
    
    print("❌ Lost Without Run History:")
    for category, items in lost_info.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  • {item}")
    
    return lost_info


def analyze_loop_detection_scenarios():
    """Analyze specific scenarios where run history helps"""
    
    print("\n" + "=" * 80)
    print("LOOP DETECTION SCENARIOS")
    print("=" * 80)
    print()
    
    scenarios = [
        {
            "name": "Scenario 1: Consistent Success",
            "history": ["S", "S", "S", "S", "S"],
            "aggregate": {"runs": 5, "successes": 5, "failures": 0},
            "with_history": "✅ Clear pattern: consistent success, continue",
            "without_history": "✅ Success rate 100%, continue",
            "verdict": "SAME - No history needed"
        },
        {
            "name": "Scenario 2: Consistent Failure",
            "history": ["F", "F", "F", "F", "F"],
            "aggregate": {"runs": 5, "successes": 0, "failures": 5},
            "with_history": "⚠️ 5 consecutive failures, force transition",
            "without_history": "⚠️ Success rate 0%, force transition",
            "verdict": "SAME - No history needed"
        },
        {
            "name": "Scenario 3: Improving Pattern",
            "history": ["F", "F", "F", "S", "S"],
            "aggregate": {"runs": 5, "successes": 2, "failures": 3},
            "with_history": "✅ Improving! 2 recent successes, continue",
            "without_history": "⚠️ Success rate 40%, force transition",
            "verdict": "DIFFERENT - History shows improvement!"
        },
        {
            "name": "Scenario 4: Degrading Pattern",
            "history": ["S", "S", "F", "F", "F"],
            "aggregate": {"runs": 5, "successes": 2, "failures": 3},
            "with_history": "⚠️ Degrading! 3 recent failures, force transition",
            "without_history": "⚠️ Success rate 40%, force transition",
            "verdict": "SAME - Both detect problem"
        },
        {
            "name": "Scenario 5: Oscillating",
            "history": ["S", "F", "S", "F", "S"],
            "aggregate": {"runs": 5, "successes": 3, "failures": 2},
            "with_history": "⚠️ Unstable oscillation, investigate",
            "without_history": "✅ Success rate 60%, continue",
            "verdict": "DIFFERENT - History reveals instability!"
        },
        {
            "name": "Scenario 6: Recent Recovery",
            "history": ["F", "F", "F", "F", "S"],
            "aggregate": {"runs": 5, "successes": 1, "failures": 4},
            "with_history": "✅ Just recovered! Give it a chance",
            "without_history": "⚠️ Success rate 20%, force transition",
            "verdict": "DIFFERENT - History shows recovery!"
        },
        {
            "name": "Scenario 7: Single Recent Failure",
            "history": ["S", "S", "S", "S", "F"],
            "aggregate": {"runs": 5, "successes": 4, "failures": 1},
            "with_history": "✅ One failure after 4 successes, continue",
            "without_history": "✅ Success rate 80%, continue",
            "verdict": "SAME - Both allow continuation"
        }
    ]
    
    critical_differences = 0
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}")
        print(f"  History: {' → '.join(scenario['history'])}")
        print(f"  Aggregate: {scenario['aggregate']}")
        print(f"  With History: {scenario['with_history']}")
        print(f"  Without History: {scenario['without_history']}")
        print(f"  Verdict: {scenario['verdict']}")
        
        if "DIFFERENT" in scenario['verdict']:
            critical_differences += 1
    
    print("\n" + "=" * 80)
    print(f"CRITICAL DIFFERENCES: {critical_differences}/7 scenarios")
    print("=" * 80)
    
    return scenarios, critical_differences


def analyze_polytopic_impact():
    """Analyze impact on polytopic structure"""
    
    print("\n" + "=" * 80)
    print("POLYTOPIC STRUCTURE IMPACT")
    print("=" * 80)
    print()
    
    print("Current 7D Structure:")
    dimensions = [
        "1. Temporal - Time-based operations",
        "2. Functional - Purpose and capability",
        "3. Data - Information flow",
        "4. State - State management",
        "5. Error - Error handling",
        "6. Context - Contextual awareness",
        "7. Integration - Cross-phase dependencies"
    ]
    
    for dim in dimensions:
        print(f"  {dim}")
    
    print("\n" + "-" * 80)
    print("With Run History, we could add:")
    print("-" * 80)
    
    enhanced_dimensions = [
        {
            "dimension": "Temporal Enhancement",
            "current": "Only tracks last_run timestamp",
            "with_history": "Track full temporal sequence, detect trends",
            "benefit": "Better understanding of phase behavior over time"
        },
        {
            "dimension": "State Enhancement",
            "current": "Aggregate counts only",
            "with_history": "Detailed state transitions, pattern detection",
            "benefit": "Precise loop detection, trend analysis"
        },
        {
            "dimension": "Error Enhancement",
            "current": "Total failure count",
            "with_history": "Consecutive failure tracking, recovery detection",
            "benefit": "Distinguish stuck vs recovering phases"
        }
    ]
    
    for enh in enhanced_dimensions:
        print(f"\n{enh['dimension']}:")
        print(f"  Current: {enh['current']}")
        print(f"  With History: {enh['with_history']}")
        print(f"  Benefit: {enh['benefit']}")


def recommend_implementation():
    """Recommend run history implementation"""
    
    print("\n" + "=" * 80)
    print("RECOMMENDATION: IMPLEMENT RUN HISTORY")
    print("=" * 80)
    print()
    
    print("✅ REASONS TO IMPLEMENT:")
    reasons = [
        "1. Detect improving patterns (F F F S S) - avoid premature transition",
        "2. Detect degrading patterns (S S F F F) - early intervention",
        "3. Detect oscillating behavior (S F S F S) - instability warning",
        "4. Detect recent recovery (F F F F S) - give phase a chance",
        "5. Better diagnostics - see exact sequence of events",
        "6. Temporal analysis - understand phase behavior over time",
        "7. Pattern recognition - identify recurring issues"
    ]
    
    for reason in reasons:
        print(f"  {reason}")
    
    print("\n" + "-" * 80)
    print("PROPOSED IMPLEMENTATION:")
    print("-" * 80)
    
    implementation = """
@dataclass
class PhaseState:
    last_run: Optional[str] = None
    runs: int = 0
    successes: int = 0
    failures: int = 0
    
    # NEW: Run history (limited to last N runs)
    run_history: List[Dict[str, Any]] = field(default_factory=list)
    max_history: int = 20  # Keep last 20 runs
    
    def record_run(self, success: bool, task_id: str = None, 
                   files_created: List[str] = None, 
                   files_modified: List[str] = None):
        '''Record a phase run with full details'''
        self.last_run = datetime.now().isoformat()
        self.runs += 1
        
        if success:
            self.successes += 1
        else:
            self.failures += 1
        
        # Record in history
        run_record = {
            'timestamp': self.last_run,
            'success': success,
            'task_id': task_id,
            'files_created': files_created or [],
            'files_modified': files_modified or []
        }
        
        self.run_history.append(run_record)
        
        # Limit history size
        if len(self.run_history) > self.max_history:
            self.run_history = self.run_history[-self.max_history:]
    
    def get_consecutive_failures(self) -> int:
        '''Count consecutive failures from end of history'''
        count = 0
        for run in reversed(self.run_history):
            if not run['success']:
                count += 1
            else:
                break
        return count
    
    def get_consecutive_successes(self) -> int:
        '''Count consecutive successes from end of history'''
        count = 0
        for run in reversed(self.run_history):
            if run['success']:
                count += 1
            else:
                break
        return count
    
    def get_recent_success_rate(self, n: int = 5) -> float:
        '''Get success rate over last N runs'''
        recent = self.run_history[-n:] if len(self.run_history) >= n else self.run_history
        if not recent:
            return 0.0
        successes = sum(1 for r in recent if r['success'])
        return successes / len(recent)
    
    def is_improving(self, window: int = 5) -> bool:
        '''Check if success rate is improving'''
        if len(self.run_history) < window * 2:
            return False
        
        older = self.run_history[-window*2:-window]
        recent = self.run_history[-window:]
        
        older_rate = sum(1 for r in older if r['success']) / len(older)
        recent_rate = sum(1 for r in recent if r['success']) / len(recent)
        
        return recent_rate > older_rate
    
    def is_degrading(self, window: int = 5) -> bool:
        '''Check if success rate is degrading'''
        if len(self.run_history) < window * 2:
            return False
        
        older = self.run_history[-window*2:-window]
        recent = self.run_history[-window:]
        
        older_rate = sum(1 for r in older if r['success']) / len(older)
        recent_rate = sum(1 for r in recent if r['success']) / len(recent)
        
        return recent_rate < older_rate
    
    def is_oscillating(self, threshold: int = 3) -> bool:
        '''Check if alternating between success and failure'''
        if len(self.run_history) < threshold * 2:
            return False
        
        recent = self.run_history[-threshold*2:]
        changes = 0
        
        for i in range(1, len(recent)):
            if recent[i]['success'] != recent[i-1]['success']:
                changes += 1
        
        # If changes >= threshold, it's oscillating
        return changes >= threshold
"""
    
    print(implementation)
    
    print("\n" + "-" * 80)
    print("ENHANCED LOOP DETECTION:")
    print("-" * 80)
    
    enhanced_detection = """
def _should_force_transition(self, state, current_phase: str, last_result=None) -> bool:
    '''Enhanced loop detection with run history'''
    
    # NEVER force transition after success with actual work
    if last_result and last_result.success:
        if last_result.files_created or last_result.files_modified:
            if hasattr(state, 'no_update_counts'):
                state.no_update_counts[current_phase] = 0
            return False
    
    # Check no-update count
    no_update_count = state.no_update_counts.get(current_phase, 0) if hasattr(state, 'no_update_counts') else 0
    if no_update_count >= 3:
        self.logger.warning(f"Phase {current_phase} returned 'no updates' {no_update_count} times")
        return True
    
    # Enhanced checks with run history
    if hasattr(state, 'phases') and current_phase in state.phases:
        phase_state = state.phases[current_phase]
        
        # Check if phase is improving - DON'T force transition
        if hasattr(phase_state, 'is_improving') and phase_state.is_improving():
            self.logger.info(f"Phase {current_phase} is improving, continuing")
            return False
        
        # Check for consecutive failures - FORCE transition
        if hasattr(phase_state, 'get_consecutive_failures'):
            consecutive_failures = phase_state.get_consecutive_failures()
            if consecutive_failures >= 3:
                self.logger.warning(
                    f"Phase {current_phase} has {consecutive_failures} consecutive failures"
                )
                return True
        
        # Check if oscillating - FORCE transition (unstable)
        if hasattr(phase_state, 'is_oscillating') and phase_state.is_oscillating():
            self.logger.warning(f"Phase {current_phase} is oscillating (unstable)")
            return True
        
        # Fallback to aggregate success rate
        if phase_state.runs >= 3:
            success_rate = phase_state.successes / phase_state.runs
            if success_rate < 0.3:
                self.logger.warning(
                    f"Phase {current_phase} has low success rate: "
                    f"{phase_state.successes}/{phase_state.runs} ({success_rate:.1%})"
                )
                return True
    
    return False
"""
    
    print(enhanced_detection)
    
    print("\n" + "=" * 80)
    print("IMPACT SUMMARY")
    print("=" * 80)
    print()
    
    impact = {
        "Storage Cost": "~20 records × 100 bytes = 2KB per phase (negligible)",
        "Performance Cost": "Minimal - only accessed during loop detection",
        "Benefit": "Significantly better loop detection and diagnostics",
        "Risk": "Low - backward compatible, optional feature"
    }
    
    for key, value in impact.items():
        print(f"  {key}: {value}")
    
    print("\n✅ RECOMMENDATION: IMPLEMENT RUN HISTORY")
    print("   Priority: HIGH")
    print("   Complexity: LOW")
    print("   Impact: HIGH")


if __name__ == "__main__":
    analyze_current_state_tracking()
    scenarios, critical_diff = analyze_loop_detection_scenarios()
    analyze_polytopic_impact()
    recommend_implementation()
    
    print("\n" + "=" * 80)
    print("FINAL VERDICT")
    print("=" * 80)
    print()
    print(f"✅ Run history would improve loop detection in {critical_diff}/7 scenarios")
    print("✅ Enables detection of improving patterns (avoid premature transition)")
    print("✅ Enables detection of degrading patterns (early intervention)")
    print("✅ Enables detection of oscillating behavior (instability warning)")
    print("✅ Minimal storage and performance cost")
    print()
    print("🎯 RECOMMENDATION: IMPLEMENT RUN HISTORY")
    print("   This addresses the user's concern about tracking patterns over time")
    print("   and provides significantly better loop detection capabilities.")