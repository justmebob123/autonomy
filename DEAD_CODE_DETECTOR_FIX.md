# Critical Bug Fix: DeadCodeResult Missing unused_classes Attribute

## The Error

```
[ERROR] Dead code detection failed: 'DeadCodeResult' object has no attribute 'unused_classes'
```

## Root Cause

The `DeadCodeResult` dataclass was missing the `unused_classes` attribute, but multiple parts of the codebase were trying to access it:

1. **analysis_tools.py** - Line 193: `for file, cls in result.unused_classes`
2. **analysis_tools.py** - Line 204: `result.total_unused_classes`
3. **qa.py** - Line 948: `if gap_result.unused_classes`
4. **planning.py** - Line 601: `dead_code_result.unused_classes`
5. **handlers.py** - Line 2525: `result.total_unused_classes`

The `DeadCodeResult` class only had:
- `unused_functions`
- `unused_methods`
- `unused_imports`

But was missing:
- `unused_classes` ❌
- `total_unused_classes` property ❌

## The Fix

### 1. Added `unused_classes` Field to DeadCodeResult

```python
@dataclass
class DeadCodeResult:
    """Result of dead code analysis."""
    unused_functions: List[Tuple[str, str, int]] = field(default_factory=list)
    unused_methods: List[Tuple[str, str, int]] = field(default_factory=list)
    unused_classes: List[Tuple[str, str]] = field(default_factory=list)  # ADDED
    unused_imports: Dict[str, List[Tuple[str, int, str]]] = field(default_factory=dict)
```

### 2. Added `total_unused_classes` Property

```python
@property
def total_unused_classes(self) -> int:
    return len(self.unused_classes)
```

### 3. Updated `to_dict()` Method

```python
'unused_classes': [
    {'name': cls, 'file': file}
    for file, cls in self.unused_classes
],
```

### 4. Added Class Tracking to DeadCodeDetector

```python
# In __init__:
self.all_classes_defined: Dict[str, Tuple[str, int]] = {}
self.all_classes_used: Set[str] = set()

# In analyze_file:
for class_name, line in visitor.classes_defined.items():
    self.all_classes_defined[class_name] = (relative_path, line)

self.all_classes_used.update(visitor.functions_called)
```

### 5. Added `get_unused_classes()` Method

```python
def get_unused_classes(self) -> List[Tuple[str, str]]:
    """Get list of unused classes."""
    unused = []
    for class_name, (file, line) in self.all_classes_defined.items():
        if class_name not in self.all_classes_used:
            if not class_name.startswith('_'):
                unused.append((file, class_name))
    return sorted(unused)
```

### 6. Updated `analyze()` to Populate unused_classes

```python
result = DeadCodeResult(
    unused_functions=self.get_unused_functions(),
    unused_methods=self.get_unused_methods(),
    unused_classes=self.get_unused_classes(),  # ADDED
    unused_imports=self.get_unused_imports()
)
```

### 7. Updated Report Generation

```python
# Unused classes
lines.append(f"## UNUSED CLASSES ({result.total_unused_classes})")
lines.append("")
for file, class_name in result.unused_classes:
    lines.append(f"- {class_name} in {file}")
lines.append("")
```

## Impact

### Before Fix
- ❌ `detect_dead_code` tool crashed with AttributeError
- ❌ System couldn't analyze dead code
- ❌ Debugging phase failed repeatedly

### After Fix
- ✅ `detect_dead_code` tool works correctly
- ✅ Tracks unused classes alongside functions/methods
- ✅ Provides complete dead code analysis
- ✅ Debugging phase can proceed

## Files Modified

- `pipeline/analysis/dead_code.py` - Added complete class tracking functionality

## Testing

The fix ensures:
1. ✅ `DeadCodeResult` has all required attributes
2. ✅ Class tracking works alongside function/method tracking
3. ✅ Reports include unused classes
4. ✅ All code accessing `unused_classes` now works

## Related Issues

This bug was discovered while investigating why the debugging phase was failing with 206 tasks. The dead code detector was being called but crashing due to the missing attribute.

This is separate from the merge bug (which created corrupted files) - this is a missing feature in the dead code detector itself.