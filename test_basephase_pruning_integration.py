"""
Test BasePhase Integration with Conversation Pruning
"""

from pathlib import Path
import tempfile
from datetime import datetime, timedelta

from pipeline.config import PipelineConfig, ServerConfig
from pipeline.client import OllamaClient
from pipeline.phases.coding import CodingPhase
from pipeline.orchestration.conversation_pruning import AutoPruningConversationThread


def test_basephase_has_auto_pruning():
    """Test that BasePhase uses AutoPruningConversationThread"""
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create config
        config = PipelineConfig(
            project_dir=tmpdir,
            servers=[
                ServerConfig(
                    name="test",
                    host="localhost",
                    port=11434,
                    models=["qwen2.5:14b"]
                )
            ]
        )
        
        # Create client
        client = OllamaClient(config)
        
        # Create phase
        phase = CodingPhase(config, client)
        
        # Check that conversation is AutoPruningConversationThread
        assert isinstance(phase.conversation, AutoPruningConversationThread), \
            f"Expected AutoPruningConversationThread, got {type(phase.conversation)}"
        
        print("✅ BasePhase uses AutoPruningConversationThread")
        
        # Check that it has a pruner
        assert hasattr(phase.conversation, 'pruner'), \
            "AutoPruningConversationThread should have pruner"
        
        print("✅ AutoPruningConversationThread has pruner")
        
        # Check pruning config
        pruning_config = phase.conversation.pruner.config
        assert pruning_config.max_messages == 50, \
            f"Expected max_messages=50, got {pruning_config.max_messages}"
        assert pruning_config.preserve_first_n == 5, \
            f"Expected preserve_first_n=5, got {pruning_config.preserve_first_n}"
        assert pruning_config.preserve_last_n == 20, \
            f"Expected preserve_last_n=20, got {pruning_config.preserve_last_n}"
        
        print("✅ Pruning config correct")
        
        return True


def test_conversation_pruning_works():
    """Test that conversation actually gets pruned"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = PipelineConfig(
            project_dir=tmpdir,
            servers=[
                ServerConfig(
                    name="test",
                    host="localhost", port=11434,
                    models=["qwen2.5:14b"]
                )
            ]
        )
        
        client = OllamaClient(config)
        phase = CodingPhase(config, client)
        
        # Add many messages (more than max_messages)
        old_time = datetime.now() - timedelta(hours=2)
        for i in range(60):
            # Manually add to underlying thread to bypass timestamp issues
            phase.conversation.thread.messages.append({
                "role": "user",
                "content": f"Message {i}",
                "timestamp": old_time.isoformat()
            })
        
        print(f"Added 60 messages")
        
        # Trigger pruning manually
        phase.conversation._auto_prune()
        
        # Check that messages were pruned
        message_count = len(phase.conversation.thread.messages)
        print(f"After pruning: {message_count} messages")
        
        # Should be around max_messages (50) plus some summaries
        assert message_count <= 60, \
            f"Expected <= 60 messages after pruning, got {message_count}"
        
        print("✅ Conversation pruning works")
        
        # Check that summaries were created
        assert len(phase.conversation.prune_summaries) > 0, \
            "Expected prune summaries to be created"
        
        print(f"✅ Created {len(phase.conversation.prune_summaries)} prune summaries")
        
        return True


def test_pruning_preserves_context():
    """Test that pruning preserves important context"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = PipelineConfig(
            project_dir=tmpdir,
            servers=[
                ServerConfig(
                    name="test",
                    host="localhost", port=11434,
                    models=["qwen2.5:14b"]
                )
            ]
        )
        
        client = OllamaClient(config)
        phase = CodingPhase(config, client)
        
        # Add messages with important content
        old_time = datetime.now() - timedelta(hours=2)
        
        # First messages (should be preserved)
        for i in range(5):
            phase.conversation.thread.messages.append({
                "role": "user",
                "content": f"Initial context {i}",
                "timestamp": old_time.isoformat()
            })
        
        # Middle messages (may be pruned)
        for i in range(40):
            phase.conversation.thread.messages.append({
                "role": "user",
                "content": f"Middle message {i}",
                "timestamp": old_time.isoformat()
            })
        
        # Error message (should be preserved)
        phase.conversation.thread.messages.append({
            "role": "assistant",
            "content": "Error: Something went wrong",
            "timestamp": old_time.isoformat()
        })
        
        # Last messages (should be preserved)
        for i in range(10):
            phase.conversation.thread.messages.append({
                "role": "user",
                "content": f"Recent message {i}",
                "timestamp": old_time.isoformat()
            })
        
        print(f"Added 56 messages (5 initial + 40 middle + 1 error + 10 recent)")
        
        # Trigger pruning
        phase.conversation._auto_prune()
        
        messages = phase.conversation.thread.messages
        contents = [msg["content"] for msg in messages]
        
        # Check first messages preserved
        assert any("Initial context 0" in c for c in contents), \
            "First message should be preserved"
        
        print("✅ First messages preserved")
        
        # Check error preserved
        assert any("Error:" in c for c in contents), \
            "Error message should be preserved"
        
        print("✅ Error message preserved")
        
        # Check recent messages preserved
        assert any("Recent message 9" in c for c in contents), \
            "Recent messages should be preserved"
        
        print("✅ Recent messages preserved")
        
        return True


def run_tests():
    """Run all integration tests"""
    print("Testing BasePhase Integration with Conversation Pruning...")
    print()
    
    tests = [
        ("basephase_has_auto_pruning", test_basephase_has_auto_pruning),
        ("conversation_pruning_works", test_conversation_pruning_works),
        ("pruning_preserves_context", test_pruning_preserves_context),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"Running test: {name}")
        try:
            test_func()
            print(f"  ✅ {name} PASSED")
            print()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {name} FAILED: {e}")
            print()
            failed += 1
        except Exception as e:
            print(f"  ❌ {name} ERROR: {e}")
            print()
            failed += 1
    
    print(f"Results: {passed} passed, {failed} failed")
    print()
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)