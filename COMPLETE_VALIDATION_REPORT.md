# Complete Validation Report

## Summary

**Total Validators:** 9
**Passed:** 2
**Failed:** 7

## Detailed Results

### Type Usage Validator

**Status:** ❌ FAIL

**Errors:**
```
Traceback (most recent call last):
  File "/workspace/autonomy/pipeline/analysis/type_usage_validator.py", line 16, in <module>
    from .validation_config import ValidationConfig
ImportError: attempted relative import with no known parent package

```

### Method Existence Validator

**Status:** ❌ FAIL

**Errors:**
```
Traceback (most recent call last):
  File "/workspace/autonomy/pipeline/analysis/method_existence_validator.py", line 16, in <module>
    from .validation_config import ValidationConfig, get_project_root, detect_project_name
ImportError: attempted relative import with no known parent package

```

### Method Signature Validator

**Status:** ❌ FAIL

**Errors:**
```
Traceback (most recent call last):
  File "/workspace/autonomy/pipeline/analysis/method_signature_validator.py", line 16, in <module>
    from .symbol_table import SymbolTable
ImportError: attempted relative import with no known parent package

```

### Function Call Validator

**Status:** ❌ FAIL

**Errors:**
```
Traceback (most recent call last):
  File "/workspace/autonomy/pipeline/analysis/function_call_validator.py", line 20, in <module>
    from .validation_config import ValidationConfig
ImportError: attempted relative import with no known parent package

```

### Enum Attribute Validator

**Status:** ❌ FAIL

**Errors:**
```
Traceback (most recent call last):
  File "/workspace/autonomy/pipeline/analysis/enum_attribute_validator.py", line 16, in <module>
    from .symbol_table import SymbolTable
ImportError: attempted relative import with no known parent package

```

### Keyword Argument Validator

**Status:** ✅ PASS

**Output:**
```
🔍 Validating keyword arguments in: .
================================================================================

📊 SUMMARY
   Methods found: 2469
   Total errors: 0
   By severity:

✅ NO ERRORS FOUND

================================================================================

```

### Dict Structure Validator

**Status:** ❌ FAIL

**Errors:**
```
/bin/sh: 1: Syntax error: word unexpected (expecting ")")

```

### Strict Method Validator

**Status:** ✅ PASS

**Output:**
```
📁 Project: .

🔍 Building symbol table...
✅ Symbol table built: 710 classes

🔍 Running strict method validation...
⚠️  Error processing test_unified_model_tool.py: 'ClassInfo' object has no attribute 'get'
⚠️  Error processing test_specialist_requests.py: 'ClassInfo' object has no attribute 'get'
⚠️  Error processing analyze_all_publish_calls.py: 'ClassInfo' object has no attribute 'get'
⚠️  Error processing test_specialists.py: 'ClassInfo' object has no attribute 'get'
⚠️  Error processing implement_learning_systems.py: 'ClassInfo' object has no attribute 'get'
⚠️  Error processing analyze_deep_implementation.py: 'ClassInfo' object has no attribute 'get'
⚠️  Error processing analyze_polytopic_comprehensive.py: 'ClassInfo' object has no attribute 'get'
⚠️  Error processing analyze_placeholders.py: 'ClassInfo' object has no attribute 'get'
⚠️  Error processing analyze_polytopic_deep.py: 'ClassInfo' object has no attribute 'get'
⚠️  Error processing HYPERDIMENSIONAL_ANALYSIS_FRAMEWORK.py:
... (truncated)
```

**Errors:**
```
  Duplicate classes: 2

```

### Syntax Validator

**Status:** ❌ FAIL

**Errors:**
```
Traceback (most recent call last):
  File "/workspace/autonomy/pipeline/syntax_validator.py", line 10, in <module>
    from .logging_setup import get_logger
ImportError: attempted relative import with no known parent package

```

