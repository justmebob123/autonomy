"""
Test Suite for Specialist Implementations

Tests all specialist models:
- CodingSpecialist
- ReasoningSpecialist
- AnalysisSpecialist
- FunctionGemmaMediator
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline.orchestration.specialists import (
    CodingSpecialist,
    CodingTask,
    ReasoningSpecialist,
    ReasoningTask,
    ReasoningType,
    AnalysisSpecialist,
    AnalysisTask,
    AnalysisType,
    FunctionGemmaMediator,
    InterpretationRequest,
)


class MockModelTool:
    """Mock ModelTool for testing"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.call_count = 0
        
    def execute(self, messages, system_prompt=None, tools=None):
        """Mock execute method"""
        self.call_count += 1
        
        # Return mock response based on model type
        if "coding" in self.model_name.lower():
            return {
                "success": True,
                "response": "I will implement the function with proper error handling and type hints.",
                "tool_calls": [
                    {
                        "name": "write_file",
                        "parameters": {
                            "file_path": "test.py",
                            "content": "def test(): pass"
                        }
                    }
                ]
            }
        elif "reasoning" in self.model_name.lower() or "qwen" in self.model_name.lower():
            return {
                "success": True,
                "response": "After analyzing the problem, I recommend Option 1 because it provides the best balance of performance and maintainability.",
                "tool_calls": []
            }
        elif "analysis" in self.model_name.lower():
            return {
                "success": True,
                "response": "Code review complete. Found 2 issues: missing docstring and unused import.",
                "tool_calls": [
                    {
                        "name": "flag_issue",
                        "parameters": {
                            "severity": "medium",
                            "category": "documentation",
                            "description": "Missing docstring",
                            "location": "line 1"
                        }
                    }
                ]
            }
        elif "gemma" in self.model_name.lower():
            return {
                "success": True,
                "response": '{"tool_call": {"name": "read_file", "parameters": {"file_path": "test.py"}}, "confidence": "high", "reasoning": "Inferred from context"}',
                "tool_calls": []
            }
        else:
            return {
                "success": True,
                "response": "Mock response",
                "tool_calls": []
            }


def test_coding_specialist():
    """Test CodingSpecialist"""
    print("\n" + "="*60)
    print("TEST 1: CodingSpecialist")
    print("="*60)
    
    # Create mock model tool
    model_tool = MockModelTool("qwen2.5-coder:32b")
    
    # Create specialist
    specialist = CodingSpecialist(model_tool)
    
    # Test 1: System prompt generation
    print("\n1. Testing system prompt generation...")
    task = CodingTask(
        file_path="src/main.py",
        task_type="create",
        description="Create a new function",
        context={"requirements": "Must handle errors"}
    )
    prompt = specialist.get_system_prompt(task)
    assert "expert coding specialist" in prompt.lower()
    assert "create new code" in prompt.lower()
    print("   ✓ System prompt generated correctly")
    
    # Test 2: Tool availability
    print("\n2. Testing tool availability...")
    tools = specialist.get_available_tools(task)
    tool_names = [t["name"] for t in tools]
    assert "read_file" in tool_names
    assert "write_file" in tool_names
    assert "search_code" in tool_names
    print(f"   ✓ {len(tools)} tools available: {', '.join(tool_names)}")
    
    # Test 3: Task execution
    print("\n3. Testing task execution...")
    result = specialist.execute_task(task)
    assert result["success"] == True
    assert "tool_calls" in result
    # Tool calls come from the model execution
    print(f"   ✓ Task executed successfully")
    print(f"   ✓ Generated {len(result['tool_calls'])} tool call(s)")
    
    # Test 4: Code review
    print("\n4. Testing code review...")
    review = specialist.review_code(
        "test.py",
        "def test():\n    pass"
    )
    assert review["success"] == True
    assert "review" in review
    print("   ✓ Code review completed")
    
    # Test 5: Result analysis
    print("\n5. Testing result analysis...")
    analysis = result["analysis"]
    assert "complete" in analysis
    assert "quality_score" in analysis
    print(f"   ✓ Quality score: {analysis['quality_score']:.2f}")
    print(f"   ✓ Complete: {analysis['complete']}")
    
    print("\n✅ CodingSpecialist: ALL TESTS PASSED")
    return True


def test_reasoning_specialist():
    """Test ReasoningSpecialist"""
    print("\n" + "="*60)
    print("TEST 2: ReasoningSpecialist")
    print("="*60)
    
    # Create mock model tool
    model_tool = MockModelTool("qwen2.5:32b")
    
    # Create specialist
    specialist = ReasoningSpecialist(model_tool)
    
    # Test 1: System prompt generation
    print("\n1. Testing system prompt generation...")
    task = ReasoningTask(
        reasoning_type=ReasoningType.DECISION_MAKING,
        question="Which approach should we use?",
        context={"options": ["A", "B", "C"]},
        options=[
            {"name": "Option A", "pros": "Fast", "cons": "Complex"},
            {"name": "Option B", "pros": "Simple", "cons": "Slow"}
        ]
    )
    prompt = specialist.get_system_prompt(task)
    assert "expert reasoning specialist" in prompt.lower()
    assert "multi-criteria analysis" in prompt.lower()
    print("   ✓ System prompt generated correctly")
    
    # Test 2: Framework loading
    print("\n2. Testing reasoning frameworks...")
    frameworks = specialist.reasoning_frameworks
    assert "strategic_planning" in frameworks
    assert "problem_analysis" in frameworks
    assert "decision_making" in frameworks
    assert "failure_diagnosis" in frameworks
    print(f"   ✓ {len(frameworks)} frameworks loaded")
    
    # Test 3: Tool availability
    print("\n3. Testing tool availability...")
    tools = specialist.get_available_tools(task)
    tool_names = [t["name"] for t in tools]
    assert "gather_data" in tool_names
    assert "analyze_pattern" in tool_names
    assert "evaluate_option" in tool_names
    print(f"   ✓ {len(tools)} tools available: {', '.join(tool_names)}")
    
    # Test 4: Task execution
    print("\n4. Testing task execution...")
    result = specialist.execute_task(task)
    assert result["success"] == True
    assert "structured_reasoning" in result
    print("   ✓ Task executed successfully")
    
    # Test 5: Failure diagnosis
    print("\n5. Testing failure diagnosis...")
    diagnosis = specialist.diagnose_failure(
        "System keeps failing after 20 iterations",
        {"recent_errors": ["timeout", "empty tool name"]}
    )
    assert "diagnosis" in diagnosis
    assert "root_cause" in diagnosis
    print("   ✓ Failure diagnosis completed")
    
    # Test 6: Decision making
    print("\n6. Testing decision making...")
    decision = specialist.make_decision(
        "Which model should we use?",
        [
            {"name": "14b", "speed": "fast", "quality": "good"},
            {"name": "32b", "speed": "slow", "quality": "excellent"}
        ],
        ["speed", "quality", "cost"],
        {"budget": "limited"}
    )
    assert "decision" in decision
    assert "confidence" in decision
    print(f"   ✓ Decision made with {decision['confidence']} confidence")
    
    print("\n✅ ReasoningSpecialist: ALL TESTS PASSED")
    return True


def test_analysis_specialist():
    """Test AnalysisSpecialist"""
    print("\n" + "="*60)
    print("TEST 3: AnalysisSpecialist")
    print("="*60)
    
    # Create mock model tool
    model_tool = MockModelTool("qwen2.5:14b")
    
    # Create specialist
    specialist = AnalysisSpecialist(model_tool)
    
    # Test 1: System prompt generation
    print("\n1. Testing system prompt generation...")
    task = AnalysisTask(
        analysis_type=AnalysisType.CODE_REVIEW,
        target="def test(): pass",
        context={"file_path": "test.py"},
        quick_mode=True
    )
    prompt = specialist.get_system_prompt(task)
    assert "expert analysis specialist" in prompt.lower()
    assert "quick analysis" in prompt.lower()
    print("   ✓ System prompt generated correctly")
    
    # Test 2: Pattern loading
    print("\n2. Testing analysis patterns...")
    patterns = specialist.analysis_patterns
    assert "code_smells" in patterns
    assert "security_issues" in patterns
    assert "performance_issues" in patterns
    assert "style_issues" in patterns
    print(f"   ✓ {len(patterns)} pattern categories loaded")
    
    # Test 3: Tool availability
    print("\n3. Testing tool availability...")
    tools = specialist.get_available_tools(task)
    tool_names = [t["name"] for t in tools]
    assert "flag_issue" in tool_names
    assert "check_pattern" in tool_names
    print(f"   ✓ {len(tools)} tools available: {', '.join(tool_names)}")
    
    # Test 4: Task execution
    print("\n4. Testing task execution...")
    result = specialist.execute_task(task)
    assert result["success"] == True
    assert "findings" in result
    print("   ✓ Task executed successfully")
    
    # Test 5: Quick code review
    print("\n5. Testing quick code review...")
    review = specialist.quick_code_review(
        "test.py",
        "def test():\n    pass"
    )
    assert "findings" in review
    assert "passed" in review
    print(f"   ✓ Review completed, passed: {review['passed']}")
    
    # Test 6: Quality check
    print("\n6. Testing quality check...")
    quality = specialist.check_quality(
        "test.py",
        "def test():\n    pass",
        {"style": "PEP 8"}
    )
    assert "quality_score" in quality
    assert "passed" in quality
    print(f"   ✓ Quality score: {quality['quality_score']:.1f}/100")
    
    # Test 7: Pattern detection
    print("\n7. Testing pattern detection...")
    patterns = specialist.detect_patterns(
        "for i in range(10):\n    for j in range(10):\n        pass",
        ["nested_loops", "complexity"]
    )
    assert "patterns_found" in patterns
    print(f"   ✓ Pattern detection completed")
    
    print("\n✅ AnalysisSpecialist: ALL TESTS PASSED")
    return True


def test_function_gemma_mediator():
    """Test FunctionGemmaMediator"""
    print("\n" + "="*60)
    print("TEST 4: FunctionGemmaMediator")
    print("="*60)
    
    # Create mock model tool
    model_tool = MockModelTool("functiongemma")
    
    # Create mediator
    mediator = FunctionGemmaMediator(model_tool)
    
    # Test 1: System prompt generation
    print("\n1. Testing system prompt generation...")
    request = InterpretationRequest(
        original_response='{"name": "", "parameters": {}}',
        context={"intent": "read file"},
        available_tools=[
            {
                "name": "read_file",
                "description": "Read a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"}
                    },
                    "required": ["file_path"]
                }
            }
        ]
    )
    prompt = mediator.get_system_prompt(request)
    assert "functiongemma" in prompt.lower()
    assert "tool call" in prompt.lower()
    print("   ✓ System prompt generated correctly")
    
    # Test 2: Pattern loading
    print("\n2. Testing interpretation patterns...")
    patterns = mediator.interpretation_patterns
    assert "empty_tool_name" in patterns
    assert "malformed_json" in patterns
    assert "natural_language" in patterns
    print(f"   ✓ {len(patterns)} interpretation patterns loaded")
    
    # Test 3: Interpretation
    print("\n3. Testing interpretation...")
    result = mediator.interpret(request)
    assert "interpretation" in result
    assert "confidence" in result
    print(f"   ✓ Interpretation completed with {result['confidence']} confidence")
    
    # Test 4: Fix empty tool name
    print("\n4. Testing empty tool name fix...")
    fix_result = mediator.fix_empty_tool_name(
        {"name": "", "parameters": {}},
        {"intent": "read test.py"},
        request.available_tools
    )
    assert "success" in fix_result
    print(f"   ✓ Fix attempt completed, success: {fix_result['success']}")
    
    # Test 5: Repair malformed JSON
    print("\n5. Testing JSON repair...")
    repair_result = mediator.repair_malformed_json(
        '{"name": "test", "params": {incomplete'
    )
    assert "success" in repair_result
    print(f"   ✓ Repair attempt completed")
    
    # Test 6: Convert natural language
    print("\n6. Testing natural language conversion...")
    convert_result = mediator.convert_natural_language_to_tool_call(
        "Please read the test.py file",
        request.available_tools,
        {}
    )
    assert "success" in convert_result
    print(f"   ✓ Conversion attempt completed")
    
    # Test 7: Validate parameters
    print("\n7. Testing parameter validation...")
    validate_result = mediator.validate_and_fix_parameters(
        {"name": "read_file", "parameters": {}},
        request.available_tools[0],
        {"file_path": "test.py"}
    )
    assert "success" in validate_result
    # Validation field may or may not be present depending on result
    validation_status = validate_result.get('validation', validate_result.get('error', 'unknown'))
    print(f"   ✓ Validation: {validation_status}")
    
    print("\n✅ FunctionGemmaMediator: ALL TESTS PASSED")
    return True


def test_integration():
    """Test integration between specialists"""
    print("\n" + "="*60)
    print("TEST 5: Integration Tests")
    print("="*60)
    
    # Create all specialists
    coding_tool = MockModelTool("qwen2.5-coder:32b")
    reasoning_tool = MockModelTool("qwen2.5:32b")
    analysis_tool = MockModelTool("qwen2.5:14b")
    gemma_tool = MockModelTool("functiongemma")
    
    coding_specialist = CodingSpecialist(coding_tool)
    reasoning_specialist = ReasoningSpecialist(reasoning_tool)
    analysis_specialist = AnalysisSpecialist(analysis_tool)
    gemma_mediator = FunctionGemmaMediator(gemma_tool)
    
    print("\n1. Testing specialist collaboration workflow...")
    
    # Step 1: Reasoning specialist plans approach
    print("   Step 1: Reasoning specialist plans approach...")
    plan_task = ReasoningTask(
        reasoning_type=ReasoningType.STRATEGIC_PLANNING,
        question="How should we implement this feature?",
        context={"feature": "user authentication"}
    )
    plan_result = reasoning_specialist.execute_task(plan_task)
    assert plan_result["success"]
    print("   ✓ Plan created")
    
    # Step 2: Coding specialist implements
    print("   Step 2: Coding specialist implements...")
    code_task = CodingTask(
        file_path="auth.py",
        task_type="create",
        description="Implement authentication",
        context={"plan": plan_result["analysis"]}
    )
    code_result = coding_specialist.execute_task(code_task)
    assert code_result["success"]
    print("   ✓ Code implemented")
    
    # Step 3: Analysis specialist reviews
    print("   Step 3: Analysis specialist reviews...")
    review_task = AnalysisTask(
        analysis_type=AnalysisType.CODE_REVIEW,
        target="def authenticate(): pass",
        context={"file_path": "auth.py"}
    )
    review_result = analysis_specialist.execute_task(review_task)
    assert review_result["success"]
    print("   ✓ Code reviewed")
    
    # Step 4: If issues found, reasoning specialist diagnoses
    print("   Step 4: Reasoning specialist diagnoses issues...")
    if review_result["findings"]["issues"]:
        diagnosis = reasoning_specialist.diagnose_failure(
            "Code review found issues",
            {"issues": review_result["findings"]["issues"]}
        )
        assert "diagnosis" in diagnosis
        print("   ✓ Issues diagnosed")
    else:
        print("   ✓ No issues to diagnose")
    
    # Step 5: FunctionGemma mediates if needed
    print("   Step 5: FunctionGemma mediates ambiguous responses...")
    if not code_result["tool_calls"]:
        interpretation = gemma_mediator.interpret(
            InterpretationRequest(
                original_response=code_result["response"],
                context={"task": "implement auth"},
                available_tools=coding_specialist.get_available_tools(code_task)
            )
        )
        print("   ✓ Response interpreted")
    else:
        print("   ✓ No interpretation needed")
    
    print("\n✅ Integration: ALL TESTS PASSED")
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("SPECIALIST IMPLEMENTATIONS TEST SUITE")
    print("="*60)
    
    tests = [
        ("CodingSpecialist", test_coding_specialist),
        ("ReasoningSpecialist", test_reasoning_specialist),
        ("AnalysisSpecialist", test_analysis_specialist),
        ("FunctionGemmaMediator", test_function_gemma_mediator),
        ("Integration", test_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name}: FAILED")
            print(f"   Error: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name:30s} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)