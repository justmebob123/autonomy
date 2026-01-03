#!/usr/bin/env python3
"""
Script to analyze and implement message bus subscriptions for all phases.

This will enable reactive coordination where phases can respond to events
from other phases in real-time.
"""

import sys
from pathlib import Path
from typing import Dict, List, Set

sys.path.insert(0, str(Path(__file__).parent))

# Define subscription strategy for each phase
PHASE_SUBSCRIPTIONS = {
    'qa': {
        'subscriptions': [
            'FILE_CREATED',      # Review newly created files
            'FILE_MODIFIED',     # Review modified files
            'TASK_COMPLETED',    # Check if QA needed
            'PHASE_COMPLETED'    # Coordinate with other phases
        ],
        'rationale': 'QA needs to review files after creation/modification'
    },
    'coding': {
        'subscriptions': [
            'TASK_STARTED',      # Know when tasks begin
            'ISSUE_FOUND',       # Address issues found by QA
            'PHASE_COMPLETED'    # Coordinate with other phases
        ],
        'rationale': 'Coding needs to respond to QA issues and task assignments'
    },
    'debugging': {
        'subscriptions': [
            'ISSUE_FOUND',       # Debug issues found by QA
            'TASK_FAILED',       # Debug failed tasks
            'PHASE_ERROR',       # Debug phase errors
            'SYSTEM_ALERT'       # Respond to system alerts
        ],
        'rationale': 'Debugging needs to respond to all types of issues'
    },
    'documentation': {
        'subscriptions': [
            'FILE_CREATED',      # Document new files
            'FILE_MODIFIED',     # Update docs for changes
            'PHASE_COMPLETED',   # Update after phase completion
            'SYSTEM_ALERT'       # Document system changes
        ],
        'rationale': 'Documentation needs to track all system changes'
    },
    'planning': {
        'subscriptions': [
            'TASK_COMPLETED',    # Plan next tasks
            'PHASE_COMPLETED',   # Coordinate planning
            'ISSUE_FOUND',       # Plan fixes for issues
            'SYSTEM_ALERT'       # Respond to system alerts
        ],
        'rationale': 'Planning needs to coordinate with all phases'
    },
    'project_planning': {
        'subscriptions': [
            'PHASE_COMPLETED',   # Track phase completions
            'TASK_COMPLETED',    # Track task completions
            'SYSTEM_ALERT'       # Respond to system alerts
        ],
        'rationale': 'Project planning needs high-level coordination'
    },
    'investigation': {
        'subscriptions': [
            'ISSUE_FOUND',       # Investigate issues
            'TASK_FAILED',       # Investigate failures
            'PHASE_ERROR',       # Investigate phase errors
            'SYSTEM_ALERT'       # Investigate alerts
        ],
        'rationale': 'Investigation needs to respond to all problem indicators'
    },
    'refactoring': {
        'subscriptions': [
            'ISSUE_FOUND',       # Refactor to fix issues
            'PHASE_COMPLETED',   # Coordinate refactoring
            'SYSTEM_ALERT'       # Respond to architecture alerts
        ],
        'rationale': 'Refactoring needs to respond to code quality issues'
    },
    'prompt_improvement': {
        'subscriptions': [
            'PHASE_COMPLETED',   # Learn from phase completions
            'TASK_FAILED',       # Improve prompts for failures
            'SYSTEM_ALERT'       # Respond to prompt issues
        ],
        'rationale': 'Prompt improvement needs to learn from execution'
    },
    'tool_evaluation': {
        'subscriptions': [
            'PHASE_COMPLETED',   # Evaluate tool usage
            'TASK_FAILED',       # Evaluate tool failures
            'SYSTEM_ALERT'       # Respond to tool issues
        ],
        'rationale': 'Tool evaluation needs to track tool effectiveness'
    },
    'tool_design': {
        'subscriptions': [
            'PHASE_ERROR',       # Design tools for errors
            'TASK_FAILED',       # Design tools for failures
            'SYSTEM_ALERT'       # Respond to tool needs
        ],
        'rationale': 'Tool design needs to respond to tool gaps'
    },
    'role_design': {
        'subscriptions': [
            'PHASE_COMPLETED',   # Learn from phase needs
            'TASK_FAILED',       # Design roles for failures
            'SYSTEM_ALERT'       # Respond to role needs
        ],
        'rationale': 'Role design needs to respond to specialist needs'
    },
    'prompt_design': {
        'subscriptions': [
            'PHASE_COMPLETED',   # Learn from phase needs
            'TASK_FAILED',       # Design prompts for failures
            'SYSTEM_ALERT'       # Respond to prompt needs
        ],
        'rationale': 'Prompt design needs to respond to prompt gaps'
    },
    'role_improvement': {
        'subscriptions': [
            'PHASE_COMPLETED',   # Learn from role usage
            'TASK_FAILED',       # Improve roles for failures
            'SYSTEM_ALERT'       # Respond to role issues
        ],
        'rationale': 'Role improvement needs to learn from execution'
    }
}


def generate_subscription_code(phase_name: str, subscriptions: List[str]) -> str:
    """Generate code for message bus subscriptions."""
    
    code = f'''
        # MESSAGE BUS: Subscribe to relevant events
        if self.message_bus:
            from ..messaging import MessageType
            self._subscribe_to_messages([
'''
    
    for sub in subscriptions:
        code += f'                MessageType.{sub},\n'
    
    code += '''            ])
            self.logger.info(f"  📡 Subscribed to {len(subscriptions)} message types")
'''
    
    return code


def main():
    """Main entry point."""
    print("=" * 80)
    print("📡 Message Bus Subscription Strategy")
    print("=" * 80)
    
    for phase_name, config in PHASE_SUBSCRIPTIONS.items():
        print(f"\n{phase_name}:")
        print(f"  Subscriptions: {len(config['subscriptions'])}")
        print(f"  Rationale: {config['rationale']}")
        print(f"  Events:")
        for sub in config['subscriptions']:
            print(f"    - {sub}")
    
    print("\n" + "=" * 80)
    print("📝 Subscription Code Generation")
    print("=" * 80)
    
    for phase_name, config in PHASE_SUBSCRIPTIONS.items():
        print(f"\n### {phase_name} ###")
        code = generate_subscription_code(phase_name, config['subscriptions'])
        print(code)


if __name__ == "__main__":
    main()