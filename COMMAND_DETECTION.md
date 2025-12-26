# Intelligent Command Detection System

## Overview

The autonomy system now includes an intelligent command detection feature that automatically determines the correct command to run your project. This eliminates the need to manually specify the `--command` argument in most cases.

## How It Works

When you run the system without providing a `--command` argument, the CommandDetector analyzes your project structure and attempts to identify the appropriate command using multiple detection strategies:

### Detection Strategies (in priority order)

1. **Python Package Detection**
   - Looks for `__main__.py` in subdirectories
   - Detects if current directory is a Python package
   - Example: `python -m mypackage`

2. **Python Script Detection**
   - Searches for common entry points: `main.py`, `run.py`, `app.py`, `start.py`, `server.py`, `manage.py`
   - Analyzes `.py` files for `if __name__ == "__main__"` blocks
   - Example: `python main.py`

3. **Node.js Project Detection**
   - Reads `package.json` for start scripts
   - Checks for `npm start`, `npm run dev`, or main entry point
   - Example: `npm start`

4. **Makefile Detection**
   - Looks for `Makefile`, `makefile`, or `GNUmakefile`
   - Searches for `run:` or `start:` targets
   - Example: `make run`

5. **Docker Detection**
   - Detects `docker-compose.yml` or `Dockerfile`
   - Extracts CMD from Dockerfile if available
   - Example: `docker-compose up`

6. **Shell Script Detection**
   - Finds executable shell scripts: `run.sh`, `start.sh`, `launch.sh`
   - Example: `./run.sh`

7. **Generic Executable Detection**
   - Identifies any executable files in project root
   - Example: `./myapp`

## Usage

### Basic Usage (Auto-Detection)

```bash
# Let the system detect the command automatically
python3 run.py --debug-qa /path/to/project

# With verbose output
python3 run.py --debug-qa -vv /path/to/project

# With log file monitoring
python3 run.py --debug-qa --follow /path/to/log /path/to/project
```

### Manual Command Override

You can still manually specify a command if needed:

```bash
# Explicitly provide command
python3 run.py --debug-qa --command "python main.py --arg1 --arg2" /path/to/project

# With environment variables
python3 run.py --debug-qa --command "ENV_VAR=value python app.py" /path/to/project
```

## Examples

### Example 1: Python Package

**Project Structure:**
```
myproject/
├── mypackage/
│   ├── __init__.py
│   ├── __main__.py
│   └── core.py
└── setup.py
```

**Auto-detected command:** `python -m mypackage`

### Example 2: Python Script

**Project Structure:**
```
myproject/
├── main.py
├── utils.py
└── requirements.txt
```

**Auto-detected command:** `python main.py`

### Example 3: Node.js Application

**Project Structure:**
```
myproject/
├── package.json
├── index.js
└── node_modules/
```

**package.json:**
```json
{
  "scripts": {
    "start": "node index.js"
  }
}
```

**Auto-detected command:** `npm start`

### Example 4: Makefile Project

**Project Structure:**
```
myproject/
├── Makefile
├── src/
└── build/
```

**Makefile:**
```makefile
run:
    ./build/myapp
```

**Auto-detected command:** `make run`

## Detection Output

When auto-detection runs, you'll see output like:

```
🤖 No --command provided, attempting auto-detection...
✅ Auto-detected command: python main.py
   Reason: Found Python entry point: main.py
   Python files: 5 found
```

If detection fails:

```
🤖 No --command provided, attempting auto-detection...
⚠️  Could not auto-detect command: Could not detect appropriate command for this project
   You can specify a command with --command 'your command here'
   Continuing with static analysis only (no runtime testing).
```

## Programmatic Usage

You can also use the CommandDetector programmatically:

```python
from pipeline.command_detector import CommandDetector

# Create detector
detector = CommandDetector("/path/to/project")

# Detect command
command, reason = detector.detect_command()
if command:
    print(f"Command: {command}")
    print(f"Reason: {reason}")

# Get project info
info = detector.get_project_info()
print(f"Python files: {info['python_files']}")
print(f"Config files: {info['config_files']}")
```

## Benefits

1. **Convenience**: No need to remember or type the command every time
2. **Consistency**: Always uses the correct command for the project
3. **Flexibility**: Can still override with manual command when needed
4. **Intelligence**: Understands multiple project types and structures
5. **Transparency**: Shows what was detected and why

## Fallback Behavior

If command detection fails:
- The system continues with **static analysis only**
- Syntax errors and import errors are still detected and fixed
- Runtime testing is skipped (no program execution)
- You can still manually provide `--command` to enable runtime testing

## Supported Project Types

- ✅ Python packages (with `__main__.py`)
- ✅ Python scripts (with `if __name__ == "__main__"`)
- ✅ Node.js applications (with `package.json`)
- ✅ Makefile-based projects
- ✅ Docker/Docker Compose projects
- ✅ Shell script-based projects
- ✅ Generic executable projects

## Future Enhancements

Planned improvements:
- Support for more project types (Rust, Go, Java, etc.)
- Learning from user corrections (if user overrides, remember for next time)
- Support for complex multi-command projects
- Integration with project-specific configuration files
- Detection of test commands vs. run commands

## Troubleshooting

### Detection Not Working?

1. **Check project structure**: Ensure your project has recognizable entry points
2. **Use verbose mode**: Run with `-vv` to see detailed detection process
3. **Manual override**: Use `--command` to specify the correct command
4. **File permissions**: Ensure executable files have proper permissions

### Wrong Command Detected?

1. **Manual override**: Use `--command` to specify the correct command
2. **Report issue**: Help improve detection by reporting the case
3. **Check priority**: Detection uses priority order - earlier matches win

### Need Custom Arguments?

Always use `--command` for commands with custom arguments:

```bash
python3 run.py --debug-qa --command "python main.py --custom-arg value" /path/to/project
```

## Implementation Details

The CommandDetector is implemented in `pipeline/command_detector.py` and uses:
- File system analysis (pathlib)
- JSON parsing for package.json
- AST analysis for Python files
- Regex patterns for Makefile parsing
- Permission checks for executables

The detection is fast (< 100ms) and non-invasive (read-only operations).