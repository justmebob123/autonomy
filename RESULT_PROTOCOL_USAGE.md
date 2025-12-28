# Result Protocol Usage Guide

## Overview

The Result Protocol provides a standardized interface for handling operation results across the autonomy codebase. It ensures consistent access to success status, data, errors, and metadata regardless of the underlying result type.

## The Result Protocol

```python
from pipeline.result_protocol import Result

class Result(Protocol):
    @property
    def success(self) -> bool:
        """Whether the operation succeeded"""
        
    @property
    def data(self) -> Any:
        """Result data (if successful)"""
        
    @property
    def error(self) -> Optional[str]:
        """Error message (if failed)"""
        
    @property
    def metadata(self) -> Dict[str, Any]:
        """Additional metadata"""
```

## Using Result Protocol

### 1. Wrapping Subprocess Results

```python
from pipeline.result_protocol import SubprocessResult
import subprocess

# Run a command
proc = subprocess.run(['ls', '-la'], capture_output=True, text=True)

# Wrap in Result protocol
result = SubprocessResult(proc)

# Access with standard interface
if result.success:
    print(f"Output: {result.data}")
else:
    print(f"Error: {result.error}")
    print(f"Return code: {result.metadata['returncode']}")
```

### 2. Wrapping Dict Results

```python
from pipeline.result_protocol import DictResult

# Existing dict-based result
analysis_result = {
    'success': True,
    'data': {'findings': [...], 'recommendations': [...]},
    'analysis_time': 1.5
}

# Wrap in Result protocol
result = DictResult(analysis_result)

# Access with standard interface
if result.success:
    findings = result.data['findings']
    analysis_time = result.metadata['analysis_time']
```

### 3. Auto-Wrapping with ensure_result()

```python
from pipeline.result_protocol import ensure_result

def process_result(raw_result):
    """Process any result type"""
    # Automatically wrap in appropriate adapter
    result = ensure_result(raw_result)
    
    # Now use standard interface
    if result.success:
        return result.data
    else:
        raise Exception(result.error)

# Works with subprocess
proc = subprocess.run(['echo', 'test'], capture_output=True, text=True)
process_result(proc)

# Works with dict
process_result({'success': True, 'data': 'test'})

# Works with objects already implementing Result
process_result(SubprocessResult(proc))
```

## Creating Custom Result Types

### Option 1: Implement the Protocol

```python
class CustomResult:
    """Custom result that implements Result protocol"""
    
    def __init__(self, success: bool, data: Any, error: Optional[str] = None):
        self._success = success
        self._data = data
        self._error = error
        self._metadata = {}
    
    @property
    def success(self) -> bool:
        return self._success
    
    @property
    def data(self) -> Any:
        return self._data
    
    @property
    def error(self) -> Optional[str]:
        return self._error
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata
```

### Option 2: Use DictResult

```python
def my_operation():
    """Return dict that can be wrapped in DictResult"""
    try:
        data = perform_operation()
        return {
            'success': True,
            'data': data,
            'operation_time': 1.5,
            'items_processed': 100
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'partial_data': None
        }

# Usage
result = DictResult(my_operation())
```

## Migration Strategy

### Phase 1: Add Protocol (✅ Complete)
- Created Result protocol
- Created adapters for common types
- Tested implementation

### Phase 2: Gradual Adoption (Current)
- Use `ensure_result()` when consuming results from multiple sources
- Wrap subprocess calls with `SubprocessResult`
- Wrap dict results with `DictResult`
- No need to change existing code immediately

### Phase 3: Standardization (Future)
- Update PhaseResult to implement Result protocol
- Update ModelResult to implement Result protocol
- Gradually migrate dict-based results to use DictResult

## Benefits

1. **Consistent Interface**: All results accessed the same way
2. **Type Safety**: Protocol enables type checking
3. **Error Handling**: Standardized error access
4. **Metadata**: Consistent way to attach additional info
5. **Backward Compatible**: Works with existing code via adapters

## Examples from Codebase

### Before (Inconsistent)
```python
# Different ways to check success
if result.returncode == 0:  # subprocess
if result.get('success'):   # dict
if result.success:          # object

# Different ways to get data
data = result.stdout        # subprocess
data = result.get('data')   # dict
data = result.data          # object
```

### After (Consistent)
```python
from pipeline.result_protocol import ensure_result

result = ensure_result(raw_result)

# Always the same
if result.success:
    data = result.data
else:
    error = result.error
```

## Testing

```python
from pipeline.result_protocol import Result

def test_my_function():
    result = my_function()
    
    # Verify it implements Result protocol
    assert isinstance(result, Result)
    
    # Test success case
    assert result.success == True
    assert result.data is not None
    assert result.error is None
    
    # Test metadata
    assert 'operation_time' in result.metadata
```

## Best Practices

1. **Use ensure_result()** when consuming results from unknown sources
2. **Wrap subprocess calls** immediately with SubprocessResult
3. **Return dicts** that can be wrapped with DictResult
4. **Document** what your result.data contains
5. **Include metadata** for debugging and monitoring
6. **Test** that your results implement the protocol

## Questions?

See `test_result_protocol.py` for comprehensive examples and tests.