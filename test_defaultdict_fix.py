#!/usr/bin/env python3
"""
Test to verify defaultdict serialization fix
"""

import json
import sys
from pathlib import Path

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.state.manager import PipelineState, StateManager
from datetime import datetime

def test_serialization_cycle():
    """Test that state can be serialized and deserialized correctly"""
    print("🧪 Testing serialization cycle...")
    
    # Create a state with performance metrics and learned patterns
    state = PipelineState()
    
    # Add performance metrics
    state.performance_metrics['test_metric'] = [
        {'value': 1.0, 'timestamp': datetime.now().isoformat()},
        {'value': 2.0, 'timestamp': datetime.now().isoformat()}
    ]
    
    # Add learned patterns
    state.learned_patterns['test_pattern'] = [
        {'data': 'pattern1', 'timestamp': datetime.now().isoformat()},
        {'data': 'pattern2', 'timestamp': datetime.now().isoformat()}
    ]
    
    print("✓ Created state with metrics and patterns")
    
    # Serialize to dict
    state_dict = state.to_dict()
    print("✓ Serialized to dict")
    
    # Verify types
    assert isinstance(state_dict['performance_metrics'], dict), "performance_metrics should be dict"
    assert isinstance(state_dict['learned_patterns'], dict), "learned_patterns should be dict"
    print("✓ Verified dict types")
    
    # Serialize to JSON
    json_str = json.dumps(state_dict, indent=2)
    print("✓ Serialized to JSON")
    
    # Deserialize from JSON
    loaded_dict = json.loads(json_str)
    print("✓ Deserialized from JSON")
    
    # Recreate state
    loaded_state = PipelineState.from_dict(loaded_dict)
    print("✓ Recreated state from dict")
    
    # Verify data integrity
    assert 'test_metric' in loaded_state.performance_metrics, "test_metric should exist"
    assert len(loaded_state.performance_metrics['test_metric']) == 2, "Should have 2 metrics"
    assert 'test_pattern' in loaded_state.learned_patterns, "test_pattern should exist"
    assert len(loaded_state.learned_patterns['test_pattern']) == 2, "Should have 2 patterns"
    print("✓ Verified data integrity")
    
    # Verify types after deserialization
    assert isinstance(loaded_state.performance_metrics, dict), "performance_metrics should be dict after load"
    assert isinstance(loaded_state.learned_patterns, dict), "learned_patterns should be dict after load"
    print("✓ Verified types after deserialization")
    
    print("\n✅ All tests passed!")
    return True

def test_state_manager_methods():
    """Test StateManager methods with the fix"""
    print("\n🧪 Testing StateManager methods...")
    
    import tempfile
    import shutil
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create state manager
        manager = StateManager(temp_dir)
        state = PipelineState()
        
        # Test add_performance_metric
        manager.add_performance_metric(state, 'cpu_usage', 75.5)
        manager.add_performance_metric(state, 'cpu_usage', 80.2)
        manager.add_performance_metric(state, 'memory_usage', 60.0)
        
        assert 'cpu_usage' in state.performance_metrics, "cpu_usage should exist"
        assert len(state.performance_metrics['cpu_usage']) == 2, "Should have 2 cpu_usage metrics"
        assert 'memory_usage' in state.performance_metrics, "memory_usage should exist"
        print("✓ add_performance_metric works correctly")
        
        # Test learn_pattern
        manager.learn_pattern(state, 'error_pattern', {'type': 'syntax', 'count': 5})
        manager.learn_pattern(state, 'error_pattern', {'type': 'runtime', 'count': 3})
        manager.learn_pattern(state, 'success_pattern', {'type': 'completion', 'count': 10})
        
        assert 'error_pattern' in state.learned_patterns, "error_pattern should exist"
        assert len(state.learned_patterns['error_pattern']) == 2, "Should have 2 error patterns"
        assert 'success_pattern' in state.learned_patterns, "success_pattern should exist"
        print("✓ learn_pattern works correctly")
        
        # Test save/load cycle
        manager.save(state)
        loaded_state = manager.load()
        
        assert 'cpu_usage' in loaded_state.performance_metrics, "cpu_usage should persist"
        assert 'error_pattern' in loaded_state.learned_patterns, "error_pattern should persist"
        print("✓ save/load cycle works correctly")
        
        print("\n✅ All StateManager tests passed!")
        return True
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    try:
        test_serialization_cycle()
        test_state_manager_methods()
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED - defaultdict fix is working!")
        print("="*60)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)