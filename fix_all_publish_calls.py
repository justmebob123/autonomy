#!/usr/bin/env python3
"""
Fix all incorrect MessageBus.publish() calls in the codebase.

This script will:
1. Find all incorrect publish() calls
2. Convert them to the correct Message object pattern
3. Create backup files before modifying
4. Generate a detailed report of changes
"""

import re
from pathlib import Path
from typing import List, Dict, Any
import shutil

def backup_file(filepath: Path) -> Path:
    """Create a backup of the file."""
    backup_path = filepath.with_suffix(filepath.suffix + '.backup')
    shutil.copy2(filepath, backup_path)
    return backup_path

def fix_planning_phase(filepath: Path) -> Dict[str, Any]:
    """Fix planning.py publish calls."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes = []
    
    # Pattern 1: self.message_bus.publish(MessageType.X, source=..., payload={...})
    # Replace with proper Message object
    
    # Find the _publish_architecture_events method
    pattern = r'self\.message_bus\.publish\(\s*MessageType\.(\w+),\s*source=([^,]+),\s*payload=\{([^}]+)\}\s*\)'
    
    def replace_func(match):
        msg_type = match.group(1)
        source = match.group(2)
        payload_content = match.group(3)
        
        changes.append({
            'line': content[:match.start()].count('\n') + 1,
            'old': match.group(0),
            'new': f'Message object with MessageType.{msg_type}'
        })
        
        # Build the replacement
        return f'''Message(
                sender={source},
                recipient="broadcast",
                message_type=MessageType.{msg_type},
                priority=MessagePriority.HIGH,
                payload={{{payload_content}}}
            )'''
    
    # First, we need to add the Message import if not present
    if 'from ..messaging import Message' not in content:
        # Find the MessageType import line
        import_pattern = r'from \.\.messaging import MessageType'
        if re.search(import_pattern, content):
            content = re.sub(
                import_pattern,
                'from ..messaging import Message, MessageType, MessagePriority',
                content
            )
        else:
            # Add import at the top of the method
            content = content.replace(
                'from ..messaging import MessageType',
                'from ..messaging import Message, MessageType, MessagePriority',
                1
            )
    
    # Now replace all the publish calls
    content = re.sub(pattern, replace_func, content, flags=re.MULTILINE | re.DOTALL)
    
    # Also need to wrap the Message in publish()
    content = re.sub(
        r'self\.message_bus\.publish\(\s*Message\(',
        'self.message_bus.publish(Message(',
        content
    )
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return {'file': str(filepath), 'changes': len(changes), 'details': changes}
    
    return {'file': str(filepath), 'changes': 0, 'details': []}

def fix_documentation_phase(filepath: Path) -> Dict[str, Any]:
    """Fix documentation.py publish calls."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes = []
    
    # Same pattern as planning
    pattern = r'self\.message_bus\.publish\(\s*MessageType\.(\w+),\s*source=([^,]+),\s*payload=\{([^}]+)\}\s*\)'
    
    def replace_func(match):
        msg_type = match.group(1)
        source = match.group(2)
        payload_content = match.group(3)
        
        changes.append({
            'line': content[:match.start()].count('\n') + 1,
            'old': match.group(0),
            'new': f'Message object with MessageType.{msg_type}'
        })
        
        return f'''Message(
                sender={source},
                recipient="broadcast",
                message_type=MessageType.{msg_type},
                priority=MessagePriority.HIGH,
                payload={{{payload_content}}}
            )'''
    
    # Add imports
    if 'from ..messaging import Message' not in content:
        content = content.replace(
            'from ..messaging import MessageType',
            'from ..messaging import Message, MessageType, MessagePriority',
            1
        )
    
    content = re.sub(pattern, replace_func, content, flags=re.MULTILINE | re.DOTALL)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return {'file': str(filepath), 'changes': len(changes), 'details': changes}
    
    return {'file': str(filepath), 'changes': 0, 'details': []}

def fix_refactoring_phase(filepath: Path) -> Dict[str, Any]:
    """Fix refactoring.py publish calls."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes = []
    
    # Pattern: self.message_bus.publish(MessageType.X, {...})
    pattern = r'self\.message_bus\.publish\(MessageType\.(\w+),\s*\{([^}]+)\}\)'
    
    def replace_func(match):
        msg_type = match.group(1)
        payload_content = match.group(2)
        
        changes.append({
            'line': content[:match.start()].count('\n') + 1,
            'old': match.group(0),
            'new': f'Message object with MessageType.{msg_type}'
        })
        
        return f'''self.message_bus.publish(Message(
                sender=self.phase_name,
                recipient="broadcast",
                message_type=MessageType.{msg_type},
                priority=MessagePriority.NORMAL,
                payload={{{payload_content}}}
            ))'''
    
    # Add imports
    if 'from ..messaging import Message' not in content:
        # Find MessageType import
        if 'from ..messaging import MessageType' in content:
            content = content.replace(
                'from ..messaging import MessageType',
                'from ..messaging import Message, MessageType, MessagePriority',
                1
            )
        else:
            # Add at the beginning of methods that use it
            content = re.sub(
                r'(if self\.message_bus:\s+from \.\.messaging import MessageType)',
                r'\1, Message, MessagePriority',
                content
            )
    
    content = re.sub(pattern, replace_func, content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return {'file': str(filepath), 'changes': len(changes), 'details': changes}
    
    return {'file': str(filepath), 'changes': 0, 'details': []}

def main():
    print("=" * 80)
    print("FIXING ALL MESSAGEBUS.PUBLISH() CALLS")
    print("=" * 80)
    print()
    
    project_root = Path(".")
    
    files_to_fix = [
        project_root / "pipeline" / "phases" / "planning.py",
        project_root / "pipeline" / "phases" / "documentation.py",
        project_root / "pipeline" / "phases" / "refactoring.py"
    ]
    
    all_results = []
    
    for filepath in files_to_fix:
        if not filepath.exists():
            print(f"⚠️  File not found: {filepath}")
            continue
        
        print(f"📝 Processing: {filepath.name}")
        
        # Create backup
        backup_path = backup_file(filepath)
        print(f"   ✅ Backup created: {backup_path.name}")
        
        # Fix the file
        if 'planning' in filepath.name:
            result = fix_planning_phase(filepath)
        elif 'documentation' in filepath.name:
            result = fix_documentation_phase(filepath)
        elif 'refactoring' in filepath.name:
            result = fix_refactoring_phase(filepath)
        else:
            result = {'file': str(filepath), 'changes': 0, 'details': []}
        
        all_results.append(result)
        
        if result['changes'] > 0:
            print(f"   ✅ Fixed {result['changes']} publish() calls")
        else:
            print(f"   ℹ️  No changes needed")
        print()
    
    # Summary
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    total_changes = sum(r['changes'] for r in all_results)
    print(f"   Total files processed: {len(all_results)}")
    print(f"   Total publish() calls fixed: {total_changes}")
    print()
    
    if total_changes > 0:
        print("✅ All MessageBus.publish() calls have been fixed!")
        print()
        print("Next steps:")
        print("1. Review the changes in each file")
        print("2. Run validation tools to verify fixes")
        print("3. Test the pipeline to ensure it works")
        print("4. Commit the changes")
    
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())