# Complete Validator Analysis

**Total Validators:** 13

**Average Polytopic Score:** 6.00/6 (100.0%)

## Detailed Analysis

### type_usage_validator.py

- **File:** `pipeline/analysis/type_usage_validator.py`
- **Lines:** 645
- **Classes:** TypeUsageError, LegacyTypeInfo, TypeTracker, TypeUsageChecker, TypeUsageValidator
- **Validation Methods:** validate_all, _validate_file
- **Polytopic Score:** 6/6

**Integration Status:**
- Message Bus: ✅
- Pattern Recognition: ✅
- Correlation Engine: ✅
- Optimizer: ✅
- Adaptive Prompts: ✅
- Dimensional Space: ✅

### method_existence_validator.py

- **File:** `pipeline/analysis/method_existence_validator.py`
- **Lines:** 550
- **Classes:** MethodExistenceError, MethodExistenceValidator, MethodCallVisitor
- **Validation Methods:** 
- **Polytopic Score:** 6/6

**Integration Status:**
- Message Bus: ✅
- Pattern Recognition: ✅
- Correlation Engine: ✅
- Optimizer: ✅
- Adaptive Prompts: ✅
- Dimensional Space: ✅

### method_signature_validator.py

- **File:** `pipeline/analysis/method_signature_validator.py`
- **Lines:** 416
- **Classes:** MethodSignatureError, MethodCollector, MethodCallChecker, MethodSignatureValidator
- **Validation Methods:** validate_all, _validate_file
- **Polytopic Score:** 6/6

**Integration Status:**
- Message Bus: ✅
- Pattern Recognition: ✅
- Correlation Engine: ✅
- Optimizer: ✅
- Adaptive Prompts: ✅
- Dimensional Space: ✅

### function_call_validator.py

- **File:** `pipeline/analysis/function_call_validator.py`
- **Lines:** 540
- **Classes:** FunctionCallError, FunctionCallValidator
- **Validation Methods:** validate_all, _validate_file
- **Polytopic Score:** 6/6

**Integration Status:**
- Message Bus: ✅
- Pattern Recognition: ✅
- Correlation Engine: ✅
- Optimizer: ✅
- Adaptive Prompts: ✅
- Dimensional Space: ✅

### enum_attribute_validator.py

- **File:** `pipeline/analysis/enum_attribute_validator.py`
- **Lines:** 390
- **Classes:** EnumAttributeError, EnumCollector, EnumUsageChecker, EnumAttributeValidator
- **Validation Methods:** validate_all, _validate_file
- **Polytopic Score:** 6/6

**Integration Status:**
- Message Bus: ✅
- Pattern Recognition: ✅
- Correlation Engine: ✅
- Optimizer: ✅
- Adaptive Prompts: ✅
- Dimensional Space: ✅

### dict_structure_validator.py

- **File:** `pipeline/analysis/dict_structure_validator.py`
- **Lines:** 644
- **Classes:** DictStructureError, DictStructureValidator
- **Validation Methods:** validate_all, _validate_file, _validate_dict_get, _validate_dict_subscript
- **Polytopic Score:** 6/6

**Integration Status:**
- Message Bus: ✅
- Pattern Recognition: ✅
- Correlation Engine: ✅
- Optimizer: ✅
- Adaptive Prompts: ✅
- Dimensional Space: ✅

### keyword_argument_validator.py

- **File:** `bin/validators/keyword_argument_validator.py`
- **Lines:** 494
- **Classes:** KeywordArgumentError, MethodSignatureCollector, KeywordArgumentChecker, KeywordArgumentValidator
- **Validation Methods:** validate_all, _validate_file
- **Polytopic Score:** 6/6

**Integration Status:**
- Message Bus: ✅
- Pattern Recognition: ✅
- Correlation Engine: ✅
- Optimizer: ✅
- Adaptive Prompts: ✅
- Dimensional Space: ✅

### strict_method_validator.py

- **File:** `bin/validators/strict_method_validator.py`
- **Lines:** 367
- **Classes:** StrictMethodValidator
- **Validation Methods:** validate, _validate_file, _validate_class, _validate_method_call
- **Polytopic Score:** 6/6

**Integration Status:**
- Message Bus: ✅
- Pattern Recognition: ✅
- Correlation Engine: ✅
- Optimizer: ✅
- Adaptive Prompts: ✅
- Dimensional Space: ✅

### syntax_validator.py

- **File:** `pipeline/syntax_validator.py`
- **Lines:** 299
- **Classes:** SyntaxValidator
- **Validation Methods:** validate_python_code, validate_and_fix
- **Polytopic Score:** 6/6

**Integration Status:**
- Message Bus: ✅
- Pattern Recognition: ✅
- Correlation Engine: ✅
- Optimizer: ✅
- Adaptive Prompts: ✅
- Dimensional Space: ✅

### tool_validator.py

- **File:** `pipeline/tool_validator.py`
- **Lines:** 654
- **Classes:** ToolMetrics, ToolValidator
- **Validation Methods:** validate_tool_creation_request, _validate_contexts, validate_parameters
- **Polytopic Score:** 6/6

**Integration Status:**
- Message Bus: ✅
- Pattern Recognition: ✅
- Correlation Engine: ✅
- Optimizer: ✅
- Adaptive Prompts: ✅
- Dimensional Space: ✅

### filename_validator.py

- **File:** `pipeline/validation/filename_validator.py`
- **Lines:** 519
- **Classes:** IssueLevel, FilenameIssue, FilenameValidator
- **Validation Methods:** validate
- **Polytopic Score:** 6/6

**Integration Status:**
- Message Bus: ✅
- Pattern Recognition: ✅
- Correlation Engine: ✅
- Optimizer: ✅
- Adaptive Prompts: ✅
- Dimensional Space: ✅

### architecture_validator.py

- **File:** `pipeline/analysis/architecture_validator.py`
- **Lines:** 527
- **Classes:** ArchitectureViolation, ArchitectureValidator
- **Validation Methods:** validate_file_locations, validate_naming_conventions, validate_all
- **Polytopic Score:** 6/6

**Integration Status:**
- Message Bus: ✅
- Pattern Recognition: ✅
- Correlation Engine: ✅
- Optimizer: ✅
- Adaptive Prompts: ✅
- Dimensional Space: ✅

### validator_coordinator.py

- **File:** `pipeline/analysis/validator_coordinator.py`
- **Lines:** 206
- **Classes:** ValidatorCoordinator
- **Validation Methods:** validate_all
- **Polytopic Score:** 6/6

**Integration Status:**
- Message Bus: ✅
- Pattern Recognition: ✅
- Correlation Engine: ✅
- Optimizer: ✅
- Adaptive Prompts: ✅
- Dimensional Space: ✅

