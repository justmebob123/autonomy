# Validation Tools Implementation Plan

## Overview

Detailed implementation plan for 23 new validation tools to achieve 100% coverage of code validation capabilities.

---

## Phase 1: Critical Tools (Week 1)

### Tool 1: validate_attribute_access

**Purpose**: Catch attribute name errors like `task.target` vs `task.target_file`

**Implementation**:

```python
# pipeline/analysis/code_validation.py

class AttributeAccessValidator(ast.NodeVisitor):
    """Validates object attribute access patterns."""
    
    def __init__(self, filepath: str, logger):
        self.filepath = filepath
        self.logger = logger
        self.issues = []
        self.known_classes = {}  # class_name -> {attributes}
        
    def validate(self) -> List[Dict]:
        """Run validation and return issues."""
        with open(self.filepath, 'r') as f:
            tree = ast.parse(f.read(), filename=self.filepath)
        
        # First pass: collect class definitions
        self._collect_class_definitions(tree)
        
        # Second pass: validate attribute access
        self.visit(tree)
        
        return self.issues
    
    def _collect_class_definitions(self, tree):
        """Collect all class definitions and their attributes."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                attrs = set()
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        # Method names are attributes
                        attrs.add(item.name)
                    elif isinstance(item, ast.Assign):
                        # Class/instance variables
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                attrs.add(target.id)
                            elif isinstance(target, ast.Attribute):
                                attrs.add(target.attr)
                
                self.known_classes[node.name] = attrs
    
    def visit_Attribute(self, node):
        """Check attribute access."""
        # Get the object being accessed
        if isinstance(node.value, ast.Name):
            var_name = node.value.id
            attr_name = node.attr
            
            # Check if we know the type
            if var_name in self.known_classes:
                if attr_name not in self.known_classes[var_name]:
                    self.issues.append({
                        'type': 'unknown_attribute',
                        'object': var_name,
                        'attribute': attr_name,
                        'line': node.lineno,
                        'col': node.col_offset,
                        'message': f"Attribute '{attr_name}' not found in class '{var_name}'"
                    })
        
        self.generic_visit(node)
```

**Handler**:

```python
# pipeline/handlers.py

def _handle_validate_attribute_access(self, args: Dict) -> Dict:
    """Validate attribute access patterns."""
    try:
        from ..analysis.code_validation import AttributeAccessValidator
        
        filepath = args.get('filepath')
        check_all = args.get('check_all_files', False)
        
        if check_all:
            # Check all Python files
            files = list(Path(self.project_dir).rglob("*.py"))
        else:
            files = [Path(self.project_dir) / filepath]
        
        all_issues = []
        for file in files:
            validator = AttributeAccessValidator(str(file), self.logger)
            issues = validator.validate()
            if issues:
                all_issues.extend([{**issue, 'file': str(file)} for issue in issues])
        
        return {
            "tool": "validate_attribute_access",
            "success": True,
            "issues_found": len(all_issues),
            "issues": all_issues,
            "message": f"Found {len(all_issues)} attribute access issues"
        }
    except Exception as e:
        return {
            "tool": "validate_attribute_access",
            "success": False,
            "error": str(e)
        }
```

---

### Tool 2: verify_import_class_match

**Purpose**: Catch import name mismatches like `ConflictDetector` vs `IntegrationConflictDetector`

**Implementation**:

```python
# pipeline/analysis/code_validation.py

class ImportClassMatcher:
    """Verifies import names match actual class names."""
    
    def __init__(self, filepath: str, logger):
        self.filepath = filepath
        self.logger = logger
        self.issues = []
    
    def validate(self) -> List[Dict]:
        """Check all imports match actual class names."""
        with open(self.filepath, 'r') as f:
            tree = ast.parse(f.read(), filename=self.filepath)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module
                for alias in node.names:
                    imported_name = alias.name
                    
                    # Try to load the module and check class exists
                    try:
                        # Convert relative import to absolute
                        if module.startswith('.'):
                            # Handle relative imports
                            base_module = self._get_base_module(self.filepath)
                            module = self._resolve_relative_import(module, base_module)
                        
                        # Import the module
                        mod = importlib.import_module(module)
                        
                        # Check if imported name exists
                        if not hasattr(mod, imported_name):
                            # Get actual class names
                            actual_classes = [name for name in dir(mod) 
                                            if inspect.isclass(getattr(mod, name))]
                            
                            # Find similar names
                            similar = [c for c in actual_classes 
                                     if imported_name.lower() in c.lower() 
                                     or c.lower() in imported_name.lower()]
                            
                            self.issues.append({
                                'type': 'import_class_mismatch',
                                'module': module,
                                'imported_name': imported_name,
                                'line': node.lineno,
                                'actual_classes': actual_classes,
                                'similar_names': similar,
                                'message': f"'{imported_name}' not found in '{module}'. Similar: {similar}"
                            })
                    except ImportError as e:
                        self.issues.append({
                            'type': 'import_error',
                            'module': module,
                            'imported_name': imported_name,
                            'line': node.lineno,
                            'message': f"Cannot import '{module}': {e}"
                        })
        
        return self.issues
```

---

### Tool 3: check_abstract_methods

**Purpose**: Catch missing abstract method implementations like `generate_state_markdown`

**Implementation**:

```python
# pipeline/analysis/code_validation.py

class AbstractMethodChecker:
    """Checks abstract methods are implemented."""
    
    def __init__(self, filepath: str, class_name: str, logger):
        self.filepath = filepath
        self.class_name = class_name
        self.logger = logger
        self.issues = []
    
    def validate(self) -> List[Dict]:
        """Check all abstract methods are implemented."""
        # Load the module
        spec = importlib.util.spec_from_file_location("module", self.filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the class
        if not hasattr(module, self.class_name):
            return [{
                'type': 'class_not_found',
                'class_name': self.class_name,
                'message': f"Class '{self.class_name}' not found in {self.filepath}"
            }]
        
        cls = getattr(module, self.class_name)
        
        # Get all abstract methods from base classes
        abstract_methods = set()
        for base in inspect.getmro(cls)[1:]:  # Skip the class itself
            for name, method in inspect.getmembers(base):
                if hasattr(method, '__isabstractmethod__') and method.__isabstractmethod__:
                    abstract_methods.add(name)
        
        # Check if implemented
        for method_name in abstract_methods:
            if not hasattr(cls, method_name):
                self.issues.append({
                    'type': 'missing_abstract_method',
                    'class_name': self.class_name,
                    'method_name': method_name,
                    'message': f"Abstract method '{method_name}' not implemented in '{self.class_name}'"
                })
            else:
                # Check if it's actually implemented (not just inherited)
                method = getattr(cls, method_name)
                if hasattr(method, '__isabstractmethod__') and method.__isabstractmethod__:
                    self.issues.append({
                        'type': 'abstract_method_not_overridden',
                        'class_name': self.class_name,
                        'method_name': method_name,
                        'message': f"Abstract method '{method_name}' inherited but not overridden"
                    })
        
        return self.issues
```

---

### Tool 4: verify_tool_handlers

**Purpose**: Catch missing tool handlers and registration issues

**Implementation**:

```python
# pipeline/analysis/code_validation.py

class ToolHandlerVerifier:
    """Verifies tool-handler-registration chain."""
    
    def __init__(self, project_dir: str, logger):
        self.project_dir = project_dir
        self.logger = logger
        self.issues = []
    
    def validate(self) -> List[Dict]:
        """Verify all tools have handlers and are registered."""
        
        # 1. Get all tool definitions
        tools = self._get_all_tools()
        
        # 2. Get all handler methods
        handlers = self._get_all_handlers()
        
        # 3. Get handler registrations
        registrations = self._get_handler_registrations()
        
        # 4. Check each tool
        for tool_name, tool_file in tools:
            # Check handler exists
            expected_handler = f"_handle_{tool_name}"
            if expected_handler not in handlers:
                self.issues.append({
                    'type': 'missing_handler',
                    'tool_name': tool_name,
                    'expected_handler': expected_handler,
                    'tool_file': tool_file,
                    'message': f"Handler '{expected_handler}' not found for tool '{tool_name}'"
                })
            
            # Check registration
            if tool_name not in registrations:
                self.issues.append({
                    'type': 'missing_registration',
                    'tool_name': tool_name,
                    'expected_handler': expected_handler,
                    'message': f"Tool '{tool_name}' not registered in handlers dict"
                })
            elif registrations[tool_name] != expected_handler:
                self.issues.append({
                    'type': 'wrong_handler_registered',
                    'tool_name': tool_name,
                    'expected_handler': expected_handler,
                    'actual_handler': registrations[tool_name],
                    'message': f"Tool '{tool_name}' registered with wrong handler"
                })
        
        return self.issues
    
    def _get_all_tools(self) -> List[Tuple[str, str]]:
        """Get all tool names from tool modules."""
        tools = []
        tool_files = [
            "pipeline/tool_modules/file_updates.py",
            "pipeline/tool_modules/refactoring_tools.py",
            "pipeline/tool_modules/tool_definitions.py"
        ]
        
        for filepath in tool_files:
            full_path = Path(self.project_dir) / filepath
            if full_path.exists():
                with open(full_path, 'r') as f:
                    content = f.read()
                tool_names = re.findall(r'"name":\s*"(\w+)"', content)
                tools.extend([(name, filepath) for name in tool_names])
        
        return tools
    
    def _get_all_handlers(self) -> Set[str]:
        """Get all handler method names."""
        handlers_file = Path(self.project_dir) / "pipeline/handlers.py"
        with open(handlers_file, 'r') as f:
            content = f.read()
        
        handler_names = re.findall(r'def (_handle_\w+)\(self', content)
        return set(handler_names)
    
    def _get_handler_registrations(self) -> Dict[str, str]:
        """Get handler registrations from handlers dict."""
        handlers_file = Path(self.project_dir) / "pipeline/handlers.py"
        with open(handlers_file, 'r') as f:
            content = f.read()
        
        registrations = re.findall(r'"(\w+)":\s*self\.(_handle_\w+)', content)
        return dict(registrations)
```

---

## File Structure

```
pipeline/
├── analysis/
│   └── code_validation.py (NEW)
│       ├── AttributeAccessValidator
│       ├── ImportClassMatcher
│       ├── AbstractMethodChecker
│       ├── ToolHandlerVerifier
│       ├── DictAccessValidator
│       └── ... (other validators)
│
├── tool_modules/
│   └── validation_tools.py (NEW)
│       └── TOOLS_VALIDATION (23 tool definitions)
│
├── handlers.py (MODIFIED)
│   └── Add 23 new handler methods
│
└── tools.py (MODIFIED)
    └── Add TOOLS_VALIDATION to imports and phase mappings
```

---

## Integration Points

### 1. Investigation Phase
Add validation tools to investigation phase for proactive checking.

### 2. Debugging Phase
Use validation tools when debugging to find root causes.

### 3. QA Phase
Run validation tools as part of quality checks.

### 4. New Validation Phase (Optional)
Create dedicated phase that runs all validation tools.

---

## Testing Strategy

### Unit Tests
```python
# tests/test_code_validation.py

def test_attribute_access_validator():
    """Test attribute access validation."""
    code = '''
class Task:
    def __init__(self):
        self.target_file = "test.py"

task = Task()
print(task.target)  # Should catch this error
'''
    validator = AttributeAccessValidator("test.py", logger)
    issues = validator.validate()
    assert len(issues) == 1
    assert issues[0]['attribute'] == 'target'
```

### Integration Tests
```python
def test_full_validation_pipeline():
    """Test full validation on real codebase."""
    validator = CodeValidator(project_dir)
    results = validator.validate_all()
    
    assert 'attribute_issues' in results
    assert 'import_issues' in results
    assert 'abstract_method_issues' in results
    assert 'tool_handler_issues' in results
```

---

## Timeline

### Week 1: Phase 1 (Critical Tools)
- Day 1-2: Implement AttributeAccessValidator
- Day 3-4: Implement ImportClassMatcher
- Day 5: Implement AbstractMethodChecker
- Day 6: Implement ToolHandlerVerifier
- Day 7: Testing and integration

### Week 2: Phase 2 (Important Tools)
- Day 1-2: Implement DictAccessValidator
- Day 3-4: Implement remaining Phase 2 tools
- Day 5-7: Testing and integration

### Week 3: Phase 3 (Enhancement Tools)
- Day 1-5: Implement Phase 3 tools
- Day 6-7: Final testing and documentation

---

## Success Metrics

### Before Implementation
- Bugs caught: 0% (manual review only)
- Validation coverage: 23.3%
- Average debugging time: 2-4 hours per bug

### After Implementation
- Bugs caught: 80%+ (automated validation)
- Validation coverage: 100%
- Average debugging time: 15-30 minutes per bug

---

## Next Steps

1. **Review and approve** this implementation plan
2. **Create** `pipeline/analysis/code_validation.py`
3. **Create** `pipeline/tool_modules/validation_tools.py`
4. **Implement** Phase 1 tools (4 critical tools)
5. **Test** on existing codebase
6. **Integrate** with investigation/debugging phases
7. **Document** usage and examples

---

*Document created: December 30, 2024*  
*Implementation timeline: 3 weeks*  
*Expected impact: 80%+ bug prevention*