"""
Tool Validation and Enhancement System

Provides comprehensive tool validation, effectiveness tracking, and deprecation management.

Features:
- Stricter tool creation criteria (5+ attempts)
- Parameter type validation
- Similar tool detection
- Effectiveness tracking (success rate, usage frequency)
- Performance metrics
- Automatic deprecation of unused/failed tools
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
import json
import re
import difflib

from .logging_setup import get_logger

# Polytopic Integration Imports
from pipeline.messaging.message_bus import MessageBus, Message, MessageType, MessagePriority
from pipeline.pattern_recognition import PatternRecognitionSystem
from pipeline.correlation_engine import CorrelationEngine
from pipeline.analytics.optimizer import OptimizationEngine
from pipeline.adaptive_prompts import AdaptivePromptSystem
from pipeline.polytopic.dimensional_space import DimensionalSpace



class ToolMetrics:
    """Metrics for a single tool."""
    
    def __init__(self, tool_name: str, project_root: str = "."):
        self.tool_name = tool_name
        self.project_root = project_root
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.total_execution_time = 0.0
        self.first_used = None
        self.last_used = None
        self.error_types = Counter()
        self.usage_by_phase = Counter()
    
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
        self.validator_name = 'ToolValidator'

    def record_call(self, success: bool, execution_time: float = 0.0, 
                   phase: str = None, error_type: str = None):
        """Record a tool call."""
        self.total_calls += 1
        
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
            if error_type:
                self.error_types[error_type] += 1
        
        self.total_execution_time += execution_time
        
        now = datetime.now()
        if not self.first_used:
            self.first_used = now
        self.last_used = now
        
        if phase:
            self.usage_by_phase[phase] += 1
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls
    
    @property
    def avg_execution_time(self) -> float:
        """Calculate average execution time."""
        if self.total_calls == 0:
            return 0.0
        return self.total_execution_time / self.total_calls
    
    @property
    def days_since_last_use(self) -> int:
        """Days since last use."""
        if not self.last_used:
            return 999
        return (datetime.now() - self.last_used).days
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'tool_name': self.tool_name,
            'total_calls': self.total_calls,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'success_rate': self.success_rate,
            'avg_execution_time': self.avg_execution_time,
            'first_used': self.first_used.isoformat() if self.first_used else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'days_since_last_use': self.days_since_last_use,
            'error_types': dict(self.error_types),
            'usage_by_phase': dict(self.usage_by_phase)
        }


class ToolValidator:
    """
    Enhanced tool validation and management system.
    
    Features:
    - Stricter creation criteria (5+ attempts)
    - Parameter validation
    - Similar tool detection
    - Effectiveness tracking
    - Automatic deprecation
    """
    
    def __init__(self, project_dir: Path):
        """
        Initialize tool validator.
        
        Args:
            project_dir: Project directory path
        """
        self.project_dir = project_dir
        self.logger = get_logger()
        
        # Configuration
        self.min_attempts_for_creation = 5  # Increased from 3
        self.similarity_threshold = 0.8
        self.min_success_rate = 0.2
        self.deprecation_days = 30
        
        # Metrics storage
        self.tool_metrics: Dict[str, ToolMetrics] = {}
        
        # Validation rules
        self.parameter_types = {
            'string': str,
            'integer': int,
            'number': float,
            'boolean': bool,
            'array': list,
            'object': dict
        }
        
        # Load existing metrics
        self.load_metrics()
    
    def validate_tool_creation_request(self, tool_name: str, 
                                      attempts: int,
                                      contexts: List[Dict]) -> Tuple[bool, str]:
        """
        Validate if a tool should be created.
        
        Args:
            tool_name: Name of the proposed tool
            attempts: Number of attempts to use this tool
            contexts: List of usage contexts
        
        Returns:
            Tuple of (should_create, reason)
        """
        # Check 1: Minimum attempts
        if attempts < self.min_attempts_for_creation:
            return False, f"Insufficient attempts ({attempts}/{self.min_attempts_for_creation})"
        
        # Check 2: Valid tool name
        if not self._is_valid_tool_name(tool_name):
            return False, f"Invalid tool name format: {tool_name}"
        
        # Check 3: Check for similar existing tools
        similar_tools = self.find_similar_tools(tool_name)
        if similar_tools:
            return False, f"Similar tools exist: {', '.join(similar_tools)}"
        
        # Check 4: Validate contexts are meaningful
        if not self._validate_contexts(contexts):
            return False, "Contexts are not meaningful enough"
        
        return True, "All validation checks passed"
    
    def _is_valid_tool_name(self, tool_name: str) -> bool:
        """Check if tool name follows naming conventions."""
        # Tool name should be lowercase with hyphens
        pattern = r'^[a-z][a-z0-9-]*[a-z0-9]$'
        return bool(re.match(pattern, tool_name))
    
    def _validate_contexts(self, contexts: List[Dict]) -> bool:
        """Validate that contexts provide meaningful information."""
        if len(contexts) < 3:
            return False
        
        # Check if contexts have descriptions
        descriptions = [c.get('description', '') for c in contexts]
        if not all(descriptions):
            return False
        
        # Check if descriptions are diverse (not all the same)
        unique_descriptions = set(descriptions)
        if len(unique_descriptions) < 2:
            return False
        
        return True
    
    def find_similar_tools(self, tool_name: str, 
                          existing_tools: List[str] = None) -> List[str]:
        """
        Find tools with similar names.
        
        Args:
            tool_name: Name to check
            existing_tools: List of existing tool names (optional)
        
        Returns:
            List of similar tool names
        """
        if existing_tools is None:
            pass
            # Load from tool registry if available
            existing_tools = self._get_existing_tools()
        
        similar = []
        for existing in existing_tools:
            similarity = difflib.SequenceMatcher(None, tool_name, existing).ratio()
            if similarity >= self.similarity_threshold:
                similar.append(existing)
        
        return similar
    
    def _get_existing_tools(self) -> List[str]:
        """Get list of existing tool names from tool registry."""
        try:
            from pipeline.tool_registry import ToolRegistry
            
            registry = ToolRegistry()
            return registry.get_all_tool_names()
        except Exception:
            pass
            # If registry not available, return empty list
            return []
    
    def validate_parameters(self, parameters: Dict) -> Tuple[bool, List[str]]:
        """
        Validate tool parameters.
        
        Args:
            parameters: Parameter specification
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        for param_name, param_spec in parameters.items():
            pass
            # Check parameter name format
            if not re.match(r'^[a-z_][a-z0-9_]*$', param_name):
                errors.append(f"Invalid parameter name: {param_name}")
            
            # Check parameter has type
            if 'type' not in param_spec:
                errors.append(f"Parameter {param_name} missing type")
                continue
            
            # Check type is valid
            param_type = param_spec['type']
            if param_type not in self.parameter_types:
                errors.append(f"Invalid type for {param_name}: {param_type}")
            
            # Check parameter has description
            if 'description' not in param_spec:
                errors.append(f"Parameter {param_name} missing description")
        
        return len(errors) == 0, errors
    
    def record_tool_usage(self, tool_name: str, success: bool,
                         execution_time: float = 0.0,
                         phase: str = None,
                         error_type: str = None):
        """
        Record tool usage for effectiveness tracking.
        
        Args:
            tool_name: Name of the tool
            success: Whether the call was successful
            execution_time: Execution time in seconds
            phase: Phase where tool was used
            error_type: Type of error if failed
        """
        if tool_name not in self.tool_metrics:
            self.tool_metrics[tool_name] = ToolMetrics(tool_name)
        
        self.tool_metrics[tool_name].record_call(
            success=success,
            execution_time=execution_time,
            phase=phase,
            error_type=error_type
        )
        
    
    def get_tool_effectiveness(self, tool_name: str) -> Optional[Dict]:
        """
        Get effectiveness metrics for a tool.
        
        Args:
            tool_name: Name of the tool
        
        Returns:
            Dictionary with effectiveness metrics or None
        """
        if tool_name not in self.tool_metrics:
            return None
        
        return self.tool_metrics[tool_name].to_dict()
    
    def get_all_tool_metrics(self) -> Dict[str, Dict]:
        """Get metrics for all tools."""
        return {
            name: metrics.to_dict()
            for name, metrics in self.tool_metrics.items()
        }
    
    def identify_deprecated_tools(self) -> List[Tuple[str, str]]:
        """
        Identify tools that should be deprecated.
        
        Returns:
            List of (tool_name, reason) tuples
        """
        deprecated = []
        
        for tool_name, metrics in self.tool_metrics.items():
            pass
            # Reason 1: Unused for too long
            if metrics.days_since_last_use > self.deprecation_days:
                deprecated.append((
                    tool_name,
                    f"Unused for {metrics.days_since_last_use} days"
                ))
                continue
            
            # Reason 2: Low success rate with sufficient data
            if metrics.total_calls >= 10 and metrics.success_rate < self.min_success_rate:
                deprecated.append((
                    tool_name,
                    f"Low success rate: {metrics.success_rate:.1%}"
                ))
                continue
        
        return deprecated
    
    def get_tool_recommendations(self) -> Dict[str, List[str]]:
        """
        Get recommendations for tool improvements.
        
        Returns:
            Dictionary with recommendations by category
        """
        recommendations = {
            'high_performers': [],
            'needs_improvement': [],
            'deprecated': [],
            'underutilized': []
        }
        
        for tool_name, metrics in self.tool_metrics.items():
            pass
            # High performers
            if metrics.success_rate > 0.9 and metrics.total_calls >= 10:
                recommendations['high_performers'].append(tool_name)
            
            # Needs improvement
            elif 0.5 <= metrics.success_rate <= 0.9 and metrics.total_calls >= 5:
                recommendations['needs_improvement'].append(tool_name)
            
            # Deprecated
            elif metrics.success_rate < self.min_success_rate and metrics.total_calls >= 10:
                recommendations['deprecated'].append(tool_name)
            
            # Underutilized
            elif metrics.total_calls < 5 and metrics.days_since_last_use < 30:
                recommendations['underutilized'].append(tool_name)
        
        return recommendations
    
    def generate_effectiveness_report(self) -> str:
        """
        Generate a comprehensive effectiveness report.
        
        Returns:
            Formatted report string
        """
        report = ["# Tool Effectiveness Report", ""]
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Total Tools Tracked: {len(self.tool_metrics)}")
        report.append("")
        
        # Summary statistics
        if self.tool_metrics:
            total_calls = sum(m.total_calls for m in self.tool_metrics.values())
            avg_success_rate = sum(m.success_rate for m in self.tool_metrics.values()) / len(self.tool_metrics)
            
            report.append("## Summary Statistics")
            report.append(f"- Total Tool Calls: {total_calls}")
            report.append(f"- Average Success Rate: {avg_success_rate:.1%}")
            report.append("")
        
        # Recommendations
        recommendations = self.get_tool_recommendations()
        
        report.append("## Recommendations")
        report.append("")
        
        if recommendations['high_performers']:
            report.append("### High Performers ✅")
            for tool in recommendations['high_performers']:
                metrics = self.tool_metrics[tool]
                report.append(f"- **{tool}**: {metrics.success_rate:.1%} success rate, {metrics.total_calls} calls")
            report.append("")
        
        if recommendations['needs_improvement']:
            report.append("### Needs Improvement ⚠️")
            for tool in recommendations['needs_improvement']:
                metrics = self.tool_metrics[tool]
                report.append(f"- **{tool}**: {metrics.success_rate:.1%} success rate, {metrics.total_calls} calls")
            report.append("")
        
        if recommendations['deprecated']:
            report.append("### Deprecated ❌")
            for tool in recommendations['deprecated']:
                metrics = self.tool_metrics[tool]
                report.append(f"- **{tool}**: {metrics.success_rate:.1%} success rate, {metrics.total_calls} calls")
            report.append("")
        
        if recommendations['underutilized']:
            report.append("### Underutilized 📊")
            for tool in recommendations['underutilized']:
                metrics = self.tool_metrics[tool]
                report.append(f"- **{tool}**: {metrics.total_calls} calls, last used {metrics.days_since_last_use} days ago")
            report.append("")
        
        # Detailed metrics
        report.append("## Detailed Metrics")
        report.append("")
        
        for tool_name in sorted(self.tool_metrics.keys()):
            metrics = self.tool_metrics[tool_name]
            report.append(f"### {tool_name}")
            report.append(f"- Total Calls: {metrics.total_calls}")
            report.append(f"- Success Rate: {metrics.success_rate:.1%}")
            report.append(f"- Avg Execution Time: {metrics.avg_execution_time:.3f}s")
            report.append(f"- Last Used: {metrics.days_since_last_use} days ago")
            if metrics.error_types:
                report.append(f"- Common Errors: {dict(metrics.error_types)}")
            report.append("")
        
        return "\n".join(report)
    
    def save_metrics(self):
        """Save metrics to disk."""
        metrics_file = self.project_dir / '.pipeline' / 'tool_metrics.json'
        metrics_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'metrics': {
                name: metrics.to_dict()
                for name, metrics in self.tool_metrics.items()
            },
            'config': {
                'min_attempts_for_creation': self.min_attempts_for_creation,
                'similarity_threshold': self.similarity_threshold,
                'min_success_rate': self.min_success_rate,
                'deprecation_days': self.deprecation_days
            },
            'last_updated': datetime.now().isoformat()
        }
        
        with open(metrics_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"💾 Saved metrics for {len(self.tool_metrics)} tools")
    
    def load_metrics(self):
        """Load metrics from disk."""
        metrics_file = self.project_dir / '.pipeline' / 'tool_metrics.json'
        
        if not metrics_file.exists():
            return
        
        try:
            with open(metrics_file, 'r') as f:
                data = json.load(f)
            
            # Load metrics
            for tool_name, metrics_data in data.get('metrics', {}).items():
                metrics = ToolMetrics(tool_name)
                metrics.total_calls = metrics_data['total_calls']
                metrics.successful_calls = metrics_data['successful_calls']
                metrics.failed_calls = metrics_data['failed_calls']
                metrics.total_execution_time = metrics_data.get('avg_execution_time', 0) * metrics_data['total_calls']
                
                if metrics_data.get('first_used'):
                    metrics.first_used = datetime.fromisoformat(metrics_data['first_used'])
                if metrics_data.get('last_used'):
                    metrics.last_used = datetime.fromisoformat(metrics_data['last_used'])
                
                metrics.error_types = Counter(metrics_data.get('error_types', {}))
                metrics.usage_by_phase = Counter(metrics_data.get('usage_by_phase', {}))
                
                self.tool_metrics[tool_name] = metrics
            
            # Load config
            config = data.get('config', {})
            self.min_attempts_for_creation = config.get('min_attempts_for_creation', 5)
            self.similarity_threshold = config.get('similarity_threshold', 0.8)
            self.min_success_rate = config.get('min_success_rate', 0.2)
            self.deprecation_days = config.get('deprecation_days', 30)
            
            self.logger.info(f"📂 Loaded metrics for {len(self.tool_metrics)} tools")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load metrics: {e}")
    
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

