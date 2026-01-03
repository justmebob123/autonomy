#!/usr/bin/env python3
"""
Add full 6-engine integration to all phases
"""

import re
from pathlib import Path

PHASES_TO_UPDATE = [
    'coding.py',
    'debugging.py', 
    'planning.py',
    'documentation.py',
    'investigation.py',
    'project_planning.py'
]

def add_correlation_and_optimization(filepath: Path):
    """Add correlation and optimization calls after adaptive_prompts"""
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern to find adaptive_prompts block
    pattern = r'(# ADAPTIVE PROMPTS:.*?self\.update_system_prompt_with_adaptation\({[^}]+}\)\s*)'
    
    replacement = r'''\1
        # CORRELATION ENGINE: Get cross-phase correlations
        correlations = self.get_cross_phase_correlation({
            'phase': self.phase_name
        })
        if correlations:
            self.logger.debug(f"  🔗 Found {len(correlations)} cross-phase correlations")
        
        # PATTERN OPTIMIZER: Get optimization suggestions
        optimization = self.get_optimization_suggestion({
            'current_strategy': 'phase_execution'
        })
        if optimization and optimization.get('suggestions'):
            self.logger.debug(f"  💡 Optimization suggestions available")
        '''
    
    # Check if already added
    if 'CORRELATION ENGINE' in content:
        print(f"  ⏭️  {filepath.name}: Already has correlation/optimization")
        return False
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"  ✅ {filepath.name}: Added correlation and optimization")
        return True
    else:
        print(f"  ⚠️  {filepath.name}: Pattern not found")
        return False

def add_pattern_and_analytics_to_events(filepath: Path):
    """Add pattern recording and analytics after message_bus.publish calls"""
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern to find message_bus.publish blocks
    pattern = r'(self\.message_bus\.publish\([^)]+\))\s*\n'
    
    replacement = r'''\1
                    
                    # PATTERN RECOGNITION: Record execution pattern
                    self.record_execution_pattern({
                        'pattern_type': 'event_published',
                        'event': 'phase_event'
                    })
                    
                    # ANALYTICS: Track event metric
                    self.track_phase_metric({
                        'metric': 'event_published'
                    })
'''
    
    # Check if already added
    if 'PATTERN RECOGNITION: Record execution pattern' in content:
        print(f"  ⏭️  {filepath.name}: Already has pattern/analytics")
        return False
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"  ✅ {filepath.name}: Added pattern recording and analytics")
        return True
    else:
        print(f"  ⚠️  {filepath.name}: No message_bus.publish found")
        return False

def main():
    phases_dir = Path('pipeline/phases')
    
    print("🔧 Adding full 6-engine integration to phases...")
    print()
    
    updated_count = 0
    
    for phase_file in PHASES_TO_UPDATE:
        filepath = phases_dir / phase_file
        if not filepath.exists():
            print(f"  ❌ {phase_file}: File not found")
            continue
        
        print(f"📝 Processing {phase_file}...")
        
        # Add correlation and optimization
        if add_correlation_and_optimization(filepath):
            updated_count += 1
        
        # Add pattern and analytics (optional, only if message_bus.publish exists)
        add_pattern_and_analytics_to_events(filepath)
        
        print()
    
    print(f"✅ Updated {updated_count} phase files")

if __name__ == '__main__':
    main()