#!/usr/bin/env python3
"""
Debug script to analyze objective state and task relationships.
This will trace the EXACT state of objectives and tasks.
"""

import json
from pathlib import Path

# Load state
state_file = Path("/home/ai/AI/web/.autonomy/state.json")
if not state_file.exists():
    print("ERROR: state.json not found")
    exit(1)

with open(state_file) as f:
    state = json.load(f)

print("="*80)
print("STATE ANALYSIS")
print("="*80)
print()

# Analyze tasks
print("TASKS:")
print(f"  Total tasks: {len(state.get('tasks', {}))}")
print()

# Count by status
status_counts = {}
for task_id, task in state.get('tasks', {}).items():
    status = task.get('status', 'UNKNOWN')
    status_counts[status] = status_counts.get(status, 0) + 1

print("  Tasks by status:")
for status, count in sorted(status_counts.items()):
    print(f"    {status}: {count}")
print()

# Analyze objectives
print("OBJECTIVES:")
for level in ['primary', 'secondary', 'tertiary']:
    level_objs = state.get('objectives', {}).get(level, {})
    print(f"  {level.upper()}: {len(level_objs)} objectives")
    
    for obj_id, obj_data in level_objs.items():
        title = obj_data.get('title', 'Unknown')
        task_list = obj_data.get('tasks', [])
        total_tasks = obj_data.get('total_tasks', 0)
        completed_tasks = obj_data.get('completed_tasks', [])
        completion = obj_data.get('completion_percentage', 0)
        
        print(f"    - {obj_id}: {title}")
        print(f"      Tasks in list: {len(task_list)}")
        print(f"      Total tasks: {total_tasks}")
        print(f"      Completed: {len(completed_tasks)}")
        print(f"      Completion: {completion}%")
        
        # Check if task IDs in objective actually exist in state.tasks
        if task_list:
            existing = sum(1 for tid in task_list if tid in state.get('tasks', {}))
            print(f"      Tasks that exist in state: {existing}/{len(task_list)}")
            
            # Show first 5 task IDs
            print(f"      First 5 task IDs: {task_list[:5]}")
        print()

print("="*80)
print("ANALYSIS COMPLETE")
print("="*80)