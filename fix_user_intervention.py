#!/usr/bin/env python3
"""
Fix user intervention to use AI UserProxy instead of blocking for human input.
"""

import re

def fix_debugging_phase():
    """Replace user intervention with AI UserProxy consultation."""
    
    # Read the file
    with open('pipeline/phases/debugging.py', 'r') as f:
        lines = f.readlines()
    
    # Find and replace the pattern
    new_lines = []
    i = 0
    replacements = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is the start of the pattern
        if "if intervention and intervention.get('requires_user_input'):" in line:
            # Check next few lines to confirm this is the right pattern
            if i + 1 < len(lines) and "# Critical: Must escalate to user" in lines[i + 1]:
                # Found it! Replace this block
                indent = ' ' * 11  # Match the indentation
                
                new_lines.append(f"{indent}if intervention and intervention.get('requires_user_input'):\n")
                new_lines.append(f"{indent}    # AUTONOMOUS: Consult AI UserProxy specialist instead of blocking\n")
                new_lines.append(f"{indent}    self.logger.info(&quot;\\n&quot; + &quot;=&quot;*80)\n")
                new_lines.append(f"{indent}    self.logger.info(&quot;🤖 AUTONOMOUS USER PROXY CONSULTATION&quot;)\n")
                new_lines.append(f"{indent}    self.logger.info(&quot;=&quot;*80)\n")
                new_lines.append(f"{indent}    self.logger.info(&quot;Loop detected - consulting AI specialist for guidance...&quot;)\n")
                new_lines.append(f"{indent}    \n")
                new_lines.append(f"{indent}    # Import and create UserProxyAgent\n")
                new_lines.append(f"{indent}    from pipeline.user_proxy import UserProxyAgent\n")
                new_lines.append(f"{indent}    user_proxy = UserProxyAgent(\n")
                new_lines.append(f"{indent}        role_registry=self.role_registry,\n")
                new_lines.append(f"{indent}        prompt_registry=self.prompt_registry,\n")
                new_lines.append(f"{indent}        tool_registry=self.tool_registry,\n")
                new_lines.append(f"{indent}        client=self.client,\n")
                new_lines.append(f"{indent}        logger=self.logger\n")
                new_lines.append(f"{indent}    )\n")
                new_lines.append(f"{indent}    \n")
                new_lines.append(f"{indent}    # Get guidance from AI specialist\n")
                new_lines.append(f"{indent}    guidance_result = user_proxy.get_guidance(\n")
                new_lines.append(f"{indent}        error_info={{\n")
                new_lines.append(f"{indent}            'type': error_type,\n")
                new_lines.append(f"{indent}            'message': error_message,\n")
                new_lines.append(f"{indent}            'file': filepath,\n")
                new_lines.append(f"{indent}            'line': line_number\n")
                new_lines.append(f"{indent}        }},\n")
                new_lines.append(f"{indent}        loop_info={{\n")
                new_lines.append(f"{indent}            'type': intervention.get('type', 'Unknown'),\n")
                new_lines.append(f"{indent}            'iterations': intervention.get('iterations', 0),\n")
                new_lines.append(f"{indent}            'pattern': intervention.get('pattern', 'Unknown')\n")
                new_lines.append(f"{indent}        }},\n")
                new_lines.append(f"{indent}        debugging_history=self.action_tracker.get_recent_actions(10) if hasattr(self, 'action_tracker') else [],\n")
                new_lines.append(f"{indent}        context={{'intervention': intervention}}\n")
                new_lines.append(f"{indent}    )\n")
                new_lines.append(f"{indent}    \n")
                new_lines.append(f"{indent}    # Apply the guidance\n")
                new_lines.append(f"{indent}    guidance = guidance_result.get('guidance', '')\n")
                new_lines.append(f"{indent}    self.logger.info(f&quot;\\n✓ AI Guidance: {{guidance}}&quot;)\n")
                new_lines.append(f"{indent}    \n")
                new_lines.append(f"{indent}    # Continue with the guidance (don't return failure)\n")
                new_lines.append(f"{indent}    # The guidance will be incorporated into the next iteration\n")
                
                # Skip the old lines (find the closing parenthesis of PhaseResult)
                i += 1  # Skip the comment line
                while i < len(lines):
                    if 'data={\'intervention\': intervention}' in lines[i] or 'data={"intervention": intervention}' in lines[i]:
                        i += 1  # Skip this line
                        if i < len(lines) and ')' in lines[i]:
                            i += 1  # Skip the closing paren
                        break
                    i += 1
                
                replacements += 1
                continue
        
        # Keep the line as-is
        new_lines.append(line)
        i += 1
    
    # Write back
    with open('pipeline/phases/debugging.py', 'w') as f:
        f.writelines(new_lines)
    
    print(f"✓ Replaced {replacements} occurrences of user intervention with AI UserProxy")
    return replacements

if __name__ == '__main__':
    count = fix_debugging_phase()
    if count > 0:
        print(f"✓ Successfully updated debugging.py")
    else:
        print("⚠ No replacements made - pattern not found")