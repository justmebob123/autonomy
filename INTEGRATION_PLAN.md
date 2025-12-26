# Proper Integration Plan - Hyperdimensional Self-Awareness

## Problem
I created parallel systems instead of integrating into the existing codebase.

## Existing Architecture

### Core Classes
1. **PhaseCoordinator** (`pipeline/coordinator.py`) - Main orchestrator
2. **BasePhase** (`pipeline/phases/base.py`) - Base for all phases
3. **StateManager** (`pipeline/state/manager.py`) - State management
4. **PromptRegistry** (`pipeline/prompt_registry.py`) - Dynamic prompts
5. **ToolRegistry** (`pipeline/tool_registry.py`) - Dynamic tools
6. **RoleRegistry** (`pipeline/role_registry.py`) - Dynamic roles
7. **OllamaClient** (`pipeline/client.py`) - LLM communication

### Existing Integration Points
- BasePhase already has: `prompt_registry`, `tool_registry`, `role_registry`
- PhaseCoordinator already manages phase transitions
- StateManager already handles persistence

## Correct Integration Approach

### 1. Enhance PhaseCoordinator with Polytopic Awareness

**File:** `pipeline/coordinator.py`

Add to `PhaseCoordinator.__init__`:
```python
# Polytopic structure awareness
self.polytope = {
    'vertices': {},  # phase_name -> dimensional_profile
    'edges': {},     # phase_name -> [adjacent_phases]
    'dimensions': 7,
    'self_awareness_level': 0.0
}
self._initialize_polytopic_structure()
```

Add methods:
```python
def _initialize_polytopic_structure(self):
    """Initialize polytopic structure from existing phases"""
    
def _select_next_phase_polytopic(self, state):
    """Select next phase using polytopic adjacency"""
    
def _adapt_to_context(self, state):
    """Adapt orchestration based on current context"""
```

### 2. Enhance BasePhase with Self-Awareness

**File:** `pipeline/phases/base.py`

Add to `BasePhase.__init__`:
```python
# Self-awareness
self.dimensional_profile = {
    'temporal': 0.0,
    'functional': 0.0,
    'data': 0.0,
    'state': 0.0,
    'error': 0.0,
    'context': 0.0,
    'integration': 0.0
}
self.self_awareness_level = 0.0
self.adjacencies = []
```

Add methods:
```python
def adapt_to_situation(self, situation):
    """Adapt phase behavior based on situation"""
    
def get_adaptive_prompt(self, context):
    """Generate adaptive prompt based on context and self-awareness"""
```

### 3. Enhance PromptRegistry with Dynamic Generation

**File:** `pipeline/prompt_registry.py`

Add methods:
```python
def generate_adaptive_prompt(self, phase_name, context, dimensional_profile, adjacencies):
    """Generate prompt that reflects polytopic structure and self-awareness"""
    
def _add_self_awareness_context(self, prompt, self_awareness_level):
    """Add self-awareness context to prompt"""
    
def _add_adjacency_awareness(self, prompt, adjacencies):
    """Add adjacency awareness to prompt"""
```

### 4. Enhance StateManager with Unified State

**File:** `pipeline/state/manager.py`

Add to state:
```python
# Add to PipelineState
correlation_history: List[Dict] = []
learned_patterns: Dict[str, List] = {}
dimensional_expansions: List[Dict] = []
```

Add methods:
```python
def add_correlation(self, correlation):
    """Add correlation to history"""
    
def learn_pattern(self, pattern_type, pattern):
    """Learn a pattern"""
```

### 5. Create CorrelationEngine as Utility

**File:** `pipeline/correlation_engine.py` (KEEP THIS - it's a utility)

But integrate it into PhaseCoordinator:
```python
# In PhaseCoordinator.__init__
from .correlation_engine import CorrelationEngine
self.correlation_engine = CorrelationEngine()
```

### 6. Integrate Continuous Monitor

**File:** `pipeline/continuous_monitor.py` (KEEP THIS - it's a utility)

But integrate with RuntimeTester properly.

## Implementation Steps

### Step 1: Enhance PhaseCoordinator
- Add polytopic structure representation
- Add context-aware phase selection
- Add self-awareness tracking
- Integrate correlation engine

### Step 2: Enhance BasePhase
- Add dimensional profile
- Add self-awareness
- Add adaptive prompt generation
- Add situation adaptation

### Step 3: Enhance PromptRegistry
- Add dynamic prompt generation
- Add self-awareness context
- Add adjacency awareness
- Add recursive depth markers

### Step 4: Enhance StateManager
- Add correlation tracking
- Add pattern learning
- Add dimensional expansion log

### Step 5: Clean Up
- Remove parallel implementations
- Keep only utilities (CorrelationEngine, ContinuousMonitor)
- Update documentation

## Files to Modify (Not Create)

1. ✅ `pipeline/coordinator.py` - Add polytopic awareness
2. ✅ `pipeline/phases/base.py` - Add self-awareness
3. ✅ `pipeline/prompt_registry.py` - Add dynamic generation
4. ✅ `pipeline/state/manager.py` - Add unified state features
5. ✅ `pipeline/runtime_tester.py` - Add production mode

## Files to Keep (Utilities)

1. ✅ `pipeline/correlation_engine.py` - Utility for correlation analysis
2. ✅ `pipeline/continuous_monitor.py` - Utility for continuous monitoring
3. ✅ `pipeline/unified_state.py` - Can be merged into StateManager

## Files to Remove (Parallel Implementations)

1. ❌ `pipeline/adaptive_orchestrator.py` - Merge into PhaseCoordinator
2. ❌ `pipeline/dynamic_prompt_generator.py` - Merge into PromptRegistry
3. ❌ `pipeline/self_aware_role_system.py` - Merge into BasePhase
4. ❌ `pipeline/hyperdimensional_integration.py` - Merge into PhaseCoordinator

## Result

After proper integration:
- PhaseCoordinator becomes self-aware orchestrator
- BasePhase becomes self-aware base class
- PromptRegistry generates adaptive prompts
- StateManager tracks everything
- No parallel systems
- Clean, integrated architecture