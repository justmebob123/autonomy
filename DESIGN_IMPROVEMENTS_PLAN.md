# Pipeline Design Improvements Plan

## Core Design Principles

### 1. Project-Agnostic Design
- **NEVER hardcode project names** (no 'asas', 'test-automation', etc.)
- **NEVER hardcode directory structures** (no assumptions about 'core/', 'src/', etc.)
- Pipeline should work for ANY project structure
- Use dynamic discovery, not hardcoded patterns

### 2. Production Code First Philosophy
- **Default behavior**: Create production code
- **Tests**: Only when explicitly requested or after production code exists
- **Documentation**: Only when explicitly requested or at project completion
- **Priority weighting**: Production code should be 90%+ of work

### 3. Intelligent Task Classification
Instead of hardcoded patterns, use:
- File extension analysis (.py, .js, .java, etc.)
- Content analysis (is this a test? is this docs?)
- Project structure learning (discover patterns, don't assume)
- LLM-based classification when needed

## Specific Changes Needed

### A. Remove All Hardcoded Patterns

**Current Problems:**
```python
# BAD: Hardcoded project name
if 'asas' in task.target_file:

# BAD: Hardcoded test patterns
if 'test_' in task.target_file or '/tests/' in task.target_file:

# BAD: Hardcoded directory assumptions
for possible_path in [base_name, f'core/{base_name}', f'src/{base_name}']:
```

**Better Approach:**
```python
# GOOD: Generic classification
def classify_file_type(file_path: str) -> FileType:
    """Classify file based on actual content and context, not patterns."""
    # Use file extension, content analysis, project structure
    # Return: PRODUCTION_CODE, TEST, DOCUMENTATION, CONFIG, etc.

# GOOD: Dynamic structure discovery
def discover_project_structure(project_dir: Path) -> ProjectStructure:
    """Learn the project's actual structure."""
    # Find where production code lives
    # Find where tests live (if any)
    # Find where docs live (if any)
    # Return discovered structure, don't assume
```

### B. Redesign Priority System

**Current Problem:**
- Priority 10-80: Production code
- Priority 90-100: Tests
- But coordinator still creates/accepts test tasks too easily

**Better Approach:**
```python
class TaskPriority:
    CRITICAL_PRODUCTION = 10  # Core functionality
    HIGH_PRODUCTION = 30      # Important features
    MEDIUM_PRODUCTION = 50    # Standard features
    LOW_PRODUCTION = 70       # Nice-to-have features
    
    # Tests should be MUCH lower priority
    TESTS = 200               # Only after production code
    DOCUMENTATION = 300       # Only when requested
    REFACTORING = 150         # After core features work
```

### C. Update Planning Phase Prompt

**Remove:**
- Guidance to create tests
- Guidance to create documentation
- Balanced approach between code/tests/docs

**Add:**
- **PRIMARY FOCUS: Production code only**
- Tests only if explicitly requested in MASTER_PLAN
- Documentation only if explicitly requested
- Default to creating working features, not test suites

### D. Update Coordinator Logic

**Remove:**
- All hardcoded project names
- All hardcoded directory patterns
- Test-before-production checks (too aggressive)

**Add:**
- Generic file type classification
- Dynamic project structure learning
- Simple rule: If not explicitly a test/doc, treat as production code
- Let planning phase handle task creation, coordinator just executes

### E. Simplify Task Selection

**Current:** Complex logic with hardcoded patterns
**Better:** Simple priority-based selection

```python
def select_next_task(self, tasks: List[Task]) -> Optional[Task]:
    """Select highest priority task that's ready to execute."""
    # Filter to ready tasks (dependencies met)
    ready = [t for t in tasks if self._dependencies_met(t)]
    
    # Sort by priority (lower number = higher priority)
    ready.sort(key=lambda t: t.priority)
    
    # Return first ready task
    return ready[0] if ready else None
```

## Implementation Order

1. **Remove hardcoded patterns** (coordinator.py, planning.py)
2. **Simplify task selection** (coordinator.py)
3. **Update planning prompt** (prompts.py) - Focus on production code
4. **Add generic classification** (new utility module)
5. **Test with multiple projects** (verify project-agnostic design)

## Success Criteria

✅ Pipeline works with ANY project structure
✅ No hardcoded project names anywhere
✅ 90%+ of tasks are production code
✅ Tests/docs only created when explicitly needed
✅ Simple, maintainable code
✅ Easy to understand and modify