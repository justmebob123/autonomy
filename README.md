# AI Development Pipeline

An intelligent, multi-stage development pipeline that uses multiple Ollama servers
to autonomously develop, test, and deploy code based on a master plan.

## Features

- **Multi-Server Ollama Support**: Uses multiple Ollama servers (ollama01, ollama02)
  with intelligent model selection
- **Intelligent Model Selection**: Automatically selects the best model for each task
  based on capabilities and requirements
- **Multi-Stage Pipeline**:
  - Planning: Creates development tasks from MASTER_PLAN.md
  - Development: Implements code changes
  - QA: Automated code quality checks and AI review
  - Debug: AI-assisted debugging with suggested fixes
  - Commit: Automatic git commit and push on success
- **Step Tracking Files**:
  - `NEXT_STEPS.md`: Development task tracking
  - `QA_STEPS.md`: Quality assurance checklist
  - `DEBUG_STEPS.md`: Debugging workflow
- **Git Integration**: Automatic commits and pushes to your private git server

## Prerequisites

- Python 3.10+
- Git
- curl
- Access to Ollama servers (ollama01.clacorp.com, ollama02.clacorp.com)
- SSH key configured for git.clacorp.com

## Installation

### Option 1: Quick Install

```bash
# Clone or download the pipeline
mkdir -p ~/ai-dev-pipeline
cd ~/ai-dev-pipeline

# Download files (or copy them)
# ... (files should be in place)

# Make executable
chmod +x run_pipeline.sh

# Install Python dependencies
pip3 install --user requests pyyaml
```

### Option 2: Full Setup Script

```bash
#!/bin/bash
# Save as install.sh and run

INSTALL_DIR="$HOME/ai-dev-pipeline"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Create the files (copy pipeline.py, run_pipeline.sh, etc.)
# Or clone from your git repo:
# git clone git@git.clacorp.com:tools/ai-dev-pipeline.git .

# Install dependencies
pip3 install --user requests pyyaml

# Make executable
chmod +x run_pipeline.sh

# Add to PATH (optional)
echo 'export PATH="$HOME/ai-dev-pipeline:$PATH"' >> ~/.bashrc
source ~/.bashrc

echo "Installation complete!"
echo "Run: run_pipeline.sh --help"
```

## Usage

### Basic Usage

```bash
# Navigate to your project
cd /path/to/your/project

# Make sure MASTER_PLAN.md exists (see template)
# Run the pipeline
~/ai-dev-pipeline/run_pipeline.sh
```

### Command Line Options

```bash
# Show help
./run_pipeline.sh --help

# Run in specific directory
./run_pipeline.sh -d /path/to/project

# Custom git remote
./run_pipeline.sh -r git@github.com:user/repo.git

# Custom branch
./run_pipeline.sh -b develop

# Limit iterations
./run_pipeline.sh -i 5

# Only discover models (no development)
./run_pipeline.sh --discover

# Only run pre-flight checks
./run_pipeline.sh --check
```

### Environment Variables

```bash
export PROJECT_DIR=/path/to/project
export GIT_REMOTE=git@git.clacorp.com:user/repo.git
export GIT_BRANCH=main
export MAX_ITERATIONS=10
export TIMEOUT=600

./run_pipeline.sh
```

## Configuration

### MASTER_PLAN.md (Required)

Create a `MASTER_PLAN.md` in your project root. This file defines:
- Project vision and objectives
- Architecture and structure
- Development rules and constraints
- Quality standards
- Current phase and milestones

**Important**: The pipeline reads this file but NEVER modifies it.

See `templates/MASTER_PLAN.md` for a complete example.

### config.yaml (Optional)

For advanced configuration, copy `config.yaml` to your project:

```yaml
ollama:
  servers:
    - name: ollama01
      host: ollama01.clacorp.com
      port: 11434
    - name: ollama02
      host: ollama02.clacorp.com
      port: 11434
  timeout: 600

git:
  remote: git@git.clacorp.com:user/repo.git
  branch: main
  auto_push: true

pipeline:
  max_dev_iterations: 10
  max_qa_iterations: 5
  max_debug_iterations: 5
```

## Pipeline Stages

### 1. Model Discovery

The pipeline discovers all available models on configured Ollama servers:

```
ollama01.clacorp.com:
  - llama3.2:latest (3.2B)

ollama02.clacorp.com:
  - phi3:mini (3.8B)
  - llama3.2:3b (3.2B)
  - llama3.1:latest (8.0B)
```

### 2. Planning

- Reads `MASTER_PLAN.md` (read-only)
- Analyzes current codebase
- Creates `NEXT_STEPS.md` with development tasks
- Resumes from existing `NEXT_STEPS.md` if present

### 3. Development

For each task in `NEXT_STEPS.md`:
- Selects best model for development (prefers larger models)
- Implements the task
- Updates/creates files
- Marks task complete

### 4. Quality Assurance

- Runs automated syntax checks
- Runs linters (ruff, flake8)
- AI-powered code review
- Creates `QA_STEPS.md` if issues found

### 5. Debugging (if needed)

- Analyzes errors
- Uses AI to suggest fixes
- Creates `DEBUG_STEPS.md`
- Attempts automatic fixes (with caution)

### 6. Commit & Push

- Stages all changes
- Creates descriptive commit message
- Pushes to configured remote

## Model Selection

The pipeline intelligently selects models based on task requirements:

| Task | Preferred Capabilities | Typical Model |
|------|----------------------|---------------|
| Planning | Reasoning, Analysis | llama3.1:latest |
| Development | Coding, Reasoning | llama3.1:latest |
| QA Review | Analysis, Reasoning | llama3.1:latest |
| Debugging | Coding, Analysis | llama3.1:latest |
| Simple Tasks | Speed | phi3:mini, llama3.2 |

You can also ask the AI to select the best model:

```python
# The pipeline can ask a model which model to use
model = selector.ask_model_for_selection("complex debugging task")
```

## Output Files

The pipeline creates/updates these files in your project:

| File | Purpose | Modified By |
|------|---------|-------------|
| `MASTER_PLAN.md` | Project objectives | Human only (read-only for AI) |
| `NEXT_STEPS.md` | Development tasks | Pipeline |
| `QA_STEPS.md` | QA checklist | Pipeline |
| `DEBUG_STEPS.md` | Debug workflow | Pipeline |
| `pipeline.log` | Detailed logs | Pipeline |
| `.pipeline/` | Pipeline state | Pipeline |

## Troubleshooting

### Ollama Server Not Responding

```bash
# Check server status
curl http://ollama01.clacorp.com:11434/api/tags

# If 403 error, configure Ollama to accept remote connections:
# On the Ollama server, add to /etc/systemd/system/ollama.service:
# Environment="OLLAMA_HOST=0.0.0.0"
# Then: systemctl daemon-reload && systemctl restart ollama
```

### Git Push Failing

```bash
# Check SSH key
ssh -T git@git.clacorp.com

# Add SSH key if needed
ssh-add ~/.ssh/id_rsa
```

### Pipeline Stuck/Slow

- Check if Ollama is overloaded: `curl http://server:11434/api/ps`
- Reduce `MAX_ITERATIONS`
- Use faster models for simple tasks

### Model Selection Issues

```bash
# Run discovery to see available models
./run_pipeline.sh --discover

# Check model capabilities in pipeline.py ModelSelector.MODEL_CAPABILITIES
```

## Examples

### Example 1: New Python Project

```bash
mkdir my-project && cd my-project
git init

# Create MASTER_PLAN.md with your objectives
cat > MASTER_PLAN.md << 'EOF'
# MASTER PLAN: My Project

## Vision
A CLI tool that does X, Y, Z.

## Objectives
1. Parse command line arguments
2. Process input files
3. Generate output

## Rules
- All functions must have docstrings
- Use type hints
- Handle errors gracefully
EOF

# Run pipeline
~/ai-dev-pipeline/run_pipeline.sh -r git@git.clacorp.com:user/my-project.git
```

### Example 2: Existing Project

```bash
cd /path/to/existing/project

# Create MASTER_PLAN.md describing current state and next steps
# Run pipeline
~/ai-dev-pipeline/run_pipeline.sh
```

### Example 3: Continuous Development

```bash
# Run in a loop for continuous development
while true; do
    ~/ai-dev-pipeline/run_pipeline.sh -i 5
    echo "Sleeping 60 seconds..."
    sleep 60
done
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AI Development Pipeline                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ Discovery│───▶│ Planning │───▶│   Dev    │───▶│    QA    │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                        │               │         │
│                                        │               ▼         │
│                                        │         ┌──────────┐   │
│                                        │         │  Debug   │   │
│                                        │         └──────────┘   │
│                                        │               │         │
│                                        ▼               ▼         │
│                                   ┌──────────────────────┐      │
│                                   │   Commit & Push      │      │
│                                   └──────────────────────┘      │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                        Ollama Servers                            │
│  ┌─────────────────────┐    ┌─────────────────────────────┐    │
│  │ ollama01.clacorp.com│    │ ollama02.clacorp.com        │    │
│  │ - llama3.2:latest   │    │ - llama3.1:latest (8B)      │    │
│  └─────────────────────┘    │ - llama3.2:3b               │    │
│                              │ - phi3:mini                 │    │
│                              └─────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## License

MIT License - Feel free to modify and distribute.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the pipeline on itself! (`./run_pipeline.sh`)
5. Submit a pull request
