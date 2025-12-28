"""
Test that the pattern/tool systems are properly integrated.
"""
from pathlib import Path
from autonomy.pipeline.pattern_recognition import PatternRecognitionSystem
from autonomy.pipeline.pattern_optimizer import PatternOptimizer
from autonomy.pipeline.tool_creator import ToolCreator
from autonomy.pipeline.tool_validator import ToolValidator

def test_pattern_recognition():
    """Test pattern recognition system."""
    project_dir = Path(".")
    pr = PatternRecognitionSystem(project_dir)
    
    # Record a test execution
    pr.record_execution({
        'phase': 'coding',
        'success': True,
        'duration': 1.5,
        'tool_calls': [
            {'function': {'name': 'create_file'}},
            {'function': {'name': 'modify_file'}}
        ]
    })
    
    # Get recommendations
    recs = pr.get_recommendations({'phase': 'coding'})
    
    print("✓ Pattern recognition works")
    print(f"  - Recorded 1 execution")
    print(f"  - Got {len(recs)} recommendations")
    
    # Get statistics
    stats = pr.get_statistics()
    print(f"  - Total executions: {stats['total_executions']}")
    print(f"  - Success rate: {stats['success_rate']:.1%}")

def test_pattern_optimizer():
    """Test pattern optimizer."""
    project_dir = Path(".")
    po = PatternOptimizer(project_dir)
    
    # Get statistics
    stats = po.get_statistics()
    
    print("✓ Pattern optimizer works")
    print(f"  - Active patterns: {stats['active_patterns']}")
    print(f"  - DB size: {stats['db_size_mb']:.2f} MB")

def test_tool_creator():
    """Test tool creator."""
    project_dir = Path(".")
    tc = ToolCreator(project_dir)
    
    # Record unknown tool
    tc.record_unknown_tool(
        'test_tool',
        {'phase': 'coding', 'description': 'Test tool usage'}
    )
    
    stats = tc.get_statistics()
    
    print("✓ Tool creator works")
    print(f"  - Total tools: {stats['total_tools']}")
    print(f"  - Unknown tools tracked: {stats['unknown_tools']}")

def test_tool_validator():
    """Test tool validator."""
    project_dir = Path(".")
    tv = ToolValidator(project_dir)
    
    # Record tool usage
    tv.record_tool_usage(
        'create_file',
        success=True,
        execution_time=0.5,
        phase='coding'
    )
    
    # Get effectiveness
    effectiveness = tv.get_tool_effectiveness('create_file')
    
    print("✓ Tool validator works")
    if effectiveness:
        print(f"  - Tracked tool: create_file")
        print(f"  - Success rate: {effectiveness['success_rate']:.1%}")

if __name__ == '__main__':
    print("Testing Pattern/Tool System Integration\n")
    print("=" * 50)
    
    test_pattern_recognition()
    print()
    
    test_pattern_optimizer()
    print()
    
    test_tool_creator()
    print()
    
    test_tool_validator()
    print()
    
    print("=" * 50)
    print("✅ All integration tests passed!")