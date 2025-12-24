# Changelog

## [Unreleased] - 2024-12-24

### Added
- **Debug/QA Mode**: New `--debug-qa` command-line flag for continuous error detection and quality assurance
  - Comprehensive syntax error detection across all Python files
  - Import error checking with detailed reporting
  - AST-based deep syntax validation
  - Continuous loop for iterative debugging
  - User-friendly error reporting with file names, line numbers, and code snippets
  - Automatic exit when all errors are resolved
  - Manual exit option with Ctrl+C

### Features
- Scans all Python files recursively in project directory
- Skips `__pycache__`, `venv`, and `.venv` directories automatically
- Provides detailed error messages with:
  - File path (relative to project root)
  - Error type (SyntaxError, ImportError, etc.)
  - Line number and column position
  - Code snippet showing the problematic line
  - Clear error descriptions

### Documentation
- Added `DEBUG_QA_MODE.md` with comprehensive usage guide
- Updated help text in `run.py` to include new flag
- Added examples and best practices

### Use Cases
- Pre-deployment quality assurance
- Continuous debugging during development
- Error detection before running the full pipeline
- Code quality verification

### Usage
```bash
# Run debug/QA mode on current directory
python run.py . --debug-qa

# Run debug/QA mode on specific project
python run.py /path/to/project --debug-qa
```

### Technical Details
- Implemented in `run_debug_qa_mode()` function in `run.py`
- Uses `py_compile` for syntax checking
- Uses `ast.parse()` for deep syntax validation
- Uses `subprocess` for import verification
- Timeout protection for long-running import checks
- Graceful handling of KeyboardInterrupt

### Notes
- This mode is specifically for debugging and QA, not for new development
- Designed to work independently of the main development pipeline
- Returns exit code 0 on success, 1 on error