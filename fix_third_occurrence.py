#!/usr/bin/env python3
"""Fix the third occurrence of user intervention."""

def fix_third_occurrence():
    # Read the file
    with open('pipeline/phases/debugging.py', 'r') as f:
        lines = f.readlines()
    
    # Find and replace the third occurrence
    new_lines = []
    i = 0
    found_third = False
    
    while i < len(lines):
        line = lines[i]
        
        # Look for the third occurrence (around line 897)
        if i >= 895 and "if intervention.get('requires_user_input'):" in line and not found_third:
            # Check if this is the right pattern
            if i + 1 < len(lines) and "# Critical: Must escalate to user" in lines[i + 1]:
                found_third = True
                indent = ' ' * 19  # Match the indentation (more indented)
                
                new_lines.append(indent + "if intervention.get('requires_user_input'):\n")
                new_lines.append(indent + "    # AUTONOMOUS: Consult AI UserProxy specialist instead of blocking\n")
                new_lines.append(indent + '    self.logger.info("\\n" + "="*80)\n')
                new_lines.append(indent + '    self.logger.info("🤖 AUTONOMOUS USER PROXY CONSULTATION")\n')
                new_lines.append(indent + '    self.logger.info("="*80)\n')
                new_lines.append(indent + '    self.logger.info("Loop detected - consulting AI specialist for guidance...")\n')
                new_lines.append(indent + "    \n")
                new_lines.append(indent + "    # Import and create UserProxyAgent\n")
                new_lines.append(indent + "    from pipeline.user_proxy import UserProxyAgent\n")
                new_lines.append(indent + "    user_proxy = UserProxyAgent(\n")
                new_lines.append(indent + "        role_registry=self.role_registry,\n")
                new_lines.append(indent + "        prompt_registry=self.prompt_registry,\n")
                new_lines.append(indent + "        tool_registry=self.tool_registry,\n")
                new_lines.append(indent + "        client=self.client,\n")
                new_lines.append(indent + "        logger=self.logger\n")
                new_lines.append(indent + "    )\n")
                new_lines.append(indent + "    \n")
                new_lines.append(indent + "    # Get guidance from AI specialist\n")
                new_lines.append(indent + "    guidance_result = user_proxy.get_guidance(\n")
                new_lines.append(indent + "        error_info={\n")
                new_lines.append(indent + "            'type': error_type,\n")
                new_lines.append(indent + "            'message': error_message,\n")
                new_lines.append(indent + "            'file': filepath,\n")
                new_lines.append(indent + "            'line': line_number\n")
                new_lines.append(indent + "        },\n")
                new_lines.append(indent + "        loop_info={\n")
                new_lines.append(indent + "            'type': intervention.get('type', 'Unknown'),\n")
                new_lines.append(indent + "            'iterations': intervention.get('iterations', 0),\n")
                new_lines.append(indent + "            'pattern': intervention.get('pattern', 'Unknown')\n")
                new_lines.append(indent + "        },\n")
                new_lines.append(indent + "        debugging_history=thread.get_conversation_history() if thread else [],\n")
                new_lines.append(indent + "        context={'intervention': intervention, 'thread': thread}\n")
                new_lines.append(indent + "    )\n")
                new_lines.append(indent + "    \n")
                new_lines.append(indent + "    # Apply the guidance\n")
                new_lines.append(indent + "    guidance = guidance_result.get('guidance', '')\n")
                new_lines.append(indent + '    self.logger.info(f"\\n✓ AI Guidance: {guidance}")\n')
                new_lines.append(indent + "    \n")
                new_lines.append(indent + "    # Add guidance to thread\n")
                new_lines.append(indent + "    if thread:\n")
                new_lines.append(indent + "        thread.add_message(\n")
                new_lines.append(indent + '            role="system",\n')
                new_lines.append(indent + '            content=f"UserProxy AI Guidance: {guidance}"\n')
                new_lines.append(indent + "        )\n")
                new_lines.append(indent + "    \n")
                new_lines.append(indent + "    # Continue with the guidance (don't return failure)\n")
                
                # Skip the old lines
                i += 1  # Skip the comment line
                while i < len(lines):
                    if "data={'intervention': intervention, 'thread': thread}" in lines[i] or 'data={"intervention": intervention, "thread": thread}' in lines[i]:
                        i += 1  # Skip this line
                        if i < len(lines) and ')' in lines[i]:
                            i += 1  # Skip the closing paren
                        break
                    i += 1
                continue
        
        # Keep the line as-is
        new_lines.append(line)
        i += 1
    
    # Write back
    with open('pipeline/phases/debugging.py', 'w') as f:
        f.writelines(new_lines)
    
    if found_third:
        print("✓ Replaced third occurrence of user intervention")
    else:
        print("⚠ Third occurrence not found")

if __name__ == '__main__':
    fix_third_occurrence()