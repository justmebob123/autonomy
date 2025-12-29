# Example ARCHITECTURE.md

This is an example ARCHITECTURE.md file that projects can use as a template.

## Project Structure

### Library Directories
Directories containing reusable library code (meant to be imported):
- `alerts/` - Alert handling and notification system
- `monitors/` - Monitoring and health check components
- `core/` - Core functionality and base classes
- `reports/` - Report generation and formatting
- `cli/` - Command-line interface utilities

### Application Directories
Directories containing application-specific code:
- `pipeline/` - Main pipeline orchestration
- `app/` - Application entry points
- `services/` - Service implementations

### Test Directories
Directories containing test code:
- `tests/` - Unit and integration tests
- `test/` - Alternative test directory

## Naming Conventions

### File Naming
- **Preferred**: `snake_case.py` with descriptive names (e.g., `email_handler.py`)
- **Alternative**: Short descriptive names (e.g., `email.py`) when in feature directory
- **Avoid**: Generic names without context (e.g., `utils.py`, `helpers.py`)

### Module Naming
- **Preferred**: Feature-based names (e.g., `email_alerts`, `user_management`)
- **Library modules**: Short names acceptable (e.g., `email`, `auth`) when in library directory

### Class Naming
- **Standard**: `PascalCase` (e.g., `EmailHandler`, `AlertManager`)
- **Suffix conventions**: 
  - `*Handler` for request/event handlers
  - `*Manager` for resource managers
  - `*Service` for business logic services

## Module Organization

### Current Organization: Hybrid Approach
The project uses a hybrid of feature-based and layer-based organization:

**Library Layer** (reusable components):
```
alerts/
├── __init__.py
├── email.py          # Email alert handler
└── slack.py          # Slack alert handler

monitors/
├── __init__.py
└── health.py         # Health monitoring

core/
├── __init__.py
├── config.py         # Configuration management
└── logging.py        # Logging utilities
```

**Application Layer** (orchestration):
```
pipeline/
├── __init__.py
├── coordinator.py    # Main orchestration
├── email_alerts.py   # Pipeline-specific email integration
└── phases/           # Pipeline phases
```

## Integration Guidelines

### Duplicate Detection Rules
- **Pattern**: Files with similar functionality in different directories
- **Example**: `pipeline/email_alerts.py` and `alerts/email.py`
- **Action**: Flag as integration conflict, review both implementations
- **Resolution**: Merge features, standardize on library location (`alerts/email.py`)

### Dead Code Review Rules
- **Library modules** may appear unused during development
- **Don't delete** library code without integration review
- **Mark for review** with context about potential usage
- **Check imports** across entire codebase before flagging as dead

### Conflict Resolution Process
1. **Detect**: Identify files with similar names or functionality
2. **Analyze**: Compare feature sets and implementations
3. **Decide**: Determine correct location based on:
   - Is it reusable? → Library directory
   - Is it application-specific? → Application directory
4. **Merge**: Combine features into unified implementation
5. **Clean**: Delete obsolete file and update imports

### Integration Priorities
1. **Library code first**: Implement in library directories
2. **Application integration**: Use library code from application layer
3. **Avoid duplication**: Don't reimplement library functionality
4. **Standardize naming**: Follow conventions consistently

## Current Known Issues

### Integration Conflicts
- `pipeline/email_alerts.py` vs `alerts/email.py`
  - **Status**: Duplicate implementation detected
  - **Recommendation**: Review both, merge to `alerts/email.py`, update pipeline imports
  - **Priority**: High - causes confusion and maintenance burden

### Naming Inconsistencies
- None currently identified

### Dead Code Candidates
- None currently identified (all library code assumed to be for future integration)