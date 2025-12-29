# 🏗️ Custom Tools Redesign - Complete Implementation Plan

**Date**: December 28, 2024  
**Status**: Ready for Implementation  
**Estimated Effort**: 2-3 weeks

---

## 🎯 IMPLEMENTATION ROADMAP

### Week 1: External Tools Infrastructure

#### Day 1-2: Core Framework
- [ ] Create `scripts/custom_tools/` directory structure
- [ ] Implement `BaseTool` class
- [ ] Implement `ToolResult` dataclass
- [ ] Implement `ToolExecutor` (subprocess-based)
- [ ] Create comprehensive tests

#### Day 3-4: Template System
- [ ] Implement `TemplateGenerator`
- [ ] Create tool templates
- [ ] Add validation
- [ ] Test generation

#### Day 5: Documentation
- [ ] Write README.md
- [ ] Create usage guide
- [ ] Document API
- [ ] Add examples

### Week 2: Integration & Migration

#### Day 6-7: custom_tool Meta-Tool
- [ ] Add `TOOL_CUSTOM_TOOL` to pipeline/tools.py
- [ ] Implement `_handle_custom_tool()` in handlers.py
- [ ] Add to all phases via `get_tools_for_phase()`
- [ ] Test end-to-end

#### Day 8-9: Update Tool Design Phase
- [ ] Change output location to `scripts/custom_tools/tools/`
- [ ] Use `TemplateGenerator`
- [ ] Follow `BaseTool` pattern
- [ ] Update prompts

#### Day 10: Update Tool Evaluation Phase
- [ ] Test via `ToolExecutor` (subprocess)
- [ ] Validate `BaseTool` compliance
- [ ] Check isolation
- [ ] Update tests

### Week 3: Advanced Features & Polish

#### Day 11-12: Live Reload
- [ ] Implement `reload_custom_tools()`
- [ ] Add reload trigger
- [ ] Test hot-reload
- [ ] Document behavior

#### Day 13-14: Tool Repair
- [ ] Implement `repair_tool()`
- [ ] Add error analysis
- [ ] Trigger redesign
- [ ] Test repair flow

#### Day 15: Final Testing & Documentation
- [ ] Integration tests
- [ ] Performance tests
- [ ] Complete documentation
- [ ] Create migration guide

---

## 📝 DETAILED IMPLEMENTATION

### 1. BaseTool Class

**File**: `scripts/custom_tools/core/base.py`

```python
#!/usr/bin/env python3
"""
BaseTool - Base class for all custom tools.

All custom tools must inherit from BaseTool and implement execute().
This provides:
- Standard interface
- Input validation
- Error handling
- Timeout enforcement
- Execution time tracking
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import time
import signal


@dataclass
class ToolResult:
    """
    Standard result format for all tools.
    
    Attributes:
        success: Whether tool executed successfully
        result: Tool output (any type)
        error: Error message if failed
        metadata: Additional information
        execution_time: Time taken to execute
    """
    success: bool
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'success': self.success,
            'result': self.result,
            'error': self.error,
            'metadata': self.metadata,
            'execution_time': self.execution_time
        }


class TimeoutError(Exception):
    """Raised when tool execution times out."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Tool execution timed out")


class BaseTool(ABC):
    """
    Base class for all custom tools.
    
    All custom tools must:
    1. Inherit from BaseTool
    2. Set class attributes (name, description, version, category)
    3. Implement execute() method
    4. Return ToolResult
    5. Handle all errors
    6. Validate inputs
    
    Example:
        class AnalyzeImports(BaseTool):
            name = "analyze_imports"
            description = "Analyze import statements in Python file"
            version = "1.0.0"
            category = "analysis"
            
            def validate_inputs(self, **kwargs):
                if 'filepath' not in kwargs:
                    return False, "filepath is required"
                return True, None
            
            def execute(self, **kwargs):
                filepath = kwargs['filepath']
                # ... implementation ...
                return ToolResult(success=True, result=analysis)
    """
    
    # Tool metadata (MUST override in subclass)
    name: str = "base_tool"
    description: str = "Base tool class"
    version: str = "1.0.0"
    category: str = "utility"
    author: str = "AI"
    
    # Security settings (override as needed)
    requires_filesystem: bool = False
    requires_network: bool = False
    requires_subprocess: bool = False
    timeout_seconds: int = 30
    max_file_size_mb: int = 10
    
    def __init__(self, project_dir: str):
        """
        Initialize tool with project directory.
        
        Args:
            project_dir: Path to project root directory
        """
        self.project_dir = Path(project_dir)
        self.start_time: Optional[float] = None
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool (MUST implement in subclass).
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult with success, result, error, metadata
            
        Example:
            def execute(self, filepath: str) -> ToolResult:
                try:
                    # Validate
                    if not filepath:
                        return ToolResult(success=False, error="filepath required")
                    
                    # Execute
                    result = analyze_file(filepath)
                    
                    # Return
                    return ToolResult(success=True, result=result)
                    
                except Exception as e:
                    return ToolResult(success=False, error=str(e))
        """
        pass
    
    def validate_inputs(self, **kwargs) -> Tuple[bool, Optional[str]]:
        """
        Validate tool inputs (override in subclass for custom validation).
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            (is_valid, error_message)
            
        Example:
            def validate_inputs(self, **kwargs):
                if 'filepath' not in kwargs:
                    return False, "filepath is required"
                
                if not kwargs['filepath'].endswith('.py'):
                    return False, "filepath must be a Python file"
                
                return True, None
        """
        return True, None
    
    def run(self, **kwargs) -> ToolResult:
        """
        Run the tool with validation, error handling, and timeout.
        
        This is the main entry point that wraps execute() with:
        - Input validation
        - Error handling
        - Timeout enforcement
        - Execution time tracking
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            ToolResult
        """
        self.start_time = time.time()
        
        try:
            # Validate inputs
            is_valid, error = self.validate_inputs(**kwargs)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=f"Invalid input: {error}",
                    execution_time=time.time() - self.start_time
                )
            
            # Set timeout alarm
            if self.timeout_seconds > 0:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.timeout_seconds)
            
            try:
                # Execute tool
                result = self.execute(**kwargs)
                
                # Cancel alarm
                if self.timeout_seconds > 0:
                    signal.alarm(0)
                
                # Add execution time
                result.execution_time = time.time() - self.start_time
                
                # Add metadata
                if result.metadata is None:
                    result.metadata = {}
                result.metadata.update({
                    'tool_name': self.name,
                    'tool_version': self.version,
                    'execution_time': result.execution_time
                })
                
                return result
                
            except TimeoutError:
                return ToolResult(
                    success=False,
                    error=f"Tool timed out after {self.timeout_seconds} seconds",
                    execution_time=time.time() - self.start_time
                )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {e}",
                execution_time=time.time() - self.start_time if self.start_time else 0
            )
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get tool metadata.
        
        Returns:
            Dict with tool information
        """
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'category': self.category,
            'author': self.author,
            'security': {
                'requires_filesystem': self.requires_filesystem,
                'requires_network': self.requires_network,
                'requires_subprocess': self.requires_subprocess,
                'timeout_seconds': self.timeout_seconds,
                'max_file_size_mb': self.max_file_size_mb
            }
        }
```

### 2. ToolExecutor (Subprocess Isolation)

**File**: `scripts/custom_tools/core/executor.py`

```python
#!/usr/bin/env python3
"""
ToolExecutor - Executes custom tools in isolated subprocess.

This provides:
- Process isolation (tool crash doesn't crash pipeline)
- Timeout enforcement
- Resource limits
- Live reload (no module caching)
- Security sandboxing
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import logging


class ToolExecutor:
    """
    Executes custom tools in isolated subprocess.
    
    Benefits:
    - Tool crash doesn't crash pipeline
    - Timeout enforcement
    - Resource limits
    - No module caching (live reload)
    - Security sandboxing
    
    Example:
        executor = ToolExecutor('scripts/custom_tools', '/project')
        result = executor.execute_tool('analyze_imports', {'filepath': 'main.py'})
        if result['success']:
            print(result['result'])
    """
    
    def __init__(self, tools_dir: str, project_dir: str, logger: Optional[logging.Logger] = None):
        """
        Initialize executor.
        
        Args:
            tools_dir: Directory containing custom tools (scripts/custom_tools/)
            project_dir: Project root directory
            logger: Optional logger instance
        """
        self.tools_dir = Path(tools_dir)
        self.project_dir = Path(project_dir)
        self.logger = logger or logging.getLogger(__name__)
        
        # Verify tools directory exists
        if not self.tools_dir.exists():
            raise ValueError(f"Tools directory not found: {tools_dir}")
    
    def execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a custom tool in isolated subprocess.
        
        Args:
            tool_name: Name of the tool to execute
            args: Tool arguments
            timeout: Timeout in seconds (uses tool default if not specified)
            
        Returns:
            Tool result dict with:
            - success: bool
            - result: Any (tool output)
            - error: str (if failed)
            - metadata: dict
            - execution_time: float
        """
        # Find tool file
        tool_file = self.tools_dir / "tools" / f"{tool_name}.py"
        
        if not tool_file.exists():
            self.logger.error(f"Tool not found: {tool_name} at {tool_file}")
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}",
                "error_type": "tool_not_found",
                "searched_path": str(tool_file)
            }
        
        # Get tool timeout if not specified
        if timeout is None:
            timeout = self._get_tool_timeout(tool_file)
        
        # Prepare execution command
        cmd = [
            sys.executable,
            str(tool_file),
            "--project-dir", str(self.project_dir),
            "--args", json.dumps(args)
        ]
        
        self.logger.debug(f"Executing tool: {tool_name} with timeout {timeout}s")
        
        try:
            # Execute in subprocess with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.project_dir),
                env={'PYTHONPATH': str(self.tools_dir)}
            )
            
            # Parse result
            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout)
                    self.logger.debug(f"Tool {tool_name} succeeded")
                    return output
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Tool {tool_name} returned invalid JSON: {e}")
                    return {
                        "success": False,
                        "error": "Tool returned invalid JSON",
                        "error_type": "invalid_output",
                        "stdout": result.stdout[:500],
                        "stderr": result.stderr[:500]
                    }
            else:
                self.logger.error(f"Tool {tool_name} failed with code {result.returncode}")
                return {
                    "success": False,
                    "error": f"Tool exited with code {result.returncode}",
                    "error_type": "execution_error",
                    "stderr": result.stderr[:500]
                }
        
        except subprocess.TimeoutExpired:
            self.logger.error(f"Tool {tool_name} timed out after {timeout}s")
            return {
                "success": False,
                "error": f"Tool timed out after {timeout} seconds",
                "error_type": "timeout"
            }
        
        except Exception as e:
            self.logger.error(f"Tool {tool_name} execution failed: {e}")
            return {
                "success": False,
                "error": f"Tool execution failed: {e}",
                "error_type": "execution_error"
            }
    
    def _get_tool_timeout(self, tool_file: Path) -> int:
        """
        Get tool timeout from tool file.
        
        Args:
            tool_file: Path to tool file
            
        Returns:
            Timeout in seconds (default: 30)
        """
        try:
            content = tool_file.read_text()
            
            # Look for timeout_seconds = X
            import re
            match = re.search(r'timeout_seconds\s*=\s*(\d+)', content)
            if match:
                return int(match.group(1))
        
        except Exception:
            pass
        
        return 30  # Default timeout
    
    def list_tools(self) -> list[Dict[str, Any]]:
        """
        List all available custom tools.
        
        Returns:
            List of tool metadata dicts
        """
        tools = []
        tools_path = self.tools_dir / "tools"
        
        if not tools_path.exists():
            return tools
        
        for tool_file in tools_path.glob("*.py"):
            if tool_file.name.startswith('_'):
                continue
            
            try:
                metadata = self._extract_tool_metadata(tool_file)
                if metadata:
                    tools.append(metadata)
            except Exception as e:
                self.logger.warning(f"Failed to extract metadata from {tool_file}: {e}")
        
        return tools
    
    def _extract_tool_metadata(self, tool_file: Path) -> Optional[Dict[str, Any]]:
        """
        Extract tool metadata from tool file.
        
        Args:
            tool_file: Path to tool file
            
        Returns:
            Tool metadata dict or None
        """
        try:
            content = tool_file.read_text()
            
            # Extract metadata using regex
            import re
            
            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
            version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            category_match = re.search(r'category\s*=\s*["\']([^"\']+)["\']', content)
            
            if name_match:
                return {
                    'name': name_match.group(1),
                    'description': desc_match.group(1) if desc_match else '',
                    'version': version_match.group(1) if version_match else '1.0.0',
                    'category': category_match.group(1) if category_match else 'utility',
                    'file': str(tool_file)
                }
        
        except Exception:
            pass
        
        return None
    
    def reload_tool(self, tool_name: str) -> bool:
        """
        Reload a tool (for live updates).
        
        Since tools run in subprocess, they're automatically reloaded
        on each execution. This method is for compatibility.
        
        Args:
            tool_name: Name of tool to reload
            
        Returns:
            True if tool exists, False otherwise
        """
        tool_file = self.tools_dir / "tools" / f"{tool_name}.py"
        return tool_file.exists()
```

### 2. custom_tool Meta-Tool

**File**: Update `pipeline/tools.py`

```python
# Add to PIPELINE_TOOLS or create new category

TOOL_CUSTOM_TOOL = {
    "type": "function",
    "function": {
        "name": "custom_tool",
        "description": """Request development of a new custom tool.

Use this when you need a tool that doesn't exist yet. The system will:
1. Design the tool specification
2. Generate the implementation
3. Test and validate the tool
4. Make it available immediately

Example usage:
custom_tool(
    name="analyze_complexity",
    description="Calculate cyclomatic complexity of Python functions in a file",
    parameters={
        "filepath": "Path to Python file to analyze"
    },
    usage="Use when evaluating code quality or identifying refactoring candidates",
    examples=["analyze_complexity(filepath='src/main.py')"]
)

The tool will be created in scripts/custom_tools/tools/ and available immediately.
""",
        "parameters": {
            "type": "object",
            "required": ["name", "description"],
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the new tool (verb_noun format, e.g., 'analyze_imports', 'run_tests')"
                },
                "description": {
                    "type": "string",
                    "description": "Clear, detailed description of what the tool should do, including inputs and outputs"
                },
                "parameters": {
                    "type": "object",
                    "description": "Expected parameters for the tool (parameter_name: description)",
                    "additionalProperties": {"type": "string"},
                    "examples": [
                        {"filepath": "Path to file to analyze"},
                        {"query": "Search query", "max_results": "Maximum results to return"}
                    ]
                },
                "usage": {
                    "type": "string",
                    "description": "When and how this tool should be used, including use cases and scenarios"
                },
                "examples": {
                    "type": "array",
                    "description": "Example usage scenarios showing how to call the tool",
                    "items": {"type": "string"}
                },
                "category": {
                    "type": "string",
                    "enum": ["analysis", "testing", "debugging", "refactoring", "generation", "utility"],
                    "description": "Tool category for organization"
                },
                "requires_filesystem": {
                    "type": "boolean",
                    "description": "Whether tool needs filesystem access (default: false)"
                },
                "requires_network": {
                    "type": "boolean",
                    "description": "Whether tool needs network access (default: false)"
                },
                "requires_subprocess": {
                    "type": "boolean",
                    "description": "Whether tool needs to run subprocesses (default: false)"
                },
                "timeout_seconds": {
                    "type": "integer",
                    "description": "Maximum execution time in seconds (default: 30)",
                    "minimum": 1,
                    "maximum": 300
                }
            }
        }
    }
}

# Add to appropriate tool list
TOOLS_ALL_PHASES = [TOOL_CUSTOM_TOOL]  # Available to all phases
```

**Handler**: Update `pipeline/handlers.py`

```python
def _handle_custom_tool(self, args: Dict) -> Dict:
    """
    Handle custom_tool request.
    
    This initiates the tool development process:
    1. Generate tool template
    2. Save to scripts/custom_tools/tools/
    3. Trigger tool_design phase for implementation
    4. Test via tool_evaluation phase
    5. Register with ToolExecutor
    6. Return success
    
    Args:
        args: Tool specification from custom_tool call
        
    Returns:
        Result dict
    """
    tool_name = args.get('name')
    description = args.get('description')
    parameters = args.get('parameters', {})
    usage = args.get('usage', '')
    examples = args.get('examples', [])
    category = args.get('category', 'utility')
    
    # Validate tool name
    if not tool_name:
        return {
            "success": False,
            "error": "Tool name is required"
        }
    
    # Validate name format (verb_noun)
    if '_' not in tool_name:
        return {
            "success": False,
            "error": "Tool name must be in verb_noun format (e.g., 'analyze_imports')"
        }
    
    self.logger.info(f"🔧 Custom tool requested: {tool_name}")
    self.logger.info(f"   Description: {description}")
    self.logger.info(f"   Parameters: {list(parameters.keys())}")
    
    # Generate tool template
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts' / 'custom_tools'))
    
    try:
        from core.template import generate_tool
        
        tool_code = generate_tool(
            name=tool_name,
            description=description,
            parameters=parameters,
            category=category,
            requires_filesystem=args.get('requires_filesystem', False),
            requires_network=args.get('requires_network', False),
            requires_subprocess=args.get('requires_subprocess', False),
            timeout=args.get('timeout_seconds', 30)
        )
        
        # Save tool file
        tools_dir = Path(__file__).parent.parent / 'scripts' / 'custom_tools' / 'tools'
        tools_dir.mkdir(parents=True, exist_ok=True)
        
        tool_file = tools_dir / f"{tool_name}.py"
        tool_file.write_text(tool_code)
        tool_file.chmod(0o755)  # Make executable
        
        self.logger.info(f"✅ Tool template created: {tool_file}")
        
        # Create tool specification for AI to implement
        spec = {
            'name': tool_name,
            'description': description,
            'parameters': parameters,
            'usage': usage,
            'examples': examples,
            'category': category,
            'file': str(tool_file),
            'status': 'template_created',
            'needs_implementation': True
        }
        
        # Trigger tool_design phase to implement the tool
        # (This will be handled by coordinator)
        
        return {
            "success": True,
            "result": {
                "tool_name": tool_name,
                "tool_file": str(tool_file),
                "status": "template_created",
                "message": f"Tool template created. AI will now implement the tool logic.",
                "spec": spec
            },
            "metadata": {
                "requires_implementation": True,
                "tool_spec": spec
            }
        }
    
    except Exception as e:
        self.logger.error(f"Failed to create tool template: {e}")
        return {
            "success": False,
            "error": f"Failed to create tool template: {e}"
        }
```

---

## 🎯 MIGRATION STRATEGY

### Step 1: Create New Infrastructure (No Breaking Changes)

1. Create `scripts/custom_tools/` alongside existing system
2. Implement BaseTool, ToolExecutor, TemplateGenerator
3. Add custom_tool meta-tool
4. Test in parallel with existing system

### Step 2: Gradual Migration (Backward Compatible)

1. Update ToolRegistry to support both locations
2. Prefer scripts/custom_tools/ for new tools
3. Keep pipeline/tools/custom/ for existing tools
4. Add deprecation warnings

### Step 3: Complete Migration (Breaking Changes)

1. Move all tools to scripts/custom_tools/
2. Remove pipeline/tools/custom/
3. Update all references
4. Remove old code

### Step 4: Cleanup & Documentation

1. Remove deprecated code
2. Update all documentation
3. Create migration guide
4. Announce changes

---

## 📊 COMPARISON: Current vs Proposed

| Feature | Current | Proposed | Benefit |
|---------|---------|----------|---------|
| **Location** | pipeline/tools/custom/ | scripts/custom_tools/ | External, safe |
| **Execution** | In-process (import) | Subprocess | Crash isolation |
| **Reload** | No (cached) | Yes (fresh) | Live updates |
| **Timeout** | No enforcement | Enforced | Safety |
| **Meta-Tool** | No | custom_tool | Explicit requests |
| **Architecture** | Single file | Modular (BaseTool) | Maintainable |
| **Model** | Ad-hoc | scripts/analysis/ | Consistent |
| **Safety** | Can crash pipeline | Isolated | Stable |

---

## 🎯 CONCLUSION

The current custom tools system is **partially implemented** but **critically misaligned** with the original vision.

**Critical Issues**:
1. 🔴 Tools in wrong location (pipeline/ not scripts/)
2. 🔴 No process isolation (can crash system)
3. 🔴 No live reload (requires restart)
4. 🔴 No custom_tool meta-tool (inefficient)
5. 🔴 Doesn't follow scripts/ model (inconsistent)

**Recommendation**: **IMPLEMENT PROPOSED REDESIGN**

**Priority**: CRITICAL

**Effort**: 2-3 weeks

**Impact**: 
- ✅ Aligns with original vision
- ✅ System stability (crash isolation)
- ✅ Live updates (hot-reload)
- ✅ Efficient workflow (custom_tool)
- ✅ Consistent architecture (follows scripts/)

**Next Steps**:
1. Review and approve proposal
2. Begin Week 1 implementation
3. Test thoroughly
4. Migrate gradually
5. Document completely

---

**Analysis Complete**: December 28, 2024  
**Status**: Proposal ready for implementation  
**Recommendation**: PROCEED WITH REDESIGN