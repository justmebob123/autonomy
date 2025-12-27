"""
Test Self-Development Infrastructure

Tests for:
- Background arbiter observer
- Pattern recognition system
- Tool creator system
"""

from pathlib import Path
import time
import tempfile

from pipeline.background_arbiter import BackgroundArbiter, ConversationEvent
from pipeline.pattern_recognition import PatternRecognitionSystem
from pipeline.tool_creator import ToolCreator


def test_background_arbiter():
    """Test background arbiter observer."""
    print("Testing Background Arbiter Observer")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        arbiter = BackgroundArbiter(project_dir)
        
        # Start arbiter
        arbiter.start()
        assert arbiter.running, "Arbiter should be running"
        print("✅ Arbiter started")
        
        # Add confusion event
        event = ConversationEvent(
            phase="coding",
            role="assistant",
            content="I don't understand what you mean by that"
        )
        arbiter.add_event(event)
        
        # Give arbiter time to process
        time.sleep(0.5)
        
        # Check interventions
        summary = arbiter.get_intervention_summary()
        assert summary['total'] > 0, "Should have detected confusion"
        print(f"✅ Detected {summary['total']} interventions")
        
        # Add complexity event
        event2 = ConversationEvent(
            phase="coding",
            role="assistant",
            content="This is too complex, please simplify"
        )
        arbiter.add_event(event2)
        time.sleep(0.5)
        
        summary = arbiter.get_intervention_summary()
        assert summary['total'] >= 2, "Should have detected complexity"
        print(f"✅ Total interventions: {summary['total']}")
        
        # Stop arbiter
        arbiter.stop()
        assert not arbiter.running, "Arbiter should be stopped"
        print("✅ Arbiter stopped")


def test_pattern_recognition():
    """Test pattern recognition system."""
    print("\nTesting Pattern Recognition System")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        pattern_system = PatternRecognitionSystem(project_dir)
        
        # Record successful execution
        execution1 = {
            'phase': 'coding',
            'success': True,
            'tool_calls': [
                {'function': {'name': 'create_file'}},
                {'function': {'name': 'write_content'}}
            ],
            'duration': 5.2
        }
        pattern_system.record_execution(execution1)
        print("✅ Recorded successful execution")
        
        # Record failed execution
        execution2 = {
            'phase': 'coding',
            'success': False,
            'tool_calls': [
                {'function': {'name': 'create_file'}}
            ],
            'errors': [
                {'type': 'syntax_error', 'message': 'Invalid syntax'}
            ],
            'duration': 2.1
        }
        pattern_system.record_execution(execution2)
        print("✅ Recorded failed execution")
        
        # Record another successful execution with same pattern
        execution3 = {
            'phase': 'coding',
            'success': True,
            'tool_calls': [
                {'function': {'name': 'create_file'}},
                {'function': {'name': 'write_content'}}
            ],
            'duration': 4.8
        }
        pattern_system.record_execution(execution3)
        print("✅ Recorded another successful execution")
        
        # Get statistics
        stats = pattern_system.get_statistics()
        assert stats['total_executions'] == 3, "Should have 3 executions"
        assert stats['success_rate'] > 0.5, "Should have >50% success rate"
        print(f"✅ Success rate: {stats['success_rate']:.2%}")
        
        # Get recommendations
        recommendations = pattern_system.get_recommendations({'phase': 'coding'})
        print(f"✅ Generated {len(recommendations)} recommendations")
        
        # Save and load patterns
        pattern_system.save_patterns()
        print("✅ Saved patterns")
        
        # Create new system and load
        pattern_system2 = PatternRecognitionSystem(project_dir)
        pattern_system2.load_patterns()
        stats2 = pattern_system2.get_statistics()
        assert stats2['total_executions'] == 3, "Should load 3 executions"
        print("✅ Loaded patterns")


def test_tool_creator():
    """Test tool creator system."""
    print("\nTesting Tool Creator System")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        tool_creator = ToolCreator(project_dir)
        
        # Record unknown tool attempts
        tool_creator.record_unknown_tool('validate_json', {
            'phase': 'coding',
            'description': 'Need to validate JSON format'
        })
        print("✅ Recorded unknown tool attempt (1/3)")
        
        tool_creator.record_unknown_tool('validate_json', {
            'phase': 'coding',
            'description': 'Validate JSON structure'
        })
        print("✅ Recorded unknown tool attempt (2/3)")
        
        tool_creator.record_unknown_tool('validate_json', {
            'phase': 'coding',
            'description': 'Check JSON validity'
        })
        print("✅ Recorded unknown tool attempt (3/3)")
        
        # Check if tool creation was proposed
        pending = tool_creator.get_pending_requests()
        assert len(pending) > 0, "Should have pending tool creation request"
        print(f"✅ Tool creation proposed: {pending[0]['spec'].name}")
        
        # Approve tool creation
        spec = tool_creator.approve_tool_creation(0)
        assert spec is not None, "Should create tool spec"
        print(f"✅ Tool created: {spec.name}")
        
        # Get tool definitions
        definitions = tool_creator.get_tool_definitions()
        assert len(definitions) > 0, "Should have tool definitions"
        print(f"✅ Tool definitions: {len(definitions)}")
        
        # Request explicit tool creation
        tool_creator.request_tool_creation(
            'format_code',
            'Format code according to style guide',
            {
                'code': {'type': 'string', 'description': 'Code to format'},
                'style': {'type': 'string', 'description': 'Style guide to use'}
            },
            requester='user'
        )
        print("✅ Explicit tool creation requested")
        
        # Get statistics
        stats = tool_creator.get_statistics()
        print(f"✅ Total tools: {stats['total_tools']}")
        print(f"✅ Pending requests: {stats['pending_requests']}")
        
        # Save and load
        tool_creator.save_tool_specs()
        print("✅ Saved tool specs")
        
        tool_creator2 = ToolCreator(project_dir)
        tool_creator2.load_tool_specs()
        stats2 = tool_creator2.get_statistics()
        assert stats2['total_tools'] == stats['total_tools'], "Should load same number of tools"
        print("✅ Loaded tool specs")


def test_integration():
    """Test integration of all systems."""
    print("\nTesting System Integration")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Initialize all systems
        arbiter = BackgroundArbiter(project_dir)
        pattern_system = PatternRecognitionSystem(project_dir)
        tool_creator = ToolCreator(project_dir)
        
        arbiter.start()
        print("✅ All systems initialized")
        
        # Simulate execution with all systems
        execution = {
            'phase': 'coding',
            'success': True,
            'tool_calls': [
                {'function': {'name': 'create_file'}},
                {'function': {'name': 'unknown_tool'}}
            ],
            'duration': 3.5
        }
        
        # Record in pattern system
        pattern_system.record_execution(execution)
        
        # Record unknown tool
        tool_creator.record_unknown_tool('unknown_tool', {
            'phase': 'coding',
            'description': 'Attempted to use unknown tool'
        })
        
        # Add event to arbiter
        event = ConversationEvent(
            phase="coding",
            role="assistant",
            content="Successfully created file"
        )
        arbiter.add_event(event)
        
        time.sleep(0.5)
        
        print("✅ Simulated execution across all systems")
        
        # Get statistics from all systems
        arbiter_summary = arbiter.get_intervention_summary()
        pattern_stats = pattern_system.get_statistics()
        tool_stats = tool_creator.get_statistics()
        
        print(f"✅ Arbiter interventions: {arbiter_summary['total']}")
        print(f"✅ Pattern executions: {pattern_stats['total_executions']}")
        print(f"✅ Unknown tools: {tool_stats['unknown_tools']}")
        
        arbiter.stop()
        print("✅ Integration test complete")


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Self-Development Infrastructure")
    print("=" * 60)
    
    test_background_arbiter()
    test_pattern_recognition()
    test_tool_creator()
    test_integration()
    
    print("\n" + "=" * 60)
    print("✅ All self-development tests passed!")
    print("=" * 60)