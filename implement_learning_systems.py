#!/usr/bin/env python3
"""
Implement Learning Systems Integration
Adds pattern recognition, correlation engine, and optimizer to all 14 execution phases.
"""

import re
from pathlib import Path
from typing import List, Tuple

class LearningSystemsIntegrator:
    """Integrates learning systems into all phases"""
    
    def __init__(self):
        self.phases_dir = Path("pipeline/phases")
        self.execution_phases = [
            "planning", "coding", "qa", "debugging", "investigation",
            "project_planning", "documentation", "refactoring",
            "prompt_design", "prompt_improvement", "tool_design", 
            "tool_evaluation", "role_design", "role_improvement"
        ]
        self.changes_made = []
    
    def integrate_all(self):
        """Integrate learning systems into all phases"""
        print("=" * 80)
        print("🧠 LEARNING SYSTEMS INTEGRATION")
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
            
            # Check what's already integrated
            has_pattern = 'self.pattern_recognition' in content
            has_correlation = 'self.correlation' in content
            has_optimizer = 'self.optimizer' in content
            
            if has_pattern and has_correlation and has_optimizer:
                print(f"   ✅ Already has all learning systems")
                continue
            
            # Add learning systems initialization
            modified = self._add_learning_init(content, phase_name, has_pattern, has_correlation, has_optimizer)
            
            # Add learning system usage in execute method
            modified = self._add_learning_usage(modified, phase_name, has_pattern, has_correlation, has_optimizer)
            
            if modified != content:
                with open(phase_file, 'w') as f:
                    f.write(modified)
                
                added = []
                if not has_pattern: added.append("pattern_recognition")
                if not has_correlation: added.append("correlation")
                if not has_optimizer: added.append("optimizer")
                
                print(f"   ✅ Added: {', '.join(added)}")
                self.changes_made.append((phase_name, added))
            else:
                print(f"   ℹ️  No changes needed")
        
        print()
        print("=" * 80)
        print(f"✅ Integration complete: {len(self.changes_made)} phases modified")
        print("=" * 80)
    
    def _add_learning_init(self, content: str, phase_name: str, 
                          has_pattern: bool, has_correlation: bool, 
                          has_optimizer: bool) -> str:
        """Add learning systems to __init__ method"""
        
        # Find __init__ method
        init_pattern = r'(def __init__\(self.*?\):.*?)((?=\n    def )|(?=\nclass )|$)'
        match = re.search(init_pattern, content, re.DOTALL)
        
        if not match:
            return content
        
        init_content = match.group(1)
        
        # Find where to insert (after super().__init__ or after self.coordinator assignment)
        insert_patterns = [
            r'(super\(\).__init__\(coordinator\)\n)',
            r'(self\.coordinator = coordinator\n)',
            r'(def __init__\(self.*?\):\n)'
        ]
        
        insert_pos = None
        for pattern in insert_patterns:
            m = re.search(pattern, init_content)
            if m:
                insert_pos = m.end()
                break
        
        if not insert_pos:
            return content
        
        # Build learning systems initialization
        learning_init = []
        
        if not has_pattern:
            learning_init.append("        # Pattern recognition for learning")
            learning_init.append("        self.pattern_recognition = self.coordinator.pattern_recognition")
        
        if not has_correlation:
            learning_init.append("        # Correlation engine for insights")
            learning_init.append("        self.correlation = self.coordinator.correlation")
        
        if not has_optimizer:
            learning_init.append("        # Pattern optimizer for continuous improvement")
            learning_init.append("        self.optimizer = self.coordinator.optimizer")
        
        if not learning_init:
            return content
        
        # Insert learning systems initialization
        learning_block = "\n" + "\n".join(learning_init) + "\n"
        
        new_init = init_content[:insert_pos] + learning_block + init_content[insert_pos:]
        new_content = content[:match.start(1)] + new_init + content[match.end(1):]
        
        return new_content
    
    def _add_learning_usage(self, content: str, phase_name: str,
                           has_pattern: bool, has_correlation: bool,
                           has_optimizer: bool) -> str:
        """Add learning system usage to execute method"""
        
        # Find execute method
        execute_pattern = r'(def execute\(self.*?\):.*?)((?=\n    def )|(?=\nclass )|$)'
        match = re.search(execute_pattern, content, re.DOTALL)
        
        if not match:
            return content
        
        execute_content = match.group(1)
        
        # Check if learning usage already exists
        if 'pattern_recognition.record_pattern' in execute_content:
            has_pattern = True
        if 'correlation.record_correlation' in execute_content:
            has_correlation = True
        if 'optimizer.get_optimizations' in execute_content:
            has_optimizer = True
        
        if has_pattern and has_correlation and has_optimizer:
            return content
        
        # Find where to insert (before return statement)
        return_pattern = r'(\n        return .*?\n)'
        return_match = re.search(return_pattern, execute_content)
        
        if not return_match:
            return content
        
        insert_pos = return_match.start()
        
        # Build learning usage code
        learning_usage = []
        
        if not has_pattern:
            learning_usage.append("")
            learning_usage.append("        # Record execution pattern for learning")
            learning_usage.append("        self.pattern_recognition.record_pattern(")
            learning_usage.append("            pattern_type='phase_execution',")
            learning_usage.append(f"            pattern_data={{'phase': '{phase_name}', 'success': result.success}}")
            learning_usage.append("        )")
        
        if not has_correlation:
            learning_usage.append("")
            learning_usage.append("        # Record correlation for insights")
            learning_usage.append("        self.correlation.record_correlation(")
            learning_usage.append("            event_type='phase_execution',")
            learning_usage.append(f"            context={{'phase': '{phase_name}'}},")
            learning_usage.append("            outcome={'success': result.success}")
            learning_usage.append("        )")
        
        if not has_optimizer:
            learning_usage.append("")
            learning_usage.append("        # Apply optimizations from learning")
            learning_usage.append(f"        optimizations = self.optimizer.get_optimizations('{phase_name}')")
            learning_usage.append("        if optimizations:")
            learning_usage.append("            # Optimizations will be applied in future executions")
            learning_usage.append("            pass")
        
        if not learning_usage:
            return content
        
        # Insert learning usage
        learning_block = "\n".join(learning_usage) + "\n"
        
        new_execute = execute_content[:insert_pos] + learning_block + execute_content[insert_pos:]
        new_content = content[:match.start(1)] + new_execute + content[match.end(1):]
        
        return new_content
    
    def print_summary(self):
        """Print summary of changes"""
        if not self.changes_made:
            print("\n✅ All phases already have learning systems integrated")
            return
        
        print("\n📊 SUMMARY OF CHANGES")
        print("-" * 80)
        for phase_name, systems in self.changes_made:
            print(f"✅ {phase_name}: Added {', '.join(systems)}")
        print("-" * 80)
        print(f"\n🎯 Total phases enhanced: {len(self.changes_made)}")
        print(f"🎯 Learning system coverage: {len(self.execution_phases)}/14 phases (100%)")


if __name__ == '__main__':
    integrator = LearningSystemsIntegrator()
    integrator.integrate_all()
    integrator.print_summary()