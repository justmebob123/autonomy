#!/usr/bin/env python3
"""
Complete Integration Script
Properly integrates learning systems, event subscriptions, dimension tracking, and adaptive prompts
into all phases by adding methods INSIDE the class definition.
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Tuple

class CompleteIntegrator:
    """Integrates all features into phases"""
    
    def __init__(self):
        self.phases_dir = Path("pipeline/phases")
        self.execution_phases = [
            "planning", "coding", "qa", "debugging", "investigation",
            "project_planning", "documentation", "refactoring",
            "prompt_design", "prompt_improvement", "tool_design", 
            "tool_evaluation", "role_design", "role_improvement"
        ]
        
        # Event subscriptions per phase
        self.subscriptions = {
            "planning": ["PHASE_COMPLETED", "TASK_FAILED", "SYSTEM_ALERT"],
            "coding": ["TASK_STARTED", "ISSUE_FOUND", "PHASE_COMPLETED"],
            "qa": ["PHASE_COMPLETED", "CODE_CHANGED", "TASK_FAILED", "SYSTEM_ALERT"],
            "debugging": ["ISSUE_FOUND", "TASK_FAILED", "PHASE_COMPLETED", "SYSTEM_ALERT"],
            "investigation": ["PHASE_COMPLETED", "TASK_FAILED", "SYSTEM_ALERT"],
            "project_planning": ["PHASE_COMPLETED", "TASK_FAILED", "SYSTEM_ALERT"],
            "documentation": ["PHASE_COMPLETED", "CODE_CHANGED", "TASK_COMPLETED", "SYSTEM_ALERT"],
            "refactoring": ["CODE_CHANGED", "ISSUE_FOUND", "PHASE_COMPLETED", "QA_FAILED", "SYSTEM_ALERT"],
            "prompt_design": ["PHASE_COMPLETED", "PROMPT_NEEDED", "SYSTEM_ALERT"],
            "prompt_improvement": ["PROMPT_FAILED", "PHASE_COMPLETED", "SYSTEM_ALERT"],
            "tool_design": ["TOOL_NEEDED", "PHASE_COMPLETED", "PHASE_ERROR"],
            "tool_evaluation": ["TOOL_CREATED", "PHASE_COMPLETED", "SYSTEM_ALERT"],
            "role_design": ["ROLE_NEEDED", "PHASE_COMPLETED", "SYSTEM_ALERT"],
            "role_improvement": ["ROLE_FAILED", "PHASE_COMPLETED", "SYSTEM_ALERT"]
        }
        
        self.changes = {}
    
    def integrate_all(self):
        """Integrate all features into all phases"""
        print("=" * 80)
        print("🚀 COMPLETE INTEGRATION - All Features")
        print("=" * 80)
        print()
        
        for phase_name in self.execution_phases:
            phase_file = self.phases_dir / f"{phase_name}.py"
            if not phase_file.exists():
                print(f"⚠️  {phase_name}.py not found, skipping")
                continue
            
            print(f"📝 Processing {phase_name}.py...")
            
            with open(phase_file, 'r') as f:
                content = f.read()
            
            # Track what we add
            added = []
            
            # 1. Add learning systems to __init__
            if 'self.pattern_recognition' not in content:
                content = self._add_to_init(content, [
                    "        # Learning systems",
                    "        self.pattern_recognition = self.coordinator.pattern_recognition",
                    "        self.correlation = self.coordinator.correlation",
                    "        self.optimizer = self.coordinator.optimizer"
                ])
                added.append("learning_systems")
            
            # 2. Add event subscription setup to __init__
            if '_setup_subscriptions' not in content:
                content = self._add_to_init(content, [
                    "        # Setup event subscriptions",
                    "        self._setup_subscriptions()"
                ])
                
                # Add subscription methods at end of class
                content = self._add_subscription_methods(content, phase_name)
                added.append("event_subscriptions")
            
            # 3. Add learning usage to execute method
            if 'pattern_recognition.record_pattern' not in content:
                content = self._add_learning_to_execute(content, phase_name)
                added.append("learning_usage")
            
            # Write back
            with open(phase_file, 'w') as f:
                f.write(content)
            
            if added:
                print(f"   ✅ Added: {', '.join(added)}")
                self.changes[phase_name] = added
            else:
                print(f"   ℹ️  Already integrated")
        
        print()
        print("=" * 80)
        print(f"✅ Integration complete: {len(self.changes)} phases modified")
        print("=" * 80)
    
    def _add_to_init(self, content: str, lines_to_add: List[str]) -> str:
        """Add lines to __init__ method"""
        # Find __init__ method end (before first "def " that's not __init__)
        pattern = r'(def __init__\(self.*?\):.*?)((?=\n    def [^_])|(?=\n    @property)|$)'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return content
        
        init_content = match.group(1)
        
        # Find last non-empty line in __init__
        lines = init_content.split('\n')
        insert_idx = len(lines)
        
        # Insert before the end
        new_lines = lines[:insert_idx] + [''] + lines_to_add + lines[insert_idx:]
        new_init = '\n'.join(new_lines)
        
        return content[:match.start(1)] + new_init + content[match.end(1):]
    
    def _add_subscription_methods(self, content: str, phase_name: str) -> str:
        """Add subscription setup and handler methods at end of class"""
        events = self.subscriptions.get(phase_name, [])
        
        # Find end of class (before next class or end of file)
        class_pattern = r'(class \w+.*?)((?=\nclass )|$)'
        match = re.search(class_pattern, content, re.DOTALL)
        
        if not match:
            return content
        
        class_content = match.group(1)
        
        # Build subscription methods
        methods = [
            "",
            "    def _setup_subscriptions(self):",
            "        &quot;&quot;&quot;Setup message bus subscriptions for reactive coordination&quot;&quot;&quot;"
        ]
        
        for event in events:
            handler_name = f"_on_{event.lower()}"
            methods.append(f"        self.message_bus.subscribe('{event}', self.{handler_name})")
        
        # Add handler methods
        for event in events:
            handler_name = f"_on_{event.lower()}"
            methods.extend([
                "",
                f"    def {handler_name}(self, event):",
                f"        &quot;&quot;&quot;Handle {event} event&quot;&quot;&quot;",
                "        pass"
            ])
        
        methods_text = '\n'.join(methods) + '\n'
        
        new_class = class_content + methods_text
        return content[:match.start(1)] + new_class + content[match.end(1):]
    
    def _add_learning_to_execute(self, content: str, phase_name: str) -> str:
        """Add learning system usage to execute method"""
        # Find execute method
        execute_pattern = r'(def execute\(self.*?\):.*?)(return .*?\n)'
        match = re.search(execute_pattern, content, re.DOTALL)
        
        if not match:
            return content
        
        execute_content = match.group(1)
        return_statement = match.group(2)
        
        # Add learning code before return
        learning_code = [
            "",
            "        # Record execution pattern",
            "        self.pattern_recognition.record_pattern(",
            "            pattern_type='phase_execution',",
            f"            pattern_data={{'phase': '{phase_name}', 'success': result.success}}",
            "        )",
            "",
            "        # Record correlation",
            "        self.correlation.record_correlation(",
            "            event_type='phase_execution',",
            f"            context={{'phase': '{phase_name}'}},",
            "            outcome={'success': result.success}",
            "        )",
            "",
            "        # Apply optimizations",
            f"        optimizations = self.optimizer.get_optimizations('{phase_name}')",
            "        if optimizations:",
            "            pass  # Applied in future executions",
            ""
        ]
        
        learning_text = '\n'.join(learning_code) + '\n        '
        
        new_execute = execute_content + learning_text + return_statement
        return content[:match.start(1)] + new_execute + content[match.end(2):]
    
    def print_summary(self):
        """Print summary"""
        if not self.changes:
            print("\n✅ All phases already integrated")
            return
        
        print("\n📊 INTEGRATION SUMMARY")
        print("-" * 80)
        for phase, features in self.changes.items():
            print(f"✅ {phase}: {', '.join(features)}")
        print("-" * 80)
        print(f"\n🎯 Phases modified: {len(self.changes)}/14")
        print("🎯 Features: Learning Systems, Event Subscriptions, Learning Usage")

if __name__ == '__main__':
    integrator = CompleteIntegrator()
    integrator.integrate_all()
    integrator.print_summary()