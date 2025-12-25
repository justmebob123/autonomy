"""
Error-specific debugging strategies.

This module provides specialized strategies for different error types,
helping the AI understand and fix errors more effectively.
"""
from typing import Dict, List, Optional


class ErrorStrategy:
    """Base class for error-specific strategies."""
    
    def __init__(self, error_type: str):
        self.error_type = error_type
    
    def get_investigation_steps(self, issue: Dict) -> List[str]:
        """Get investigation steps for this error type."""
        raise NotImplementedError
    
    def get_fix_approaches(self, issue: Dict) -> List[Dict]:
        """Get potential fix approaches for this error type."""
        raise NotImplementedError
    
    def enhance_prompt(self, base_prompt: str, issue: Dict) -> str:
        """Enhance the base prompt with error-specific guidance."""
        investigation = "\n".join(f"{i}. {step}" for i, step in enumerate(self.get_investigation_steps(issue), 1))
        
        approaches = "\n\n".join(
            f"**Approach {i}: {approach['name']}**\n"
            f"{approach['description']}\n"
            f"Steps:\n" + "\n".join(f"  - {step}" for step in approach['steps'])
            for i, approach in enumerate(self.get_fix_approaches(issue), 1)
        )
        
        enhancement = f"""

## ERROR-SPECIFIC STRATEGY: {self.error_type}

### Investigation Steps:
{investigation}

### Recommended Fix Approaches:
{approaches}

"""
        return base_prompt + enhancement


class UnboundLocalErrorStrategy(ErrorStrategy):
    """Strategy for UnboundLocalError."""
    
    def __init__(self):
        super().__init__('UnboundLocalError')
    
    def get_investigation_steps(self, issue: Dict) -> List[str]:
        """Investigation steps for UnboundLocalError."""
        variable_name = self._extract_variable_name(issue)
        line_num = issue.get('line', 'unknown')
        
        return [
            f"READ THE FILE to see the complete code structure",
            f"FIND where '{variable_name}' is used at line {line_num}",
            f"SEARCH for where '{variable_name}' is defined (use grep or search_code)",
            f"CHECK if '{variable_name}' is defined BEFORE line {line_num}",
            f"CHECK if '{variable_name}' is in the correct scope (not in a conditional block)",
            f"TRACE the execution flow to understand when '{variable_name}' should be available"
        ]
    
    def get_fix_approaches(self, issue: Dict) -> List[Dict]:
        """Fix approaches for UnboundLocalError."""
        variable_name = self._extract_variable_name(issue)
        line_num = issue.get('line', 'unknown')
        
        return [
            {
                'name': 'Move Definition Earlier',
                'description': f"Move the definition of '{variable_name}' to BEFORE line {line_num}",
                'steps': [
                    f"Find where '{variable_name}' is currently defined",
                    f"Move that definition to before line {line_num}",
                    "Ensure proper indentation and scope",
                    "Verify no other code depends on the original location"
                ]
            },
            {
                'name': 'Initialize Variable',
                'description': f"Initialize '{variable_name}' with a default value before use",
                'steps': [
                    f"Add '{variable_name} = None' or appropriate default before line {line_num}",
                    "Ensure it's in the correct scope (same indentation level)",
                    "Consider what default value makes sense (None, [], {}, etc.)"
                ]
            },
            {
                'name': 'Fix Scope Issue',
                'description': f"Fix the scope issue for '{variable_name}'",
                'steps': [
                    f"Check if '{variable_name}' is defined inside a conditional block (if/try/etc.)",
                    "Ensure it's defined in ALL code paths that reach line {line_num}",
                    "Or move the definition to outer scope before the conditional"
                ]
            }
        ]
    
    def _extract_variable_name(self, issue: Dict) -> str:
        """Extract variable name from error message."""
        message = issue.get('message', '')
        # "cannot access local variable 'servers' where it is not associated with a value"
        if "'" in message:
            parts = message.split("'")
            if len(parts) >= 2:
                return parts[1]
        return 'unknown'


class KeyErrorStrategy(ErrorStrategy):
    """Strategy for KeyError."""
    
    def __init__(self):
        super().__init__('KeyError')
    
    def get_investigation_steps(self, issue: Dict) -> List[str]:
        """Investigation steps for KeyError."""
        key_name = self._extract_key_name(issue)
        
        return [
            f"READ THE FILE to see the dictionary access",
            f"FIND where the dictionary is created/populated",
            f"CHECK what keys the dictionary actually has",
            f"VERIFY if '{key_name}' should exist in the dictionary",
            f"CHECK if there's a typo in the key name",
            f"DETERMINE if the key is optional or required"
        ]
    
    def get_fix_approaches(self, issue: Dict) -> List[Dict]:
        """Fix approaches for KeyError."""
        key_name = self._extract_key_name(issue)
        
        return [
            {
                'name': 'Add Missing Key',
                'description': f"Add the missing '{key_name}' key to the dictionary",
                'steps': [
                    "Find where the dictionary is created",
                    f"Add '{key_name}': value to the dictionary initialization",
                    "Ensure proper value type based on usage"
                ]
            },
            {
                'name': 'Use .get() Method',
                'description': f"Use .get() with default value instead of direct access",
                'steps': [
                    f"Change dict['{key_name}'] to dict.get('{key_name}', default)",
                    "Choose appropriate default value (None, '', [], etc.)",
                    "Ensure code handles the default value correctly"
                ]
            },
            {
                'name': 'Fix Key Name',
                'description': f"Fix typo or incorrect key name",
                'steps': [
                    "Print or log the actual keys in the dictionary",
                    "Find the correct key name (might be similar)",
                    "Update the code to use correct key"
                ]
            }
        ]
    
    def _extract_key_name(self, issue: Dict) -> str:
        """Extract key name from error message."""
        message = issue.get('message', '')
        # KeyError: 'url'
        if "'" in message:
            parts = message.split("'")
            if len(parts) >= 2:
                return parts[1]
        return 'unknown'


class AttributeErrorStrategy(ErrorStrategy):
    """Strategy for AttributeError."""
    
    def __init__(self):
        super().__init__('AttributeError')
    
    def get_investigation_steps(self, issue: Dict) -> List[str]:
        """Investigation steps for AttributeError."""
        return [
            "READ THE FILE to see the attribute access",
            "FIND what type of object is being accessed",
            "CHECK what attributes/methods the object actually has",
            "VERIFY if the attribute name is correct (check for typos)",
            "DETERMINE if the object is the expected type"
        ]
    
    def get_fix_approaches(self, issue: Dict) -> List[Dict]:
        """Fix approaches for AttributeError."""
        return [
            {
                'name': 'Fix Attribute Name',
                'description': "Correct the attribute/method name",
                'steps': [
                    "Check the object's class definition",
                    "Find the correct attribute name",
                    "Update the code to use correct name"
                ]
            },
            {
                'name': 'Add Missing Attribute',
                'description': "Add the missing attribute to the class",
                'steps': [
                    "Find the class definition",
                    "Add the missing attribute/method",
                    "Implement appropriate functionality"
                ]
            },
            {
                'name': 'Fix Object Type',
                'description': "Ensure the object is the correct type",
                'steps': [
                    "Check where the object is created",
                    "Verify it's the expected type",
                    "Fix the object creation if wrong type"
                ]
            }
        ]


class NameErrorStrategy(ErrorStrategy):
    """Strategy for NameError."""
    
    def __init__(self):
        super().__init__('NameError')
    
    def get_investigation_steps(self, issue: Dict) -> List[str]:
        """Investigation steps for NameError."""
        return [
            "READ THE FILE to see where the name is used",
            "CHECK if the name is defined anywhere in the file",
            "CHECK if the name should be imported",
            "VERIFY if there's a typo in the name",
            "CHECK the scope (local vs global)"
        ]
    
    def get_fix_approaches(self, issue: Dict) -> List[Dict]:
        """Fix approaches for NameError."""
        return [
            {
                'name': 'Add Import',
                'description': "Import the missing name",
                'steps': [
                    "Determine which module contains the name",
                    "Add appropriate import statement",
                    "Verify the import path is correct"
                ]
            },
            {
                'name': 'Define Variable',
                'description': "Define the missing variable",
                'steps': [
                    "Determine where the variable should be defined",
                    "Add variable definition with appropriate value",
                    "Ensure proper scope"
                ]
            },
            {
                'name': 'Fix Typo',
                'description': "Correct the name spelling",
                'steps': [
                    "Find similar names in the code",
                    "Identify the correct spelling",
                    "Update the code"
                ]
            }
        ]


class TypeErrorStrategy(ErrorStrategy):
    """Strategy for TypeError - especially function call parameter errors."""
    
    def __init__(self):
        super().__init__('TypeError')
    
    def get_investigation_steps(self, issue: Dict) -> List[str]:
        """Investigation steps for TypeError."""
        error_msg = issue.get('message', '')
        
        # Check if it's a function call parameter error
        if 'unexpected keyword argument' in error_msg or 'got an unexpected' in error_msg:
            return [
                "CRITICAL: This is a function call parameter error",
                "STEP 1: Use get_function_signature to extract the target function's signature",
                "STEP 2: Compare the signature with the actual function call",
                "STEP 3: Identify which parameters are INVALID (not in signature)",
                "STEP 4: Determine if parameters should be REMOVED or if function signature needs updating"
            ]
        elif 'missing' in error_msg and 'required' in error_msg:
            return [
                "This is a missing required parameter error",
                "Use get_function_signature to see what parameters are required",
                "Check the function call to see what's missing",
                "Add the missing required parameters"
            ]
        else:
            return [
                "Read the error message carefully to understand the type mismatch",
                "Check what type is expected vs what type is provided",
                "Fix the type conversion or parameter"
            ]
    
    def get_fix_approaches(self, issue: Dict) -> List[Dict]:
        """Fix approaches for TypeError."""
        error_msg = issue.get('message', '')
        
        if 'unexpected keyword argument' in error_msg or 'got an unexpected' in error_msg:
            # Extract parameter name from error message
            import re
            match = re.search(r"unexpected keyword argument '(\w+)'", error_msg)
            param_name = match.group(1) if match else 'unknown'
            
            return [
                {
                    'name': 'Remove Invalid Parameter (MOST COMMON)',
                    'description': f"Remove the '{param_name}' parameter from the function call",
                    'steps': [
                        f"Find the function call that passes '{param_name}'",
                        f"Remove the '{param_name}=...' line from the call",
                        "Ensure proper syntax (remove trailing comma if needed)",
                        "Use modify_python_file to apply the fix"
                    ]
                },
                {
                    'name': 'Update Function Signature (LESS COMMON)',
                    'description': f"Add '{param_name}' parameter to the function definition",
                    'steps': [
                        "Find the function definition",
                        f"Add '{param_name}' to the parameter list",
                        "Implement handling for the new parameter",
                        "Use modify_python_file to apply the fix"
                    ]
                }
            ]
        else:
            return [
                {
                    'name': 'Fix Type Mismatch',
                    'description': "Convert the value to the expected type",
                    'steps': [
                        "Identify the expected type",
                        "Add type conversion (int(), str(), list(), etc.)",
                        "Use modify_python_file to apply the fix"
                    ]
                }
            ]
    
    def enhance_prompt(self, base_prompt: str, issue: Dict) -> str:
        """Enhance prompt with TypeError-specific guidance."""
        error_msg = issue.get('message', '')
        
        if 'unexpected keyword argument' in error_msg or 'got an unexpected' in error_msg:
            # Extract parameter name
            import re
            match = re.search(r"unexpected keyword argument '(\w+)'", error_msg)
            param_name = match.group(1) if match else 'unknown'
            
            enhancement = f"""

## ⚠️ CRITICAL: FUNCTION CALL PARAMETER ERROR ⚠️

This is a TypeError caused by passing an INVALID parameter to a function.

**The Problem:**
- The function call passes parameter '{param_name}'
- But the function definition does NOT accept '{param_name}'

**What You MUST Do:**

1. **You already called get_function_signature** - Review the results
2. **Compare the signature with the function call** - Which parameters are invalid?
3. **IMMEDIATELY call modify_python_file** to remove the invalid parameter

**DO NOT:**
- Call get_function_signature again (you already have the signature)
- Just explain what to do (you must CALL the tool)
- Add more investigation (you have all the information)

**CALL modify_python_file NOW** to remove '{param_name}' from the function call.

Example:
```json
{{
    "name": "modify_python_file",
    "arguments": {{
        "filepath": "path/to/file.py",
        "original_code": "function_call(\\n    param1=value1,\\n    {param_name}=value,\\n    param2=value2\\n)",
        "new_code": "function_call(\\n    param1=value1,\\n    param2=value2\\n)"
    }}
}}
```

**FIX IT NOW - Call modify_python_file to remove the invalid parameter.**
"""
            return base_prompt + enhancement
        else:
            return super().enhance_prompt(base_prompt, issue)


# Strategy registry
ERROR_STRATEGIES = {
    'UnboundLocalError': UnboundLocalErrorStrategy(),
    'KeyError': KeyErrorStrategy(),
    'AttributeError': AttributeErrorStrategy(),
    'NameError': NameErrorStrategy(),
    'TypeError': TypeErrorStrategy(),
}


def get_strategy(error_type: str) -> Optional[ErrorStrategy]:
    """
    Get strategy for error type.
    
    Args:
        error_type: Type of error (e.g., 'UnboundLocalError')
        
    Returns:
        ErrorStrategy instance or None if no strategy exists
    """
    return ERROR_STRATEGIES.get(error_type)


def enhance_prompt_with_strategy(base_prompt: str, issue: Dict) -> str:
    """
    Enhance prompt with error-specific strategy if available.
    
    Args:
        base_prompt: Base debugging prompt
        issue: Issue dictionary with error information
        
    Returns:
        Enhanced prompt with strategy guidance
    """
    error_type = issue.get('type', 'RuntimeError')
    strategy = get_strategy(error_type)
    
    if strategy:
        return strategy.enhance_prompt(base_prompt, issue)
    else:
        return base_prompt