"""
Tests for Conversation Pruning System
"""

from datetime import datetime, timedelta
from pipeline.orchestration.conversation_pruning import (
    ConversationPruner,
    PruningConfig,
    AutoPruningConversationThread
)
from pipeline.orchestration.conversation_manager import ConversationThread


class TestConversationPruner:
    """Test ConversationPruner"""
    
    def test_should_prune(self):
        """Test pruning detection"""
        config = PruningConfig(max_messages=10)
        pruner = ConversationPruner(config)
        
        # Should not prune with few messages
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(5)]
        assert not pruner.should_prune(messages)
        
        # Should prune with many messages
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(15)]
        assert pruner.should_prune(messages)
    
    def test_preserve_first_and_last(self):
        """Test that first and last messages are preserved"""
        config = PruningConfig(
            max_messages=10,
            preserve_first_n=3,
            preserve_last_n=3
        )
        pruner = ConversationPruner(config)
        
        # Create 20 messages
        messages = [
            {"role": "user", "content": f"Message {i}", "timestamp": datetime.now().isoformat()}
            for i in range(20)
        ]
        
        pruned, summary = pruner.prune_messages(messages)
        
        # Should keep first 3 and last 3
        assert len(pruned) <= config.max_messages
        assert pruned[0]["content"] == "Message 0"
        assert pruned[1]["content"] == "Message 1"
        assert pruned[2]["content"] == "Message 2"
        assert pruned[-1]["content"] == "Message 19"
        assert pruned[-2]["content"] == "Message 18"
        assert pruned[-3]["content"] == "Message 17"
    
    def test_preserve_errors(self):
        """Test that error messages are preserved"""
        config = PruningConfig(
            max_messages=10,
            preserve_first_n=2,
            preserve_last_n=2,
            preserve_errors=True
        )
        pruner = ConversationPruner(config)
        
        # Create messages with some errors
        messages = []
        for i in range(20):
            content = f"Message {i}"
            if i == 10:
                content = "Error: Something went wrong"
            messages.append({
                "role": "user",
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
        
        pruned, summary = pruner.prune_messages(messages)
        
        # Error message should be preserved
        error_contents = [msg["content"] for msg in pruned]
        assert any("Error:" in content for content in error_contents)
    
    def test_preserve_decisions(self):
        """Test that decision messages are preserved"""
        config = PruningConfig(
            max_messages=10,
            preserve_first_n=2,
            preserve_last_n=2,
            preserve_decisions=True
        )
        pruner = ConversationPruner(config)
        
        # Create messages with some decisions
        messages = []
        for i in range(20):
            content = f"Message {i}"
            if i == 10:
                content = "Decided to use strategy A"
            messages.append({
                "role": "assistant",
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
        
        pruned, summary = pruner.prune_messages(messages)
        
        # Decision message should be preserved
        decision_contents = [msg["content"] for msg in pruned]
        assert any("Decided" in content for content in decision_contents)
    
    def test_preserve_tool_calls(self):
        """Test that messages with tool calls are preserved"""
        config = PruningConfig(
            max_messages=10,
            preserve_first_n=2,
            preserve_last_n=2
        )
        pruner = ConversationPruner(config)
        
        # Create messages with some tool calls
        messages = []
        for i in range(20):
            msg = {
                "role": "assistant",
                "content": f"Message {i}",
                "timestamp": datetime.now().isoformat()
            }
            if i == 10:
                msg["tool_calls"] = [{"name": "execute_code", "arguments": {}}]
            messages.append(msg)
        
        pruned, summary = pruner.prune_messages(messages)
        
        # Tool call message should be preserved
        tool_call_messages = [msg for msg in pruned if msg.get("tool_calls")]
        assert len(tool_call_messages) > 0
    
    def test_age_based_preservation(self):
        """Test that recent messages are not pruned"""
        config = PruningConfig(
            max_messages=10,
            preserve_first_n=2,
            preserve_last_n=2,
            min_prune_age_minutes=30
        )
        pruner = ConversationPruner(config)
        
        # Create messages with different ages
        messages = []
        now = datetime.now()
        
        for i in range(20):
            # Make some messages recent
            if i >= 15:
                timestamp = now
            else:
                timestamp = now - timedelta(minutes=60)
            
            messages.append({
                "role": "user",
                "content": f"Message {i}",
                "timestamp": timestamp.isoformat()
            })
        
        pruned, summary = pruner.prune_messages(messages)
        
        # Recent messages should be preserved
        recent_messages = [msg for msg in pruned if "Message 1" in msg["content"] and int(msg["content"].split()[1]) >= 15]
        assert len(recent_messages) > 0
    
    def test_summary_creation(self):
        """Test that summaries are created"""
        config = PruningConfig(
            max_messages=10,
            preserve_first_n=2,
            preserve_last_n=2,
            summarize_pruned=True
        )
        pruner = ConversationPruner(config)
        
        # Create messages
        messages = [
            {"role": "user", "content": f"Message {i}", "timestamp": datetime.now().isoformat()}
            for i in range(20)
        ]
        
        pruned, summary = pruner.prune_messages(messages)
        
        # Summary should be created
        assert summary is not None
        assert "Pruned" in summary
        assert "messages" in summary
    
    def test_summary_includes_errors(self):
        """Test that summary includes errors"""
        config = PruningConfig(
            max_messages=10,
            preserve_first_n=2,
            preserve_last_n=2,
            summarize_pruned=True
        )
        pruner = ConversationPruner(config)
        
        # Create messages with errors
        messages = []
        for i in range(20):
            content = f"Message {i}"
            if i == 5:
                content = "Error: File not found"
            messages.append({
                "role": "user",
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
        
        pruned, summary = pruner.prune_messages(messages)
        
        # Summary should mention errors
        assert summary is not None
        assert "Error" in summary or "error" in summary.lower()
    
    def test_stats_tracking(self):
        """Test that statistics are tracked"""
        config = PruningConfig(max_messages=10)
        pruner = ConversationPruner(config)
        
        # Create and prune messages
        messages = [
            {"role": "user", "content": f"Message {i}", "timestamp": datetime.now().isoformat()}
            for i in range(20)
        ]
        
        pruned, summary = pruner.prune_messages(messages)
        
        # Check stats
        stats = pruner.get_stats()
        assert stats["total_pruned"] > 0
        assert stats["summaries_created"] > 0


class TestAutoPruningConversationThread:
    """Test AutoPruningConversationThread"""
    
    def test_auto_pruning_on_add(self):
        """Test that pruning happens automatically"""
        # Create base thread
        thread = ConversationThread(
            model="test-model",
            role="assistant",
            max_context_tokens=8192
        )
        
        # Wrap with auto-pruning
        config = PruningConfig(max_messages=10)
        pruner = ConversationPruner(config)
        auto_thread = AutoPruningConversationThread(thread, pruner)
        
        # Add many messages
        for i in range(20):
            auto_thread.add_message("user", f"Message {i}")
        
        # Should have been pruned
        assert len(auto_thread.thread.messages) <= config.max_messages + 5  # +5 for summary messages
    
    def test_prune_summaries_stored(self):
        """Test that prune summaries are stored"""
        thread = ConversationThread(
            model="test-model",
            role="assistant",
            max_context_tokens=8192
        )
        
        config = PruningConfig(max_messages=10, summarize_pruned=True)
        pruner = ConversationPruner(config)
        auto_thread = AutoPruningConversationThread(thread, pruner)
        
        # Add many messages to trigger multiple prunes
        for i in range(30):
            auto_thread.add_message("user", f"Message {i}")
        
        # Should have summaries
        assert len(auto_thread.prune_summaries) > 0
    
    def test_stats_include_pruning(self):
        """Test that stats include pruning info"""
        thread = ConversationThread(
            model="test-model",
            role="assistant",
            max_context_tokens=8192
        )
        
        config = PruningConfig(max_messages=10)
        pruner = ConversationPruner(config)
        auto_thread = AutoPruningConversationThread(thread, pruner)
        
        # Add messages
        for i in range(20):
            auto_thread.add_message("user", f"Message {i}")
        
        # Get stats
        stats = auto_thread.get_stats()
        
        # Should include pruning stats
        assert "pruning" in stats
        assert stats["pruning"]["total_pruned"] > 0


def run_tests():
    """Run all tests"""
    print("Testing Conversation Pruning System...")
    print()
    
    # Test ConversationPruner
    print("Testing ConversationPruner...")
    test_pruner = TestConversationPruner()
    
    tests = [
        ("should_prune", test_pruner.test_should_prune),
        ("preserve_first_and_last", test_pruner.test_preserve_first_and_last),
        ("preserve_errors", test_pruner.test_preserve_errors),
        ("preserve_decisions", test_pruner.test_preserve_decisions),
        ("preserve_tool_calls", test_pruner.test_preserve_tool_calls),
        ("age_based_preservation", test_pruner.test_age_based_preservation),
        ("summary_creation", test_pruner.test_summary_creation),
        ("summary_includes_errors", test_pruner.test_summary_includes_errors),
        ("stats_tracking", test_pruner.test_stats_tracking),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            failed += 1
    
    print()
    print("Testing AutoPruningConversationThread...")
    test_auto = TestAutoPruningConversationThread()
    
    auto_tests = [
        ("auto_pruning_on_add", test_auto.test_auto_pruning_on_add),
        ("prune_summaries_stored", test_auto.test_prune_summaries_stored),
        ("stats_include_pruning", test_auto.test_stats_include_pruning),
    ]
    
    for name, test_func in auto_tests:
        try:
            test_func()
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            failed += 1
    
    print()
    print(f"Results: {passed} passed, {failed} failed")
    print()
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)