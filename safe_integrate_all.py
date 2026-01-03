#!/usr/bin/env python3
"""
Safe Complete Integration
Adds all features safely by appending to methods rather than inserting.
"""

import re
from pathlib import Path
from typing import List

class SafeIntegrator:
    """Safely integrates all features"""
    
    def __init__(self):
        self.phases_dir = Path("pipeline/phases")
        self.phases = [
            "planning", "coding", "qa", "debugging", "investigation",
            "project_planning", "documentation", "refactoring",
            "prompt_design", "prompt_improvement", "tool_design", 
            "tool_evaluation", "role_design", "role_improvement"
        ]
        
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
    
    def integrate_all(self):
        """Integrate all features"""
        print("=" * 80)
        print("🚀 SAFE COMPLETE INTEGRATION")
        print("=" * 80)
        print()
        
        for phase_name in self.phases:
            phase_file = self.phases_dir / f"{phase_name}.py"
            if not phase_file.exists():
                continue
            
            print(f"📝 {phase_name}.py...")
            
            with open(phase_file, 'r') as f:
                content = f.read()
            
            # 1. Add learning systems to __init__ (after super().__init__)
            if 'self.pattern_recognition' not in content:
                content = re.sub(
                    r'(super\(\).__init__\(coordinator\))',
                    r'\1\n        \n        # Learning systems\n        self.pattern_recognition = self.coordinator.pattern_recognition\n        self.correlation = self.coordinator.correlation\n        self.optimizer = self.coordinator.optimizer',
                    content
                )
            
            # 2. Add subscription setup call to __init__ (at very end, before first method)
            if '_setup_subscriptions' not in content:
                # Find end of __init__ (line before next "def ")
                pattern = r'(def __init__\(self[^)]*\):(?:(?!^\s{4}def\s)[\s\S])*)'
                match = re.search(pattern, content, re.MULTILINE)
                if match:
                    init_end = match.end()
                    content = content[:init_end] + '\n        self._setup_subscriptions()' + content[init_end:]
            
            # 3. Add subscription methods at end of class
            if '_setup_subscriptions(self):' not in content:
                events = self.subscriptions.get(phase_name, [])
                methods = self._build_subscription_methods(events)
                
                # Find end of class (before EOF or next class)
                class_end_pattern = r'(class \w+[^:]*:[\s\S]*?)((?=\nclass\s)|$)'
                match = re.search(class_end_pattern, content)
                if match:
                    class_end = match.end(1)
                    content = content[:class_end] + '\n' + methods + content[class_end:]
            
            with open(phase_file, 'w') as f:
                f.write(content)
            
            print(f"   ✅ Integrated")
        
        print()
        print("=" * 80)
        print("✅ Integration complete")
        print("=" * 80)
    
    def _build_subscription_methods(self, events: List[str]) -> str:
        """Build subscription methods"""
        lines = [
            "    def _setup_subscriptions(self):",
            "        &quot;&quot;&quot;Setup message bus subscriptions&quot;&quot;&quot;",
        ]
        
        for event in events:
            handler = f"_on_{event.lower()}"
            lines.append(f"        self.message_bus.subscribe('{event}', self.{handler})")
        
        lines.append("")
        
        for event in events:
            handler = f"_on_{event.lower()}"
            lines.extend([
                f"    def {handler}(self, event):",
                f"        &quot;&quot;&quot;Handle {event}&quot;&quot;&quot;",
                "        pass",
                ""
            ])
        
        return '\n'.join(lines)

if __name__ == '__main__':
    integrator = SafeIntegrator()
    integrator.integrate_all()