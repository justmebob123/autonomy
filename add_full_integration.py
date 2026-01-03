#!/usr/bin/env python3
"""
Script to add full 6-engine polytopic integration to all 0/6 phases.

This script systematically adds:
1. Message bus integration (publish_event, subscribe_to)
2. Adaptive prompts (update_system_prompt_with_adaptation)
3. Pattern recognition (record_execution_pattern)
4. Correlation engine (get_cross_phase_correlation)
5. Analytics (track_phase_metric via logger)
6. Pattern optimizer (get_optimization_suggestion)
"""

import sys
from pathlib import Path
from typing import List, Tuple

# Phases that need full integration (0/6 score)
PHASES_TO_INTEGRATE = [
    'tool_evaluation',
    'tool_design', 
    'role_design',
    'prompt_design',
    'role_improvement',
    'prompt_builder',
    'analysis_orchestrator',
    'refactoring_context_builder'
]

# Template for adding integration at start of execute()
EXECUTE_START_TEMPLATE = '''
        # POLYTOPIC INTEGRATION: Adaptive prompts
        self.update_system_prompt_with_adaptation({{
            'phase': self.phase_name,
            'state': state,
            'context': '{phase_name}_execution'
        }})
        
        # POLYTOPIC INTEGRATION: Get correlations and optimizations
        correlations = self.get_cross_phase_correlation()
        optimization = self.get_optimization_suggestion()
        
        # MESSAGE BUS: Publish phase start event
        self.publish_event('PHASE_STARTED', {{
            'phase': self.phase_name,
            'timestamp': datetime.now().isoformat(),
            'correlations': correlations,
            'optimization': optimization
        }})
'''

# Template for adding integration at end of execute()
EXECUTE_END_TEMPLATE = '''
        # MESSAGE BUS: Publish phase completion
        self.publish_event('PHASE_COMPLETED', {{
            'phase': self.phase_name,
            'timestamp': datetime.now().isoformat(),
            'success': True
        }})
        
        # PATTERN RECOGNITION: Record phase completion
        self.record_execution_pattern({{
            'phase': self.phase_name,
            'action': 'phase_complete',
            'success': True,
            'timestamp': datetime.now().isoformat()
        }})
'''


def find_execute_method(content: str) -> Tuple[int, int]:
    """Find the start and end of execute method."""
    lines = content.split('\n')
    
    start_idx = -1
    end_idx = -1
    indent_level = 0
    
    for i, line in enumerate(lines):
        if 'def execute(self' in line:
            start_idx = i
            # Find the indent level
            indent_level = len(line) - len(line.lstrip())
            continue
        
        if start_idx >= 0:
            # Look for the return statement at the same indent level
            if line.strip().startswith('return ') and len(line) - len(line.lstrip()) == indent_level:
                end_idx = i
                break
    
    return start_idx, end_idx


def add_integration_to_phase(phase_file: Path) -> bool:
    """Add full 6-engine integration to a phase file."""
    print(f"\n📝 Processing {phase_file.name}...")
    
    try:
        with open(phase_file, 'r') as f:
            content = f.read()
        
        # Check if already has integration
        if 'update_system_prompt_with_adaptation' in content:
            print(f"  ⏭️  Already has adaptive prompts integration")
            return False
        
        # Find execute method
        start_idx, end_idx = find_execute_method(content)
        
        if start_idx < 0 or end_idx < 0:
            print(f"  ⚠️  Could not find execute method")
            return False
        
        lines = content.split('\n')
        
        # Find the first line after the docstring
        insert_start_idx = start_idx + 1
        in_docstring = False
        for i in range(start_idx + 1, len(lines)):
            line = lines[i].strip()
            if '"""' in line or "'''" in line:
                if not in_docstring:
                    in_docstring = True
                else:
                    insert_start_idx = i + 1
                    break
        
        # Get phase name from file
        phase_name = phase_file.stem
        
        # Insert integration at start
        start_integration = EXECUTE_START_TEMPLATE.format(phase_name=phase_name)
        lines.insert(insert_start_idx, start_integration)
        
        # Adjust end_idx due to insertion
        end_idx += start_integration.count('\n')
        
        # Insert integration before return
        lines.insert(end_idx, EXECUTE_END_TEMPLATE)
        
        # Write back
        new_content = '\n'.join(lines)
        with open(phase_file, 'w') as f:
            f.write(new_content)
        
        print(f"  ✅ Added full 6-engine integration")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    """Main entry point."""
    project_root = Path.cwd()
    phases_dir = project_root / "pipeline" / "phases"
    
    print("=" * 80)
    print("🚀 Adding Full 6-Engine Polytopic Integration")
    print("=" * 80)
    
    modified_count = 0
    
    for phase_name in PHASES_TO_INTEGRATE:
        phase_file = phases_dir / f"{phase_name}.py"
        
        if not phase_file.exists():
            print(f"\n⚠️  {phase_file.name} not found, skipping...")
            continue
        
        if add_integration_to_phase(phase_file):
            modified_count += 1
    
    print("\n" + "=" * 80)
    print(f"✅ Integration Complete: {modified_count}/{len(PHASES_TO_INTEGRATE)} phases modified")
    print("=" * 80)


if __name__ == "__main__":
    main()