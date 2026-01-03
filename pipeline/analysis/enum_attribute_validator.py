"""
Enum Attribute Validator

Validates that Enum attributes exist before they are accessed.
Detects invalid enum member access like MessageType.INVALID_ATTRIBUTE.

Now uses shared SymbolTable for improved accuracy.
"""

import ast
from typing import Dict, List, Set, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from .symbol_table import SymbolTable

# Polytopic Integration Imports
from pipeline.messaging.message_bus import MessageBus, Message, MessageType, MessagePriority
from pipeline.pattern_recognition import PatternRecognitionSystem
from pipeline.correlation_engine import CorrelationEngine
from pipeline.analytics.optimizer import OptimizationEngine
from pipeline.adaptive_prompts import AdaptivePromptSystem
from pipeline.polytopic.dimensional_space import DimensionalSpace



@dataclass
class EnumAttributeError:
    """Represents an enum attribute validation error."""
    file: str
    line: int
    enum_name: str
    attribute: str
    valid_attributes: List[str]
    message: str
    severity: str


class EnumCollector(ast.NodeVisitor):
    """Collects all Enum definitions in a file."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.enums: Dict[str, Set[str]] = {}  # enum_name -> set of valid attributes
        
        # Polytopic Integration
        self.message_bus = MessageBus()
        self.pattern_recognition = PatternRecognitionSystem(self.project_root)
        self.correlation_engine = CorrelationEngine()
        self.optimizer = OptimizationEngine()
        self.adaptive_prompts = AdaptivePromptSystem(
            self.project_root,
            self.pattern_recognition
        )
        self.dimensional_space = DimensionalSpace()
        
        # Validation tracking
        self.validation_count = 0
        self.validator_name = 'EnumAttributeValidator'

    def visit_ClassDef(self, node: ast.ClassDef):
        """Check if class is an Enum and collect its members."""
        # Check if class inherits from Enum
        is_enum = False
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == 'Enum':
                is_enum = True
                break
        
        if is_enum:
            # Collect enum members
            members = set()
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            members.add(target.id)
                elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    members.add(item.target.id)
            
            self.enums[node.name] = members
        
        self.generic_visit(node)


class EnumUsageChecker(ast.NodeVisitor):
    """Checks that Enum attributes are valid."""
    
    def __init__(self, filepath: Path, project_root: Path, all_enums: Dict[str, Set[str]]):
        self.filepath = filepath
        self.project_root = project_root
        self.all_enums = all_enums
        self.errors: List[EnumAttributeError] = []
        self.imports: Dict[str, str] = {}  # alias -> original_name
        
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track imports to resolve enum names."""
        if node.module:
            for alias in node.names:
                imported_name = alias.name
                alias_name = alias.asname if alias.asname else imported_name
                self.imports[alias_name] = imported_name
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute):
        """Check enum attribute access."""
        # Check if this is accessing an attribute on a Name (e.g., MessageType.SOMETHING)
        if isinstance(node.value, ast.Name):
            enum_name = node.value.id
            attribute = node.attr
            
            # Resolve import alias
            if enum_name in self.imports:
                enum_name = self.imports[enum_name]
            
            # Check if this is a known enum
            if enum_name in self.all_enums:
                valid_attrs = self.all_enums[enum_name]
                
                # Check if attribute exists
                if attribute not in valid_attrs:
                    # Get suggestions (similar names)
                    suggestions = self._get_suggestions(attribute, valid_attrs)
                    suggestion_text = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
                    
                    self.errors.append(EnumAttributeError(
                        file=str(self.filepath.relative_to(self.project_root)),
                        line=node.lineno,
                        enum_name=enum_name,
                        attribute=attribute,
                        valid_attributes=sorted(valid_attrs),
                        message=f"Enum '{enum_name}' has no attribute '{attribute}'.{suggestion_text}",
                        severity='critical'
                    ))
        
        self.generic_visit(node)
    
    def _get_suggestions(self, attr: str, valid_attrs: Set[str], max_suggestions: int = 3) -> List[str]:
        """Get suggestions for similar attribute names."""
        attr_lower = attr.lower()
        suggestions = []
        
        # Find attributes with similar names
        for valid_attr in valid_attrs:
            if attr_lower in valid_attr.lower() or valid_attr.lower() in attr_lower:
                suggestions.append(valid_attr)
                if len(suggestions) >= max_suggestions:
                    break
        
        return suggestions


class EnumAttributeValidator:
    """Validates that Enum attributes exist before they are accessed."""
    
    def __init__(self, project_root: str, symbol_table: Optional[SymbolTable] = None):
        self.project_root = Path(project_root)
        self.errors: List[EnumAttributeError] = []
        self.symbol_table = symbol_table
        self.all_enums: Dict[str, Set[str]] = {}
        # Polytopic Integration
        self.message_bus = MessageBus()
        self.pattern_recognition = PatternRecognitionSystem(self.project_root)
        self.correlation_engine = CorrelationEngine()
        self.optimizer = OptimizationEngine()
        self.adaptive_prompts = AdaptivePromptSystem(
            self.project_root,
            self.pattern_recognition
        )
        self.dimensional_space = DimensionalSpace()
        
        # Validation tracking
        self.validation_count = 0
        self.validator_name = 'EnumAttributeValidator'

        
    def validate_all(self) -> Dict:
        """
        Validate all enum attribute usage in the project.
        
        Returns:
            Dict with validation results
        """
        self.errors = []
        
        # Use SymbolTable if available, otherwise collect enums
        if self.symbol_table:
            self.all_enums = self.symbol_table.enums.copy()
        else:
            # Fallback: collect enums ourselves
            self._collect_enums()
        
        # Validate enum usage
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            self._validate_file(py_file)
        
        
        
        
        # Build result dict first
        result = {
            'errors': [
                {
                    'file': e.file,
                    'line': e.line,
                    'enum_name': e.enum_name,
                    'attribute': e.attribute,
                    'valid_attributes': e.valid_attributes,
                    'message': e.message,
                    'severity': e.severity
                }
                for e in self.errors
            ],
            'total_errors': len(self.errors),
            'enums_found': len(self.all_enums),
            'by_severity': self._count_by_severity()
        }
        
# Polytopic Integration: Record patterns and optimize
        self.validation_count += 1
        self._record_validation_pattern(self.errors if hasattr(self, 'errors') else [])
        self._optimize_validation(result)
        
        # Publish validation completed event
        self._publish_validation_event('validation_completed', {
            'total_errors': result.get('total_errors', 0),
            'validation_count': self.validation_count
        })
        
        
        return result

    
    def _collect_enums(self):
        """Collect all enum definitions in the project (fallback when no SymbolTable)."""
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                tree = ast.parse(source, filename=str(py_file))
                
                collector = EnumCollector(str(py_file))
                collector.visit(tree)
                
                # Merge enums from this file
                self.all_enums.update(collector.enums)
                
            except Exception as e:
                # Skip files that can't be parsed
                pass
    
    def _validate_file(self, filepath: Path):
        """Validate enum usage in a single file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=str(filepath))
            
            checker = EnumUsageChecker(filepath, self.project_root, self.all_enums)
            checker.visit(tree)
            
            self.errors.extend(checker.errors)
            
        except Exception as e:
            # Skip files that can't be parsed
            pass
    
    def _count_by_severity(self) -> Dict[str, int]:
        """Count errors by severity."""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for error in self.errors:
            counts[error.severity] = counts.get(error.severity, 0) + 1
        return counts
    
    def _publish_validation_event(self, event_type: str, payload: dict):
        """Publish validation events using existing message types."""
        message_type_map = {
            'validation_started': MessageType.SYSTEM_INFO,
            'validation_completed': MessageType.SYSTEM_INFO,
            'validation_error': MessageType.SYSTEM_WARNING,
            'validation_critical': MessageType.SYSTEM_ALERT,
            'validation_insight': MessageType.SYSTEM_INFO,
        }
        
        message_type = message_type_map.get(event_type, MessageType.SYSTEM_INFO)
        
        message = Message(
            sender=self.validator_name,
            recipient='ALL',
            message_type=message_type,
            priority=MessagePriority.NORMAL,
            payload={
                'event': event_type,
                'validator': self.validator_name,
                **payload
            }
        )
        
        self.message_bus.publish(message)
    
    def _record_validation_pattern(self, errors: list):
        """Record validation patterns for learning."""
        if not errors:
            return
        
        # Record execution data
        execution_data = {
            'phase': 'validation',
            'tool': self.validator_name,
            'success': len([e for e in errors if self._get_severity(e) == 'high']) == 0,
            'error_count': len(errors),
            'validation_count': self.validation_count
        }
        
        self.pattern_recognition.record_execution(execution_data)
        
        # Add findings to correlation engine
        for error in errors:
            component = self._get_error_file(error)
            finding = {
                'type': f'{self.validator_name}_error',
                'error_type': self._get_error_type(error),
                'severity': self._get_severity(error),
                'message': self._get_error_message(error)
            }
            
            self.correlation_engine.add_finding(component, finding)
        
        # Find correlations
        correlations = self.correlation_engine.correlate()
        
        if correlations:
            self._publish_validation_event('validation_insight', {
                'type': 'validation_correlations',
                'correlations': correlations
            })
    
    def _optimize_validation(self, result: dict):
        """Optimize validation based on results."""
        # Record quality metrics
        self.optimizer.record_quality_metric(
            f'{self.validator_name}_errors',
            result.get('total_errors', 0)
        )
        
        if 'by_severity' in result:
            self.optimizer.record_quality_metric(
                f'{self.validator_name}_high_severity',
                result.get('by_severity', {}).get('high', 0)
            )
    
    def _get_error_file(self, error):
        """Extract file path from error."""
        if isinstance(error, dict):
            return error.get('file', 'unknown')
        elif hasattr(error, 'file'):
            return error.file
        elif hasattr(error, 'filepath'):
            return error.filepath
        return 'unknown'
    
    def _get_error_type(self, error):
        """Extract error type from error."""
        if isinstance(error, dict):
            return error.get('error_type', 'unknown')
        elif hasattr(error, 'error_type'):
            return error.error_type
        elif hasattr(error, 'type'):
            return error.type
        return 'unknown'
    
    def _get_severity(self, error):
        """Extract severity from error."""
        if isinstance(error, dict):
            return error.get('severity', 'medium')
        elif hasattr(error, 'severity'):
            return error.severity
        return 'medium'
    
    def _get_error_message(self, error):
        """Extract message from error."""
        if isinstance(error, dict):
            return error.get('message', '')
        elif hasattr(error, 'message'):
            return error.message
        elif hasattr(error, 'msg'):
            return error.msg
        return str(error)

