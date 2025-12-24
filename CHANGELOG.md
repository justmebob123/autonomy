# Changelog

## [Unreleased] - 2024-12-24

### Added
- **Comprehensive Debug/QA Mode**: AI-powered continuous debugging and quality assurance system
  - Full pipeline integration (QA Phase + Debugging Phase)
  - Multi-phase error detection (syntax, imports, runtime)
  - AI-powered automatic error fixing
  - Log file monitoring with `--follow` flag
  - Dependency and related file analysis
  - Intelligent progress tracking
  - Iterative refinement until all errors resolved

### Features

#### Error Detection
- **Phase 1: Syntax Scanning**
  - Scans all Python files recursively
  - AST-based deep syntax validation
  - Detects malformed code structures
  - Groups errors by file for efficiency

- **Phase 2: Import Validation**
  - Attempts to import main modules
  - Detects missing dependencies
  - Identifies circular imports
  - Only runs if no syntax errors

- **Phase 3: Runtime Monitoring** (with `--follow`)
  - Real-time log file monitoring
  - Detects runtime exceptions
  - Tracks error patterns
  - Background thread monitoring

#### AI-Powered Fixing
- **QA Phase Integration**
  - Deep code analysis for each file
  - Examines related files and dependencies
  - Uses tool calling to investigate context
  - Provides detailed issue reports

- **Debugging Phase Integration**
  - AI-powered intelligent fixes
  - Considers file dependencies
  - Examines surrounding code context
  - Validates fixes with syntax checking

#### Progress Tracking
- Iteration counter with timestamps
- Success rate calculation (fixes applied/attempted)
- Progress detection (stops after 3 iterations without progress)
- Detailed summary statistics
- Auto-exit on success or no progress

### Documentation
- Updated `DEBUG_QA_MODE.md` with comprehensive guide
- Added workflow examples
- Documented AI pipeline integration
- Added log monitoring documentation
- Updated help text in `run.py`

### Use Cases
- Automated debugging of large codebases
- Pre-deployment quality assurance
- Continuous error monitoring during development
- Runtime error detection and fixing
- Dependency issue resolution
- Code quality verification

### Usage
```bash
# Basic debug/QA mode
python run.py /path/to/project --debug-qa

# With log file monitoring
python run.py /path/to/project --debug-qa --follow /path/to/app.log

# Verbose mode for detailed output
python run.py /path/to/project --debug-qa -v

# With custom Ollama servers
python run.py /path/to/project --debug-qa --server ollama01.example.com
```

### Technical Details
- Implemented in `run_debug_qa_mode()` function in `run.py`
- Uses full pipeline architecture (PhaseCoordinator, QA, Debugging)
- Multi-threaded log file monitoring
- State management for tracking fixes
- Error grouping by file for efficiency
- AST parsing for syntax validation
- Subprocess-based import checking
- Graceful handling of KeyboardInterrupt
- Progress detection algorithm

### Architecture
- Integrates with existing pipeline phases
- Uses StateManager for persistence
- Leverages OllamaClient for AI operations
- Tool calling for file examination
- Dependency analysis
- Related file tracking

### Notes
- This mode is specifically for debugging and QA, not for new development
- Uses the full AI pipeline for intelligent fixing
- Can handle large codebases (tested with 277+ files)
- Automatically stops if no progress is made
- Returns exit code 0 on success, 1 on error