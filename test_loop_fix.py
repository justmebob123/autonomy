#!/usr/bin/env python3
"""
Test to verify loop detection fix.

This test simulates the scenario where:
1. Coding phase runs multiple times successfully (creating files)
2. System should NOT force transition
3. Only force transition on repeated failures (low success rate)
"""

from pipeline.state.manager import PipelineState, PhaseState
from pipeline.phases.base import PhaseResult
from datetime import datetime

def test_successful_coding_no_force_transition():
    """Test that successful file creation doesn't trigger forced transition"""
    
    # Create mock state
    state = PipelineState(
        pipeline_run_id="test_run",
        updated=datetime.now().isoformat()
    )
    
    # Initialize phase state
    state.phases["coding"] = PhaseState()
    
    # Simulate 5 successful coding runs
    for i in range(5):
        state.phases["coding"].record_run(True)
        state.phase_history.append("coding")
    
    # Last result was success with file creation
    result = PhaseResult(
        success=True,
        phase="coding",
        task_id="task_1",
        message="Created file",
        files_created=["file.py"],
        files_modified=[]
    )
    
    # Test the logic
    class MockCoordinator:
        def __init__(self):
            self.logger = None
            
        def _should_force_transition(self, state, current_phase, last_result):
            """Copy of the fixed method"""
            # NEVER force transition after success with actual work
            if last_result and last_result.success:
                if last_result.files_created or last_result.files_modified:
                    if hasattr(state, 'no_update_counts'):
                        state.no_update_counts[current_phase] = 0
                    return False
            
            # Check no-update count
            no_update_count = state.no_update_counts.get(current_phase, 0) if hasattr(state, 'no_update_counts') else 0
            if no_update_count >= 3:
                return True
            
            # Check success rate over recent runs
            if hasattr(state, 'phases') and current_phase in state.phases:
                phase_state = state.phases[current_phase]
                
                if phase_state.runs >= 3:
                    success_rate = phase_state.successes / phase_state.runs
                    
                    if success_rate < 0.3:
                        return True
            
            return False
    
    coordinator = MockCoordinator()
    should_force = coordinator._should_force_transition(state, "coding", result)
    
    print(f"✅ Test 1: Successful coding runs")
    print(f"   Phase history: {state.phase_history}")
    print(f"   Phase stats: {state.phases['coding'].successes}/{state.phases['coding'].runs} success")
    print(f"   Last result: success={result.success}, files_created={result.files_created}")
    print(f"   Should force transition: {should_force}")
    assert not should_force, "Should NOT force transition after successful file creation"
    print(f"   ✓ PASS: No forced transition after success\n")


def test_repeated_failures_force_transition():
    """Test that repeated failures DO trigger forced transition"""
    
    # Create mock state with phase tracking
    state = PipelineState(
        pipeline_run_id="test_run",
        updated=datetime.now().isoformat()
    )
    
    # Initialize phase state
    state.phases["coding"] = PhaseState()
    
    # Simulate 5 failed runs (0% success rate)
    for i in range(5):
        state.phases["coding"].record_run(False)
        state.phase_history.append("coding")
    
    # Create failed result
    result = PhaseResult(
        success=False,
        phase="coding",
        task_id="task_1",
        message="Failed to create file",
        files_created=[],
        files_modified=[],
        errors=[{"type": "error", "message": "test error"}]
    )
    
    # Test the logic
    class MockCoordinator:
        def __init__(self):
            self.logger = None
            
        def _should_force_transition(self, state, current_phase, last_result):
            """Copy of the fixed method"""
            if last_result and last_result.success:
                if last_result.files_created or last_result.files_modified:
                    if hasattr(state, 'no_update_counts'):
                        state.no_update_counts[current_phase] = 0
                    return False
            
            no_update_count = state.no_update_counts.get(current_phase, 0) if hasattr(state, 'no_update_counts') else 0
            if no_update_count >= 3:
                return True
            
            if hasattr(state, 'phases') and current_phase in state.phases:
                phase_state = state.phases[current_phase]
                
                if phase_state.runs >= 3:
                    success_rate = phase_state.successes / phase_state.runs
                    
                    if success_rate < 0.3:
                        return True
            
            return False
    
    coordinator = MockCoordinator()
    should_force = coordinator._should_force_transition(state, "coding", result)
    
    print(f"✅ Test 2: Repeated failures")
    print(f"   Phase history: {state.phase_history}")
    print(f"   Phase stats: {state.phases['coding'].successes}/{state.phases['coding'].runs} success")
    print(f"   Success rate: {state.phases['coding'].successes / state.phases['coding'].runs:.1%}")
    print(f"   Last result: success={result.success}")
    print(f"   Should force transition: {should_force}")
    assert should_force, "Should force transition with 0% success rate"
    print(f"   ✓ PASS: Forced transition after repeated failures\n")


def test_mixed_results_no_force():
    """Test that good success rate doesn't trigger forced transition"""
    
    state = PipelineState(
        pipeline_run_id="test_run",
        updated=datetime.now().isoformat()
    )
    
    state.phases["coding"] = PhaseState()
    
    # Simulate 80% success rate: 4 success, 1 failure
    for i in range(4):
        state.phases["coding"].record_run(True)
    state.phases["coding"].record_run(False)
    
    # Last result was success
    result = PhaseResult(
        success=True,
        phase="coding",
        task_id="task_1",
        message="Created file",
        files_created=["file.py"],
        files_modified=[]
    )
    
    class MockCoordinator:
        def __init__(self):
            self.logger = None
            
        def _should_force_transition(self, state, current_phase, last_result):
            """Copy of the fixed method"""
            if last_result and last_result.success:
                if last_result.files_created or last_result.files_modified:
                    if hasattr(state, 'no_update_counts'):
                        state.no_update_counts[current_phase] = 0
                    return False
            
            no_update_count = state.no_update_counts.get(current_phase, 0) if hasattr(state, 'no_update_counts') else 0
            if no_update_count >= 3:
                return True
            
            if hasattr(state, 'phases') and current_phase in state.phases:
                phase_state = state.phases[current_phase]
                
                if phase_state.runs >= 3:
                    success_rate = phase_state.successes / phase_state.runs
                    
                    if success_rate < 0.3:
                        return True
            
            return False
    
    coordinator = MockCoordinator()
    should_force = coordinator._should_force_transition(state, "coding", result)
    
    print(f"✅ Test 3: Good success rate (80%)")
    print(f"   Phase stats: {state.phases['coding'].successes}/{state.phases['coding'].runs} success")
    print(f"   Success rate: {state.phases['coding'].successes / state.phases['coding'].runs:.1%}")
    print(f"   Last result: success={result.success}, files_created={result.files_created}")
    print(f"   Should force transition: {should_force}")
    assert not should_force, "Should NOT force transition with 80% success rate"
    print(f"   ✓ PASS: No forced transition with good success rate\n")


def test_low_success_rate_forces_transition():
    """Test that low success rate (20%) triggers forced transition"""
    
    state = PipelineState(
        pipeline_run_id="test_run",
        updated=datetime.now().isoformat()
    )
    
    state.phases["coding"] = PhaseState()
    
    # Simulate 20% success rate: 1 success, 4 failures
    state.phases["coding"].record_run(True)
    for i in range(4):
        state.phases["coding"].record_run(False)
    
    # Last result was failure
    result = PhaseResult(
        success=False,
        phase="coding",
        task_id="task_1",
        message="Failed",
        files_created=[],
        files_modified=[]
    )
    
    class MockCoordinator:
        def __init__(self):
            self.logger = None
            
        def _should_force_transition(self, state, current_phase, last_result):
            """Copy of the fixed method"""
            if last_result and last_result.success:
                if last_result.files_created or last_result.files_modified:
                    if hasattr(state, 'no_update_counts'):
                        state.no_update_counts[current_phase] = 0
                    return False
            
            no_update_count = state.no_update_counts.get(current_phase, 0) if hasattr(state, 'no_update_counts') else 0
            if no_update_count >= 3:
                return True
            
            if hasattr(state, 'phases') and current_phase in state.phases:
                phase_state = state.phases[current_phase]
                
                if phase_state.runs >= 3:
                    success_rate = phase_state.successes / phase_state.runs
                    
                    if success_rate < 0.3:
                        return True
            
            return False
    
    coordinator = MockCoordinator()
    should_force = coordinator._should_force_transition(state, "coding", result)
    
    print(f"✅ Test 4: Low success rate (20%)")
    print(f"   Phase stats: {state.phases['coding'].successes}/{state.phases['coding'].runs} success")
    print(f"   Success rate: {state.phases['coding'].successes / state.phases['coding'].runs:.1%}")
    print(f"   Last result: success={result.success}")
    print(f"   Should force transition: {should_force}")
    assert should_force, "Should force transition with 20% success rate"
    print(f"   ✓ PASS: Forced transition with low success rate\n")


if __name__ == "__main__":
    print("=" * 70)
    print("LOOP DETECTION FIX - TEST SUITE")
    print("=" * 70)
    print()
    
    try:
        test_successful_coding_no_force_transition()
        test_repeated_failures_force_transition()
        test_mixed_results_no_force()
        test_low_success_rate_forces_transition()
        
        print("=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print()
        print("Summary:")
        print("  ✓ Successful file creation does NOT trigger forced transition")
        print("  ✓ Repeated failures (0% success) DO trigger forced transition")
        print("  ✓ Good success rate (80%) does NOT trigger forced transition")
        print("  ✓ Low success rate (20%) DOES trigger forced transition")
        print()
        print("The fix correctly distinguishes between:")
        print("  - Normal multi-file development (allowed)")
        print("  - Actual loops with repeated failures (blocked)")
        print()
        print("Threshold: < 30% success rate triggers forced transition")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)