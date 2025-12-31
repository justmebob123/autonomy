# Validation Configuration Guide

## Overview

The code validators are now **project-agnostic** and can be customized for any Python project through a configuration file. This guide explains how to configure the validators for your specific project needs.

## Configuration File

### Location

The validators automatically look for a configuration file in these locations (in order):
1. Path specified via `--config` command-line argument
2. `.validation_config.json` in the project root
3. If no config found, uses sensible defaults

### Format

The configuration file is a JSON file with the following structure:

```json
{
  "known_base_classes": {
    "BaseClassName": ["method1", "method2"]
  },
  "stdlib_classes": ["ClassName1", "ClassName2"],
  "function_patterns": ["function1", "function2"],
  "stdlib_functions": ["func1", "func2"],
  "project_patterns": {
    "base_classes": {
      "ProjectBase": ["run", "stop"]
    },
    "custom_functions": ["project_func"]
  }
}
```

## Configuration Options

### 1. `known_base_classes`

Define base classes and their expected methods. This helps the validator understand inheritance patterns.

**Example:**
```json
{
  "known_base_classes": {
    "ast.NodeVisitor": ["visit", "generic_visit"],
    "BasePhase": ["execute", "chat_with_history"],
    "CustomTool": ["run", "execute", "validate"]
  }
}
```

**Use Case:** When you have base classes that define methods that subclasses should have.

### 2. `stdlib_classes`

List standard library or third-party classes that should skip validation.

**Example:**
```json
{
  "stdlib_classes": [
    "Path", "PosixPath",
    "dict", "list", "set",
    "Logger", "Thread"
  ]
}
```

**Use Case:** Prevent false positives for well-known library classes.

### 3. `function_patterns`

List functions that return objects (not classes) that should be recognized.

**Example:**
```json
{
  "function_patterns": [
    "get_logger",
    "get_config",
    "create_instance",
    "factory_method"
  ]
}
```

**Use Case:** Factory functions, getters, and other patterns that return objects.

### 4. `stdlib_functions`

List standard library or common functions with flexible signatures.

**Example:**
```json
{
  "stdlib_functions": [
    "parse", "get", "post",
    "format", "join", "split",
    "read", "write", "open"
  ]
}
```

**Use Case:** Functions that have variable arguments or are too common to validate strictly.

### 5. `project_patterns`

Project-specific patterns that extend the defaults.

**Example:**
```json
{
  "project_patterns": {
    "base_classes": {
      "ProjectBase": ["initialize", "cleanup"],
      "ServiceBase": ["start", "stop", "restart"]
    },
    "custom_functions": [
      "get_service",
      "create_handler",
      "build_pipeline"
    ]
  }
}
```

**Use Case:** Project-specific base classes and functions.

## Usage Examples

### Basic Usage (No Config)

```bash
# Uses default configuration
python bin/validate_all.py .
```

### With Custom Config

```bash
# Use specific config file
python bin/validate_all.py . --config my_config.json
```

### Individual Validators

```bash
# Type usage validation
python bin/validate_type_usage.py . --config my_config.json

# Method existence validation
python bin/validate_method_existence.py . --config my_config.json

# Function call validation
python bin/validate_function_calls.py . --config my_config.json
```

## Creating a Config for Your Project

### Step 1: Start with Example

Copy the example configuration:
```bash
cp .validation_config.example.json .validation_config.json
```

### Step 2: Identify Your Base Classes

Look for base classes in your project:
```python
class MyBaseClass(ABC):
    def required_method(self):
        pass
```

Add them to `known_base_classes`:
```json
{
  "known_base_classes": {
    "MyBaseClass": ["required_method"]
  }
}
```

### Step 3: Add Project-Specific Patterns

Identify common patterns in your project:
- Factory functions
- Getter functions
- Service locators
- Custom base classes

Add them to the appropriate sections.

### Step 4: Test and Refine

Run the validators and check for false positives:
```bash
python bin/validate_all.py .
```

If you see false positives, add the relevant classes/functions to your config.

## Default Configuration

The validators come with sensible defaults that work for most Python projects:

### Default Base Classes
- `ast.NodeVisitor` - AST visitor pattern
- `ABC` - Abstract base classes
- `object` - Python base object

### Default Standard Library Classes
- **pathlib**: `Path`, `PosixPath`, `WindowsPath`
- **builtins**: `dict`, `list`, `set`, `tuple`, `str`, `int`, `float`, `bool`
- **collections**: `defaultdict`, `OrderedDict`, `Counter`, `deque`
- **datetime**: `datetime`, `date`, `time`, `timedelta`
- **threading**: `Thread`, `Lock`, `Event`, `Queue`
- **logging**: `Logger`, `Handler`, `Formatter`
- And many more...

### Default Function Patterns
- `getattr`, `hasattr`, `isinstance`, `type`
- `open`, `print`, `input`
- `enumerate`, `zip`, `map`, `filter`
- And many more...

## Project-Agnostic Design

The validators are designed to work with **any Python project** without hardcoding:

1. **Dynamic Project Detection**: Automatically detects project name from `setup.py`, `pyproject.toml`, or directory name
2. **Flexible Import Resolution**: Handles both absolute and relative imports
3. **Configurable Rules**: All validation rules can be customized
4. **Sensible Defaults**: Works out-of-the-box for most projects

## Troubleshooting

### False Positives

If you see false positives:
1. Check if the class/function should be in `stdlib_classes` or `function_patterns`
2. Add project-specific patterns to `project_patterns`
3. Verify base class methods are listed in `known_base_classes`

### Missing Errors

If the validator misses real errors:
1. Check if classes are incorrectly listed in `stdlib_classes`
2. Verify function signatures are correct
3. Ensure base classes are properly defined

### Configuration Not Loading

1. Verify JSON syntax is correct
2. Check file path is correct
3. Ensure file is named `.validation_config.json` or use `--config` flag

## Best Practices

1. **Start Small**: Begin with the example config and add only what you need
2. **Document Changes**: Comment why you added specific entries
3. **Version Control**: Commit your config file to version control
4. **Team Alignment**: Ensure team agrees on validation rules
5. **Regular Updates**: Update config as project evolves

## Advanced Usage

### Multiple Configs

Use different configs for different parts of your project:
```bash
# Validate core with strict rules
python bin/validate_all.py core/ --config strict_config.json

# Validate tests with relaxed rules
python bin/validate_all.py tests/ --config test_config.json
```

### CI/CD Integration

Add validation to your CI/CD pipeline:
```yaml
# .github/workflows/validate.yml
- name: Validate Code
  run: |
    python bin/validate_all.py . --config .validation_config.json
```

### Pre-commit Hook

Add validation as a pre-commit hook:
```bash
#!/bin/bash
python bin/validate_all.py . --config .validation_config.json
```

## Support

For issues or questions:
1. Check this guide
2. Review the example config
3. Examine the default configuration in `validation_config.py`
4. Open an issue on the project repository

---

**Note**: The validators are designed to be helpful, not perfect. Use them as a guide to improve code quality, not as absolute truth. Always apply human judgment when reviewing validation results.