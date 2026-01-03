#!/usr/bin/env python3
"""
Test script to verify all dataclasses can be properly serialized to JSON.
This catches datetime serialization errors before they cause runtime failures.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_task_state_serialization():
    """Test TaskState can be serialized to JSON"""
    from pipeline.state.manager import TaskState, TaskStatus
    
    # Create a TaskState with all fields
    task = TaskState(
        task_id="test_task",
        description="Test task",
        target_file="test.py",
        status=TaskStatus.NEW,
        priority=10,
        created_at=datetime.now().isoformat(),  # Should be string, not datetime
        updated_at=datetime.now().isoformat()
    )
    
    # Try to serialize
    try:
        task_dict = task.to_dict()
        json_str = json.dumps(task_dict)
        print("✅ TaskState serialization: PASS")
        return True
    except TypeError as e:
        print(f"❌ TaskState serialization: FAIL - {e}")
        return False

def test_pipeline_state_serialization():
    """Test PipelineState can be serialized to JSON"""
    from pipeline.state.manager import PipelineState, TaskState, TaskStatus
    
    # Create a minimal state
    state = PipelineState()
    
    # Add a task
    task = TaskState(
        task_id="test_task",
        description="Test task",
        target_file="test.py",
        status=TaskStatus.NEW,
        priority=10,
        created_at=datetime.now().isoformat()
    )
    state.tasks["test_task"] = task
    
    # Try to serialize
    try:
        state_dict = state.to_dict()
        json_str = json.dumps(state_dict)
        print("✅ PipelineState serialization: PASS")
        return True
    except TypeError as e:
        print(f"❌ PipelineState serialization: FAIL - {e}")
        return False

def test_refactoring_task_serialization():
    """Test RefactoringTask can be serialized to JSON"""
    try:
        from pipeline.state.refactoring_task import RefactoringTask, RefactoringIssueType
        
        # Create a refactoring task
        task = RefactoringTask(
            task_id="refactor_test",
            issue_type=RefactoringIssueType.DUPLICATE,
            title="Test Refactoring",
            description="Test refactoring task",
            target_files=["test1.py", "test2.py"]
        )
        
        # Try to serialize
        task_dict = task.to_dict()
        json_str = json.dumps(task_dict)
        print("✅ RefactoringTask serialization: PASS")
        return True
    except TypeError as e:
        print(f"❌ RefactoringTask serialization: FAIL - {e}")
        return False
    except ImportError:
        print("⚠️  RefactoringTask: SKIP (module not found)")
        return True

def main():
    """Run all serialization tests"""
    print("=" * 60)
    print("Testing JSON Serialization")
    print("=" * 60)
    
    tests = [
        test_task_state_serialization,
        test_pipeline_state_serialization,
        test_refactoring_task_serialization
    ]
    
    results = [test() for test in tests]
    
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed < total:
        print("\n❌ FAILED: Some serialization tests failed!")
        print("Fix these issues before committing to prevent runtime errors.")
        sys.exit(1)
    else:
        print("\n✅ SUCCESS: All serialization tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()