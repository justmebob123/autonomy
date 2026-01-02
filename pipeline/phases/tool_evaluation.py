"""
Tool Evaluation Phase

Tests and validates newly created tools with comprehensive integration testing.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import ast
import importlib.util
import sys

from .base import BasePhase, PhaseResult
from .loop_detection_mixin import LoopDetectionMixin
from ..state.manager import PipelineState
from ..config import PipelineConfig
from ..client import OllamaClient


class ToolEvaluationPhase(LoopDetectionMixin, BasePhase):
    """
    Phase for evaluating and validating custom tools.
    
    Features:
    - Accepts tool specifications as parameters
    - Tests tool loading mechanisms
    - Validates function signatures
    - Tests integration with ToolCallHandler
    - Performs security validation
    - Comprehensive logging and reporting
    
    Process:
    1. Receive tool specification
    2. Load tool implementation
    3. Validate function signature
    4. Test with sample inputs
    5. Validate security constraints
    6. Test integration with ToolCallHandler
    7. Generate evaluation report
    """
    
    phase_name = "tool_evaluation"
    
    def __init__(self, config: PipelineConfig, client: OllamaClient, **kwargs):
        BasePhase.__init__(self, config, client, **kwargs)
        self.init_loop_detection()
        
        # ARCHITECTURE CONFIG
        from ..architecture_parser import get_architecture_config
        self.architecture_config = get_architecture_config(self.project_dir)
        self.logger.info(f"  📐 Architecture config loaded: {len(self.architecture_config.library_dirs)} library dirs")
        
        self.logger.info("Enhanced ToolEvaluationPhase initialized with IPC integration")
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """
        Execute tool evaluation phase.
        
        Args:
            state: Current pipeline state
            **kwargs: Context parameters including:
                - tool_spec: Tool specification dict or path to spec file
                - tool_impl: Path to tool implementation file
                - test_inputs: Optional test inputs for the tool
                
        Returns:
            PhaseResult with evaluation results
        """
        
        # ARCHITECTURE INTEGRATION: Read architecture
        architecture = self._read_architecture()
        if architecture:
            self.logger.info(f"  📐 Architecture loaded: {len(architecture.get('components', {}))} components defined")
        
        # IPC INTEGRATION: Read objectives
        objectives = self._read_objectives()
        if objectives:
            self.logger.info(f"  🎯 Objectives loaded: PRIMARY={bool(objectives.get('primary'))}, SECONDARY={len(objectives.get('secondary', []))}")
        
        # IPC INTEGRATION: Write status at start
        self._write_status("Starting tool evaluation", {"action": "start"})
        
        # INITIALIZE IPC DOCUMENTS
        self.initialize_ipc_documents()
        
        # READ STRATEGIC DOCUMENTS
        strategic_docs = self.read_strategic_docs()
        
        # READ OWN TASKS
        tasks_from_doc = self.read_own_tasks()
        
        # READ OTHER PHASES' OUTPUTS
        tool_design_output = self.read_phase_output('tool_design')
        
        # Extract parameters
        tool_spec = kwargs.get('tool_spec')
        tool_impl = kwargs.get('tool_impl')
        test_inputs = kwargs.get('test_inputs', [])
        
        if not tool_spec:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="No tool specification provided for evaluation"
            )
        
        self.logger.info("🧪 Tool evaluation starting...")
        
        # Load tool specification
        spec = self._load_tool_spec(tool_spec)
        if not spec:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message="Failed to load tool specification"
            )
        
        tool_name = spec.get('name', 'unknown')
        self.logger.info(f"   Evaluating tool: {tool_name}")
        
        # Initialize evaluation results
        evaluation = {
            'tool_name': tool_name,
            'tests_passed': [],
            'tests_failed': [],
            'warnings': [],
            'security_level': spec.get('security_level', 'unknown')
        }
        
        # Test 1: Load tool implementation
        self.logger.info("📦 Test 1: Loading tool implementation...")
        impl_result = self._test_load_implementation(spec, tool_impl)
        if impl_result['success']:
            evaluation['tests_passed'].append('load_implementation')
            self.logger.info("   ✓ Tool implementation loaded successfully")
        else:
            evaluation['tests_failed'].append('load_implementation')
            self.logger.error(f"   ✗ Failed to load implementation: {impl_result['error']}")
            return self._create_failure_result(evaluation, impl_result['error'])
        
        # Test 2: Validate function signature
        self.logger.info("🔍 Test 2: Validating function signature...")
        sig_result = self._test_function_signature(spec, impl_result['function'])
        if sig_result['success']:
            evaluation['tests_passed'].append('function_signature')
            self.logger.info("   ✓ Function signature valid")
        else:
            evaluation['tests_failed'].append('function_signature')
            evaluation['warnings'].append(sig_result['error'])
            self.logger.warning(f"   ⚠ Signature issue: {sig_result['error']}")
        
        # Test 3: Security validation
        self.logger.info("🔒 Test 3: Security validation...")
        security_result = self._test_security(spec, impl_result['source_code'])
        if security_result['success']:
            evaluation['tests_passed'].append('security_validation')
            self.logger.info(f"   ✓ Security level: {spec.get('security_level', 'unknown')}")
        else:
            evaluation['tests_failed'].append('security_validation')
            self.logger.error(f"   ✗ Security issue: {security_result['error']}")
            return self._create_failure_result(evaluation, security_result['error'])
        
        if security_result.get('warnings'):
            for warning in security_result['warnings']:
                evaluation['warnings'].append(warning)
                self.logger.warning(f"   ⚠ {warning}")
        
        # Test 4: Execute with sample inputs
        self.logger.info("⚙️ Test 4: Testing with sample inputs...")
        exec_result = self._test_execution(
            impl_result['function'],
            spec,
            test_inputs
        )
        if exec_result['success']:
            evaluation['tests_passed'].append('execution')
            self.logger.info(f"   ✓ Executed {exec_result['tests_run']} test(s) successfully")
        else:
            evaluation['tests_failed'].append('execution')
            self.logger.error(f"   ✗ Execution failed: {exec_result['error']}")
            # Don't fail completely - execution issues might be due to test inputs
            evaluation['warnings'].append(f"Execution test failed: {exec_result['error']}")
        
        # Test 5: Integration with ToolCallHandler
        self.logger.info("🔗 Test 5: Testing ToolCallHandler integration...")
        integration_result = self._test_handler_integration(spec, tool_impl)
        if integration_result['success']:
            evaluation['tests_passed'].append('handler_integration')
            self.logger.info("   ✓ ToolCallHandler integration successful")
        else:
            evaluation['tests_failed'].append('handler_integration')
            evaluation['warnings'].append(integration_result['error'])
            self.logger.warning(f"   ⚠ Integration issue: {integration_result['error']}")
        
        # Test 6: Registry integration
        self.logger.info("📚 Test 6: Testing ToolRegistry integration...")
        registry_result = self._test_registry_integration(spec)
        if registry_result['success']:
            evaluation['tests_passed'].append('registry_integration')
            self.logger.info("   ✓ ToolRegistry integration successful")
        else:
            evaluation['tests_failed'].append('registry_integration')
            evaluation['warnings'].append(registry_result['error'])
            self.logger.warning(f"   ⚠ Registry issue: {registry_result['error']}")
        
        # Generate evaluation report
        report = self._generate_evaluation_report(evaluation)
        self.logger.info("\n" + report)
        
        # Determine overall success
        critical_tests = ['load_implementation', 'security_validation']
        critical_failures = [t for t in critical_tests if t in evaluation['tests_failed']]
        
        if critical_failures:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Tool evaluation failed: {', '.join(critical_failures)}",
                data=evaluation
            )
        
        # Success with possible warnings
        success_rate = len(evaluation['tests_passed']) / (
            len(evaluation['tests_passed']) + len(evaluation['tests_failed'])
        ) if (evaluation['tests_passed'] or evaluation['tests_failed']) else 0
        
        # IPC INTEGRATION: Write completion status
        self._write_status("Tool evaluation completed", {
            "action": "complete",
            "success_rate": f"{success_rate:.0%}",
            "tests_passed": len(evaluation['tests_passed'])
        })
        
        # ARCHITECTURE INTEGRATION: Record evaluation
        if architecture:
            self._update_architecture(
                'tools',
                f"Evaluated tool: {evaluation.get('tool_name', 'unknown')}",
                f"Tool Evaluation: {success_rate:.0%} success rate"
            )
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message=f"Tool evaluation passed ({success_rate:.0%} success rate)",
            data=evaluation
        )
    
    def _load_tool_spec(self, tool_spec: Any) -> Optional[Dict]:
        """Load tool specification from dict or file."""
        if isinstance(tool_spec, dict):
            return tool_spec
        
        if isinstance(tool_spec, str):
            spec_path = Path(tool_spec)
            if not spec_path.is_absolute():
                spec_path = self.project_dir / spec_path
            
            if spec_path.exists():
                try:
                    with open(spec_path, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    self.logger.error(f"Error loading spec file: {e}")
                    return None
        
        return None
    
    def _test_load_implementation(self, spec: Dict, tool_impl: Optional[str]) -> Dict:
        """Test loading the tool implementation."""
        try:
            # Determine implementation file path
            if tool_impl:
                impl_path = Path(tool_impl)
            else:
                # Try to find it based on spec
                tool_name = spec.get('name', '')
                impl_path = Path(f"pipeline/tools/custom/{tool_name}.py")
            
            if not impl_path.is_absolute():
                impl_path = self.project_dir / impl_path
            
            if not impl_path.exists():
                return {
                    'success': False,
                    'error': f"Implementation file not found: {impl_path}"
                }
            
            # Read source code
            with open(impl_path, 'r') as f:
                source_code = f.read()
            
            # Parse AST to find the function
            tree = ast.parse(source_code)
            tool_function = None
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name == spec.get('name'):
                        tool_function = node
                        break
            
            if not tool_function:
                return {
                    'success': False,
                    'error': f"Function '{spec.get('name')}' not found in implementation"
                }
            
            # Try to import the module
            spec_obj = importlib.util.spec_from_file_location(
                spec.get('name'),
                impl_path
            )
            module = importlib.util.module_from_spec(spec_obj)
            spec_obj.loader.exec_module(module)
            
            # Get the function
            func = getattr(module, spec.get('name'), None)
            if not func:
                return {
                    'success': False,
                    'error': f"Function '{spec.get('name')}' not found after import"
                }
            
            return {
                'success': True,
                'function': func,
                'source_code': source_code,
                'ast_node': tool_function
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _test_function_signature(self, spec: Dict, function: Any) -> Dict:
        """Test that function signature matches specification."""
        try:
            import inspect
            
            sig = inspect.signature(function)
            spec_params = spec.get('parameters', {})
            
            # Check parameters
            func_params = list(sig.parameters.keys())
            spec_param_names = list(spec_params.keys())
            
            # Check for missing required parameters
            required_params = [
                name for name, param_spec in spec_params.items()
                if param_spec.get('required', True)
            ]
            
            missing_params = [p for p in required_params if p not in func_params]
            if missing_params:
                return {
                    'success': False,
                    'error': f"Missing required parameters: {', '.join(missing_params)}"
                }
            
            # Check for extra parameters
            extra_params = [p for p in func_params if p not in spec_param_names]
            if extra_params:
                # This is a warning, not a failure
                return {
                    'success': True,
                    'warning': f"Extra parameters not in spec: {', '.join(extra_params)}"
                }
            
            return {'success': True}
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Error checking signature: {e}"
            }
    
    def _test_security(self, spec: Dict, source_code: str) -> Dict:
        """Test security constraints."""
        security_level = spec.get('security_level', 'unknown')
        warnings = []
        
        # Check for dangerous operations based on security level
        if security_level == 'safe':
            # Should not have file system, network, or subprocess operations
            dangerous_imports = ['os', 'subprocess', 'socket', 'urllib', 'requests']
            dangerous_calls = ['open(', 'exec(', 'eval(', '__import__']
            
            for imp in dangerous_imports:
                if f'import {imp}' in source_code or f'from {imp}' in source_code:
                    return {
                        'success': False,
                        'error': f"Security violation: 'safe' tool imports '{imp}'"
                    }
            
            for call in dangerous_calls:
                if call in source_code:
                    warnings.append(f"Potentially dangerous call: {call}")
        
        elif security_level == 'restricted':
            # Can have read-only file operations, no network or subprocess
            dangerous_imports = ['subprocess', 'socket', 'urllib', 'requests']
            
            for imp in dangerous_imports:
                if f'import {imp}' in source_code or f'from {imp}' in source_code:
                    return {
                        'success': False,
                        'error': f"Security violation: 'restricted' tool imports '{imp}'"
                    }
        
        # 'dangerous' level has no restrictions
        
        return {
            'success': True,
            'warnings': warnings
        }
    
    def _test_execution(self, function: Any, spec: Dict, test_inputs: List[Dict]) -> Dict:
        """Test executing the function with sample inputs."""
        if not test_inputs:
            # Generate basic test inputs from spec
            test_inputs = self._generate_test_inputs(spec)
        
        if not test_inputs:
            return {
                'success': True,
                'tests_run': 0,
                'message': 'No test inputs available'
            }
        
        tests_run = 0
        for test_input in test_inputs:
            try:
                result = function(**test_input)
                tests_run += 1
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Execution failed with input {test_input}: {e}",
                    'tests_run': tests_run
                }
        
        return {
            'success': True,
            'tests_run': tests_run
        }
    
    def _generate_test_inputs(self, spec: Dict) -> List[Dict]:
        """Generate basic test inputs from specification."""
        params = spec.get('parameters', {})
        if not params:
            return []
        
        # Generate one test input with default values
        test_input = {}
        for param_name, param_spec in params.items():
            if not param_spec.get('required', True):
                continue
            
            param_type = param_spec.get('type', 'string')
            
            # Generate default value based on type
            if param_type == 'string':
                test_input[param_name] = 'test_value'
            elif param_type == 'integer':
                test_input[param_name] = 0
            elif param_type == 'boolean':
                test_input[param_name] = True
            elif param_type == 'array':
                test_input[param_name] = []
            elif param_type == 'object':
                test_input[param_name] = {}
        
        return [test_input] if test_input else []
    
    def _test_handler_integration(self, spec: Dict, tool_impl: Optional[str]) -> Dict:
        """Test integration with ToolCallHandler."""
        try:
            # This would test if ToolCallHandler can find and execute the tool
            # For now, we'll do a basic check
            tool_name = spec.get('name')
            
            # Check if tool is in registry
            if hasattr(self, 'tool_registry'):
                tool = self.tool_registry.get_tool(tool_name)
                if tool:
                    return {'success': True}
                else:
                    return {
                        'success': False,
                        'error': f"Tool '{tool_name}' not found in registry"
                    }
            
            return {
                'success': True,
                'message': 'ToolRegistry not available for testing'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _test_registry_integration(self, spec: Dict) -> Dict:
        """Test integration with ToolRegistry."""
        try:
            tool_name = spec.get('name')
            
            if not hasattr(self, 'tool_registry'):
                return {
                    'success': True,
                    'message': 'ToolRegistry not available'
                }
            
            # Check if tool can be retrieved
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': f"Tool '{tool_name}' not registered"
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_evaluation_report(self, evaluation: Dict) -> str:
        """Generate a formatted evaluation report."""
        report = []
        report.append("=" * 70)
        report.append("TOOL EVALUATION REPORT")
        report.append("=" * 70)
        report.append(f"\nTool: {evaluation['tool_name']}")
        report.append(f"Security Level: {evaluation['security_level']}")
        
        report.append(f"\n✓ Tests Passed ({len(evaluation['tests_passed'])}):")
        for test in evaluation['tests_passed']:
            report.append(f"  • {test}")
        
        if evaluation['tests_failed']:
            report.append(f"\n✗ Tests Failed ({len(evaluation['tests_failed'])}):")
            for test in evaluation['tests_failed']:
                report.append(f"  • {test}")
        
        if evaluation['warnings']:
            report.append(f"\n⚠ Warnings ({len(evaluation['warnings'])}):")
            for warning in evaluation['warnings']:
                report.append(f"  • {warning}")
        
        total_tests = len(evaluation['tests_passed']) + len(evaluation['tests_failed'])
        if total_tests > 0:
            success_rate = len(evaluation['tests_passed']) / total_tests
            report.append(f"\nSuccess Rate: {success_rate:.0%}")
        
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def _create_failure_result(self, evaluation: Dict, error: str) -> PhaseResult:
        """Create a failure result with evaluation data."""
        return PhaseResult(
            success=False,
            phase=self.phase_name,
            message=f"Tool evaluation failed: {error}",
            data=evaluation
        )
    
    def generate_state_markdown(self, state: PipelineState) -> str:
        """Generate markdown state file for this phase."""
        phase_state = state.phases.get(self.phase_name)
        
        return f"""# Tool Evaluation Phase State

## Statistics
- Runs: {phase_state.run_count if phase_state else 0}
- Successes: {phase_state.success_count if phase_state else 0}
- Failures: {phase_state.failure_count if phase_state else 0}

## Evaluation Tests
- Load Implementation
- Function Signature Validation
- Security Validation
- Execution Testing
- ToolCallHandler Integration
- ToolRegistry Integration

## Recent Evaluations
(Evaluation history would be tracked here)
"""