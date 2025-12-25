# Phase 4: Tool Development Framework

**Timeline:** 2-3 weeks  
**Priority:** MEDIUM  
**Dependencies:** Phase 1 (Foundation), Phase 2 (Architecture), Phase 3 (Specialists)  
**Deliverables:** Dynamic tool creation, validation, and management system

---

## Overview

Phase 4 enables agents to propose and create custom tools dynamically during execution. This allows the system to adapt to novel situations by creating specialized tools when existing ones are insufficient.

---

## Objectives

1. **Enable Dynamic Tool Creation**: Allow agents to propose and create new tools
2. **Implement Tool Validation**: Ensure tools are safe and functional
3. **Create Tool Library**: Maintain registry of available tools
4. **Build Tool Versioning**: Track tool evolution and changes
5. **Implement Security Checks**: Sandbox and validate tool execution
6. **Create Tool Documentation**: Auto-generate tool documentation

---

## Component 1: Tool Creation Framework

### Purpose
Enable agents to propose tool specifications and have them automatically created, validated, and deployed.

### Tool Creation Workflow

```
Agent identifies need → Proposes tool spec → Tool Specialist validates →
Tool Generator creates → Security check → Testing → Deployment → Registration
```

### Implementation Details

#### File: `pipeline/tools/tool_creator.py`

```python
class ToolCreator:
    """
    Creates custom tools dynamically based on specifications.
    
    Responsibilities:
    - Parse tool specifications
    - Generate tool code
    - Validate tool functionality
    - Deploy tools
    """
    
    def __init__(self, project_dir: Path, logger):
        self.project_dir = project_dir
        self.logger = logger
        
        # Tool generation
        self.code_generator = ToolCodeGenerator()
        
        # Validation
        self.validator = ToolValidator()
        
        # Security
        self.security_checker = ToolSecurityChecker()
        
        # Testing
        self.tester = ToolTester()
        
    def create_tool(self, tool_spec: Dict) -> Dict:
        """
        Create a new tool from specification.
        
        Args:
            tool_spec: {
                'name': 'analyze_memory_usage',
                'description': 'Analyze memory usage patterns',
                'parameters': {
                    'process_id': {'type': 'integer', 'required': True},
                    'duration': {'type': 'integer', 'default': 60}
                },
                'returns': {
                    'type': 'object',
                    'properties': {...}
                },
                'implementation': 'python|bash|hybrid',
                'code': '...' or 'auto-generate',
                'dependencies': ['psutil'],
                'safety_level': 'safe|cautious|dangerous'
            }
            
        Returns:
            {
                'success': True,
                'tool_id': 'tool_001',
                'tool_definition': {...},
                'handler_function': callable,
                'validation_results': {...},
                'security_check': {...},
                'test_results': {...}
            }
        """
        
        self.logger.info(f"Creating tool: {tool_spec['name']}")
        
        # Step 1: Validate specification
        spec_validation = self.validator.validate_specification(tool_spec)
        if not spec_validation['valid']:
            return {
                'success': False,
                'error': 'Invalid specification',
                'details': spec_validation['errors']
            }
            
        # Step 2: Generate code (if not provided)
        if tool_spec.get('code') == 'auto-generate' or not tool_spec.get('code'):
            code = self.code_generator.generate(tool_spec)
        else:
            code = tool_spec['code']
            
        # Step 3: Security check
        security_check = self.security_checker.check(code, tool_spec)
        if not security_check['safe']:
            return {
                'success': False,
                'error': 'Security check failed',
                'details': security_check['issues']
            }
            
        # Step 4: Create tool implementation
        tool_impl = self._create_implementation(tool_spec, code)
        
        # Step 5: Test tool
        test_results = self.tester.test_tool(tool_impl, tool_spec)
        if not test_results['passed']:
            return {
                'success': False,
                'error': 'Tool tests failed',
                'details': test_results['failures']
            }
            
        # Step 6: Create tool definition
        tool_definition = self._create_tool_definition(tool_spec)
        
        # Step 7: Register tool
        tool_id = self._register_tool(tool_spec, tool_impl, tool_definition)
        
        return {
            'success': True,
            'tool_id': tool_id,
            'tool_definition': tool_definition,
            'handler_function': tool_impl,
            'validation_results': spec_validation,
            'security_check': security_check,
            'test_results': test_results
        }
        
    def _create_implementation(self, tool_spec: Dict, code: str) -> Callable:
        """
        Create executable tool implementation.
        
        Returns a callable function that can be used as a tool handler.
        """
        
        impl_type = tool_spec.get('implementation', 'python')
        
        if impl_type == 'python':
            return self._create_python_implementation(tool_spec, code)
        elif impl_type == 'bash':
            return self._create_bash_implementation(tool_spec, code)
        elif impl_type == 'hybrid':
            return self._create_hybrid_implementation(tool_spec, code)
        else:
            raise ValueError(f"Unknown implementation type: {impl_type}")
            
    def _create_python_implementation(self, tool_spec: Dict, code: str) -> Callable:
        """Create Python-based tool implementation."""
        
        # Create a safe execution environment
        namespace = {
            '__builtins__': self._get_safe_builtins(),
            'logger': self.logger
        }
        
        # Add allowed imports
        for dep in tool_spec.get('dependencies', []):
            if self._is_safe_dependency(dep):
                namespace[dep] = __import__(dep)
                
        # Execute code to define function
        exec(code, namespace)
        
        # Get the tool function
        tool_function = namespace.get(tool_spec['name'])
        
        if not tool_function:
            raise ValueError(f"Function {tool_spec['name']} not found in code")
            
        # Wrap in error handling
        def wrapped_tool(**kwargs):
            try:
                return {
                    'success': True,
                    'result': tool_function(**kwargs)
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
                
        return wrapped_tool
        
    def _create_tool_definition(self, tool_spec: Dict) -> Dict:
        """
        Create OpenAI-compatible tool definition.
        
        Returns:
            {
                'type': 'function',
                'function': {
                    'name': '...',
                    'description': '...',
                    'parameters': {...}
                }
            }
        """
        
        return {
            'type': 'function',
            'function': {
                'name': tool_spec['name'],
                'description': tool_spec['description'],
                'parameters': {
                    'type': 'object',
                    'properties': tool_spec['parameters'],
                    'required': [
                        k for k, v in tool_spec['parameters'].items()
                        if v.get('required', False)
                    ]
                }
            }
        }


class ToolCodeGenerator:
    """Generates tool implementation code from specifications."""
    
    def generate(self, tool_spec: Dict) -> str:
        """
        Generate tool implementation code.
        
        Uses templates and AI assistance to generate code.
        """
        
        # Select appropriate template
        template = self._select_template(tool_spec)
        
        # Generate code from template
        code = self._apply_template(template, tool_spec)
        
        # Refine with AI if needed
        if tool_spec.get('complex', False):
            code = self._refine_with_ai(code, tool_spec)
            
        return code
        
    def _select_template(self, tool_spec: Dict) -> str:
        """Select appropriate code template."""
        
        # Common patterns
        if 'analyze' in tool_spec['name'].lower():
            return 'analysis_template'
        elif 'monitor' in tool_spec['name'].lower():
            return 'monitoring_template'
        elif 'search' in tool_spec['name'].lower():
            return 'search_template'
        else:
            return 'generic_template'
            
    def _apply_template(self, template_name: str, tool_spec: Dict) -> str:
        """Apply template to generate code."""
        
        templates = {
            'analysis_template': '''
def {name}({params}):
    """
    {description}
    
    Args:
        {param_docs}
        
    Returns:
        {return_doc}
    """
    # Implementation
    result = {{}}
    
    # TODO: Add analysis logic
    
    return result
''',
            'monitoring_template': '''
def {name}({params}):
    """
    {description}
    
    Args:
        {param_docs}
        
    Returns:
        {return_doc}
    """
    import time
    
    # Monitoring logic
    start_time = time.time()
    metrics = {{}}
    
    # TODO: Add monitoring logic
    
    metrics['duration'] = time.time() - start_time
    return metrics
''',
            'search_template': '''
def {name}({params}):
    """
    {description}
    
    Args:
        {param_docs}
        
    Returns:
        {return_doc}
    """
    results = []
    
    # TODO: Add search logic
    
    return results
''',
            'generic_template': '''
def {name}({params}):
    """
    {description}
    
    Args:
        {param_docs}
        
    Returns:
        {return_doc}
    """
    # TODO: Implement {name}
    
    return {{}}
'''
        }
        
        template = templates.get(template_name, templates['generic_template'])
        
        # Fill in template
        params = ', '.join(tool_spec['parameters'].keys())
        param_docs = '\n        '.join([
            f"{k}: {v.get('description', 'No description')}"
            for k, v in tool_spec['parameters'].items()
        ])
        
        code = template.format(
            name=tool_spec['name'],
            description=tool_spec['description'],
            params=params,
            param_docs=param_docs,
            return_doc=tool_spec.get('returns', {}).get('description', 'Result dictionary')
        )
        
        return code
```

---

## Component 2: Tool Validation System

### Purpose
Validate tool specifications and implementations for correctness, safety, and functionality.

### Validation Checks

1. **Specification Validation**
   - Required fields present
   - Parameter types valid
   - Return type specified
   - Description clear

2. **Code Validation**
   - Syntax correct
   - No dangerous operations
   - Dependencies available
   - Error handling present

3. **Functional Validation**
   - Tool executes successfully
   - Returns expected format
   - Handles errors gracefully
   - Performance acceptable

### Implementation Details

#### File: `pipeline/tools/tool_validator.py`

```python
class ToolValidator:
    """Validates tool specifications and implementations."""
    
    def validate_specification(self, tool_spec: Dict) -> Dict:
        """
        Validate tool specification.
        
        Returns:
            {
                'valid': True/False,
                'errors': [...],
                'warnings': [...]
            }
        """
        
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required fields
        required_fields = ['name', 'description', 'parameters']
        for field in required_fields:
            if field not in tool_spec:
                validation['errors'].append(f"Missing required field: {field}")
                validation['valid'] = False
                
        # Validate name
        if 'name' in tool_spec:
            if not self._is_valid_name(tool_spec['name']):
                validation['errors'].append(f"Invalid tool name: {tool_spec['name']}")
                validation['valid'] = False
                
        # Validate parameters
        if 'parameters' in tool_spec:
            param_validation = self._validate_parameters(tool_spec['parameters'])
            validation['errors'].extend(param_validation['errors'])
            validation['warnings'].extend(param_validation['warnings'])
            if param_validation['errors']:
                validation['valid'] = False
                
        # Check description quality
        if 'description' in tool_spec:
            if len(tool_spec['description']) < 20:
                validation['warnings'].append("Description is too short")
                
        return validation
        
    def _is_valid_name(self, name: str) -> bool:
        """Check if tool name is valid."""
        
        # Must be valid Python identifier
        if not name.isidentifier():
            return False
            
        # Should be snake_case
        if not name.islower() or ' ' in name:
            return False
            
        return True
        
    def _validate_parameters(self, parameters: Dict) -> Dict:
        """Validate parameter specifications."""
        
        validation = {
            'errors': [],
            'warnings': []
        }
        
        for param_name, param_spec in parameters.items():
            # Check parameter name
            if not param_name.isidentifier():
                validation['errors'].append(f"Invalid parameter name: {param_name}")
                
            # Check type
            if 'type' not in param_spec:
                validation['warnings'].append(f"Parameter {param_name} missing type")
                
            # Check description
            if 'description' not in param_spec:
                validation['warnings'].append(f"Parameter {param_name} missing description")
                
        return validation


class ToolTester:
    """Tests tool implementations."""
    
    def test_tool(self, tool_impl: Callable, tool_spec: Dict) -> Dict:
        """
        Test tool implementation.
        
        Returns:
            {
                'passed': True/False,
                'tests_run': 5,
                'tests_passed': 5,
                'failures': [...]
            }
        """
        
        results = {
            'passed': True,
            'tests_run': 0,
            'tests_passed': 0,
            'failures': []
        }
        
        # Test 1: Basic execution
        test_result = self._test_basic_execution(tool_impl, tool_spec)
        results['tests_run'] += 1
        if test_result['passed']:
            results['tests_passed'] += 1
        else:
            results['failures'].append(test_result)
            results['passed'] = False
            
        # Test 2: Parameter validation
        test_result = self._test_parameter_validation(tool_impl, tool_spec)
        results['tests_run'] += 1
        if test_result['passed']:
            results['tests_passed'] += 1
        else:
            results['failures'].append(test_result)
            results['passed'] = False
            
        # Test 3: Error handling
        test_result = self._test_error_handling(tool_impl, tool_spec)
        results['tests_run'] += 1
        if test_result['passed']:
            results['tests_passed'] += 1
        else:
            results['failures'].append(test_result)
            results['passed'] = False
            
        # Test 4: Return format
        test_result = self._test_return_format(tool_impl, tool_spec)
        results['tests_run'] += 1
        if test_result['passed']:
            results['tests_passed'] += 1
        else:
            results['failures'].append(test_result)
            results['passed'] = False
            
        # Test 5: Performance
        test_result = self._test_performance(tool_impl, tool_spec)
        results['tests_run'] += 1
        if test_result['passed']:
            results['tests_passed'] += 1
        else:
            results['failures'].append(test_result)
            # Performance failure is warning, not error
            
        return results
        
    def _test_basic_execution(self, tool_impl: Callable, tool_spec: Dict) -> Dict:
        """Test that tool executes without errors."""
        
        try:
            # Create sample parameters
            params = self._create_sample_parameters(tool_spec)
            
            # Execute tool
            result = tool_impl(**params)
            
            return {
                'test': 'basic_execution',
                'passed': True,
                'result': result
            }
        except Exception as e:
            return {
                'test': 'basic_execution',
                'passed': False,
                'error': str(e)
            }
            
    def _create_sample_parameters(self, tool_spec: Dict) -> Dict:
        """Create sample parameters for testing."""
        
        params = {}
        
        for param_name, param_spec in tool_spec['parameters'].items():
            param_type = param_spec.get('type', 'string')
            
            if param_type == 'string':
                params[param_name] = 'test_value'
            elif param_type == 'integer':
                params[param_name] = 42
            elif param_type == 'boolean':
                params[param_name] = True
            elif param_type == 'array':
                params[param_name] = ['item1', 'item2']
            elif param_type == 'object':
                params[param_name] = {'key': 'value'}
            else:
                params[param_name] = None
                
        return params
```

---

## Component 3: Tool Security Checker

### Purpose
Ensure tools are safe to execute and don't pose security risks.

### Security Checks

1. **Code Analysis**
   - No dangerous imports (os.system, subprocess with shell=True)
   - No file system modifications outside project
   - No network access (unless explicitly allowed)
   - No code execution (eval, exec)

2. **Sandboxing**
   - Execute in restricted environment
   - Limited resource access
   - Timeout enforcement
   - Memory limits

3. **Permission System**
   - Tools declare required permissions
   - User approval for dangerous operations
   - Audit log of tool executions

### Implementation Details

#### File: `pipeline/tools/tool_security.py`

```python
class ToolSecurityChecker:
    """Checks tool security and safety."""
    
    def __init__(self):
        # Dangerous patterns
        self.dangerous_imports = [
            'os.system',
            'subprocess.call',
            'subprocess.run',
            'eval',
            'exec',
            '__import__',
            'compile'
        ]
        
        # Allowed imports
        self.safe_imports = [
            'json',
            'datetime',
            'time',
            'math',
            'statistics',
            'collections',
            'itertools',
            'functools',
            're',
            'pathlib',
            'typing'
        ]
        
    def check(self, code: str, tool_spec: Dict) -> Dict:
        """
        Check tool security.
        
        Returns:
            {
                'safe': True/False,
                'issues': [...],
                'warnings': [...],
                'required_permissions': [...]
            }
        """
        
        check_result = {
            'safe': True,
            'issues': [],
            'warnings': [],
            'required_permissions': []
        }
        
        # Check for dangerous patterns
        for pattern in self.dangerous_imports:
            if pattern in code:
                check_result['issues'].append(f"Dangerous pattern found: {pattern}")
                check_result['safe'] = False
                
        # Check imports
        imports = self._extract_imports(code)
        for imp in imports:
            if imp not in self.safe_imports:
                if self._is_dangerous_import(imp):
                    check_result['issues'].append(f"Dangerous import: {imp}")
                    check_result['safe'] = False
                else:
                    check_result['warnings'].append(f"Unusual import: {imp}")
                    check_result['required_permissions'].append(f"import:{imp}")
                    
        # Check file operations
        if 'open(' in code or 'Path(' in code:
            check_result['required_permissions'].append('file_access')
            check_result['warnings'].append("Tool requires file access")
            
        # Check network operations
        if 'requests.' in code or 'urllib' in code or 'socket' in code:
            check_result['required_permissions'].append('network_access')
            check_result['warnings'].append("Tool requires network access")
            
        # Check subprocess usage
        if 'subprocess' in code:
            check_result['required_permissions'].append('subprocess')
            check_result['warnings'].append("Tool uses subprocess")
            
        return check_result
        
    def _extract_imports(self, code: str) -> List[str]:
        """Extract import statements from code."""
        
        imports = []
        
        for line in code.split('\n'):
            line = line.strip()
            if line.startswith('import '):
                module = line.replace('import ', '').split()[0]
                imports.append(module)
            elif line.startswith('from '):
                module = line.split()[1]
                imports.append(module)
                
        return imports
        
    def _is_dangerous_import(self, module: str) -> bool:
        """Check if import is dangerous."""
        
        dangerous_modules = [
            'os',
            'subprocess',
            'sys',
            'ctypes',
            'pickle',
            'marshal',
            'imp',
            'importlib'
        ]
        
        return module in dangerous_modules


class ToolSandbox:
    """Executes tools in sandboxed environment."""
    
    def __init__(self):
        self.timeout = 30  # seconds
        self.memory_limit = 512 * 1024 * 1024  # 512 MB
        
    def execute(self, tool_impl: Callable, params: Dict) -> Dict:
        """
        Execute tool in sandbox.
        
        Returns:
            {
                'success': True/False,
                'result': ...,
                'error': ...,
                'execution_time': 1.5,
                'memory_used': 1024000
            }
        """
        
        import time
        import tracemalloc
        
        # Start memory tracking
        tracemalloc.start()
        start_time = time.time()
        
        try:
            # Execute with timeout
            result = self._execute_with_timeout(tool_impl, params, self.timeout)
            
            # Get memory usage
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            execution_time = time.time() - start_time
            
            return {
                'success': True,
                'result': result,
                'execution_time': execution_time,
                'memory_used': peak
            }
            
        except TimeoutError:
            tracemalloc.stop()
            return {
                'success': False,
                'error': f'Tool execution timeout ({self.timeout}s)',
                'execution_time': self.timeout
            }
            
        except Exception as e:
            tracemalloc.stop()
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc(),
                'execution_time': time.time() - start_time
            }
            
    def _execute_with_timeout(self, func: Callable, params: Dict, timeout: int):
        """Execute function with timeout."""
        
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError()
            
        # Set timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        try:
            result = func(**params)
            signal.alarm(0)  # Cancel timeout
            return result
        except:
            signal.alarm(0)  # Cancel timeout
            raise
```

---

## Component 4: Tool Library and Registry

### Purpose
Maintain a registry of all available tools with versioning, documentation, and usage tracking.

### Features

1. **Tool Registration**
   - Register new tools
   - Version tracking
   - Metadata storage

2. **Tool Discovery**
   - Search by name, category, tags
   - Find similar tools
   - Recommend tools

3. **Tool Documentation**
   - Auto-generate documentation
   - Usage examples
   - Performance metrics

4. **Tool Analytics**
   - Usage statistics
   - Success rates
   - Performance data

### Implementation Details

#### File: `pipeline/tools/tool_registry.py`

```python
class ToolRegistry:
    """Registry of all available tools."""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(exist_ok=True)
        
        # In-memory registry
        self.tools: Dict[str, ToolEntry] = {}
        
        # Load existing tools
        self._load_tools()
        
    def register_tool(self, tool_spec: Dict, tool_impl: Callable, 
                     tool_definition: Dict) -> str:
        """
        Register a new tool.
        
        Returns:
            tool_id: Unique identifier for the tool
        """
        
        tool_id = self._generate_tool_id(tool_spec['name'])
        
        entry = ToolEntry(
            tool_id=tool_id,
            name=tool_spec['name'],
            version='1.0.0',
            specification=tool_spec,
            implementation=tool_impl,
            definition=tool_definition,
            created=datetime.now(),
            updated=datetime.now(),
            usage_count=0,
            success_count=0,
            failure_count=0
        )
        
        self.tools[tool_id] = entry
        
        # Persist to disk
        self._save_tool(entry)
        
        return tool_id
        
    def get_tool(self, tool_id: str) -> Optional[ToolEntry]:
        """Get tool by ID."""
        return self.tools.get(tool_id)
        
    def search_tools(self, query: str, category: str = None) -> List[ToolEntry]:
        """
        Search for tools.
        
        Args:
            query: Search query (name, description, tags)
            category: Optional category filter
            
        Returns:
            List of matching tools
        """
        
        results = []
        
        query_lower = query.lower()
        
        for tool in self.tools.values():
            # Check name
            if query_lower in tool.name.lower():
                results.append(tool)
                continue
                
            # Check description
            if query_lower in tool.specification.get('description', '').lower():
                results.append(tool)
                continue
                
            # Check tags
            tags = tool.specification.get('tags', [])
            if any(query_lower in tag.lower() for tag in tags):
                results.append(tool)
                continue
                
        # Filter by category
        if category:
            results = [t for t in results if t.specification.get('category') == category]
            
        return results
        
    def get_tool_statistics(self, tool_id: str) -> Dict:
        """Get usage statistics for a tool."""
        
        tool = self.get_tool(tool_id)
        if not tool:
            return {}
            
        total_uses = tool.usage_count
        success_rate = tool.success_count / total_uses if total_uses > 0 else 0
        
        return {
            'tool_id': tool_id,
            'name': tool.name,
            'version': tool.version,
            'total_uses': total_uses,
            'success_count': tool.success_count,
            'failure_count': tool.failure_count,
            'success_rate': success_rate,
            'created': tool.created.isoformat(),
            'last_used': tool.updated.isoformat()
        }
        
    def record_usage(self, tool_id: str, success: bool):
        """Record tool usage."""
        
        tool = self.get_tool(tool_id)
        if not tool:
            return
            
        tool.usage_count += 1
        if success:
            tool.success_count += 1
        else:
            tool.failure_count += 1
            
        tool.updated = datetime.now()
        
        # Persist changes
        self._save_tool(tool)


@dataclass
class ToolEntry:
    """Entry in tool registry."""
    
    tool_id: str
    name: str
    version: str
    specification: Dict
    implementation: Callable
    definition: Dict
    created: datetime
    updated: datetime
    usage_count: int
    success_count: int
    failure_count: int
    tags: List[str] = field(default_factory=list)
    category: str = 'general'
```

---

## Component 5: Tool Proposal System

### Purpose
Allow agents to propose new tools when they identify gaps in available tooling.

### Proposal Workflow

```
Agent identifies need → Creates proposal → Architect reviews →
Approved → Tool Specialist creates → Testing → Deployment
```

### Implementation Details

#### File: `pipeline/tools/tool_proposer.py`

```python
class ToolProposer:
    """Allows agents to propose new tools."""
    
    def __init__(self, tool_creator: ToolCreator, tool_registry: ToolRegistry):
        self.tool_creator = tool_creator
        self.tool_registry = tool_registry
        self.pending_proposals: List[ToolProposal] = []
        
    def propose_tool(self, agent_name: str, proposal: Dict) -> str:
        """
        Propose a new tool.
        
        Args:
            agent_name: Name of proposing agent
            proposal: {
                'name': 'proposed_tool_name',
                'description': '...',
                'rationale': 'Why this tool is needed',
                'use_cases': [...],
                'parameters': {...},
                'similar_tools': [...],
                'priority': 'low|medium|high|critical'
            }
            
        Returns:
            proposal_id: Unique identifier for proposal
        """
        
        proposal_id = f"proposal_{len(self.pending_proposals) + 1}"
        
        tool_proposal = ToolProposal(
            proposal_id=proposal_id,
            agent_name=agent_name,
            proposal=proposal,
            status='pending',
            created=datetime.now()
        )
        
        self.pending_proposals.append(tool_proposal)
        
        return proposal_id
        
    def review_proposal(self, proposal_id: str, reviewer: str, 
                       decision: str, feedback: str = '') -> Dict:
        """
        Review a tool proposal.
        
        Args:
            proposal_id: ID of proposal
            reviewer: Name of reviewer (usually Architect)
            decision: 'approve|reject|modify'
            feedback: Optional feedback
            
        Returns:
            Review result
        """
        
        proposal = self._get_proposal(proposal_id)
        if not proposal:
            return {'error': 'Proposal not found'}
            
        proposal.status = decision
        proposal.reviewer = reviewer
        proposal.review_feedback = feedback
        proposal.reviewed = datetime.now()
        
        if decision == 'approve':
            # Create the tool
            result = self.tool_creator.create_tool(proposal.proposal)
            proposal.tool_id = result.get('tool_id')
            
        return {
            'proposal_id': proposal_id,
            'decision': decision,
            'feedback': feedback,
            'tool_id': proposal.tool_id if decision == 'approve' else None
        }


@dataclass
class ToolProposal:
    """Tool proposal from an agent."""
    
    proposal_id: str
    agent_name: str
    proposal: Dict
    status: str  # pending|approved|rejected|modified
    created: datetime
    reviewer: str = ''
    review_feedback: str = ''
    reviewed: Optional[datetime] = None
    tool_id: Optional[str] = None
```

---

## Integration Strategy

### Phase 4A: Core Framework (Week 1)
1. Implement ToolCreator
2. Implement ToolValidator
3. Implement ToolSecurityChecker
4. Basic testing

### Phase 4B: Registry & Management (Week 2)
1. Implement ToolRegistry
2. Implement ToolProposer
3. Create tool library
4. Integration testing

### Phase 4C: Documentation & Polish (Week 3)
1. Auto-generate tool documentation
2. Create usage examples
3. Performance optimization
4. Complete documentation

---

## Success Criteria

### Functional Requirements
- ✅ Tools can be created dynamically
- ✅ Tool validation working
- ✅ Security checks effective
- ✅ Tool registry operational
- ✅ Tool proposals can be submitted

### Performance Requirements
- ✅ Tool creation < 10 seconds
- ✅ Tool validation < 5 seconds
- ✅ Security check < 2 seconds
- ✅ Registry search < 1 second

### Quality Requirements
- ✅ 90%+ code coverage
- ✅ All security tests passing
- ✅ Documentation complete
- ✅ No critical bugs

---

## Next Phase

Upon completion of Phase 4, proceed to:
**[PHASE_5_SERVERS.md](PHASE_5_SERVERS.md)** - Multi-Server Orchestration

---

**Phase Owner:** Development Team  
**Reviewers:** Technical Lead, Security Engineer  
**Approval Required:** Yes  
**Estimated Effort:** 2-3 weeks (1 developer full-time)
</file_path>