def _get_integration_conflict_prompt(self, task: Any, context: str) -> str:
    """Prompt for integration conflicts - STEP-AWARE to prevent multiple tool outputs"""
    
    # Get target files from task
    target_files = task.target_files if task.target_files else []
    file1 = target_files[0] if len(target_files) > 0 else "file1"
    file2 = target_files[1] if len(target_files) > 1 else "file2"
    
    # Determine current step based on conversation history
    # Check what tools have been called in previous attempts
    conversation_history = self.conversation.get_context() if hasattr(self, 'conversation') else []
    
    # Count what's been done by looking at assistant messages
    files_read = set()
    architecture_read = False
    comparison_done = False
    
    for msg in conversation_history:
        if msg.get('role') == 'assistant':
            content = str(msg.get('content', ''))
            # Check for file reads
            if 'read_file' in content and file1 in content:
                files_read.add(file1)
            if 'read_file' in content and file2 in content:
                files_read.add(file2)
            if 'read_file' in content and 'ARCHITECTURE.md' in content:
                architecture_read = True
            if 'compare_file_implementations' in content:
                comparison_done = True
    
    # Determine next step
    if file1 not in files_read:
        # Step 1: Read first file
        step_num = 1
        next_tool = f'read_file(filepath="{file1}")'
        step_description = f"READ THE FIRST FILE: {file1}"
        
    elif file2 not in files_read:
        # Step 2: Read second file
        step_num = 2
        next_tool = f'read_file(filepath="{file2}")'
        step_description = f"READ THE SECOND FILE: {file2}"
        
    elif not architecture_read:
        # Step 3: Read architecture
        step_num = 3
        next_tool = 'read_file(filepath="ARCHITECTURE.md")'
        step_description = "READ ARCHITECTURE.md to see where files should be"
        
    elif not comparison_done:
        # Step 4: Compare
        step_num = 4
        next_tool = f'compare_file_implementations(file1="{file1}", file2="{file2}")'
        step_description = "COMPARE the two implementations"
        
    else:
        # Step 5: Make decision and resolve
        step_num = 5
        next_tool = "merge_file_implementations(...) OR move_file(...) OR rename_file(...)"
        step_description = "MAKE A DECISION and RESOLVE the conflict"
    
    return f"""🎯 INTEGRATION CONFLICT - STEP {step_num} OF 5

{context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  CRITICAL SYSTEM CONSTRAINT ⚠️

THE SYSTEM CAN ONLY EXECUTE **ONE** TOOL CALL PER ITERATION.

If you output multiple tool calls, ONLY THE FIRST ONE will execute.
The rest will be IGNORED and you'll be stuck in an infinite loop.

YOU MUST OUTPUT EXACTLY ONE TOOL CALL. THEN STOP.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 YOU ARE ON STEP {step_num} OF 5

🎯 YOUR NEXT ACTION:
{step_description}

💻 CALL THIS ONE TOOL:
{next_tool}

⛔ DO NOT:
- Output multiple tool calls
- Call any other tools
- Plan ahead for future steps
- Output JSON arrays

✅ DO:
- Output EXACTLY ONE tool call
- Use the exact tool shown above
- Then STOP and wait

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 PROGRESS TRACKER:
Step 1: Read {file1} {'✅' if file1 in files_read else '⏳ ← YOU ARE HERE' if step_num == 1 else '⬜'}
Step 2: Read {file2} {'✅' if file2 in files_read else '⏳ ← YOU ARE HERE' if step_num == 2 else '⬜'}
Step 3: Read ARCHITECTURE.md {'✅' if architecture_read else '⏳ ← YOU ARE HERE' if step_num == 3 else '⬜'}
Step 4: Compare implementations {'✅' if comparison_done else '⏳ ← YOU ARE HERE' if step_num == 4 else '⬜'}
Step 5: Resolve conflict {'⏳ ← YOU ARE HERE' if step_num == 5 else '⬜'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 OUTPUT YOUR ONE TOOL CALL NOW:
"""