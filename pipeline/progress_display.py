"""
Enhanced progress display for showing bug transitions clearly.
"""
from typing import Dict, Any, Set
from .error_signature import ErrorSignature


def print_bug_transition(transition: Dict[str, Any]) -> None:
    """Print a clear bug transition message."""
    
    transition_type = transition['type']
    fixed = transition['fixed']
    new = transition['new']
    persisting = transition['persisting']
    
    if transition_type == 'BUG_TRANSITION':
        print("\n" + "=" * 70)
        print("🎉 BUG FIXED! MOVING TO NEXT ERROR")
        print("=" * 70)
        print()
        
        print("✅ FIXED BUG(S):")
        for sig in fixed:
            print(f"   Type: {sig.error_type}")
            print(f"   Message: {sig.message}")
            print(f"   Location: {sig.file}:{sig.line}")
            print()
        
        print("🆕 NEW BUG(S) DISCOVERED:")
        for sig in new:
            print(f"   Type: {sig.error_type}")
            print(f"   Message: {sig.message}")
            print(f"   Location: {sig.file}:{sig.line}")
            print()
        
        if persisting:
            print("⏳ STILL WORKING ON:")
            for sig in persisting:
                print(f"   - {sig}")
            print()
        
        print("💡 ANALYSIS:")
        print("   The AI successfully fixed the previous bug(s). The new error")
        print("   discovered is a different issue, which is normal progress in")
        print("   debugging - fixing one issue often reveals the next.")
        print()
        print("=" * 70)
        print()
    
    elif transition_type == 'BUG_FIXED':
        print("\n" + "=" * 70)
        print("🎉 BUG(S) FIXED! NO NEW ERRORS")
        print("=" * 70)
        print()
        
        print("✅ FIXED BUG(S):")
        for sig in fixed:
            print(f"   Type: {sig.error_type}")
            print(f"   Message: {sig.message}")
            print(f"   Location: {sig.file}:{sig.line}")
            print()
        
        if persisting:
            print("⏳ REMAINING BUG(S):")
            for sig in persisting:
                print(f"   - {sig}")
            print()
        else:
            print("✨ ALL BUGS FIXED! System is clean.")
            print()
        
        print("=" * 70)
        print()
    
    elif transition_type == 'NEW_BUG':
        print("\n" + "=" * 70)
        print("🆕 NEW BUG(S) DISCOVERED")
        print("=" * 70)
        print()
        
        print("🆕 NEW BUG(S):")
        for sig in new:
            print(f"   Type: {sig.error_type}")
            print(f"   Message: {sig.message}")
            print(f"   Location: {sig.file}:{sig.line}")
            print()
        
        if persisting:
            print("⏳ EXISTING BUG(S):")
            for sig in persisting:
                print(f"   - {sig}")
            print()
        
        print("💡 ANALYSIS:")
        print("   New error(s) discovered. This may be due to code changes")
        print("   or deeper issues being revealed as surface problems are fixed.")
        print()
        print("=" * 70)
        print()
    
    elif transition_type == 'NO_PROGRESS':
        print("\n" + "=" * 70)
        print("⚠️  NO PROGRESS - SAME BUG(S) PERSISTING")
        print("=" * 70)
        print()
        
        print("🔴 STUCK ON:")
        for sig in persisting:
            print(f"   Type: {sig.error_type}")
            print(f"   Message: {sig.message}")
            print(f"   Location: {sig.file}:{sig.line}")
            print()
        
        print("💡 RECOMMENDATION:")
        print("   The same error(s) are persisting without progress.")
        print("   Consider:")
        print("   - Consulting a specialist for fresh perspective")
        print("   - Trying a fundamentally different approach")
        print("   - Requesting user guidance")
        print()
        print("=" * 70)
        print()


def print_progress_stats(stats: Dict[str, int]) -> None:
    """Print progress statistics."""
    print("\n" + "=" * 70)
    print("📊 PROGRESS STATISTICS")
    print("=" * 70)
    print(f"   Iterations completed: {stats['iterations']}")
    print(f"   Bugs fixed this session: {stats['bugs_fixed']}")
    print(f"   New bugs discovered: {stats['bugs_discovered']}")
    print(f"   Current active bugs: {stats['current_bugs']}")
    print(f"   Net progress: {stats['bugs_fixed'] - stats['bugs_discovered']} bugs eliminated")
    print("=" * 70)
    print()


def print_refining_fix() -> None:
    """Print message when AI is refining a fix for the same bug."""
    print("\n" + "=" * 70)
    print("🔄 REFINING FIX - SAME BUG, DIFFERENT APPROACH")
    print("=" * 70)
    print()
    print("🎯 The AI is trying a different approach to fix the same bug.")
    print("   This is normal - complex bugs often require multiple attempts")
    print("   with different strategies.")
    print()
    print("=" * 70)
    print()