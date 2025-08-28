#!/bin/bash
# Claude-AGI TUI Launcher
# Optimized, secure, and extensible launcher with multi-shell support
# Follows ShellCheck best practices and modern shell scripting patterns

set -euo pipefail  # Exit on error, undefined variables, and pipe failures
IFS=$'\n\t'       # Secure Internal Field Separator

# Script metadata
SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_NAME
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
readonly PROJECT_NAME="Claude-AGI"
readonly VENV_DIR=".venv"
readonly PYTHON_SCRIPT="claude-agi.py"

# Color codes for output (following ShellCheck recommendations)
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
# readonly BLUE='\033[0;34m' # Reserved for future use
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Logging functions with proper quoting
log_info() {
    printf "${CYAN}[INFO]${NC} %s\n" "$*" >&1
}

log_warn() {
    printf "${YELLOW}[WARN]${NC} %s\n" "$*" >&2
}

log_error() {
    printf "${RED}[ERROR]${NC} %s\n" "$*" >&2
}

log_success() {
    printf "${GREEN}[SUCCESS]${NC} %s\n" "$*" >&1
}

# Display usage information
show_usage() {
    cat << EOF
${PROJECT_NAME} TUI Launcher

Usage: ${SCRIPT_NAME} [OPTIONS]

OPTIONS:
    -h, --help          Show this help message
    -v, --verbose       Enable verbose output
    -n, --no-venv       Skip virtual environment activation
    -c, --check         Perform system checks only
    -s, --shell SHELL   Specify shell (auto-detected by default)
    --setup            Setup virtual environment if missing

EXAMPLES:
    ${SCRIPT_NAME}                    # Normal launch with auto-detection
    ${SCRIPT_NAME} --verbose          # Launch with verbose output
    ${SCRIPT_NAME} --setup            # Setup venv and launch
    ${SCRIPT_NAME} --check            # Check system requirements

SUPPORTED SHELLS:
    - bash (Bourne Again Shell)
    - zsh (Z Shell)  
    - fish (Friendly Interactive Shell)
    - dash (Debian Almquist Shell)
    - sh (POSIX Shell)

EOF
}

# Detect current shell with multiple fallback methods
detect_shell() {
    local detected_shell=""
    
    # Method 1: Check SHELL environment variable first (most reliable)
    if [[ -n "${SHELL:-}" ]]; then
        detected_shell="$(basename "$SHELL")"
    fi
    
    # Method 2: Check parent process
    if [[ -z "$detected_shell" ]] && command -v ps >/dev/null 2>&1; then
        detected_shell="$(ps -p $$ -o comm= 2>/dev/null | sed 's/^-//')"
    fi
    
    # Method 3: Check $0 variable (but filter out script names)
    if [[ -z "$detected_shell" ]]; then
        local zero_basename
        zero_basename="$(basename "$0" 2>/dev/null)"
        case "$zero_basename" in
            bash|zsh|fish|dash|sh)
                detected_shell="$zero_basename"
                ;;
            *)
                # Skip script names like "run_tui.sh"
                ;;
        esac
    fi
    
    # Method 4: Default fallback
    if [[ -z "$detected_shell" ]]; then
        detected_shell="bash"  # Default to bash as it's most common
    fi
    
    printf '%s' "$detected_shell"
}

# Validate shell compatibility
validate_shell() {
    local shell="$1"
    
    case "$shell" in
        bash|zsh|fish|dash|sh)
            return 0
            ;;
        *)
            log_warn "Unknown shell detected: $shell"
            log_warn "Proceeding with POSIX-compatible mode"
            return 1
            ;;
    esac
}

# Check if virtual environment exists
check_venv_exists() {
    [[ -d "$SCRIPT_DIR/$VENV_DIR" ]] && [[ -f "$SCRIPT_DIR/$VENV_DIR/pyvenv.cfg" ]]
}

# Get activation script path based on shell
get_activation_script() {
    local shell="$1"
    local venv_path="$SCRIPT_DIR/$VENV_DIR"
    
    case "$shell" in
        fish)
            printf '%s/bin/activate.fish' "$venv_path"
            ;;
        bash|zsh|sh|dash|*)
            printf '%s/bin/activate' "$venv_path"
            ;;
    esac
}

# Check Python availability and version
check_python() {
    local python_cmd=""
    local python_version=""
    
    # Check for Python 3 variants
    for cmd in python3 python python3.12 python3.11 python3.10 python3.9; do
        if command -v "$cmd" >/dev/null 2>&1; then
            python_cmd="$cmd"
            break
        fi
    done
    
    if [[ -z "$python_cmd" ]]; then
        log_error "Python 3 is required but not found in PATH"
        log_error "Please install Python 3.9+ to continue"
        return 1
    fi
    
    # Check Python version
    python_version="$($python_cmd --version 2>&1 | cut -d' ' -f2)"
    
    # Check minimum version (3.9+)
    local major minor
    major="$(printf '%s' "$python_version" | cut -d'.' -f1)"
    minor="$(printf '%s' "$python_version" | cut -d'.' -f2)"
    
    if [[ "$major" -lt 3 ]] || [[ "$major" -eq 3 && "$minor" -lt 9 ]]; then
        log_error "Python 3.9+ is required (found $python_version)"
        return 1
    fi
    
    printf '%s' "$python_cmd"
}

# Setup virtual environment
setup_venv() {
    local python_cmd="$1"
    
    log_info "Setting up virtual environment..."
    
    if ! "$python_cmd" -m venv "$SCRIPT_DIR/$VENV_DIR"; then
        log_error "Failed to create virtual environment"
        return 1
    fi
    
    log_success "Virtual environment created successfully"
    
    # Install requirements if available
    local requirements_file="$SCRIPT_DIR/requirements.txt"
    if [[ -f "$requirements_file" ]]; then
        log_info "Installing requirements from requirements.txt..."
        
        # Activate venv and install requirements
        local activate_script
        activate_script="$(get_activation_script "bash")"
        
        if [[ -f "$activate_script" ]]; then
            # Use subshell to avoid affecting current environment
            (
                # shellcheck source=/dev/null
                source "$activate_script" && \
                pip install --upgrade pip && \
                pip install -r "$requirements_file"
            ) || {
                log_error "Failed to install requirements"
                return 1
            }
            log_success "Requirements installed successfully"
        fi
    fi
}

# Activate virtual environment based on shell
activate_venv() {
    local shell="$1"
    local activate_script
    activate_script="$(get_activation_script "$shell")"
    
    if [[ ! -f "$activate_script" ]]; then
        log_error "Activation script not found: $activate_script"
        return 1
    fi
    
    case "$shell" in
        fish)
            if [[ -n "${VERBOSE:-}" ]]; then
                log_info "Activating virtual environment for Fish shell"
            fi
            # For fish, we need to source the fish-specific activation script
            export VIRTUAL_ENV="$SCRIPT_DIR/$VENV_DIR"
            export PATH="$VIRTUAL_ENV/bin:$PATH"
            ;;
        bash|zsh|sh|dash|*)
            if [[ -n "${VERBOSE:-}" ]]; then
                log_info "Activating virtual environment for $shell"
            fi
            # shellcheck source=/dev/null
            source "$activate_script"
            ;;
    esac
    
    # Verify activation
    if [[ -n "${VIRTUAL_ENV:-}" ]] || [[ "$PATH" == *"$VENV_DIR/bin"* ]]; then
        if [[ -n "${VERBOSE:-}" ]]; then
            log_success "Virtual environment activated"
        fi
    else
        log_error "Failed to activate virtual environment"
        return 1
    fi
}

# Check if main Python script exists
check_python_script() {
    if [[ ! -f "$SCRIPT_DIR/$PYTHON_SCRIPT" ]]; then
        log_error "Main script not found: $PYTHON_SCRIPT"
        log_error "Please ensure you're in the correct directory"
        return 1
    fi
}

# Perform system checks
perform_checks() {
    local force_shell="$1"
    log_info "Performing system checks..."
    
    # Check current directory
    if [[ ! -f "$SCRIPT_DIR/$PYTHON_SCRIPT" ]]; then
        log_error "Not in Claude-AGI project directory"
        return 1
    fi
    
    # Check Python
    local python_cmd
    if ! python_cmd="$(check_python)"; then
        return 1
    fi
    if [[ -n "${VERBOSE:-}" ]]; then
        local python_version
        python_version="$(python3 --version 2>&1 | cut -d' ' -f2)"
        log_success "Python check passed: $python_cmd (version $python_version)"
    else
        log_success "Python check passed: $python_cmd"
    fi
    
    # Check virtual environment
    if check_venv_exists; then
        log_success "Virtual environment found"
    else
        log_warn "Virtual environment not found (use --setup to create)"
    fi
    
    # Check shell compatibility
    local shell
    if [[ -n "${force_shell:-}" ]]; then
        shell="$force_shell"
    else
        shell="$(detect_shell)"
    fi
    if validate_shell "$shell"; then
        log_success "Shell compatibility check passed: $shell"
    else
        log_warn "Shell compatibility check warning: $shell"
    fi
    
    log_success "System checks completed"
}

# Launch the main application
launch_application() {
    local python_cmd="$1"
    shift  # Remove python_cmd from arguments
    
    # Change to script directory
    cd "$SCRIPT_DIR" || {
        log_error "Failed to change to script directory"
        return 1
    }
    
    if [[ -n "${VERBOSE:-}" ]]; then
        log_info "Launching $PROJECT_NAME TUI..."
        log_info "Working directory: $(pwd)"
        log_info "Python command: $python_cmd"
        log_info "Virtual environment: ${VIRTUAL_ENV:-"Not activated"}"
    fi
    
    # Execute the Python script with remaining arguments
    exec "$python_cmd" "$PYTHON_SCRIPT" "$@"
}

# Main execution function
main() {
    local shell
    local python_cmd
    local skip_venv=false
    local setup_venv=false
    local check_only=false
    local force_shell=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_usage
                return 0
                ;;
            -v|--verbose)
                export VERBOSE=true
                ;;
            -n|--no-venv)
                skip_venv=true
                ;;
            -c|--check)
                check_only=true
                ;;
            --setup)
                setup_venv=true
                ;;
            -s|--shell)
                shift
                force_shell="$1"
                ;;
            --)
                shift
                break
                ;;
            -*)
                log_error "Unknown option: $1"
                show_usage >&2
                return 1
                ;;
            *)
                break
                ;;
        esac
        shift
    done
    
    # Perform checks if requested
    if [[ "$check_only" == true ]]; then
        perform_checks "$force_shell"
        return $?
    fi
    
    # Detect shell
    if [[ -n "$force_shell" ]]; then
        shell="$force_shell"
    else
        shell="$(detect_shell)"
    fi
    
    if [[ -n "${VERBOSE:-}" ]]; then
        log_info "Detected shell: $shell"
    fi
    
    # Validate shell
    validate_shell "$shell" || true  # Continue even if shell is unknown
    
    # Check Python availability
    if ! python_cmd="$(check_python)"; then
        return 1
    fi
    
    # Check if main script exists
    if ! check_python_script; then
        return 1
    fi
    
    # Handle virtual environment
    if [[ "$skip_venv" == false ]]; then
        if ! check_venv_exists; then
            if [[ "$setup_venv" == true ]]; then
                if ! setup_venv "$python_cmd"; then
                    return 1
                fi
            else
                log_warn "Virtual environment not found"
                log_warn "Consider running with --setup to create one"
                log_warn "Continuing without virtual environment..."
            fi
        fi
        
        # Activate virtual environment if it exists
        if check_venv_exists; then
            if ! activate_venv "$shell"; then
                log_warn "Failed to activate virtual environment"
                log_warn "Continuing without virtual environment..."
            fi
        fi
    fi
    
    # Launch application
    launch_application "$python_cmd" "$@"
}

# Error handling
trap 'log_error "Script interrupted"; exit 130' INT
trap 'log_error "Script terminated"; exit 143' TERM

# Execute main function with all arguments
main "$@"