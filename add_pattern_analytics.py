#!/usr/bin/env python3
"""Add pattern_recognition and analytics calls to phases"""

from pathlib import Path

def add_to_planning():
    """Add to planning.py"""
    filepath = Path('pipeline/phases/planning.py')
    content = filepath.read_text()
    
    # Find send_message_to_phase calls and add after them
    target = 'self.send_message_to_phase(\'coding\', message)'
    if target in content and 'PATTERN RECOGNITION: Record' not in content:
        replacement = target + '''
                    
                    # PATTERN RECOGNITION: Record planning pattern
                    self.record_execution_pattern({
                        'pattern_type': 'planning_complete',
                        'success': True
                    })
                    
                    # ANALYTICS: Track planning metric
                    self.track_phase_metric({
                        'metric': 'planning_completed'
                    })'''
        content = content.replace(target, replacement, 1)
        filepath.write_text(content)
        print("✅ Updated planning.py")
        return True
    return False

def add_to_documentation():
    """Add to documentation.py"""
    filepath = Path('pipeline/phases/documentation.py')
    content = filepath.read_text()
    
    # Find send_message_to_phase calls
    target = 'self.send_message_to_phase(\'planning\', f"Documentation updated: {len(updates_made)} changes made")'
    if target in content and 'PATTERN RECOGNITION: Record' not in content:
        replacement = target + '''
            
            # PATTERN RECOGNITION: Record documentation update pattern
            self.record_execution_pattern({
                'pattern_type': 'documentation_update',
                'updates_count': len(updates_made),
                'success': True
            })
            
            # ANALYTICS: Track documentation metric
            self.track_phase_metric({
                'metric': 'documentation_updated',
                'updates_count': len(updates_made)
            })'''
        content = content.replace(target, replacement, 1)
        filepath.write_text(content)
        print("✅ Updated documentation.py")
        return True
    return False

def add_to_investigation():
    """Add to investigation.py"""
    filepath = Path('pipeline/phases/investigation.py')
    content = filepath.read_text()
    
    # Find send_message_to_phase calls
    target = 'self.send_message_to_phase(\'debugging\', f"Investigation complete for {filepath}: {findings.get(\'recommended_fix\')}")'
    if target in content and 'PATTERN RECOGNITION: Record' not in content:
        replacement = target + '''
            
            # PATTERN RECOGNITION: Record investigation pattern
            self.record_execution_pattern({
                'pattern_type': 'investigation_complete',
                'success': True
            })
            
            # ANALYTICS: Track investigation metric
            self.track_phase_metric({
                'metric': 'investigation_completed'
            })'''
        content = content.replace(target, replacement, 1)
        filepath.write_text(content)
        print("✅ Updated investigation.py")
        return True
    return False

def add_to_project_planning():
    """Add to project_planning.py"""
    filepath = Path('pipeline/phases/project_planning.py')
    content = filepath.read_text()
    
    # Find send_message_to_phase calls
    target = 'self.send_message_to_phase(\'planning\', f"Created {len(tasks_created)} new expansion tasks for cycle {state.expansion_count}")'
    if target in content and 'PATTERN RECOGNITION: Record' not in content:
        replacement = target + '''
            
            # PATTERN RECOGNITION: Record expansion pattern
            self.record_execution_pattern({
                'pattern_type': 'expansion_planning',
                'tasks_created': len(tasks_created),
                'success': True
            })
            
            # ANALYTICS: Track expansion metric
            self.track_phase_metric({
                'metric': 'expansion_planned',
                'tasks_created': len(tasks_created)
            })'''
        content = content.replace(target, replacement, 1)
        filepath.write_text(content)
        print("✅ Updated project_planning.py")
        return True
    return False

def main():
    print("🔧 Adding pattern_recognition and analytics calls...")
    print()
    
    updated = 0
    if add_to_planning(): updated += 1
    if add_to_documentation(): updated += 1
    if add_to_investigation(): updated += 1
    if add_to_project_planning(): updated += 1
    
    print()
    print(f"✅ Updated {updated} files")

if __name__ == '__main__':
    main()