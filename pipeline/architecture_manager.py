"""
Architecture Manager - Central system for managing ARCHITECTURE.md

This module provides a unified interface for reading, updating, and maintaining
the project's ARCHITECTURE.md file, which serves as the source of truth for:
- Project structure and organization
- Component definitions and responsibilities
- Integration guidelines
- Design patterns and conventions
- Architectural changes history

Enhanced with validation tool integration for comprehensive architecture analysis.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
import ast

from .architecture_analysis import (
    ArchitectureAnalysis,
    ValidationReport,
    ArchitectureDiff,
    ComponentInfo,
    IntegrationStatus,
    QualityMetrics,
    CallGraphSubset,
    PlacementValidation,
    PlacementIssue,
    IntegrationGap,
    NamingViolation,
    ComponentChange,
    ComponentMove,
    ValidationSeverity
)


class ArchitectureManager:
    """
    Manages ARCHITECTURE.md as the central source of truth.
    
    All phases must:
    1. Read architecture before making decisions
    2. Update architecture after structural changes
    3. Record architectural changes for tracking
    """
    
    def __init__(self, project_dir: Path, logger=None):
        self.project_dir = Path(project_dir)
        self.arch_file = self.project_dir / "ARCHITECTURE.md"
        self.logger = logger
        
        # Lazy-load validator coordinator (only when needed)
        self._validator = None
        self._last_analysis = None
        self._last_analysis_time = None
        
    def read_architecture(self) -> Dict[str, Any]:
        """
        Read and parse ARCHITECTURE.md into structured data.
        
        Returns:
            Dict containing:
            - structure: Project structure definition
            - components: Component definitions
            - conventions: Naming and coding conventions
            - guidelines: Integration and design guidelines
            - history: Recent architectural changes
        """
        if not self.arch_file.exists():
            if self.logger:
                self.logger.warning(f"⚠️  ARCHITECTURE.md not found, creating template")
            self._create_template()
            return self._get_empty_architecture()
        
        try:
            content = self.arch_file.read_text(encoding='utf-8')
            return self._parse_architecture(content)
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to read ARCHITECTURE.md: {e}")
            return self._get_empty_architecture()
    
    def _parse_architecture(self, content: str) -> Dict[str, Any]:
        """Parse ARCHITECTURE.md content into structured data."""
        architecture = {
            'structure': self._extract_section(content, 'Project Structure'),
            'components': self._extract_section(content, 'Components'),
            'conventions': self._extract_section(content, 'Naming Conventions'),
            'guidelines': self._extract_section(content, 'Integration Guidelines'),
            'history': self._extract_section(content, 'Change History'),
            'raw_content': content
        }
        
        return architecture
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a section from markdown content."""
        # Match ## Section Name through next ## or end of file
        pattern = rf'##\s+{re.escape(section_name)}.*?\n(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return ""
    
    def _get_empty_architecture(self) -> Dict[str, Any]:
        """Return empty architecture structure."""
        return {
            'structure': '',
            'components': '',
            'conventions': '',
            'guidelines': '',
            'history': '',
            'raw_content': ''
        }
    
    def update_section(self, section_name: str, content: str):
        """
        Update a specific section in ARCHITECTURE.md.
        
        Args:
            section_name: Name of section (e.g., "Project Structure")
            content: New content for the section
        """
        if not self.arch_file.exists():
            self._create_template()
        
        try:
            current_content = self.arch_file.read_text(encoding='utf-8')
            
            # Find and replace section
            pattern = rf'(##\s+{re.escape(section_name)}.*?\n)(.*?)(?=\n##|\Z)'
            
            def replace_section(match):
                return match.group(1) + content + '\n\n'
            
            updated_content = re.sub(
                pattern,
                replace_section,
                current_content,
                flags=re.IGNORECASE | re.DOTALL
            )
            
            # If section wasn't found, append it
            if updated_content == current_content:
                updated_content += f"\n\n## {section_name}\n\n{content}\n"
            
            self.arch_file.write_text(updated_content, encoding='utf-8')
            
            if self.logger:
                self.logger.info(f"✅ Updated ARCHITECTURE.md section: {section_name}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to update ARCHITECTURE.md: {e}")
    
    def add_component(self, name: str, description: str, location: str, 
                     responsibilities: List[str] = None):
        """
        Add a new component to the architecture.
        
        Args:
            name: Component name
            description: Component description
            location: File/directory location
            responsibilities: List of component responsibilities
        """
        # Read current components section
        arch = self.read_architecture()
        components_section = arch.get('components', '')
        
        # Create component entry
        component_entry = f"""
### {name}

**Location**: `{location}`

**Description**: {description}
"""
        
        if responsibilities:
            component_entry += "\n**Responsibilities**:\n"
            for resp in responsibilities:
                component_entry += f"- {resp}\n"
        
        component_entry += f"\n**Added**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # Append to components section
        updated_components = components_section + "\n" + component_entry
        self.update_section("Components", updated_components)
    
    def record_change(self, phase: str, change_type: str, details: Dict):
        """
        Record an architectural change in the history.
        
        Args:
            phase: Phase that made the change
            change_type: Type of change (e.g., "component_added", "structure_modified")
            details: Dictionary with change details
        """
        # Read current history
        arch = self.read_architecture()
        history_section = arch.get('history', '')
        
        # Create change entry
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        change_entry = f"""
### {timestamp} - {phase.title()} Phase

**Change Type**: {change_type}

**Details**:
"""
        
        for key, value in details.items():
            if isinstance(value, list):
                change_entry += f"- **{key}**: {', '.join(str(v) for v in value)}\n"
            else:
                change_entry += f"- **{key}**: {value}\n"
        
        # Prepend to history (most recent first)
        updated_history = change_entry + "\n" + history_section
        
        # Keep only last 20 changes to prevent bloat
        history_entries = updated_history.split('###')
        if len(history_entries) > 21:  # 1 empty + 20 entries
            history_entries = history_entries[:21]
            updated_history = '###'.join(history_entries)
        
        self.update_section("Change History", updated_history)
    
    def record_file_placement(self, file_path: str, rationale: str):
        """
        Record why a file was placed in a specific location.
        
        Args:
            file_path: Path to the file
            rationale: Explanation of placement decision
        """
        self.record_change(
            phase="system",
            change_type="file_placement",
            details={
                'file': file_path,
                'rationale': rationale
            }
        )
    
    def get_component_location(self, component_type: str) -> Optional[str]:
        """
        Get the expected location for a component type.
        
        Args:
            component_type: Type of component (e.g., "model", "service", "util")
            
        Returns:
            Expected directory path or None if not defined
        """
        arch = self.read_architecture()
        structure = arch.get('structure', '')
        
        # Look for patterns like:
        # - models/ - Database models
        # - services/ - Business logic
        
        pattern = rf'-\s+(\S+/)\s+-\s+.*{re.escape(component_type)}'
        match = re.search(pattern, structure, re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        return None
    
    def validate_file_location(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        Validate if a file is in the correct location according to architecture.
        
        Args:
            file_path: Path to the file
            file_type: Type of file (e.g., "model", "service", "test")
            
        Returns:
            Dict with:
            - valid: bool
            - expected_location: str
            - current_location: str
            - suggestion: str
        """
        expected_location = self.get_component_location(file_type)
        current_location = str(Path(file_path).parent)
        
        if not expected_location:
            return {
                'valid': True,  # Can't validate if no rule defined
                'expected_location': 'Not defined in architecture',
                'current_location': current_location,
                'suggestion': 'Define architecture rules for this component type'
            }
        
        # Check if current location matches expected
        valid = expected_location.rstrip('/') in current_location
        
        return {
            'valid': valid,
            'expected_location': expected_location,
            'current_location': current_location,
            'suggestion': f"Move to {expected_location}" if not valid else "Location is correct"
        }
    
    def _create_template(self):
        """Create ARCHITECTURE.md template if it doesn't exist."""
        template = f"""# Project Architecture

> **Purpose**: Define project structure, naming conventions, and integration guidelines
> **Updated By**: All phases (record changes here)
> **Read By**: All phases (before making decisions)
> **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Project Structure

### Directory Organization

Define your project's directory structure here. Example:

- `app/` - Main application code
  - `models/` - Database models and data structures
  - `services/` - Business logic and services
  - `controllers/` - Request handlers and controllers
  - `utils/` - Utility functions and helpers
- `tests/` - Test files
- `docs/` - Documentation

### Library vs Application Code

**Library Directories**: Reusable code meant to be imported
- Define your library directories here

**Application Directories**: Application-specific code
- Define your application directories here

## Components

Define major components of your system here.

### Example Component

**Location**: `app/services/`

**Description**: Business logic services

**Responsibilities**:
- Handle business logic
- Coordinate between models and controllers
- Implement core functionality

## Naming Conventions

### File Naming
- **Preferred**: `snake_case.py` with descriptive names
- **Example**: `user_service.py`, `data_processor.py`

### Class Naming
- **Standard**: `PascalCase`
- **Example**: `UserService`, `DataProcessor`

### Function Naming
- **Standard**: `snake_case`
- **Example**: `process_data()`, `get_user()`

## Integration Guidelines

### Duplicate Detection Rules
- Files with similar names in different directories may indicate duplication
- Action: Flag as integration conflict for review

### Dead Code Review Rules
- Library code may appear unused if not yet integrated
- Don't delete library code without review
- Mark for integration review instead

### Import Conventions
- Use absolute imports for clarity
- Group imports: standard library, third-party, local

## Change History

Recent architectural changes will be recorded here automatically by phases.

---
*This document is the source of truth for project architecture. All phases must read and update it.*
"""
        
        try:
            self.arch_file.write_text(template, encoding='utf-8')
            if self.logger:
                self.logger.info("✅ Created ARCHITECTURE.md template")
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to create ARCHITECTURE.md: {e}")
    
    # ========== VALIDATION TOOL INTEGRATION ==========
    
    @property
    def validator(self):
        """Lazy-load validator coordinator"""
        if self._validator is None:
            from .analysis.validator_coordinator import ValidatorCoordinator
            self._validator = ValidatorCoordinator(
                project_root=str(self.project_dir),
                logger=self.logger
            )
        return self._validator
    
    def analyze_current_architecture(self, force_refresh: bool = False) -> ArchitectureAnalysis:
        """
        Analyze current codebase using validation tools.
        
        Args:
            force_refresh: Force re-analysis even if cached
            
        Returns:
            ArchitectureAnalysis with:
            - Component structure (from symbol_table)
            - Call graph (from call_graph)
            - Integration status (from validators)
            - Code quality metrics (from complexity analyzer)
        """
        # Check cache (5 minute TTL)
        if not force_refresh and self._last_analysis and self._last_analysis_time:
            age = (datetime.now() - self._last_analysis_time).total_seconds()
            if age < 300:  # 5 minutes
                if self.logger:
                    self.logger.debug(f"  📦 Using cached architecture analysis ({age:.0f}s old)")
                return self._last_analysis
        
        if self.logger:
            self.logger.info("  🔍 Analyzing current architecture...")
        
        # Run all validators
        results = self.validator.validate_all()
        
        # Extract architecture information
        symbol_table = self.validator.symbol_table
        
        # Build component map
        components = self._build_component_map(symbol_table)
        
        # Get call graph
        call_graph = self._extract_call_graph(symbol_table)
        
        # Get integration status
        integration = self._calculate_integration_status(symbol_table, results)
        
        # Get quality metrics
        quality = self._extract_quality_metrics(results)
        
        # Extract validation errors
        validation_errors = []
        for validator_name, validator_results in results.items():
            if isinstance(validator_results, dict) and 'errors' in validator_results:
                for error in validator_results['errors']:
                    validation_errors.append({
                        'validator': validator_name,
                        'error': error
                    })
        
        analysis = ArchitectureAnalysis(
            timestamp=datetime.now(),
            components=components,
            call_graph=call_graph,
            integration_status=integration,
            quality_metrics=quality,
            validation_errors=validation_errors
        )
        
        # Cache result
        self._last_analysis = analysis
        self._last_analysis_time = datetime.now()
        
        if self.logger:
            self.logger.info(f"  ✅ Analysis complete: {len(components)} components, {len(validation_errors)} errors")
        
        return analysis
    
    def _build_component_map(self, symbol_table) -> Dict[str, ComponentInfo]:
        """Build component map from symbol table"""
        components = {}
        
        # Group by module/package
        for class_name, class_info in symbol_table.classes.items():
            # Extract module name (e.g., 'pipeline.phases.planning' from 'pipeline.phases.planning.PlanningPhase')
            parts = class_name.split('.')
            if len(parts) > 1:
                module = '.'.join(parts[:-1])
            else:
                module = 'root'
            
            if module not in components:
                components[module] = ComponentInfo(
                    name=module,
                    path=class_info.file,
                    classes=[],
                    functions=[],
                    dependencies=[],
                    dependents=[]
                )
            
            components[module].classes.append(class_name)
        
        # Add functions
        for func_name, func_info in symbol_table.functions.items():
            # Extract module name
            parts = func_name.split('.')
            if len(parts) > 1:
                module = '.'.join(parts[:-1])
            else:
                module = 'root'
            
            if module not in components:
                components[module] = ComponentInfo(
                    name=module,
                    path=func_info.file,
                    classes=[],
                    functions=[],
                    dependencies=[],
                    dependents=[]
                )
            
            components[module].functions.append(func_name)
        
        # Calculate dependencies from call graph
        for caller, callees in symbol_table.call_graph.items():
            caller_module = '.'.join(caller.split('.')[:-1]) if '.' in caller else 'root'
            
            for callee in callees:
                callee_module = '.'.join(callee.split('.')[:-1]) if '.' in callee else 'root'
                
                if caller_module != callee_module:
                    if caller_module in components and callee_module not in components[caller_module].dependencies:
                        components[caller_module].dependencies.append(callee_module)
                    
                    if callee_module in components and caller_module not in components[callee_module].dependents:
                        components[callee_module].dependents.append(caller_module)
        
        return components
    
    def _extract_call_graph(self, symbol_table):
        """Extract call graph from symbol table"""
        # Return the call graph result from symbol table
        from .analysis.call_graph import CallGraphResult
        
        return CallGraphResult(
            functions=symbol_table.functions,
            calls=symbol_table.call_graph,
            called_by=symbol_table.reverse_call_graph
        )
    
    def _calculate_integration_status(self, symbol_table, validation_results) -> Dict[str, IntegrationStatus]:
        """Calculate integration status per component"""
        integration_status = {}
        
        # Get integration gaps from validation results
        gaps = validation_results.get('method_existence', {}).get('errors', [])
        
        # Group by component
        for class_name, class_info in symbol_table.classes.items():
            module = '.'.join(class_name.split('.')[:-1]) if '.' in class_name else 'root'
            
            if module not in integration_status:
                # Check if class is used
                is_used = class_name in symbol_table.reverse_call_graph
                
                # Find missing integrations
                missing = []
                unused_classes = []
                
                if not is_used:
                    unused_classes.append(class_name)
                
                # Calculate integration score (0-1)
                total_methods = len(class_info.methods)
                used_methods = sum(1 for m in class_info.methods.values() 
                                 if f"{class_name}.{m.name}" in symbol_table.reverse_call_graph)
                
                score = used_methods / total_methods if total_methods > 0 else 0.0
                
                integration_status[module] = IntegrationStatus(
                    component=module,
                    is_integrated=is_used,
                    missing_integrations=missing,
                    unused_classes=unused_classes,
                    integration_score=score
                )
        
        return integration_status
    
    def _extract_quality_metrics(self, validation_results) -> Dict[str, QualityMetrics]:
        """Extract quality metrics from validation results"""
        quality_metrics = {}
        
        # Get complexity data if available
        # Get dead code data if available
        # Get validation errors
        
        # For now, return empty metrics
        # This can be enhanced when complexity analyzer is integrated
        
        return quality_metrics
    
    def validate_architecture_consistency(self, intended_arch: Optional[Dict] = None) -> ValidationReport:
        """
        Compare intended vs current architecture.
        
        Args:
            intended_arch: Intended architecture (if None, read from MASTER_PLAN.md)
            
        Returns:
            ValidationReport with:
            - Missing components
            - Extra components
            - Misplaced components
            - Integration gaps
            - Naming violations
        """
        if self.logger:
            self.logger.info("  🔍 Validating architecture consistency...")
        
        # Get current architecture
        current = self.analyze_current_architecture()
        
        # Get intended architecture
        if intended_arch is None:
            intended_arch = self._read_intended_architecture()
        
        # Compare
        missing_components = []
        extra_components = []
        misplaced_components = []
        integration_gaps = []
        naming_violations = []
        
        # Check for missing components
        intended_components = set(intended_arch.get('components', {}).keys())
        current_components = set(current.components.keys())
        
        missing_components = list(intended_components - current_components)
        extra_components = list(current_components - intended_components)
        
        # Check integration gaps
        for module, status in current.integration_status.items():
            if not status.is_integrated:
                integration_gaps.append(IntegrationGap(
                    component=module,
                    missing_integration="Component not integrated",
                    reason=f"Component has {len(status.unused_classes)} unused classes"
                ))
        
        # Determine severity
        severity = ValidationSeverity.INFO
        if missing_components or len(integration_gaps) > 5:
            severity = ValidationSeverity.CRITICAL
        elif extra_components or integration_gaps:
            severity = ValidationSeverity.WARNING
        
        is_consistent = not (missing_components or misplaced_components or 
                           (len(integration_gaps) > 5))
        
        report = ValidationReport(
            is_consistent=is_consistent,
            missing_components=missing_components,
            extra_components=extra_components,
            misplaced_components=misplaced_components,
            integration_gaps=integration_gaps,
            naming_violations=naming_violations,
            severity=severity
        )
        
        if self.logger:
            self.logger.info(f"  ✅ Validation complete: {'CONSISTENT' if is_consistent else 'DRIFT DETECTED'}")
            if missing_components:
                self.logger.warning(f"    ⚠️  Missing {len(missing_components)} components")
            if integration_gaps:
                self.logger.warning(f"    ⚠️  Found {len(integration_gaps)} integration gaps")
        
        return report
    
    def _read_intended_architecture(self) -> Dict:
        """
        Extract intended architecture from MASTER_PLAN.md.
        
        Returns:
            Dict with intended architecture specification
        """
        master_plan_path = self.project_dir / "MASTER_PLAN.md"
        
        if not master_plan_path.exists():
            if self.logger:
                self.logger.warning("  ⚠️  MASTER_PLAN.md not found")
            return {'components': {}}
        
        try:
            content = master_plan_path.read_text(encoding='utf-8')
            
            # Extract architecture section
            arch_section = self._extract_section(content, 'Architecture')
            
            # Parse components (simple parsing for now)
            components = {}
            
            # Look for component definitions
            # Format: ### ComponentName or ## ComponentName
            component_pattern = r'###?\s+([A-Z][A-Za-z0-9_]+)'
            matches = re.finditer(component_pattern, arch_section)
            
            for match in matches:
                component_name = match.group(1)
                components[component_name] = {
                    'name': component_name,
                    'defined_in': 'MASTER_PLAN.md'
                }
            
            return {'components': components}
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"  ❌ Failed to read MASTER_PLAN.md: {e}")
            return {'components': {}}
    
    def get_architecture_diff(self, previous_analysis: Optional[ArchitectureAnalysis] = None) -> ArchitectureDiff:
        """
        Get detailed diff between architectures.
        
        Args:
            previous_analysis: Previous analysis (if None, no diff)
            
        Returns:
            ArchitectureDiff with:
            - Added components
            - Removed components
            - Modified components
            - Moved components
        """
        current = self.analyze_current_architecture()
        
        if previous_analysis is None:
            # No previous analysis, all components are "added"
            return ArchitectureDiff(
                added=list(current.components.values()),
                removed=[],
                modified=[],
                moved=[]
            )
        
        # Compare
        current_names = set(current.components.keys())
        previous_names = set(previous_analysis.components.keys())
        
        added = [current.components[name] for name in (current_names - previous_names)]
        removed = [previous_analysis.components[name] for name in (previous_names - current_names)]
        
        # Check for modifications
        modified = []
        for name in (current_names & previous_names):
            curr = current.components[name]
            prev = previous_analysis.components[name]
            
            # Check if classes or functions changed
            if (set(curr.classes) != set(prev.classes) or 
                set(curr.functions) != set(prev.functions)):
                modified.append(ComponentChange(
                    component=name,
                    change_type='modified',
                    details={
                        'classes_added': list(set(curr.classes) - set(prev.classes)),
                        'classes_removed': list(set(prev.classes) - set(curr.classes)),
                        'functions_added': list(set(curr.functions) - set(prev.functions)),
                        'functions_removed': list(set(prev.functions) - set(curr.functions))
                    }
                ))
        
        # Check for moves (same component, different path)
        moved = []
        for name in (current_names & previous_names):
            curr = current.components[name]
            prev = previous_analysis.components[name]
            
            if curr.path != prev.path:
                moved.append(ComponentMove(
                    component=name,
                    old_location=prev.path,
                    new_location=curr.path,
                    reason="Path changed"
                ))
        
        return ArchitectureDiff(
            added=added,
            removed=removed,
            modified=modified,
            moved=moved
        )
    
    def get_call_graph_for_component(self, component: str) -> CallGraphSubset:
        """
        Get call graph for specific component.
        
        Args:
            component: Component name (e.g., 'pipeline.phases.planning')
            
        Returns:
            CallGraphSubset showing:
            - Functions in component
            - Calls to other components
            - Calls from other components
        """
        analysis = self.analyze_current_architecture()
        
        if component not in analysis.components:
            return CallGraphSubset(
                component=component,
                functions=[],
                internal_calls={},
                external_calls={}
            )
        
        comp_info = analysis.components[component]
        
        # Get all functions in component
        component_functions = comp_info.functions + [
            f"{cls}.{method}" 
            for cls in comp_info.classes 
            for method in self.validator.symbol_table.classes.get(cls, type('obj', (), {'methods': {}})()).methods.keys()
        ]
        
        # Filter call graph
        internal_calls = {}
        external_calls = {}
        
        for func in component_functions:
            if func in analysis.call_graph.calls:
                callees = analysis.call_graph.calls[func]
                
                internal = set()
                external = set()
                
                for callee in callees:
                    callee_module = '.'.join(callee.split('.')[:-1]) if '.' in callee else 'root'
                    
                    if callee_module == component:
                        internal.add(callee)
                    else:
                        external.add(callee)
                
                if internal:
                    internal_calls[func] = internal
                if external:
                    external_calls[func] = external
        
        return CallGraphSubset(
            component=component,
            functions=component_functions,
            internal_calls=internal_calls,
            external_calls=external_calls
        )
    
    def get_integration_status(self, component: str) -> Optional[IntegrationStatus]:
        """
        Get integration status for component.
        
        Args:
            component: Component name
            
        Returns:
            IntegrationStatus or None if component not found
        """
        analysis = self.analyze_current_architecture()
        return analysis.integration_status.get(component)
    
    def update_architecture_document(self,
                                    intended: Dict,
                                    current: ArchitectureAnalysis,
                                    diff: ArchitectureDiff,
                                    validation: Optional[ValidationReport] = None) -> None:
        """
        Update ARCHITECTURE.md with comprehensive view.
        
        Args:
            intended: Intended architecture from MASTER_PLAN
            current: Current architecture from analysis
            diff: Differences between intended and current
            validation: Optional validation report
        """
        if self.logger:
            self.logger.info("  📝 Updating ARCHITECTURE.md...")
        
        content = f"""# Architecture Document

**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status**: {'✅ CONSISTENT' if validation and validation.is_consistent else '⚠️ DRIFT DETECTED' if validation else '📊 ANALYZED'}

---

## Intended Architecture

{self._format_intended_architecture(intended)}

---

## Current Architecture

### Components ({len(current.components)})

{self._format_current_components(current.components)}

### Call Graph Statistics

- **Total Functions**: {current.call_graph.total_functions if current.call_graph else 0}
- **Total Calls**: {current.call_graph.total_calls if current.call_graph else 0}

### Integration Status

{self._format_integration_status(current.integration_status)}

---

## Validation Status

{self._format_validation_report(validation) if validation else 'No validation performed'}

---

## Changes Since Last Update

{self._format_architecture_diff(diff)}

---

## Component Details

{self._format_component_details(current.components)}

---

*This document is automatically maintained by the planning and documentation phases.*
"""
        
        try:
            self.arch_file.write_text(content, encoding='utf-8')
            if self.logger:
                self.logger.info("  ✅ ARCHITECTURE.md updated")
        except Exception as e:
            if self.logger:
                self.logger.error(f"  ❌ Failed to update ARCHITECTURE.md: {e}")
    
    def _format_intended_architecture(self, intended: Dict) -> str:
        """Format intended architecture section"""
        components = intended.get('components', {})
        
        if not components:
            return "*No intended architecture defined in MASTER_PLAN.md*"
        
        lines = []
        for name, info in components.items():
            lines.append(f"- **{name}**: {info.get('description', 'No description')}")
        
        return '\n'.join(lines)
    
    def _format_current_components(self, components: Dict[str, ComponentInfo]) -> str:
        """Format current components section"""
        if not components:
            return "*No components found*"
        
        lines = []
        for name, info in sorted(components.items()):
            lines.append(f"#### {name}")
            lines.append(f"- **Path**: `{info.path}`")
            lines.append(f"- **Classes**: {len(info.classes)}")
            lines.append(f"- **Functions**: {len(info.functions)}")
            lines.append(f"- **Dependencies**: {len(info.dependencies)}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _format_integration_status(self, integration: Dict[str, IntegrationStatus]) -> str:
        """Format integration status section"""
        if not integration:
            return "*No integration data available*"
        
        lines = []
        for module, status in sorted(integration.items()):
            emoji = "✅" if status.is_integrated else "⚠️"
            lines.append(f"- {emoji} **{module}**: {status.integration_score:.1%} integrated")
            
            if status.unused_classes:
                lines.append(f"  - Unused classes: {len(status.unused_classes)}")
        
        return '\n'.join(lines)
    
    def _format_validation_report(self, validation: ValidationReport) -> str:
        """Format validation report section"""
        lines = []
        
        lines.append(f"**Consistency**: {'✅ CONSISTENT' if validation.is_consistent else '⚠️ DRIFT DETECTED'}")
        lines.append(f"**Severity**: {validation.severity.value.upper()}")
        lines.append("")
        
        if validation.missing_components:
            lines.append(f"### Missing Components ({len(validation.missing_components)})")
            for comp in validation.missing_components:
                lines.append(f"- {comp}")
            lines.append("")
        
        if validation.extra_components:
            lines.append(f"### Extra Components ({len(validation.extra_components)})")
            for comp in validation.extra_components:
                lines.append(f"- {comp}")
            lines.append("")
        
        if validation.integration_gaps:
            lines.append(f"### Integration Gaps ({len(validation.integration_gaps)})")
            for gap in validation.integration_gaps[:5]:  # Show first 5
                lines.append(f"- **{gap.component}**: {gap.reason}")
            if len(validation.integration_gaps) > 5:
                lines.append(f"- *...and {len(validation.integration_gaps) - 5} more*")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _format_architecture_diff(self, diff: ArchitectureDiff) -> str:
        """Format architecture diff section"""
        if not diff.has_changes():
            return "*No changes since last update*"
        
        lines = []
        
        if diff.added:
            lines.append(f"### Added Components ({len(diff.added)})")
            for comp in diff.added:
                lines.append(f"- ➕ **{comp.name}**: {len(comp.classes)} classes, {len(comp.functions)} functions")
            lines.append("")
        
        if diff.removed:
            lines.append(f"### Removed Components ({len(diff.removed)})")
            for comp in diff.removed:
                lines.append(f"- ➖ **{comp.name}**")
            lines.append("")
        
        if diff.modified:
            lines.append(f"### Modified Components ({len(diff.modified)})")
            for change in diff.modified:
                lines.append(f"- 🔄 **{change.component}**: {change.change_type}")
            lines.append("")
        
        if diff.moved:
            lines.append(f"### Moved Components ({len(diff.moved)})")
            for move in diff.moved:
                lines.append(f"- 📦 **{move.component}**: {move.old_location} → {move.new_location}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _format_component_details(self, components: Dict[str, ComponentInfo]) -> str:
        """Format detailed component information"""
        if not components:
            return "*No components found*"
        
        lines = []
        
        # Show top 10 components by size
        sorted_components = sorted(
            components.items(),
            key=lambda x: len(x[1].classes) + len(x[1].functions),
            reverse=True
        )[:10]
        
        for name, info in sorted_components:
            lines.append(f"### {name}")
            lines.append(f"**Path**: `{info.path}`")
            lines.append("")
            
            if info.classes:
                lines.append(f"**Classes** ({len(info.classes)}):")
                for cls in info.classes[:5]:  # Show first 5
                    lines.append(f"- `{cls}`")
                if len(info.classes) > 5:
                    lines.append(f"- *...and {len(info.classes) - 5} more*")
                lines.append("")
            
            if info.dependencies:
                lines.append(f"**Dependencies** ({len(info.dependencies)}):")
                for dep in info.dependencies[:5]:  # Show first 5
                    lines.append(f"- `{dep}`")
                if len(info.dependencies) > 5:
                    lines.append(f"- *...and {len(info.dependencies) - 5} more*")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return '\n'.join(lines)