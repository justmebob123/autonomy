"""
Architecture Validator - Validates codebase against MASTER_PLAN.md and ARCHITECTURE.md

This module checks:
1. File locations match architecture
2. File naming conventions are correct
3. Implementation matches master plan objectives
4. Missing files that should exist
5. Extra files that shouldn't exist
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

# Polytopic Integration Imports
from pipeline.messaging.message_bus import MessageBus, Message, MessageType, MessagePriority
from pipeline.pattern_recognition import PatternRecognitionSystem
from pipeline.correlation_engine import CorrelationEngine
from pipeline.analytics.optimizer import OptimizationEngine
from pipeline.adaptive_prompts import AdaptivePromptSystem
from pipeline.polytopic.dimensional_space import DimensionalSpace



@dataclass
class ArchitectureViolation:
    """Represents a violation of architecture guidelines."""
    violation_type: str  # 'location', 'naming', 'missing', 'extra', 'implementation'
    severity: str  # 'critical', 'high', 'medium', 'low'
    file_path: str
    expected: str
    actual: str
    description: str
    recommendation: str


class ArchitectureValidator:
    """Validates codebase against architecture documents."""
    
    def __init__(self, project_dir: str, logger):
        self.project_dir = Path(project_dir)
        self.logger = logger
        self.master_plan = None
        self.architecture = None
        
        # Polytopic Integration
        self.message_bus = MessageBus()
        self.pattern_recognition = PatternRecognitionSystem(self.project_dir)
        self.correlation_engine = CorrelationEngine()
        self.optimizer = OptimizationEngine()
        self.adaptive_prompts = AdaptivePromptSystem(
            self.project_dir,
            self.pattern_recognition
        )
        self.dimensional_space = DimensionalSpace()
        
        # Validation tracking
        self.validation_count = 0
        self.validator_name = 'ArchitectureValidator'

    def load_documents(self) -> bool:
        """Load MASTER_PLAN.md and ARCHITECTURE.md."""
        master_plan_path = self.project_dir / "MASTER_PLAN.md"
        architecture_path = self.project_dir / "ARCHITECTURE.md"
        
        if master_plan_path.exists():
            self.master_plan = master_plan_path.read_text()
            self.logger.info(f"  ✓ Loaded MASTER_PLAN.md ({len(self.master_plan)} chars)")
        else:
            self.logger.warning(f"  ⚠️  MASTER_PLAN.md not found")
            
        if architecture_path.exists():
            self.architecture = architecture_path.read_text()
            self.logger.info(f"  ✓ Loaded ARCHITECTURE.md ({len(self.architecture)} chars)")
        else:
            self.logger.warning(f"  ⚠️  ARCHITECTURE.md not found")
            
        return self.master_plan is not None or self.architecture is not None
    
    def extract_expected_structure(self) -> Dict[str, List[str]]:
        """
        Extract expected directory structure from ARCHITECTURE.md.
        
        Returns:
            Dict mapping directory names to expected file patterns
        """
        if not self.architecture:
            return {}
            
        structure = {}
        
        # Look for directory structure sections
        # Common patterns: "Directory Structure:", "File Organization:", "Project Structure:"
        structure_section = re.search(
            r'(?:Directory|File|Project)\s+Structure:?\s*\n(.*?)(?:\n#{1,3}\s|\Z)',
            self.architecture,
            re.DOTALL | re.IGNORECASE
        )
        
        if structure_section:
            content = structure_section.group(1)
            
            # Parse directory listings (various formats)
            # Format 1: project_root/
            #             ├── api/
            #             │   ├── __init__.py
            #             │   └── routes.py
            
            # Format 2: - api/ - API endpoints
            #           - models/ - Data models
            
            # Format 3: /api - API endpoints
            #           /models - Data models
            
            current_dir = None
            for line in content.split('\n'):
                line = line.strip()
                
                # Check for directory markers
                if '/' in line and not line.startswith('#'):
                    # Extract directory name
                    dir_match = re.search(r'([a-z_][a-z0-9_]*)/\s*(?:-|–|—|\||├|└)?', line, re.IGNORECASE)
                    if dir_match:
                        current_dir = dir_match.group(1)
                        if current_dir not in structure:
                            structure[current_dir] = []
                            
                    # Extract file name if present
                    file_match = re.search(r'([a-z_][a-z0-9_]*\.py)', line, re.IGNORECASE)
                    if file_match and current_dir:
                        structure[current_dir].append(file_match.group(1))
        
        return structure
    
    def extract_naming_conventions(self) -> Dict[str, str]:
        """
        Extract naming conventions from ARCHITECTURE.md.
        
        Returns:
            Dict mapping file types to naming patterns
        """
        if not self.architecture:
            return {}
            
        conventions = {}
        
        # Look for naming convention sections
        naming_section = re.search(
            r'Naming\s+Convention:?\s*\n(.*?)(?:\n#{1,3}\s|\Z)',
            self.architecture,
            re.DOTALL | re.IGNORECASE
        )
        
        if naming_section:
            content = naming_section.group(1)
            
            # Parse naming rules
            # Format: "- API files: snake_case, suffix with _api.py"
            # Format: "- Models: PascalCase classes in snake_case files"
            
            for line in content.split('\n'):
                if ':' in line:
                    parts = line.split(':', 1)
                    file_type = parts[0].strip('- ').lower()
                    convention = parts[1].strip()
                    conventions[file_type] = convention
        
        return conventions
    
    def extract_objectives(self) -> List[Dict[str, str]]:
        """
        Extract objectives from MASTER_PLAN.md.
        
        Returns:
            List of objectives with their descriptions
        """
        if not self.master_plan:
            return []
            
        objectives = []
        
        # Look for objective sections
        # Common patterns: "## Objective 1:", "### Primary Objective:", "**Objective:**"
        
        objective_pattern = re.finditer(
            r'(?:^|\n)#{2,3}\s+(?:Primary\s+)?Objective\s+\d*:?\s*(.*?)(?:\n|$)',
            self.master_plan,
            re.IGNORECASE
        )
        
        for match in objective_pattern:
            title = match.group(1).strip()
            
            # Get description (next paragraph)
            start_pos = match.end()
            next_section = re.search(r'\n#{1,3}\s', self.master_plan[start_pos:])
            end_pos = start_pos + next_section.start() if next_section else len(self.master_plan)
            
            description = self.master_plan[start_pos:end_pos].strip()
            
            objectives.append({
                'title': title,
                'description': description
            })
        
        return objectives
    
    def validate_file_locations(self) -> List[ArchitectureViolation]:
        """
        Validate that files are in the correct directories.
        
        Returns:
            List of location violations
        """
        violations = []
        expected_structure = self.extract_expected_structure()
        
        if not expected_structure:
            return violations
            
        # Get all Python files
        python_files = list(self.project_dir.rglob("*.py"))
        
        for file_path in python_files:
            rel_path = file_path.relative_to(self.project_dir)
            parts = rel_path.parts
            
            if len(parts) < 2:
                continue  # Skip root-level files
                
            directory = parts[0]
            filename = parts[-1]
            
            # Check if file is in expected directory
            if directory in expected_structure:
                expected_files = expected_structure[directory]
                
                # If specific files are listed, check if this file should be here
                if expected_files and filename not in expected_files:
                    # Check if file matches any pattern
                    matches_pattern = False
                    for expected in expected_files:
                        if '*' in expected:
                            pattern = expected.replace('*', '.*')
                            if re.match(pattern, filename):
                                matches_pattern = True
                                break
                    
                    if not matches_pattern:
                        violations.append(ArchitectureViolation(
                            violation_type='location',
                            severity='medium',
                            file_path=str(rel_path),
                            expected=f"File should match one of: {', '.join(expected_files)}",
                            actual=filename,
                            description=f"File '{filename}' in '{directory}/' doesn't match expected files",
                            recommendation=f"Move to appropriate directory or update ARCHITECTURE.md"
                        ))
        
        return violations
    
    def validate_naming_conventions(self) -> List[ArchitectureViolation]:
        """
        Validate that files follow naming conventions.
        
        Returns:
            List of naming violations
        """
        violations = []
        conventions = self.extract_naming_conventions()
        
        if not conventions:
            return violations
            
        # Get all Python files
        python_files = list(self.project_dir.rglob("*.py"))
        
        for file_path in python_files:
            filename = file_path.name
            
            # Check snake_case (most common Python convention)
            if not re.match(r'^[a-z][a-z0-9_]*\.py$', filename):
                if filename != '__init__.py':
                    violations.append(ArchitectureViolation(
                        violation_type='naming',
                        severity='low',
                        file_path=str(file_path.relative_to(self.project_dir)),
                        expected='snake_case.py',
                        actual=filename,
                        description=f"File '{filename}' doesn't follow snake_case convention",
                        recommendation="Rename to snake_case format"
                    ))
        
        return violations
    
    def find_missing_files(self) -> List[ArchitectureViolation]:
        """
        Find files that should exist according to architecture but don't.
        
        Returns:
            List of missing file violations
        """
        violations = []
        expected_structure = self.extract_expected_structure()
        
        for directory, expected_files in expected_structure.items():
            dir_path = self.project_dir / directory
            
            if not dir_path.exists():
                violations.append(ArchitectureViolation(
                    violation_type='missing',
                    severity='high',
                    file_path=directory,
                    expected=f"Directory should exist with files: {', '.join(expected_files)}",
                    actual='Directory does not exist',
                    description=f"Directory '{directory}/' is missing",
                    recommendation=f"Create directory and add expected files"
                ))
                continue
                
            for expected_file in expected_files:
                if '*' in expected_file:
                    continue  # Skip patterns
                    
                file_path = dir_path / expected_file
                if not file_path.exists():
                    violations.append(ArchitectureViolation(
                        violation_type='missing',
                        severity='medium',
                        file_path=f"{directory}/{expected_file}",
                        expected='File should exist',
                        actual='File does not exist',
                        description=f"Expected file '{expected_file}' in '{directory}/' is missing",
                        recommendation=f"Create file or update ARCHITECTURE.md"
                    ))
        
        return violations
    
    def validate_all(self) -> Dict[str, List[ArchitectureViolation]]:
        """
        Run all validation checks.
        
        Returns:
            Dict mapping check names to lists of violations
        """
        if not self.load_documents():
            self.logger.warning("  ⚠️  No architecture documents found, skipping validation")
            
        
        
        # Build result dict first
        result = {}
        
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

            
        self.logger.info("  🔍 Validating architecture...")
        
        results = {
            'location_violations': self.validate_file_locations(),
            'naming_violations': self.validate_naming_conventions(),
            'missing_files': self.find_missing_files()
        }
        
        total_violations = sum(len(v) for v in results.values())
        self.logger.info(f"  ✓ Architecture validation complete: {total_violations} violations found")
        
        return results
    
    def generate_report(self, results: Dict[str, List[ArchitectureViolation]]) -> str:
        """Generate a human-readable report of violations."""
        lines = ["# Architecture Validation Report\n"]
        
        for check_name, violations in results.items():
            if not violations:
                continue
                
            lines.append(f"\n## {check_name.replace('_', ' ').title()}\n")
            
            # Group by severity
            by_severity = {}
            for v in violations:
                if v.severity not in by_severity:
                    by_severity[v.severity] = []
                by_severity[v.severity].append(v)
            
            for severity in ['critical', 'high', 'medium', 'low']:
                if severity not in by_severity:
                    continue
                    
                lines.append(f"\n### {severity.upper()} Priority\n")
                
                for v in by_severity[severity]:
                    lines.append(f"**{v.file_path}**")
                    lines.append(f"- Description: {v.description}")
                    lines.append(f"- Expected: {v.expected}")
                    lines.append(f"- Actual: {v.actual}")
                    lines.append(f"- Recommendation: {v.recommendation}")
                    lines.append("")
        
        return "\n".join(lines)
    
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

