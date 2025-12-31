# Naming Conventions and Style Guide

## Overview
This document defines the naming conventions and coding standards for the autonomy project.

## 1. File Naming

### Python Files
- **Modules**: `lowercase_with_underscores.py`
  - Example: `function_call_validator.py`, `team_orchestrator.py`
- **Test files**: `test_<module_name>.py`
  - Example: `test_custom_tools_integration.py`
- **Scripts**: `<action>_<target>.py`
  - Example: `validate_all.py`, `analyze_code.py`

### Documentation Files
- **Markdown**: `UPPERCASE_WITH_UNDERSCORES.md` for important docs
  - Example: `README.md`, `ARCHITECTURE.md`, `MASTER_PLAN.md`
- **Regular docs**: `lowercase_with_underscores.md`
  - Example: `installation_guide.md`, `api_reference.md`

## 2. Class Naming

### General Rules
- **Classes**: `PascalCase` (CapitalizedWords)
  - Example: `FunctionCallValidator`, `TeamOrchestrator`
- **Exception classes**: End with `Error` or `Exception`
  - Example: `ValidationError`, `TimeoutException`
- **Abstract base classes**: May start with `Base` or `Abstract`
  - Example: `BaseTool`, `AbstractPhase`

### Specific Patterns

#### Validators
- Pattern: `<What>Validator`
- Examples:
  - `FunctionCallValidator` - validates function calls
  - `TypeUsageValidator` - validates type usage
  - `MethodExistenceValidator` - validates method existence

#### Analyzers
- Pattern: `<What>Analyzer`
- Examples:
  - `ComplexityAnalyzer` - analyzes code complexity
  - `DeadCodeAnalyzer` - analyzes dead code
  - `RefactoringArchitectureAnalyzer` - analyzes architecture for refactoring

#### Handlers
- Pattern: `<What>Handler`
- Examples:
  - `CustomToolHandler` - handles custom tools
  - `ErrorHandler` - handles errors
  - `MessageHandler` - handles messages

#### Registries
- Pattern: `<What>Registry`
- Examples:
  - `CustomToolRegistry` - registry for custom tools
  - `ToolRegistry` - main tool registry
  - `PromptRegistry` - registry for prompts

#### Visitors (AST)
- Pattern: `<Purpose>Visitor`
- Examples:
  - `CallChainVisitor` - visits AST for call chains
  - `TypeTrackingVisitor` - visits AST for type tracking

#### Phases
- Pattern: `<Name>Phase`
- Examples:
  - `CodingPhase` - coding phase
  - `DebuggingPhase` - debugging phase
  - `RefactoringPhase` - refactoring phase

## 3. Function and Method Naming

### General Rules
- **Functions/Methods**: `lowercase_with_underscores`
  - Example: `validate_function_call()`, `get_error_strategy()`
- **Private methods**: Start with single underscore `_`
  - Example: `_collect_signatures()`, `_validate_file()`
- **Special methods**: Double underscores (dunder methods)
  - Example: `__init__()`, `__str__()`

### Specific Patterns

#### Getters
- Pattern: `get_<what>()`
- Examples:
  - `get_debug_prompt()` - returns debug prompt
  - `get_error_strategy()` - returns error strategy
  - `get_tool_metadata()` - returns tool metadata

#### Setters
- Pattern: `set_<what>()`
- Examples:
  - `set_phase()` - sets phase
  - `set_context()` - sets context

#### Checkers/Validators
- Pattern: `check_<what>()` or `validate_<what>()`
- Examples:
  - `check_function_call()` - checks function call
  - `validate_signature()` - validates signature
  - `is_valid()` - returns boolean

#### Collectors
- Pattern: `collect_<what>()` or `gather_<what>()`
- Examples:
  - `collect_imports()` - collects imports
  - `gather_context()` - gathers context

#### Analyzers
- Pattern: `analyze_<what>()`
- Examples:
  - `analyze_complexity()` - analyzes complexity
  - `analyze_dead_code()` - analyzes dead code

#### Builders
- Pattern: `build_<what>()` or `create_<what>()`
- Examples:
  - `build_context()` - builds context
  - `create_report()` - creates report

## 4. Variable Naming

### General Rules
- **Variables**: `lowercase_with_underscores`
  - Example: `error_count`, `file_path`, `user_input`
- **Constants**: `UPPERCASE_WITH_UNDERSCORES`
  - Example: `MAX_RETRIES`, `DEFAULT_TIMEOUT`, `STDLIB_MODULES`
- **Private variables**: Start with single underscore `_`
  - Example: `_cache`, `_internal_state`

### Specific Patterns

#### Collections
- Use plural names for collections
  - Example: `errors`, `functions`, `imports`
- Use descriptive names
  - Example: `function_signatures` not `funcs`
  - Example: `error_messages` not `msgs`

#### Booleans
- Use `is_`, `has_`, `can_`, `should_` prefixes
  - Example: `is_valid`, `has_errors`, `can_retry`, `should_continue`

#### Counts
- Use `num_` or `count_` prefix
  - Example: `num_errors`, `count_functions`

#### Paths
- Use `_path` or `_dir` suffix
  - Example: `file_path`, `project_dir`, `output_path`

## 5. Type Hints

### General Rules
- Always use type hints for function parameters and return types
- Use `Optional[T]` for nullable types
- Use `List[T]`, `Dict[K, V]`, `Set[T]` for collections
- Use `Union[T1, T2]` for multiple types

### Examples
```python
from typing import Dict, List, Optional, Set, Tuple, Union
from pathlib import Path

def validate_file(
    filepath: Path,
    config: Optional[Dict[str, str]] = None
) -> Tuple[bool, List[str]]:
    """Validate a file and return (is_valid, errors)."""
    pass

def collect_imports(
    files: List[Path]
) -> Dict[str, Set[str]]:
    """Collect imports from files."""
    pass
```

## 6. Docstrings

### Format
Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of function.
    
    Longer description if needed. Can span multiple lines
    and include details about the function's behavior.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is invalid
        TypeError: When param2 is wrong type
        
    Example:
        >>> function_name("test", 42)
        True
    """
    pass
```

### Class Docstrings
```python
class ClassName:
    """
    Brief description of class.
    
    Longer description of class purpose and behavior.
    
    Attributes:
        attr1: Description of attr1
        attr2: Description of attr2
        
    Example:
        >>> obj = ClassName()
        >>> obj.method()
    """
    pass
```

## 7. Import Organization

### Order
1. Standard library imports
2. Third-party imports
3. Local application imports

### Format
```python
# Standard library
import ast
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Third-party
import numpy as np
import pandas as pd

# Local
from .validators import FunctionCallValidator
from .utils import get_logger
```

## 8. Code Organization

### File Structure
```python
"""
Module docstring describing the module.
"""

# Imports
import ...

# Constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 60

# Type aliases
ErrorDict = Dict[str, List[str]]

# Classes
class MainClass:
    pass

# Functions
def helper_function():
    pass

# Main execution
if __name__ == "__main__":
    main()
```

## 9. Naming Anti-Patterns to Avoid

### Don't Use
- ❌ Single letter variables (except in loops: `i`, `j`, `k`)
- ❌ Abbreviations: `func`, `val`, `tmp`, `mgr`
- ❌ Hungarian notation: `strName`, `intCount`
- ❌ Redundant prefixes: `my_`, `the_`
- ❌ Vague names: `data`, `info`, `stuff`, `thing`

### Do Use
- ✅ Descriptive names: `function_name`, `error_count`
- ✅ Full words: `function`, `value`, `temporary`, `manager`
- ✅ Context-appropriate names
- ✅ Meaningful names that explain purpose

## 10. Examples from Codebase

### Good Examples
```python
# Classes
class FunctionCallValidator:
    """Validates function calls with context awareness."""
    
class CustomToolRegistry:
    """Registry for custom tools."""
    
class RefactoringArchitectureAnalyzer:
    """Analyzes architecture for refactoring decisions."""

# Functions
def get_debug_prompt(filepath: str, code: str, issue: dict) -> str:
    """Generate debug prompt for an issue."""
    
def collect_function_signatures() -> Dict[str, Dict]:
    """Collect all function signatures with qualified names."""
    
def validate_all() -> Dict[str, int]:
    """Validate all code in the project."""

# Variables
function_signatures: Dict[str, Dict] = {}
error_count: int = 0
is_valid: bool = True
file_imports: Dict[str, Dict[str, str]] = {}
```

## 11. Consistency Rules

### Be Consistent
- If a module uses `analyze_`, all analysis functions should use `analyze_`
- If a class uses `_private_method`, all private methods should use underscore prefix
- If a file uses `get_` for getters, all getters should use `get_`

### Project-Wide Standards
- All validators end with `Validator`
- All analyzers end with `Analyzer`
- All handlers end with `Handler`
- All registries end with `Registry`
- All phases end with `Phase`
- All visitors end with `Visitor`

## Summary

Following these naming conventions ensures:
- ✅ Code is self-documenting
- ✅ Easy to understand and maintain
- ✅ Consistent across the entire codebase
- ✅ Reduces cognitive load
- ✅ Makes code reviews easier
- ✅ Helps new contributors understand the code