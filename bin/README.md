# General Purpose Python Code Validation Tools

## Overview

This directory contains **GENERAL PURPOSE** validation tools that can analyze **ANY Python codebase**, not just this project. These tools are designed to be used standalone on any Python project.

## Philosophy

These tools are:
- ✅ **General Purpose** - Can analyze any Python codebase
- ✅ **Standalone** - Don't require project-specific configuration
- ✅ **Explicit** - Require explicit path arguments (no hidden defaults)
- ✅ **Portable** - Can be copied and used anywhere

## Available Tools

### 1. validate_all_enhanced.py
**Comprehensive validation using shared symbol table**

```bash
python bin/validate_all_enhanced.py <project_directory>
```

Runs all validators with a shared symbol table for improved accuracy:
- Type usage validation
- Method existence validation
- Function call validation
- Enum attribute validation
- Method signature validation

**Examples:**
```bash
# Analyze a Django project
python bin/validate_all_enhanced.py /home/user/my-django-project

# Analyze a Flask app
python bin/validate_all_enhanced.py /var/www/my-flask-app

# Analyze any Python code
python bin/validate_all_enhanced.py /tmp/random-python-code

# Use custom config
python bin/validate_all_enhanced.py /path/to/project --config custom.yaml
```

### 2. validate_type_usage.py
**Validates type annotations and usage**

```bash
python bin/validate_type_usage.py <project_directory>
```

Checks:
- Dataclass field types
- Type annotation consistency
- Type usage patterns

**Examples:**
```bash
python bin/validate_type_usage.py /home/user/django-app
python bin/validate_type_usage.py /var/www/flask-app
```

### 3. validate_method_existence.py
**Validates that called methods exist**

```bash
python bin/validate_method_existence.py <project_directory>
```

Detects:
- Calls to non-existent methods
- Typos in method names
- Missing method definitions

**Examples:**
```bash
python bin/validate_method_existence.py /home/user/project
python bin/validate_method_existence.py /tmp/test_code
```

### 4. validate_method_signatures.py
**Validates method call signatures**

```bash
python bin/validate_method_signatures.py <project_directory>
```

Checks:
- Correct number of arguments
- Required vs optional parameters
- Argument count mismatches

**Examples:**
```bash
python bin/validate_method_signatures.py /path/to/project
```

### 5. validate_function_calls.py
**Validates function calls**

```bash
python bin/validate_function_calls.py <project_directory>
```

Checks:
- Function existence
- Call patterns
- Import usage

**Examples:**
```bash
python bin/validate_function_calls.py /home/user/python-project
```

### 6. validate_enum_attributes.py
**Validates enum attribute access**

```bash
python bin/validate_enum_attributes.py <project_directory>
```

Checks:
- Enum member access
- Attribute existence
- Enum usage patterns

**Examples:**
```bash
python bin/validate_enum_attributes.py /path/to/project
```

### 7. validate_dict_structure.py
**Validates dictionary structure patterns**

```bash
python bin/validate_dict_structure.py <project_directory>
```

Checks:
- Dictionary key access
- Structure consistency
- Common patterns

**Examples:**
```bash
python bin/validate_dict_structure.py /home/user/project
```

### 8. validate_all.py
**Run all validators (legacy version)**

```bash
python bin/validate_all.py <project_directory>
```

Runs all validators without shared symbol table.

**Examples:**
```bash
python bin/validate_all.py /path/to/project
```

## Usage Patterns

### Analyze Any Project
```bash
# Django project
python bin/validate_all_enhanced.py ~/projects/my-django-site

# Flask application
python bin/validate_all_enhanced.py /var/www/flask-app

# FastAPI service
python bin/validate_all_enhanced.py ~/work/fastapi-service

# Random Python scripts
python bin/validate_all_enhanced.py /tmp/python-scripts
```

### Analyze Specific Subdirectories
```bash
# Only analyze the src directory
python bin/validate_type_usage.py /path/to/project/src

# Only analyze tests
python bin/validate_method_existence.py /path/to/project/tests

# Only analyze a specific module
python bin/validate_all_enhanced.py /path/to/project/myapp
```

### Integration with CI/CD
```bash
# In your CI/CD pipeline
python /path/to/autonomy/bin/validate_all_enhanced.py $PROJECT_ROOT

# Exit code 0 = no errors, 1 = errors found
if python bin/validate_all_enhanced.py .; then
    echo "Validation passed"
else
    echo "Validation failed"
    exit 1
fi
```

### Piping File Lists (Future Feature)
```bash
# Find specific files and validate
find /path/to/project -name "*.py" -type f | python bin/validate_all.py --stdin

# Validate only modified files
git diff --name-only | grep "\.py$" | python bin/validate_all.py --stdin
```

## Error Handling

All tools:
- Return exit code 0 if no errors found
- Return exit code 1 if errors found
- Print clear error messages with file:line information
- Provide severity levels (critical, high, medium, low)

## Requirements

- Python 3.8+
- No external dependencies for basic validation
- Project-specific analyzers use the `pipeline.analysis` module

## Design Principles

### 1. Explicit Over Implicit
❌ **BAD:** `python validate.py` (assumes current directory)
✅ **GOOD:** `python validate.py /path/to/project` (explicit path)

### 2. General Purpose Over Project-Specific
❌ **BAD:** Hardcoded paths, project-specific assumptions
✅ **GOOD:** Works on any Python codebase

### 3. Clear Error Messages
❌ **BAD:** "Error in file.py"
✅ **GOOD:** "file.py:42: Method 'foo' does not exist on class 'Bar'"

### 4. Portable and Standalone
❌ **BAD:** Requires specific directory structure
✅ **GOOD:** Can be copied and used anywhere

## Contributing

When adding new validators:
1. Require explicit path argument (no defaults to ".")
2. Add clear usage message
3. Support arbitrary project paths
4. Include examples in docstring
5. Return proper exit codes
6. Update this README

## Examples of Real-World Usage

### Example 1: Validating a Django Project
```bash
$ python bin/validate_all_enhanced.py ~/projects/mysite
================================================================================
  ENHANCED COMPREHENSIVE CODE VALIDATION
================================================================================

📁 Project: /home/user/projects/mysite
⏰ Started: 2026-01-03 20:00:00

Symbol Table Statistics:
   Classes: 245
   Functions: 89
   Methods: 1234
   ...

✅ NO ERRORS FOUND
```

### Example 2: Finding Errors in Flask App
```bash
$ python bin/validate_method_existence.py /var/www/flask-app
🔍 Validating method existence in: /var/www/flask-app
================================================================================

❌ ERRORS FOUND (3)
================================================================================

1. app/views.py:42
   Class: UserView
   Method: get_user_data
   Message: Method 'get_user_data' does not exist on class 'UserView'

2. app/models.py:78
   Class: User
   Method: save_to_db
   Message: Method 'save_to_db' does not exist on class 'User'
   
...
```

### Example 3: Validating Random Python Code
```bash
$ python bin/validate_type_usage.py /tmp/test_scripts
🔍 Validating type usage in: /tmp/test_scripts
================================================================================

✅ NO ERRORS FOUND
```

## FAQ

**Q: Can I use these tools on non-Python projects?**
A: No, these tools are specifically designed for Python codebases.

**Q: Do I need to install anything?**
A: Just Python 3.8+ and the tools themselves. No external dependencies for basic validation.

**Q: Can I use these tools in my own projects?**
A: Yes! These are general-purpose tools. Copy them and use them anywhere.

**Q: Why do I need to specify the path explicitly?**
A: To make it clear what's being analyzed and to avoid hidden assumptions about directory structure.

**Q: Can I validate multiple projects at once?**
A: Currently, you need to run the tool once per project. Multi-project support is planned.

**Q: What if my project has a custom structure?**
A: These tools work with any Python code structure. Just point them at the root directory.

## License

These tools are part of the autonomy project and follow the same license.

## Support

For issues or questions:
1. Check this README
2. Review the tool's docstring
3. Run with `--help` flag (if supported)
4. Check the autonomy project documentation