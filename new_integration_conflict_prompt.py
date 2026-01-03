def _get_integration_conflict_prompt(self, task: Any, context: str) -> str:
    """
    ULTRA-SIMPLIFIED prompt for integration conflicts.
    
    STRATEGY: Just escalate immediately to DEVELOPER PHASE.
    Integration conflicts are too complex for refactoring AI.
    """
    
    # Get target files from task
    target_files = task.target_files if task.target_files else []
    file1 = target_files[0] if len(target_files) > 0 else "file1"
    file2 = target_files[1] if len(target_files) > 1 else "file2"
    
    # SIMPLIFIED: Just tell AI to escalate immediately
    return f"""🚨 INTEGRATION CONFLICT - ESCALATE TO DEVELOPER PHASE 🚨

{context}

═══════════════════════════════════════════════════════════════
⚠️ CRITICAL: INTEGRATION CONFLICTS ARE TOO COMPLEX ⚠️

Integration conflicts between files require careful analysis and
decision-making that is best handled by the DEVELOPER PHASE.

Files in conflict:
• {file1}
• {file2}

═══════════════════════════════════════════════════════════════
🎯 YOUR ACTION: ESCALATE TO DEVELOPER PHASE 🎯

Use the request_developer_review tool to escalate this task:

{{{{
    "name": "request_developer_review",
    "arguments": {{{{
        "task_id": "{task.task_id}",
        "reason": "Integration conflict between {file1} and {file2}. These files have conflicting implementations that need careful review and resolution by the DEVELOPER PHASE orchestrator.",
        "priority": "high",
        "context": {{{{
            "files": ["{file1}", "{file2}"],
            "issue_type": "integration_conflict",
            "description": "{task.description if hasattr(task, 'description') else 'Integration conflict detected'}"
        }}}}
    }}}}
}}}}

═══════════════════════════════════════════════════════════════

⚠️ DO NOT:
- Try to read the files
- Try to compare the files
- Try to merge the files yourself
- Do any analysis

✅ DO:
- Use request_developer_review tool IMMEDIATELY
- Let the DEVELOPER PHASE handle this complex task

═══════════════════════════════════════════════════════════════

🎯 OUTPUT THE request_developer_review TOOL CALL NOW:
"""