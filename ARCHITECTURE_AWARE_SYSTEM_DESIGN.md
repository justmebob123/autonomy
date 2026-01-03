# Architecture-Aware Polytopic System Design

## Executive Summary

This document outlines the design for deeply integrating architecture awareness into the polytopic system, enabling planning and documentation phases to maintain a stable understanding of both **intended** and **current** architecture, validate consistency, and guide all phases with accurate architectural context.

---

## 1. Core Concepts

### 1.1 Dual Architecture Model

The system will maintain TWO architecture representations:

1. **INTENDED ARCHITECTURE** (from MASTER_PLAN.md)
   - What the system SHOULD look like
   - Defined by project objectives
   - Stable reference point
   - Updated only when objectives change

2. **CURRENT ARCHITECTURE** (from validation tools)
   - What the system ACTUALLY looks like
   - Discovered through code analysis
   - Changes with every code modification
   - Validated against intended architecture

### 1.2 Architecture Validation Loop

```
Planning Phase:
  1. Read INTENDED architecture (from MASTER_PLAN)
  2. Analyze CURRENT architecture (via validation tools)
  3. Identify GAPS between intended and current
  4. Create tasks to close gaps
  5. Update ARCHITECTURE.md with both views

Documentation Phase:
  1. Read INTENDED architecture
  2. Analyze CURRENT architecture
  3. Validate consistency
  4. Document changes
  5. Update ARCHITECTURE.md
  6. Alert if drift is significant
```

---

## 2. Enhanced ArchitectureManager

### 2.1 Current Capabilities
```python
class ArchitectureManager:
    def read_architecture() -> Dict
    def record_change(phase, change_type, details)
```

### 2.2 New Capabilities

```python
class ArchitectureManager:
    """Enhanced architecture manager with validation tool integration"""
    
    # EXISTING
    def read_architecture() -> Dict
    def record_change(phase, change_type, details)
    
    # NEW: Validation Tool Integration
    def analyze_current_architecture(self) -> ArchitectureAnalysis:
        """
        Analyze current codebase using validation tools.
        
        Returns:
            ArchitectureAnalysis with:
            - Component structure (from symbol_table)
            - Call graph (from call_graph)
            - Integration status (from validators)
            - Code quality metrics (from complexity analyzer)
        """
        
    def validate_architecture_consistency(self) -> ValidationReport:
        """
        Compare intended vs current architecture.
        
        Returns:
            ValidationReport with:
            - Missing components
            - Extra components
            - Misplaced components
            - Integration gaps
            - Naming violations
        """
    
    def get_architecture_diff(self) -> ArchitectureDiff:
        """
        Get detailed diff between intended and current.
        
        Returns:
            ArchitectureDiff with:
            - Added components
            - Removed components
            - Modified components
            - Moved components
        """
    
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
    
    def validate_component_placement(self, file_path: str) -> PlacementValidation:
        """
        Validate if file is in correct location per architecture.
        
        Args:
            file_path: Path to file
            
        Returns:
            PlacementValidation with:
            - is_valid: bool
            - expected_location: str
            - reason: str
        """
    
    def get_integration_status(self, component: str) -> IntegrationStatus:
        """
        Get integration status for component.
        
        Args:
            component: Component name
            
        Returns:
            IntegrationStatus with:
            - is_integrated: bool
            - missing_integrations: List[str]
            - unused_classes: List[str]
            - integration_score: float (0-1)
        """
    
    def update_architecture_document(self, 
                                     intended: Dict,
                                     current: ArchitectureAnalysis,
                                     diff: ArchitectureDiff) -> None:
        """
        Update ARCHITECTURE.md with comprehensive view.
        
        Args:
            intended: Intended architecture from MASTER_PLAN
            current: Current architecture from analysis
            diff: Differences between intended and current
        """
```

### 2.3 Data Structures

```python
@dataclass
class ArchitectureAnalysis:
    """Result of analyzing current architecture"""
    timestamp: datetime
    components: Dict[str, ComponentInfo]
    call_graph: CallGraphResult
    integration_status: Dict[str, IntegrationStatus]
    quality_metrics: Dict[str, QualityMetrics]
    validation_errors: List[ValidationError]
    
@dataclass
class ComponentInfo:
    """Information about a component"""
    name: str
    path: str
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    dependencies: List[str]
    dependents: List[str]
    
@dataclass
class ValidationReport:
    """Result of architecture validation"""
    is_consistent: bool
    missing_components: List[str]
    extra_components: List[str]
    misplaced_components: List[PlacementIssue]
    integration_gaps: List[IntegrationGap]
    naming_violations: List[NamingViolation]
    severity: str  # 'critical', 'warning', 'info'
    
@dataclass
class ArchitectureDiff:
    """Differences between architectures"""
    added: List[ComponentInfo]
    removed: List[ComponentInfo]
    modified: List[ComponentChange]
    moved: List[ComponentMove]
```

---

## 3. Enhanced Planning Phase

### 3.1 Current Architecture Integration

Planning phase already has:
- `_read_architecture()` - reads ARCHITECTURE.md
- `_update_architecture_doc()` - updates with analysis results
- `_analyze_existing_codebase()` - basic analysis

### 3.2 Enhanced Architecture Integration

```python
class PlanningPhase(BasePhase):
    """Enhanced planning with architecture validation"""
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """Execute with architecture validation"""
        
        # 1. READ INTENDED ARCHITECTURE
        intended_arch = self._read_intended_architecture()
        
        # 2. ANALYZE CURRENT ARCHITECTURE
        current_arch = self.arch_manager.analyze_current_architecture()
        
        # 3. VALIDATE CONSISTENCY
        validation = self.arch_manager.validate_architecture_consistency()
        
        # 4. GET DIFF
        diff = self.arch_manager.get_architecture_diff()
        
        # 5. CREATE ARCHITECTURE-AWARE TASKS
        tasks = self._create_architecture_tasks(validation, diff)
        
        # 6. UPDATE ARCHITECTURE.MD
        self.arch_manager.update_architecture_document(
            intended=intended_arch,
            current=current_arch,
            diff=diff
        )
        
        # 7. PUBLISH ARCHITECTURE EVENTS
        self._publish_architecture_events(validation, diff)
        
        # Continue with normal planning...
    
    def _read_intended_architecture(self) -> Dict:
        """
        Extract intended architecture from MASTER_PLAN.md.
        
        Parses sections like:
        - ## Architecture
        - ## Components
        - ## Structure
        
        Returns:
            Dict with intended architecture specification
        """
    
    def _create_architecture_tasks(self, 
                                   validation: ValidationReport,
                                   diff: ArchitectureDiff) -> List[TaskState]:
        """
        Create tasks to fix architecture issues.
        
        Priority order:
        1. CRITICAL: Missing required components
        2. HIGH: Misplaced components
        3. MEDIUM: Integration gaps
        4. LOW: Naming violations
        
        Args:
            validation: Validation report
            diff: Architecture diff
            
        Returns:
            List of TaskState objects
        """
    
    def _publish_architecture_events(self,
                                     validation: ValidationReport,
                                     diff: ArchitectureDiff) -> None:
        """
        Publish architecture events via message bus.
        
        Events:
        - ARCHITECTURE_VALIDATED (with validation results)
        - ARCHITECTURE_DRIFT_DETECTED (if significant drift)
        - ARCHITECTURE_COMPONENT_MISSING (for each missing component)
        - ARCHITECTURE_COMPONENT_MISPLACED (for each misplaced component)
        """
```

### 3.3 Enhanced Planning Prompt

The planning prompt will include:

```markdown
## Architecture Context

### Intended Architecture
[Extracted from MASTER_PLAN.md]

### Current Architecture
[From validation tools]
- Components: X classes, Y functions
- Integration Status: Z% integrated
- Call Graph: A functions, B calls

### Architecture Validation
[From validation report]
- Status: CONSISTENT / DRIFT DETECTED
- Missing Components: [list]
- Misplaced Components: [list]
- Integration Gaps: [list]

### Required Actions
[Tasks to fix architecture issues]
1. Create missing component X
2. Move component Y to correct location
3. Integrate component Z with A

You MUST prioritize architecture consistency tasks before feature development.
```

---

## 4. Enhanced Documentation Phase

### 4.1 Current Architecture Integration

Documentation phase already has:
- `_read_architecture()` - reads ARCHITECTURE.md
- Basic architecture awareness

### 4.2 Enhanced Architecture Integration

```python
class DocumentationPhase(BasePhase):
    """Enhanced documentation with architecture maintenance"""
    
    def execute(self, state: PipelineState, **kwargs) -> PhaseResult:
        """Execute with architecture maintenance"""
        
        # 1. READ INTENDED ARCHITECTURE
        intended_arch = self._read_intended_architecture()
        
        # 2. ANALYZE CURRENT ARCHITECTURE
        current_arch = self.arch_manager.analyze_current_architecture()
        
        # 3. VALIDATE CONSISTENCY
        validation = self.arch_manager.validate_architecture_consistency()
        
        # 4. GET DIFF SINCE LAST UPDATE
        diff = self.arch_manager.get_architecture_diff()
        
        # 5. UPDATE ARCHITECTURE.MD
        self._update_architecture_comprehensive(
            intended=intended_arch,
            current=current_arch,
            validation=validation,
            diff=diff
        )
        
        # 6. ALERT IF SIGNIFICANT DRIFT
        if validation.severity == 'critical':
            self._alert_architecture_drift(validation)
        
        # Continue with normal documentation...
    
    def _update_architecture_comprehensive(self,
                                          intended: Dict,
                                          current: ArchitectureAnalysis,
                                          validation: ValidationReport,
                                          diff: ArchitectureDiff) -> None:
        """
        Update ARCHITECTURE.md with comprehensive information.
        
        Document structure:
        
        # Architecture Document
        
        ## Intended Architecture
        [From MASTER_PLAN.md]
        
        ## Current Architecture
        [From validation tools]
        
        ## Validation Status
        [Consistency check results]
        
        ## Changes Since Last Update
        [Architecture diff]
        
        ## Required Actions
        [Tasks to fix issues]
        
        ## Component Details
        [Detailed component information]
        
        ## Call Graph
        [Key call graph information]
        
        ## Integration Status
        [Integration metrics per component]
        """
    
    def _alert_architecture_drift(self, validation: ValidationReport) -> None:
        """
        Alert about significant architecture drift.
        
        Publishes:
        - SYSTEM_ALERT event via message bus
        - Updates DOCUMENTATION_WRITE.md with alert
        - Writes to PLANNING_READ.md to request fix
        """
```

### 4.3 Enhanced Documentation Prompt

The documentation prompt will include:

```markdown
## Architecture Maintenance

You are responsible for maintaining ARCHITECTURE.md to accurately reflect:
1. INTENDED architecture (from MASTER_PLAN.md)
2. CURRENT architecture (from code analysis)
3. GAPS between intended and current
4. REQUIRED ACTIONS to close gaps

### Current Status
- Validation: [CONSISTENT / DRIFT DETECTED]
- Missing Components: X
- Misplaced Components: Y
- Integration Gaps: Z

### Your Tasks
1. Update ARCHITECTURE.md with latest analysis
2. Document all changes since last update
3. Highlight critical issues
4. Recommend corrective actions

If CRITICAL drift is detected, you MUST alert planning phase.
```

---

## 5. Enhanced IPC System

### 5.1 New Architecture-Specific Documents

```
ARCHITECTURE_STATUS.md - Current architecture validation status
ARCHITECTURE_CHANGES.md - Log of architecture changes
ARCHITECTURE_ALERTS.md - Critical architecture issues
```

### 5.2 Enhanced IPC Templates

#### PLANNING_READ.md Enhancement
```markdown
## Architecture Validation Results
[Written by documentation phase]

**Status**: CONSISTENT / DRIFT DETECTED
**Last Validated**: [timestamp]

### Critical Issues
1. Missing component: X
2. Misplaced component: Y

### Recommended Actions
1. Create component X in location A
2. Move component Y to location B
```

#### DOCUMENTATION_WRITE.md Enhancement
```markdown
## Architecture Maintenance Report
[Written by documentation phase]

**ARCHITECTURE.md Updated**: [timestamp]

### Changes Documented
- Added component X
- Removed component Y
- Updated integration status

### Validation Status
- Status: CONSISTENT
- No critical issues
```

### 5.3 Architecture Event Types

New MessageType enum values:
```python
class MessageType(Enum):
    # Existing...
    
    # Architecture events
    ARCHITECTURE_VALIDATED = "architecture_validated"
    ARCHITECTURE_DRIFT_DETECTED = "architecture_drift_detected"
    ARCHITECTURE_COMPONENT_MISSING = "architecture_component_missing"
    ARCHITECTURE_COMPONENT_MISPLACED = "architecture_component_misplaced"
    ARCHITECTURE_UPDATED = "architecture_updated"
```

---

## 6. Polytopic Integration

### 6.1 New Architecture Dimension

Add to dimensional alignment system:

```python
class DimensionalProfile:
    """Enhanced with architecture dimension"""
    
    # Existing dimensions
    temporal: float
    functional: float
    data: float
    state: float
    error: float
    context: float
    integration: float
    
    # NEW: Architecture dimension
    architecture: float  # 0.0 = no arch awareness, 1.0 = full arch awareness
```

### 6.2 Architecture Dimension Scoring

```python
def calculate_architecture_dimension(phase: str, state: PipelineState) -> float:
    """
    Calculate architecture dimension score for phase.
    
    Factors:
    - Does phase read architecture? (+0.2)
    - Does phase validate architecture? (+0.3)
    - Does phase update architecture? (+0.2)
    - Does phase use validation tools? (+0.3)
    
    Returns:
        Score from 0.0 to 1.0
    """
```

### 6.3 Architecture-Based Phase Transitions

```python
def should_transition_for_architecture(current_phase: str,
                                      validation: ValidationReport) -> Optional[str]:
    """
    Determine if architecture issues require phase transition.
    
    Rules:
    - If CRITICAL drift detected → transition to planning
    - If missing components → transition to planning
    - If misplaced components → transition to refactoring
    - If integration gaps → transition to refactoring
    
    Args:
        current_phase: Current phase name
        validation: Architecture validation report
        
    Returns:
        Next phase name or None
    """
```

### 6.4 Enhanced Coordinator

```python
class PhaseCoordinator:
    """Enhanced with architecture validation"""
    
    def _select_next_phase(self, state: PipelineState) -> str:
        """Select next phase with architecture awareness"""
        
        # 1. Check architecture validation status
        arch_validation = self.arch_manager.validate_architecture_consistency()
        
        # 2. If critical drift, force planning
        if arch_validation.severity == 'critical':
            self.logger.warning("Critical architecture drift - forcing planning phase")
            return 'planning'
        
        # 3. Continue with normal phase selection
        return super()._select_next_phase(state)
    
    def _before_phase_execution(self, phase: str, state: PipelineState) -> None:
        """Pre-execution architecture check"""
        
        # Validate architecture before each phase
        validation = self.arch_manager.validate_architecture_consistency()
        
        # Store in state for phase to use
        state.architecture_validation = validation
        
        # Publish event
        self.message_bus.publish(
            MessageType.ARCHITECTURE_VALIDATED,
            payload={'validation': validation.to_dict()}
        )
```

---

## 7. Validation Tool Integration

### 7.1 ArchitectureManager Uses ValidatorCoordinator

```python
class ArchitectureManager:
    """Enhanced with validator coordinator"""
    
    def __init__(self, project_dir: Path, logger: Logger):
        self.project_dir = project_dir
        self.logger = logger
        
        # Create validator coordinator
        self.validator = ValidatorCoordinator(
            project_root=str(project_dir),
            logger=logger
        )
    
    def analyze_current_architecture(self) -> ArchitectureAnalysis:
        """Analyze using validation tools"""
        
        # Run all validators
        results = self.validator.validate_all()
        
        # Extract architecture information
        symbol_table = self.validator.symbol_table
        
        # Build component map
        components = self._build_component_map(symbol_table)
        
        # Get call graph
        call_graph = self._extract_call_graph(symbol_table)
        
        # Get integration status
        integration = self._calculate_integration_status(results)
        
        # Get quality metrics
        quality = self._extract_quality_metrics(results)
        
        return ArchitectureAnalysis(
            timestamp=datetime.now(),
            components=components,
            call_graph=call_graph,
            integration_status=integration,
            quality_metrics=quality,
            validation_errors=results.get('errors', [])
        )
```

### 7.2 Call Graph Integration

```python
def _extract_call_graph(self, symbol_table: SymbolTable) -> CallGraphResult:
    """Extract call graph from symbol table"""
    
    # Symbol table already has call graph built
    return CallGraphResult(
        functions=symbol_table.functions,
        calls=symbol_table.call_graph,
        called_by=symbol_table.reverse_call_graph
    )

def get_component_call_graph(self, component: str) -> CallGraphSubset:
    """Get call graph for specific component"""
    
    # Filter call graph to component
    component_functions = [
        f for f in self.validator.symbol_table.functions.keys()
        if f.startswith(component)
    ]
    
    # Extract relevant calls
    calls = {}
    for func in component_functions:
        calls[func] = self.validator.symbol_table.call_graph.get(func, set())
    
    return CallGraphSubset(
        component=component,
        functions=component_functions,
        internal_calls=self._filter_internal_calls(calls, component),
        external_calls=self._filter_external_calls(calls, component)
    )
```

---

## 8. Implementation Plan

### Phase 1: ArchitectureManager Enhancement
1. Add ValidatorCoordinator integration
2. Implement analyze_current_architecture()
3. Implement validate_architecture_consistency()
4. Implement get_architecture_diff()
5. Implement update_architecture_document()

### Phase 2: Planning Phase Enhancement
1. Add _read_intended_architecture()
2. Add _create_architecture_tasks()
3. Add _publish_architecture_events()
4. Update execute() with architecture validation
5. Update planning prompt with architecture context

### Phase 3: Documentation Phase Enhancement
1. Add _update_architecture_comprehensive()
2. Add _alert_architecture_drift()
3. Update execute() with architecture maintenance
4. Update documentation prompt with architecture context

### Phase 4: IPC Enhancement
1. Add architecture-specific documents
2. Update IPC templates with architecture sections
3. Add architecture event types to MessageType enum
4. Update message bus subscriptions

### Phase 5: Polytopic Integration
1. Add architecture dimension to DimensionalProfile
2. Implement calculate_architecture_dimension()
3. Implement should_transition_for_architecture()
4. Update coordinator with architecture validation

### Phase 6: Testing
1. Test architecture validation in planning
2. Test architecture maintenance in documentation
3. Test IPC architecture communication
4. Test polytopic architecture integration

---

## 9. Benefits

### 9.1 For Planning Phase
- **Accurate Context**: Always knows intended vs current architecture
- **Smart Task Creation**: Creates tasks to fix architecture issues
- **Validation-Driven**: Uses real code analysis, not assumptions
- **Gap Detection**: Identifies missing/misplaced components

### 9.2 For Documentation Phase
- **Comprehensive Updates**: Documents both intended and current
- **Drift Detection**: Alerts when architecture diverges
- **Change Tracking**: Logs all architecture changes
- **Maintenance**: Keeps ARCHITECTURE.md accurate

### 9.3 For All Phases
- **Architecture Awareness**: All phases can query architecture
- **Validation Access**: All phases can run validation tools
- **Call Graph Access**: All phases can analyze dependencies
- **Consistency**: Single source of truth for architecture

### 9.4 For Polytopic System
- **Architecture Dimension**: New dimension for phase selection
- **Smart Transitions**: Architecture issues trigger appropriate phases
- **Validation Loop**: Continuous architecture validation
- **Self-Correction**: System detects and fixes architecture drift

---

## 10. Success Criteria

1. ✅ Planning phase validates architecture before planning
2. ✅ Documentation phase maintains accurate ARCHITECTURE.md
3. ✅ ARCHITECTURE.md shows both intended and current
4. ✅ Validation tools integrated into architecture analysis
5. ✅ Call graph accessible to all phases
6. ✅ IPC system communicates architecture status
7. ✅ Polytopic system uses architecture dimension
8. ✅ Architecture drift triggers corrective actions
9. ✅ All phases have architecture awareness
10. ✅ System self-corrects architecture issues

---

## 11. Next Steps

1. Implement ArchitectureManager enhancements
2. Update planning phase with architecture validation
3. Update documentation phase with architecture maintenance
4. Enhance IPC system with architecture documents
5. Integrate architecture dimension into polytopic structure
6. Test and validate all changes
7. Document the complete system