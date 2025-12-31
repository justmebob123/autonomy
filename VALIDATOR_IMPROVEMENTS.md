# Validator Improvements Plan

## Current Issues

### 1. Function Name Collision
**Problem**: Validator tracks functions by name only, not by module/class context
- Example: `atexit.register()` confused with custom `ModelToolRegistry.register()`
- Causes false positives when stdlib/external functions share names with custom code

**Solution**: Track functions with full qualified names (module.class.function)

### 2. Missing Stdlib Function Coverage
**Problem**: Only ~40 stdlib functions in whitelist, but Python has hundreds
- Many common functions not recognized (e.g., `atexit.register`, `logging.getLogger`)
- Causes false positives for legitimate stdlib calls

**Solution**: Expand stdlib function list or use smarter detection

### 3. Method Call Context
**Problem**: Validator doesn't distinguish between:
- `obj.method()` - method call on instance
- `module.function()` - function call from module
- `Class.method()` - static/class method call

**Solution**: Analyze call context to determine what's being called

### 4. Dynamic Signatures
**Problem**: Can't validate calls to functions with:
- Decorators that modify signatures
- Dynamic parameter generation
- Wrapper functions

**Solution**: Be more lenient with decorated functions

## Implementation Strategy

### Phase 1: Improve Function Tracking
- Track functions with qualified names (module.Class.function)
- Distinguish between methods and functions
- Handle imports properly

### Phase 2: Expand Stdlib Coverage
- Add comprehensive stdlib function list
- Auto-detect stdlib modules (sys, os, pathlib, etc.)
- Skip validation for external packages

### Phase 3: Context-Aware Validation
- Analyze import statements to resolve module.function calls
- Track class hierarchies for method resolution
- Handle attribute access chains (a.b.c.method())

### Phase 4: Decorator Awareness
- Detect common decorators (@property, @staticmethod, @classmethod)
- Skip validation for heavily decorated functions
- Handle wrapper patterns

## Expected Improvements

**Current**: 42 errors (mostly false positives)
**Target**: <10 errors (real bugs only)

**False Positive Reduction**: ~75%