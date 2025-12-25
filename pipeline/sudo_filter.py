"""
Sudo Command Filter

Filters out sudo commands from tool calls and provides clear feedback.
"""

import re
from typing import Dict, List, Tuple


class SudoFilter:
    """
    Filters sudo commands from tool calls.
    
    Provides clear feedback about why sudo is blocked and suggests alternatives.
    """
    
    def __init__(self):
        self.sudo_patterns = [
            r'^\s*sudo\s+',  # Command starts with sudo
            r'\|\s*sudo\s+',  # Piped to sudo
            r'&&\s*sudo\s+',  # Chained with sudo
            r';\s*sudo\s+',   # Sequential with sudo
        ]
        
        self.blocked_commands = []
    
    def filter_tool_call(self, tool_call: Dict) -> Tuple[bool, Dict]:
        """
        Filter a single tool call for sudo usage.
        
        Returns:
            (is_allowed, modified_tool_call)
            - is_allowed: True if command is safe, False if blocked
            - modified_tool_call: Original or modified tool call with error message
        """
        
        tool_name = tool_call.get('function', {}).get('name', '')
        
        # Only filter execute_command tool
        if tool_name != 'execute_command':
            return True, tool_call
        
        args = tool_call.get('function', {}).get('arguments', {})
        command = args.get('command', '')
        
        # Check for sudo usage
        if self._contains_sudo(command):
            # Block the command
            self.blocked_commands.append({
                'command': command,
                'tool_call': tool_call
            })
            
            # Create error response
            error_tool_call = tool_call.copy()
            error_tool_call['blocked'] = True
            error_tool_call['error'] = self._generate_sudo_error_message(command)
            
            return False, error_tool_call
        
        return True, tool_call
    
    def filter_tool_calls(self, tool_calls: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter a list of tool calls.
        
        Returns:
            (allowed_calls, blocked_calls)
        """
        
        allowed = []
        blocked = []
        
        for tool_call in tool_calls:
            is_allowed, modified_call = self.filter_tool_call(tool_call)
            
            if is_allowed:
                allowed.append(modified_call)
            else:
                blocked.append(modified_call)
        
        return allowed, blocked
    
    def _contains_sudo(self, command: str) -> bool:
        """Check if command contains sudo"""
        
        for pattern in self.sudo_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        
        return False
    
    def _generate_sudo_error_message(self, command: str) -> str:
        """Generate helpful error message for blocked sudo command"""
        
        # Extract what they were trying to do
        sudo_removed = re.sub(r'^\s*sudo\s+', '', command)
        sudo_removed = re.sub(r'\|\s*sudo\s+', '| ', sudo_removed)
        sudo_removed = re.sub(r'&&\s*sudo\s+', '&& ', sudo_removed)
        sudo_removed = re.sub(r';\s*sudo\s+', '; ', sudo_removed)
        
        message = f"""❌ SUDO COMMAND BLOCKED

**Attempted Command:**
```bash
{command}
```

**Reason:** Sudo commands are not allowed in this environment for security reasons.

**What You Were Trying To Do:**
It looks like you wanted to run: `{sudo_removed}`

**Alternatives:**

1. **If installing packages:**
   - Most common packages are already installed
   - Check if the package is available: `which <command>` or `<command> --version`
   - If truly needed, request user to install it manually

2. **If modifying system files:**
   - Work in the project directory instead: `/workspace`
   - All project files are writable without sudo
   - System files should not need modification for debugging

3. **If changing permissions:**
   - Files in `/workspace` are already writable
   - Use `chmod` without sudo for project files
   - Example: `chmod +x script.sh`

4. **If running services:**
   - Use user-space alternatives
   - Run services on high ports (>1024) which don't need sudo
   - Example: `python -m http.server 8080` instead of port 80

**What To Do:**
1. Try the command without sudo first
2. If it fails, analyze the actual error
3. Find a non-sudo alternative
4. If absolutely necessary, explain to the user what needs to be done manually

**Remember:** You have full access to the project directory and can do most debugging tasks without elevated privileges.
"""
        
        return message
    
    def get_blocked_summary(self) -> str:
        """Get summary of blocked commands"""
        
        if not self.blocked_commands:
            return "No sudo commands were blocked."
        
        summary = f"## Blocked Sudo Commands ({len(self.blocked_commands)})\n\n"
        
        for i, blocked in enumerate(self.blocked_commands, 1):
            summary += f"{i}. `{blocked['command']}`\n"
        
        summary += "\n**Note:** All these commands were blocked for security. "
        summary += "See individual error messages for alternatives.\n"
        
        return summary
    
    def clear_history(self):
        """Clear blocked command history"""
        self.blocked_commands = []


def filter_sudo_from_tool_calls(tool_calls: List[Dict]) -> Tuple[List[Dict], List[Dict], str]:
    """
    Convenience function to filter sudo from tool calls.
    
    Returns:
        (allowed_calls, blocked_calls, summary_message)
    """
    
    sudo_filter = SudoFilter()
    allowed, blocked = sudo_filter.filter_tool_calls(tool_calls)
    summary = sudo_filter.get_blocked_summary() if blocked else ""
    
    return allowed, blocked, summary