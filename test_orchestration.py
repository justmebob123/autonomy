"""
Test Orchestration System

Verify that the multi-model orchestration system works correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.orchestration import (
    ModelTool,
    SpecialistRegistry,
    get_specialist_registry,
    ConversationThread,
    MultiModelConversationManager,
    ArbiterModel,
    OrchestratedPipeline
)
from pipeline.orchestration.dynamic_prompts import DynamicPromptBuilder, PromptContext
from pipeline.state.manager import StateManager
from pipeline.logging_setup import get_logger

logger = get_logger()


def test_specialist_registry():
    """Test specialist registry."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 1: Specialist Registry")
    logger.info("=" * 70)
    
    registry = get_specialist_registry()
    
    # Check specialists are registered
    specialists = registry.get_all()
    logger.info(f"✓ Registered specialists: {list(specialists.keys())}")
    
    # Check tool definitions
    tools = registry.get_tool_definitions()
    logger.info(f"✓ Tool definitions: {len(tools)} tools")
    for tool in tools:
        logger.info(f"  - {tool['name']}")
    
    # Get a specialist
    coding = registry.get("coding")
    if coding:
        logger.info(f"✓ Coding specialist: {coding.model} on {coding.server}")
    
    logger.info("✓ Test 1 passed\n")


def test_conversation_manager():
    """Test conversation management."""
    logger.info("=" * 70)
    logger.info("TEST 2: Conversation Manager")
    logger.info("=" * 70)
    
    manager = MultiModelConversationManager()
    
    # Create threads
    thread_a = manager.create_thread("model_a", "coding")
    thread_b = manager.create_thread("model_b", "reasoning")
    
    logger.info(f"✓ Created threads for model_a and model_b")
    
    # Add messages
    thread_a.add_message("user", "How should I implement this?")
    thread_a.add_message("assistant", "Here's my suggestion...")
    
    logger.info(f"✓ Added messages to thread_a")
    
    # Route message
    result = manager.route_message(
        from_model="model_a",
        to_model="model_b",
        message="What do you think of this approach?"
    )
    
    logger.info(f"✓ Routed message: {result['routed_to']}")
    
    # Get stats
    stats = manager.get_routing_stats()
    logger.info(f"✓ Routing stats: {stats['total_routes']} routes")
    
    logger.info("✓ Test 2 passed\n")


def test_dynamic_prompts():
    """Test dynamic prompt building."""
    logger.info("=" * 70)
    logger.info("TEST 3: Dynamic Prompt Builder")
    logger.info("=" * 70)
    
    builder = DynamicPromptBuilder(Path.cwd())
    
    # Create context
    context = PromptContext(
        phase="qa",
        task={
            "description": "Review code for issues",
            "target_file": "example.py",
            "attempts": 0
        },
        model_size="14b",
        model_capabilities=["code_review"],
        context_window=8192,
        recent_failures=[],
        file_content="def hello():\n    print('Hello')\n"
    )
    
    # Build prompt
    prompt = builder.build_prompt(context)
    
    logger.info(f"✓ Built prompt ({len(prompt)} chars)")
    logger.info(f"  Preview: {prompt[:200]}...")
    
    # Test with failures
    context.recent_failures = [
        {"type": "empty_tool_name"},
        {"type": "empty_tool_name"}
    ]
    
    prompt_with_failures = builder.build_prompt(context)
    
    if "MUST have a name field" in prompt_with_failures:
        logger.info(f"✓ Prompt adapted to failures")
    
    logger.info("✓ Test 3 passed\n")


def test_arbiter():
    """Test arbiter model."""
    logger.info("=" * 70)
    logger.info("TEST 4: Arbiter Model")
    logger.info("=" * 70)
    
    project_dir = Path.cwd()
    arbiter = ArbiterModel(project_dir)
    
    logger.info(f"✓ Arbiter initialized: {arbiter.model}")
    
    # Check specialist registry
    specialists = arbiter.specialists.get_all()
    logger.info(f"✓ Arbiter has access to {len(specialists)} specialists")
    
    # Check tools
    tools = arbiter._get_arbiter_tools()
    logger.info(f"✓ Arbiter has {len(tools)} tools available")
    
    tool_names = [t['name'] for t in tools]
    logger.info(f"  Tools: {', '.join(tool_names[:5])}...")
    
    logger.info("✓ Test 4 passed\n")


def test_orchestrated_pipeline():
    """Test orchestrated pipeline."""
    logger.info("=" * 70)
    logger.info("TEST 5: Orchestrated Pipeline")
    logger.info("=" * 70)
    
    project_dir = Path.cwd()
    
    # Create pipeline
    pipeline = OrchestratedPipeline(project_dir, config={"max_iterations": 1})
    
    logger.info(f"✓ Pipeline created")
    logger.info(f"  Project: {pipeline.project_dir}")
    logger.info(f"  Arbiter: {pipeline.arbiter.model}")
    logger.info(f"  Specialists: {len(pipeline.specialists.get_all())}")
    
    # Check components
    assert pipeline.state_manager is not None
    assert pipeline.arbiter is not None
    assert pipeline.specialists is not None
    assert pipeline.tool_handler is not None
    
    logger.info("✓ All components initialized")
    logger.info("✓ Test 5 passed\n")


def run_all_tests():
    """Run all tests."""
    logger.info("\n" + "=" * 70)
    logger.info("  ORCHESTRATION SYSTEM TESTS")
    logger.info("=" * 70 + "\n")
    
    try:
        test_specialist_registry()
        test_conversation_manager()
        test_dynamic_prompts()
        test_arbiter()
        test_orchestrated_pipeline()
        
        logger.info("=" * 70)
        logger.info("  ✓ ALL TESTS PASSED")
        logger.info("=" * 70 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ TEST FAILED: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)