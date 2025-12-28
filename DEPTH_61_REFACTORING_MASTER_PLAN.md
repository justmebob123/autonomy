# Depth-61 Refactoring Master Plan

## Overview
Comprehensive refactoring plan for all high-complexity functions identified during depth-61 file-by-file examination.

**Created**: December 28, 2024  
**Status**: ACTIVE  
**Total Functions to Refactor**: 5  
**Estimated Total Effort**: 20-30 days

---

## Priority Matrix

| Priority | Function | Complexity | File | Effort | Status |
|----------|----------|------------|------|--------|--------|
| 1 - CRITICAL | run_debug_qa_mode | 192 | run.py | 5-7 days | NOT STARTED |
| 2 - URGENT | execute_with_conversation_thread | 85 | phases/debugging.py | 5-7 days | NOT STARTED |
| 3 - HIGH | _handle_modify_file | 54 | handlers.py | 2-3 days | NOT STARTED |
| 4 - HIGH | execute | 50 | phases/qa.py | 2-3 days | NOT STARTED |
| 5 - MEDIUM | _run_loop | 38 | coordinator.py | 2-3 days | NOT STARTED |

**Total Estimated Effort**: 18-26 days

---

## Refactoring #1: run.py::run_debug_qa_mode (CRITICAL)

### Current State
- **Complexity**: 192 (EXTREMELY HIGH)
- **Lines**: ~1,000+ lines
- **Nesting Levels**: 6-8 levels
- **Responsibilities**: 7+ distinct responsibilities
- **File**: run.py
- **Status**: NOT STARTED

### Issues
1. Single function with ~1,000+ lines
2. Extreme nesting (6-8 levels)
3. Multiple responsibilities (7+)
4. Difficult to test
5. Difficult to maintain
6. Difficult to understand
7. High cognitive load

### Refactoring Strategy

#### Phase 1: Analysis (Before Changes - Depth-29)
**Duration**: 1-2 days
**Prerequisites**: Complete depth-29 analysis of all affected subsystems

**Tasks**:
- [ ] Map all call stacks to depth-29
- [ ] Trace all variable flows
- [ ] Identify all subsystems that interact with run_debug_qa_mode
- [ ] Document all state mutations and side effects
- [ ] Map all error handling paths
- [ ] Identify all integration points
- [ ] Create comprehensive dependency graph
- [ ] Identify all test cases that need updating

#### Phase 2: Design (Before Changes)
**Duration**: 1 day

**Tasks**:
- [ ] Design class-based architecture
- [ ] Define class responsibilities
- [ ] Design method signatures
- [ ] Plan state management
- [ ] Design error handling strategy
- [ ] Plan testing strategy

**Proposed Architecture**:
```python
class DebugQAMode:
    """Main orchestrator for debug QA mode"""
    
    def __init__(self, config, project_dir):
        self.config = config
        self.project_dir = project_dir
        self.state_manager = StateManager(project_dir)
        self.phase_coordinator = PhaseCoordinator(config)
        self.runtime_tester = RuntimeTester(project_dir)
        
    def run(self):
        """Main entry point"""
        self._initialize()
        self._run_loop()
        self._cleanup()
        
    def _initialize(self):
        """Initialize all subsystems"""
        pass
        
    def _run_loop(self):
        """Main execution loop"""
        pass
        
    def _cleanup(self):
        """Cleanup and finalization"""
        pass

class DebugQAInitializer:
    """Handles initialization"""
    pass

class DebugQALoopManager:
    """Manages main execution loop"""
    pass

class DebugQAStateManager:
    """Manages state transitions"""
    pass

class DebugQAErrorHandler:
    """Handles errors and recovery"""
    pass
```

#### Phase 3: Implementation
**Duration**: 2-3 days

**Tasks**:
- [ ] Create DebugQAMode class
- [ ] Extract initialization logic to DebugQAInitializer
- [ ] Extract loop logic to DebugQALoopManager
- [ ] Extract state management to DebugQAStateManager
- [ ] Extract error handling to DebugQAErrorHandler
- [ ] Reduce nesting levels to 2-3 maximum
- [ ] Split into methods with single responsibility
- [ ] Add comprehensive logging
- [ ] Add type hints
- [ ] Add docstrings

**Target Metrics**:
- Complexity: <20 per method
- Nesting: ≤3 levels
- Lines per method: <50
- Responsibilities per class: 1

#### Phase 4: Testing
**Duration**: 1-2 days

**Tasks**:
- [ ] Create unit tests for each class
- [ ] Create integration tests
- [ ] Test error handling
- [ ] Test edge cases
- [ ] Verify all existing functionality works
- [ ] Performance testing
- [ ] Regression testing

#### Phase 5: Documentation
**Duration**: 0.5 days

**Tasks**:
- [ ] Update code documentation
- [ ] Update architecture documentation
- [ ] Create migration guide
- [ ] Document breaking changes (if any)

### Dependencies
- StateManager
- PhaseCoordinator
- RuntimeTester
- All phases
- Configuration system

### Risks
- High - This is a critical function
- Breaking changes possible
- Extensive testing required
- May affect other systems

### Success Criteria
- [ ] Complexity reduced from 192 to <20 per method
- [ ] All tests passing
- [ ] No regressions
- [ ] Code coverage >80%
- [ ] Documentation complete

---

## Refactoring #2: debugging.py::execute_with_conversation_thread (URGENT)

### Current State
- **Complexity**: 85 (VERY HIGH)
- **Lines**: ~730 lines
- **Nesting Levels**: 5-7 levels
- **Call Stack Depth**: 61 levels (reaches GPU kernel operations)
- **File**: pipeline/phases/debugging.py
- **Status**: NOT STARTED

### Issues
1. Very high complexity (85)
2. Deep call stacks (depth 61)
3. Main conversation loop with multiple nested operations
4. 6 search strategies for code modification
5. Loop detection and specialist consultation
6. Runtime verification integration
7. Difficult to test individual components

### Refactoring Strategy

#### Phase 1: Analysis (Before Changes - Depth-29)
**Duration**: 1 day

**Tasks**:
- [ ] Map all call stacks to depth-29
- [ ] Trace conversation flow
- [ ] Identify all tool call paths
- [ ] Document loop detection logic
- [ ] Map specialist consultation flow
- [ ] Document runtime verification flow
- [ ] Identify optimization opportunities

#### Phase 2: Design
**Duration**: 1 day

**Tasks**:
- [ ] Design state machine for conversation flow
- [ ] Design strategy pattern for tool calls
- [ ] Design caching strategy for model responses
- [ ] Plan async operations for optimization

**Proposed Architecture**:
```python
class ConversationStateMachine:
    """State machine for conversation flow"""
    states = ['INIT', 'ANALYZING', 'FIXING', 'VERIFYING', 'COMPLETE']
    
class ToolCallStrategy:
    """Base class for tool call strategies"""
    def execute(self, tool_call): pass

class ModifyFileStrategy(ToolCallStrategy):
    """Strategy for file modification"""
    pass

class ExecuteCommandStrategy(ToolCallStrategy):
    """Strategy for command execution"""
    pass

class ModelResponseCache:
    """Cache for model responses"""
    pass

class ConversationManager:
    """Manages conversation flow"""
    def __init__(self):
        self.state_machine = ConversationStateMachine()
        self.tool_strategies = {}
        self.cache = ModelResponseCache()
```

#### Phase 3: Implementation
**Duration**: 2-3 days

**Tasks**:
- [ ] Extract conversation loop to ConversationManager
- [ ] Implement state machine pattern
- [ ] Extract tool call processing to strategies
- [ ] Implement caching for model responses
- [ ] Extract loop detection to separate method
- [ ] Extract runtime verification to separate method
- [ ] Reduce nesting levels
- [ ] Add comprehensive error handling

**Target Metrics**:
- Complexity: <20 per method
- Nesting: ≤3 levels
- Lines per method: <50

#### Phase 4: Testing
**Duration**: 1-2 days

**Tasks**:
- [ ] Unit tests for state machine
- [ ] Unit tests for strategies
- [ ] Integration tests for conversation flow
- [ ] Test loop detection
- [ ] Test runtime verification
- [ ] Performance testing
- [ ] Regression testing

#### Phase 5: Optimization
**Duration**: 1 day

**Tasks**:
- [ ] Implement caching
- [ ] Optimize deep call stacks
- [ ] Consider async operations
- [ ] Profile performance
- [ ] Optimize bottlenecks

### Dependencies
- ToolCallHandler
- RuntimeTester
- LoopDetectionMixin
- TeamCoordinationFacade
- ConversationThread

### Risks
- Medium-High - Critical debugging functionality
- Performance impact possible
- Caching may introduce bugs

### Success Criteria
- [ ] Complexity reduced from 85 to <20 per method
- [ ] All tests passing
- [ ] Performance improved or maintained
- [ ] No regressions

---

## Refactoring #3: handlers.py::_handle_modify_file (HIGH)

### Current State
- **Complexity**: 54 (HIGH)
- **Lines**: ~365 lines
- **Search Strategies**: 6 different approaches
- **File**: pipeline/handlers.py
- **Status**: NOT STARTED

### Issues
1. High complexity (54)
2. 6 different search strategies in one method
3. Nested loops for line-by-line search
4. Complex AST traversal
5. Fuzzy matching with difflib
6. Difficult to test individual strategies

### Refactoring Strategy

#### Phase 1: Analysis (Before Changes - Depth-29)
**Duration**: 0.5 days

**Tasks**:
- [ ] Map all search strategy paths
- [ ] Document strategy selection logic
- [ ] Identify common patterns
- [ ] Document failure scenarios

#### Phase 2: Design
**Duration**: 0.5 days

**Tasks**:
- [ ] Design strategy pattern
- [ ] Define strategy interface
- [ ] Plan strategy selection logic

**Proposed Architecture**:
```python
class SearchStrategy(ABC):
    """Base class for search strategies"""
    @abstractmethod
    def search(self, content, old_code):
        pass

class ExactMatchStrategy(SearchStrategy):
    """Exact match search"""
    pass

class NormalizedWhitespaceStrategy(SearchStrategy):
    """Normalized whitespace search"""
    pass

class LineByLineStrategy(SearchStrategy):
    """Line-by-line search"""
    pass

class FuzzyMatchStrategy(SearchStrategy):
    """Fuzzy matching with difflib"""
    pass

class ASTBasedStrategy(SearchStrategy):
    """AST-based search"""
    pass

class RegexPatternStrategy(SearchStrategy):
    """Regex pattern search"""
    pass

class SearchStrategyManager:
    """Manages search strategies"""
    def __init__(self):
        self.strategies = [
            ExactMatchStrategy(),
            NormalizedWhitespaceStrategy(),
            LineByLineStrategy(),
            FuzzyMatchStrategy(),
            ASTBasedStrategy(),
            RegexPatternStrategy(),
        ]
    
    def find_match(self, content, old_code):
        for strategy in self.strategies:
            result = strategy.search(content, old_code)
            if result:
                return result
        return None
```

#### Phase 3: Implementation
**Duration**: 1-2 days

**Tasks**:
- [ ] Create SearchStrategy base class
- [ ] Implement each strategy as separate class
- [ ] Create SearchStrategyManager
- [ ] Refactor _handle_modify_file to use strategies
- [ ] Add comprehensive logging
- [ ] Add type hints

**Target Metrics**:
- Complexity: <15 per method
- Each strategy: <20 lines
- Main method: <50 lines

#### Phase 4: Testing
**Duration**: 1 day

**Tasks**:
- [ ] Unit tests for each strategy
- [ ] Integration tests for strategy manager
- [ ] Test edge cases
- [ ] Test failure scenarios
- [ ] Regression testing

### Dependencies
- validate_python_syntax
- FailureAnalyzer
- Path operations

### Risks
- Low-Medium - Well-isolated functionality
- Strategy selection logic must be correct

### Success Criteria
- [ ] Complexity reduced from 54 to <15 per method
- [ ] All tests passing
- [ ] Each strategy independently testable
- [ ] No regressions

---

## Refactoring #4: qa.py::execute (HIGH)

### Current State
- **Complexity**: 50 (HIGH)
- **Lines**: ~343 lines
- **File**: pipeline/phases/qa.py
- **Status**: NOT STARTED

### Issues
1. High complexity (50)
2. Multiple conditional branches for filepath/task determination
3. Loop prevention logic
4. File validation
5. Model inference
6. Tool call processing
7. State management operations

### Refactoring Strategy

#### Phase 1: Analysis (Before Changes - Depth-29)
**Duration**: 0.5 days

**Tasks**:
- [ ] Map all conditional branches
- [ ] Document filepath determination logic
- [ ] Document loop prevention logic
- [ ] Identify extraction opportunities

#### Phase 2: Design
**Duration**: 0.5 days

**Tasks**:
- [ ] Design method extraction plan
- [ ] Plan state management simplification

**Proposed Architecture**:
```python
class QAPhase(BasePhase, LoopDetectionMixin):
    
    def execute(self, state, filepath, task, **kwargs):
        """Main execution - simplified"""
        self._check_loop_prevention(state)
        filepath = self._determine_filepath(state, filepath, task)
        if not filepath:
            return self._handle_no_files(state)
        
        content = self._validate_and_read_file(filepath)
        response = self._review_file(filepath, content)
        result = self._process_review_result(state, filepath, task, response)
        return result
    
    def _check_loop_prevention(self, state):
        """Check and handle loop prevention"""
        pass
    
    def _determine_filepath(self, state, filepath, task):
        """Determine which file to review"""
        pass
    
    def _handle_no_files(self, state):
        """Handle case when no files need review"""
        pass
    
    def _validate_and_read_file(self, filepath):
        """Validate and read file content"""
        pass
    
    def _review_file(self, filepath, content):
        """Review file with model"""
        pass
    
    def _process_review_result(self, state, filepath, task, response):
        """Process review result and update state"""
        pass
```

#### Phase 3: Implementation
**Duration**: 1-2 days

**Tasks**:
- [ ] Extract _check_loop_prevention method
- [ ] Extract _determine_filepath method
- [ ] Extract _handle_no_files method
- [ ] Extract _validate_and_read_file method
- [ ] Extract _review_file method
- [ ] Extract _process_review_result method
- [ ] Simplify main execute method
- [ ] Add comprehensive logging

**Target Metrics**:
- Complexity: <15 per method
- Main execute: <30 lines
- Each extracted method: <30 lines

#### Phase 4: Testing
**Duration**: 1 day

**Tasks**:
- [ ] Unit tests for each extracted method
- [ ] Integration tests for execute
- [ ] Test loop prevention
- [ ] Test implicit approval
- [ ] Regression testing

### Dependencies
- StateManager
- ToolCallHandler
- ConversationThread
- MessageBus

### Risks
- Low - Well-defined functionality
- Loop prevention logic must remain correct

### Success Criteria
- [ ] Complexity reduced from 50 to <15 per method
- [ ] All tests passing
- [ ] Loop prevention still works correctly
- [ ] No regressions

---

## Refactoring #5: coordinator.py::_run_loop (MEDIUM)

### Current State
- **Complexity**: 38 (MEDIUM-HIGH)
- **Lines**: ~274 lines
- **File**: pipeline/coordinator.py
- **Status**: NOT STARTED

### Issues
1. Complexity 38
2. Infinite loop with multiple exit conditions
3. Complex phase selection logic
4. State management operations
5. Error handling
6. Message bus operations
7. Polytopic analysis integration

### Refactoring Strategy

#### Phase 1: Analysis (Before Changes - Depth-29)
**Duration**: 0.5 days

**Tasks**:
- [ ] Map all loop exit conditions
- [ ] Document phase selection logic
- [ ] Document state management flow
- [ ] Identify extraction opportunities

#### Phase 2: Design
**Duration**: 0.5 days

**Tasks**:
- [ ] Design state machine pattern
- [ ] Plan method extraction

**Proposed Architecture**:
```python
class CoordinatorStateMachine:
    """State machine for coordinator"""
    states = ['PLANNING', 'CODING', 'QA', 'DEBUGGING', 'DOCUMENTATION']
    
class PhaseCoordinator:
    
    def _run_loop(self):
        """Main loop - simplified"""
        self.state_machine = CoordinatorStateMachine()
        
        while not self._should_exit():
            state = self._load_state()
            action = self._determine_next_action(state)
            result = self._execute_phase(action, state)
            self._update_state(result, state)
            self._save_state(state)
            
        return self._finalize()
    
    def _should_exit(self):
        """Check if loop should exit"""
        pass
    
    def _load_state(self):
        """Load current state"""
        pass
    
    def _execute_phase(self, action, state):
        """Execute selected phase"""
        pass
    
    def _update_state(self, result, state):
        """Update state after phase execution"""
        pass
    
    def _save_state(self, state):
        """Save state to disk"""
        pass
    
    def _finalize(self):
        """Finalize and cleanup"""
        pass
```

#### Phase 3: Implementation
**Duration**: 1-2 days

**Tasks**:
- [ ] Implement state machine pattern
- [ ] Extract _should_exit method
- [ ] Extract _load_state method
- [ ] Extract _execute_phase method
- [ ] Extract _update_state method
- [ ] Extract _save_state method
- [ ] Extract _finalize method
- [ ] Simplify main loop

**Target Metrics**:
- Complexity: <15 per method
- Main loop: <30 lines
- Each extracted method: <30 lines

#### Phase 4: Testing
**Duration**: 1 day

**Tasks**:
- [ ] Unit tests for state machine
- [ ] Unit tests for each extracted method
- [ ] Integration tests for loop
- [ ] Test exit conditions
- [ ] Regression testing

### Dependencies
- StateManager
- All phases
- MessageBus
- Polytopic system

### Risks
- Medium - Core coordinator functionality
- Exit conditions must be correct

### Success Criteria
- [ ] Complexity reduced from 38 to <15 per method
- [ ] All tests passing
- [ ] Loop behavior unchanged
- [ ] No regressions

---

## Implementation Schedule

### Week 1: Critical Priority
- Days 1-2: Depth-29 analysis for run.py::run_debug_qa_mode
- Days 3-4: Design and implementation planning
- Days 5-7: Implementation of run.py refactoring

### Week 2: Urgent Priority
- Days 1-2: Depth-29 analysis for debugging.py::execute_with_conversation_thread
- Days 3-4: Design and implementation
- Days 5-7: Implementation and testing

### Week 3: High Priority
- Days 1-2: handlers.py::_handle_modify_file refactoring
- Days 3-4: qa.py::execute refactoring
- Days 5-7: Testing and documentation

### Week 4: Medium Priority & Finalization
- Days 1-2: coordinator.py::_run_loop refactoring
- Days 3-4: Integration testing
- Days 5-7: Documentation and final verification

---

## Testing Strategy

### Unit Testing
- Test each extracted method independently
- Test edge cases
- Test error handling
- Target coverage: >80%

### Integration Testing
- Test interactions between components
- Test end-to-end workflows
- Test with real data

### Regression Testing
- Verify all existing functionality works
- Compare behavior before/after refactoring
- Performance benchmarking

### Performance Testing
- Measure execution time
- Monitor memory usage
- Identify bottlenecks
- Optimize as needed

---

## Risk Mitigation

### High-Risk Refactorings
1. run.py::run_debug_qa_mode - CRITICAL functionality
2. debugging.py::execute_with_conversation_thread - Core debugging

**Mitigation**:
- Extensive testing before deployment
- Gradual rollout
- Feature flags for new code
- Easy rollback plan

### Medium-Risk Refactorings
3. handlers.py::_handle_modify_file - File operations
4. qa.py::execute - QA functionality

**Mitigation**:
- Comprehensive unit tests
- Integration testing
- Code review

### Low-Risk Refactorings
5. coordinator.py::_run_loop - Well-defined behavior

**Mitigation**:
- Standard testing
- Code review

---

## Success Metrics

### Code Quality
- [ ] All functions complexity <20
- [ ] Nesting levels ≤3
- [ ] Lines per method <50
- [ ] Test coverage >80%

### Functionality
- [ ] All tests passing
- [ ] No regressions
- [ ] Performance maintained or improved
- [ ] All features working

### Documentation
- [ ] Code documentation complete
- [ ] Architecture documentation updated
- [ ] Migration guides created
- [ ] Breaking changes documented

---

## Rollback Plan

### If Refactoring Fails
1. Revert to previous commit
2. Analyze failure
3. Update refactoring plan
4. Re-attempt with fixes

### Backup Strategy
- Create feature branch for each refactoring
- Keep main branch stable
- Merge only after full testing
- Tag releases for easy rollback

---

## Progress Tracking

### Refactoring #1: run.py::run_debug_qa_mode
- [ ] Phase 1: Analysis (0/8 tasks)
- [ ] Phase 2: Design (0/6 tasks)
- [ ] Phase 3: Implementation (0/9 tasks)
- [ ] Phase 4: Testing (0/7 tasks)
- [ ] Phase 5: Documentation (0/4 tasks)
- **Progress**: 0% (0/34 tasks)

### Refactoring #2: debugging.py::execute_with_conversation_thread
- [ ] Phase 1: Analysis (0/7 tasks)
- [ ] Phase 2: Design (0/4 tasks)
- [ ] Phase 3: Implementation (0/8 tasks)
- [ ] Phase 4: Testing (0/7 tasks)
- [ ] Phase 5: Optimization (0/5 tasks)
- **Progress**: 0% (0/31 tasks)

### Refactoring #3: handlers.py::_handle_modify_file
- [ ] Phase 1: Analysis (0/4 tasks)
- [ ] Phase 2: Design (0/3 tasks)
- [ ] Phase 3: Implementation (0/6 tasks)
- [ ] Phase 4: Testing (0/5 tasks)
- **Progress**: 0% (0/18 tasks)

### Refactoring #4: qa.py::execute
- [ ] Phase 1: Analysis (0/4 tasks)
- [ ] Phase 2: Design (0/2 tasks)
- [ ] Phase 3: Implementation (0/8 tasks)
- [ ] Phase 4: Testing (0/5 tasks)
- **Progress**: 0% (0/19 tasks)

### Refactoring #5: coordinator.py::_run_loop
- [ ] Phase 1: Analysis (0/4 tasks)
- [ ] Phase 2: Design (0/2 tasks)
- [ ] Phase 3: Implementation (0/8 tasks)
- [ ] Phase 4: Testing (0/5 tasks)
- **Progress**: 0% (0/19 tasks)

### Overall Progress
- **Total Tasks**: 121
- **Completed**: 0
- **Progress**: 0%

---

**Document Status**: ACTIVE  
**Last Updated**: December 28, 2024  
**Next Review**: After each file examination  
**Owner**: SuperNinja AI Agent