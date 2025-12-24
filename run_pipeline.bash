#!/bin/bash
#===============================================================================
# AI Development Pipeline Runner
#===============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
OLLAMA_SERVERS=("ollama01.clacorp.com" "ollama02.clacorp.com")
OLLAMA_PORT="11434"

# Script directory (where pipeline module is)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Arguments
PROJECT_DIR=""
MAX_ITERATIONS="0"
MAX_RETRIES="3"
NO_GIT=false
DISCOVER_ONLY=false
VERBOSE=false

show_help() {
    cat << EOF
AI Development Pipeline - Tool Calling Architecture

Usage: $0 -d /path/to/project [OPTIONS]

Required:
    -d, --project-dir DIR    Target project directory (must contain MASTER_PLAN.md)

Options:
    -i, --iterations N       Max iterations (0 = infinite, default: 0)
    --max-retries N          Max retries per task before skipping (default: 3)
    --no-git                 Disable git integration
    --discover               Only show available models
    -v, --verbose            Enable verbose logging
    -h, --help               Show this help

Examples:
    $0 -d ~/projects/sysadmin --no-git
    $0 -d ~/projects/sysadmin -i 10 --max-retries 2
    $0 --discover

EOF
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Python
    if ! command -v python3 &>/dev/null; then
        log_error "Python 3 required"
        exit 1
    fi
    log_success "Python: $(python3 --version)"
    
    # requests module
    if ! python3 -c "import requests" 2>/dev/null; then
        log_warn "Installing requests..."
        pip3 install --user requests
    fi
    log_success "requests: installed"
}

check_ollama_servers() {
    log_info "Checking Ollama servers..."
    
    for server in "${OLLAMA_SERVERS[@]}"; do
        if curl -s --connect-timeout 5 "http://${server}:${OLLAMA_PORT}/api/tags" > /dev/null 2>&1; then
            local models=$(curl -s "http://${server}:${OLLAMA_PORT}/api/tags" 2>/dev/null | \
                python3 -c "import sys,json; d=json.load(sys.stdin); print(', '.join(m['name'] for m in d.get('models',[]))[:80])" 2>/dev/null || echo "?")
            log_success "$server: $models"
        else
            log_warn "$server: offline"
        fi
    done
}

check_master_plan() {
    local dir="$1"
    
    if [ ! -f "$dir/MASTER_PLAN.md" ]; then
        log_error "MASTER_PLAN.md not found in $dir"
        log_info "The project directory must contain a MASTER_PLAN.md file"
        exit 1
    fi
    
    log_success "MASTER_PLAN.md found ($(wc -c < "$dir/MASTER_PLAN.md") bytes)"
}

run_pipeline() {
    # Build command - run as module from script directory
    local cmd="python3 -m pipeline"
    cmd="$cmd --project-dir $PROJECT_DIR"
    cmd="$cmd --max-retries $MAX_RETRIES"
    cmd="$cmd --iterations $MAX_ITERATIONS"
    
    [ "$NO_GIT" = true ] && cmd="$cmd --no-git"
    [ "$DISCOVER_ONLY" = true ] && cmd="$cmd --discover"
    [ "$VERBOSE" = true ] && cmd="$cmd --verbose"
    
    # Change to script directory so Python can find the module
    cd "$SCRIPT_DIR"
    
    echo
    eval $cmd
    return $?
}

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--project-dir) PROJECT_DIR="$2"; shift 2 ;;
            -i|--iterations) MAX_ITERATIONS="$2"; shift 2 ;;
            --max-retries) MAX_RETRIES="$2"; shift 2 ;;
            --no-git) NO_GIT=true; shift ;;
            --discover) DISCOVER_ONLY=true; shift ;;
            -v|--verbose) VERBOSE=true; shift ;;
            -h|--help) show_help; exit 0 ;;
            *) log_error "Unknown option: $1"; show_help; exit 1 ;;
        esac
    done
    
    # Discovery mode doesn't need project dir
    if [ "$DISCOVER_ONLY" = true ]; then
        PROJECT_DIR="${PROJECT_DIR:-.}"
        check_dependencies
        check_ollama_servers
        run_pipeline
        exit $?
    fi
    
    # Validate project dir
    if [ -z "$PROJECT_DIR" ]; then
        log_error "Project directory required: -d /path/to/project"
        show_help
        exit 1
    fi
    
    # Ensure project dir exists
    mkdir -p "$PROJECT_DIR"
    PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"
    
    # Print banner
    echo
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                    AI DEVELOPMENT PIPELINE                           ║${NC}"
    echo -e "${CYAN}║                  Tool Calling Architecture                           ║${NC}"
    echo -e "${CYAN}╠══════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║${NC}  TARGET: ${GREEN}$PROJECT_DIR${NC}"
    echo -e "${CYAN}║${NC}  Git: ${GREEN}$([ "$NO_GIT" = true ] && echo "DISABLED" || echo "Enabled")${NC}"
    echo -e "${CYAN}║${NC}  Max retries: ${GREEN}$MAX_RETRIES${NC} per task"
    echo -e "${CYAN}║${NC}  Iterations: ${GREEN}$([ "$MAX_ITERATIONS" = "0" ] && echo "∞" || echo "$MAX_ITERATIONS")${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════╝${NC}"
    echo
    
    # Pre-flight checks
    check_dependencies
    check_ollama_servers
    check_master_plan "$PROJECT_DIR"
    
    # Run the pipeline
    run_pipeline
    exit $?
}

main "$@"
