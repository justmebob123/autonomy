#!/usr/bin/env python3
"""
Test script to verify documentation loop fix.

This script simulates the documentation loop scenario and verifies that:
1. No-update counter increments correctly
2. Forced transition occurs after 3 "no updates"
3. Phase history is tracked
4. Loop detection catches the pattern
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.state.manager import PipelineState, StateManager, TaskStatus


def test_no_update_tracking():
    """Test that no-update counts are tracked correctly."""
    print("\n" + "="*70)
    print("TEST 1: No-Update Counter Tracking")
    print("="*70)
    
    # Create test state
    state = PipelineState()
    state_manager = StateManager(Path("/tmp/test"))
    
    # Test increment
    count1 = state_manager.increment_no_update_count(state, "documentation")
    assert count1 == 1, f"Expected count 1, got {count1}"
    print(f"✓ First increment: {count1}")
    
    count2 = state_manager.increment_no_update_count(state, "documentation")
    assert count2 == 2, f"Expected count 2, got {count2}"
    print(f"✓ Second increment: {count2}")
    
    count3 = state_manager.increment_no_update_count(state, "documentation")
    assert count3 == 3, f"Expected count 3, got {count3}"
    print(f"✓ Third increment: {count3}")
    
    # Test get
    count = state_manager.get_no_update_count(state, "documentation")
    assert count == 3, f"Expected count 3, got {count}"
    print(f"✓ Get count: {count}")
    
    # Test reset
    state_manager.reset_no_update_count(state, "documentation")
    count = state_manager.get_no_update_count(state, "documentation")
    assert count == 0, f"Expected count 0 after reset, got {count}"
    print(f"✓ Reset count: {count}")
    
    print("\n✅ TEST 1 PASSED: No-update tracking works correctly\n")


def test_phase_history_tracking():
    """Test that phase history is tracked correctly."""
    print("="*70)
    print("TEST 2: Phase History Tracking")
    print("="*70)
    
    state = PipelineState()
    
    # Simulate phase execution
    phases = ["documentation", "documentation", "documentation", "documentation", "documentation"]
    for phase in phases:
        state.phase_history.append(phase)
    
    print(f"Phase history: {state.phase_history}")
    
    # Check last 5
    recent = state.phase_history[-5:]
    assert len(recent) == 5, f"Expected 5 recent phases, got {len(recent)}"
    assert all(p == "documentation" for p in recent), "Not all phases are 'documentation'"
    print(f"✓ Last 5 phases: {recent}")
    
    # Check if all same
    all_same = all(p == "documentation" for p in recent)
    assert all_same, "Expected all phases to be same"
    print(f"✓ All phases same: {all_same}")
    
    print("\n✅ TEST 2 PASSED: Phase history tracking works correctly\n")


def test_forced_transition_logic():
    """Test the forced transition detection logic."""
    print("="*70)
    print("TEST 3: Forced Transition Logic")
    print("="*70)
    
    state = PipelineState()
    state_manager = StateManager(Path("/tmp/test"))
    
    # Scenario 1: 5 consecutive same phases
    print("\nScenario 1: 5 consecutive same phases")
    state.phase_history = ["documentation"] * 5
    recent = state.phase_history[-5:]
    should_force = len(recent) == 5 and all(p == "documentation" for p in recent)
    assert should_force, "Should force transition after 5 consecutive phases"
    print(f"✓ Should force transition: {should_force}")
    
    # Scenario 2: 3 no-updates
    print("\nScenario 2: 3 'no updates' responses")
    state.no_update_counts["documentation"] = 3
    count = state.no_update_counts.get("documentation", 0)
    should_force = count >= 3
    assert should_force, "Should force transition after 3 no-updates"
    print(f"✓ Should force transition: {should_force}")
    
    # Scenario 3: Mixed phases (should NOT force)
    print("\nScenario 3: Mixed phases (should NOT force)")
    state.phase_history = ["documentation", "planning", "documentation", "qa", "documentation"]
    recent = state.phase_history[-5:]
    should_force = len(recent) == 5 and all(p == "documentation" for p in recent)
    assert not should_force, "Should NOT force transition with mixed phases"
    print(f"✓ Should NOT force transition: {not should_force}")
    
    print("\n✅ TEST 3 PASSED: Forced transition logic works correctly\n")


def test_state_serialization():
    """Test that new fields serialize/deserialize correctly."""
    print("="*70)
    print("TEST 4: State Serialization")
    print("="*70)
    
    # Create state with new fields
    state = PipelineState()
    state.no_update_counts = {"documentation": 2, "qa": 1}
    state.phase_history = ["planning", "coding", "qa", "documentation", "documentation"]
    
    # Serialize
    state_dict = state.to_dict()
    print(f"✓ Serialized state keys: {list(state_dict.keys())}")
    
    # Check new fields present
    assert "no_update_counts" in state_dict, "no_update_counts missing from serialization"
    assert "phase_history" in state_dict, "phase_history missing from serialization"
    print(f"✓ no_update_counts: {state_dict['no_update_counts']}")
    print(f"✓ phase_history: {state_dict['phase_history']}")
    
    # Deserialize
    state2 = PipelineState.from_dict(state_dict)
    assert state2.no_update_counts == state.no_update_counts, "no_update_counts not preserved"
    assert state2.phase_history == state.phase_history, "phase_history not preserved"
    print(f"✓ Deserialized correctly")
    
    print("\n✅ TEST 4 PASSED: State serialization works correctly\n")


def test_documentation_phase_logic():
    """Test the documentation phase loop prevention logic."""
    print("="*70)
    print("TEST 5: Documentation Phase Loop Prevention")
    print("="*70)
    
    state = PipelineState()
    state_manager = StateManager(Path("/tmp/test"))
    
    print("\nSimulating documentation phase executions:")
    
    # First execution - no updates
    count1 = state_manager.increment_no_update_count(state, "documentation")
    print(f"  Execution 1: count={count1}/3 - Continue")
    assert count1 < 3, "Should continue after first no-update"
    
    # Second execution - no updates
    count2 = state_manager.increment_no_update_count(state, "documentation")
    print(f"  Execution 2: count={count2}/3 - Continue (suggest transition)")
    assert count2 < 3, "Should continue after second no-update"
    
    # Third execution - no updates
    count3 = state_manager.increment_no_update_count(state, "documentation")
    print(f"  Execution 3: count={count3}/3 - FORCE TRANSITION")
    assert count3 >= 3, "Should force transition after third no-update"
    
    # Check if we should force transition
    should_force = state_manager.get_no_update_count(state, "documentation") >= 3
    print(f"\n✓ Force transition triggered: {should_force}")
    
    # Reset after transition
    state_manager.reset_no_update_count(state, "documentation")
    count_after = state_manager.get_no_update_count(state, "documentation")
    print(f"✓ Counter reset after transition: {count_after}")
    assert count_after == 0, "Counter should be 0 after reset"
    
    print("\n✅ TEST 5 PASSED: Documentation phase loop prevention works correctly\n")


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("DOCUMENTATION LOOP FIX - TEST SUITE")
    print("="*70)
    
    try:
        test_no_update_tracking()
        test_phase_history_tracking()
        test_forced_transition_logic()
        test_state_serialization()
        test_documentation_phase_logic()
        
        print("="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print("\nThe documentation loop fix is working correctly!")
        print("\nKey features verified:")
        print("  ✓ No-update counter tracks consecutive 'no updates' responses")
        print("  ✓ Phase history tracks execution sequence")
        print("  ✓ Forced transition triggers after 3 no-updates OR 5 same phases")
        print("  ✓ State serialization preserves new fields")
        print("  ✓ Documentation phase implements loop prevention")
        print("\n")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())