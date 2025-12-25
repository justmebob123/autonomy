#!/usr/bin/env python3
"""
Tool to display AI responses and conversation threads in real-time.
Shows what the AI is thinking and doing.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def show_conversation_thread(thread_file: Path):
    """Display a conversation thread in readable format."""
    try:
        with open(thread_file, 'r') as f:
            thread = json.load(f)
        
        print("\n" + "="*80)
        print(f"CONVERSATION THREAD: {thread_file.name}")
        print("="*80)
        
        # Show metadata
        print(f"\nFile: {thread.get('filepath', 'Unknown')}")
        print(f"Error: {thread.get('error_type', 'Unknown')} - {thread.get('error_message', 'Unknown')}")
        print(f"Line: {thread.get('line_number', 'Unknown')}")
        print(f"Current Attempt: {thread.get('current_attempt', 0)}")
        
        # Show conversation history
        messages = thread.get('conversation_history', [])
        print(f"\n{'='*80}")
        print(f"CONVERSATION HISTORY ({len(messages)} messages)")
        print("="*80)
        
        for i, msg in enumerate(messages, 1):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')
            
            print(f"\n[{i}] {role.upper()} ({timestamp})")
            print("-" * 80)
            print(content[:2000])  # First 2000 chars
            if len(content) > 2000:
                print(f"\n... ({len(content) - 2000} more characters)")
            
            # Show tool results if present
            if 'tool_results' in msg:
                print("\n📋 TOOL RESULTS:")
                for result in msg['tool_results']:
                    print(f"  - {result.get('tool', 'unknown')}: {result.get('success', False)}")
        
        # Show attempts
        attempts = thread.get('attempts', [])
        if attempts:
            print(f"\n{'='*80}")
            print(f"ATTEMPTS ({len(attempts)} total)")
            print("="*80)
            
            for i, attempt in enumerate(attempts, 1):
                print(f"\n[Attempt {i}]")
                print(f"  Success: {attempt.get('success', False)}")
                print(f"  Timestamp: {attempt.get('timestamp', 'Unknown')}")
                if 'error' in attempt:
                    print(f"  Error: {attempt['error']}")
        
        # Show file snapshots
        snapshots = thread.get('file_snapshots', {})
        if snapshots:
            print(f"\n{'='*80}")
            print(f"FILE SNAPSHOTS ({len(snapshots)} versions)")
            print("="*80)
            for attempt_num, content in snapshots.items():
                print(f"\n[After Attempt {attempt_num}] ({len(content)} chars)")
        
    except Exception as e:
        print(f"Error reading thread: {e}")

def show_latest_threads(project_dir: Path, n: int = 5):
    """Show the N most recent conversation threads."""
    threads_dir = project_dir / '.pipeline' / 'conversation_threads'
    
    if not threads_dir.exists():
        print(f"No conversation threads found in {threads_dir}")
        return
    
    # Get all thread files sorted by modification time
    thread_files = sorted(
        threads_dir.glob('thread_*.json'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if not thread_files:
        print(f"No thread files found in {threads_dir}")
        return
    
    print(f"\n{'='*80}")
    print(f"SHOWING {min(n, len(thread_files))} MOST RECENT THREADS")
    print(f"Total threads: {len(thread_files)}")
    print("="*80)
    
    for thread_file in thread_files[:n]:
        show_conversation_thread(thread_file)
        print("\n")

def show_ai_activity_log(project_dir: Path, n: int = 100):
    """Show recent AI activity from the log."""
    log_file = project_dir / 'ai_activity.log'
    
    if not log_file.exists():
        print(f"No AI activity log found at {log_file}")
        return
    
    print("\n" + "="*80)
    print("AI ACTIVITY LOG (Last 100 lines)")
    print("="*80 + "\n")
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    for line in lines[-n:]:
        print(line.rstrip())

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 show_ai_responses.py <project_dir> [num_threads]")
        print("\nExample: python3 show_ai_responses.py ../test-automation 3")
        sys.exit(1)
    
    project_dir = Path(sys.argv[1])
    num_threads = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    # Show AI activity log
    show_ai_activity_log(project_dir)
    
    # Show conversation threads
    show_latest_threads(project_dir, num_threads)