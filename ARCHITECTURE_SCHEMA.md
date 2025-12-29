# Architecture Document Schema

This document defines the schema for ARCHITECTURE.md files in projects managed by the autonomy pipeline.

## Purpose

The ARCHITECTURE.md file serves as the **single source of truth** for:
- Project structure and organization
- Library vs application code distinction
- Naming conventions
- Module organization patterns
- Integration guidelines

## Schema

### 1. Project Structure Section

```markdown
## Project Structure

### Library Directories
Directories containing reusable library code (meant to be imported):
- `core/` - Core functionality and utilities
- `lib/` - Shared libraries
- `utils/` - Utility functions
- `models/` - Data models

### Application Directories
Directories containing application-specific code:
- `app/` - Main application code
- `services/` - Service implementations
- `api/` - API endpoints

### Test Directories
Directories containing test code:
- `tests/` - Test files
- `test/` - Alternative test directory
```

### 2. Naming Conventions Section

```markdown
## Naming Conventions

### File Naming
- **Preferred**: `snake_case.py` (e.g., `email_handler.py`)
- **Alternative**: `snake_case.py` (e.g., `email.py`)
- **Avoid**: `camelCase.py`, `PascalCase.py`

### Module Naming
- **Preferred**: Descriptive names (e.g., `email_alerts`, `user_management`)
- **Avoid**: Generic names (e.g., `utils`, `helpers`) without context

### Class Naming
- **Standard**: `PascalCase` (e.g., `EmailHandler`, `UserManager`)
```

### 3. Module Organization Section

```markdown
## Module Organization

### Feature-Based Organization
Group related functionality together:
```
project/
├── email/
│   ├── __init__.py
│   ├── handler.py
│   ├── templates.py
│   └── validators.py
├── users/
│   ├── __init__.py
│   ├── models.py
│   └── services.py
```

### Layer-Based Organization
Organize by architectural layer:
```
project/
├── models/
│   ├── user.py
│   └── email.py
├── services/
│   ├── user_service.py
│   └── email_service.py
└── handlers/
    ├── user_handler.py
    └── email_handler.py
```
```

### 4. Integration Guidelines Section

```markdown
## Integration Guidelines

### Duplicate Detection Rules
- Files with similar names in different directories may indicate duplication
- Example: `pipeline/email_alerts.py` and `alerts/email.py`
- Action: Flag as integration conflict for review

### Dead Code Review Rules
- Library code may appear unused if not yet integrated
- Don't delete library code without review
- Mark for integration review instead

### Conflict Resolution Process
1. Identify duplicate implementations
2. Compare feature sets
3. Determine correct location based on architecture
4. Merge features into unified implementation
5. Delete obsolete file
```

## Usage by Pipeline

The pipeline uses this schema to:

1. **Parse ARCHITECTURE.md** in the project directory
2. **Extract library directories** from "Library Directories" section
3. **Extract naming conventions** from "Naming Conventions" section
4. **Apply integration rules** from "Integration Guidelines" section
5. **Make architecture-aware decisions** instead of hardcoded assumptions

## Example ARCHITECTURE.md

See `ARCHITECTURE_EXAMPLE.md` for a complete example.