# Project-Agnostic Validator Improvements

## Overview
Make all validation tools project-agnostic and remove hardcoded references to "autonomy" project.

## Tasks

### 1. Remove Hardcoded Project Names
- [x] Fix method_existence_validator.py - remove hardcoded "autonomy" prefix handling
- [x] Make import path resolution dynamic based on actual project structure
- [x] Remove any other project-specific assumptions

### 2. Make Base Classes Configurable
- [x] Move known_base_classes to configuration file
- [x] Move stdlib_classes to configuration file
- [x] Move function_patterns to configuration file
- [x] Allow users to extend these lists via config

### 3. Improve Import Resolution
- [x] Detect project root dynamically (look for setup.py, pyproject.toml, etc.)
- [x] Build import map from actual project structure
- [x] Handle relative imports correctly without hardcoding
- [x] Support multiple project layouts (src/, flat, etc.)

### 4. Configuration System
- [x] Create validation_config.py module
- [x] Allow customization of:
  - Known base classes and their methods
  - Standard library classes to skip
  - Function patterns to recognize
  - Custom validation rules
- [x] Provide sensible defaults that work for most projects
- [x] Create example config file (.validation_config.example.json)

### 5. Update All Validators
- [x] type_tracker.py - ensure project-agnostic
- [x] type_usage_validator.py - ensure project-agnostic
- [x] method_existence_validator.py - remove hardcoding
- [x] function_call_validator.py - ensure project-agnostic

### 6. Update bin/ Scripts
- [x] validate_all.py - add config support
- [x] validate_type_usage.py - add config support
- [x] validate_method_existence.py - add config support
- [x] validate_function_calls.py - add config support

### 7. Documentation
- [x] Create VALIDATION_CONFIG_GUIDE.md with configuration options
- [x] Add examples for different project types
- [x] Document how to customize validators
- [x] Add troubleshooting guide

### 8. Testing
- [x] Test on autonomy project (45 errors - working correctly)
- [ ] Create test for simple Python project
- [ ] Verify configuration loading works
- [ ] Verify project name detection works