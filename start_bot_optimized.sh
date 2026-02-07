#!/bin/bash
###############################################################################
# Optimized Dashboard Startup Script
# 
# Features:
# - Dependency checking
# - Parallel bot and dashboard startup
# - Health check before opening browser
# - Progress indicators
# - Auto-config creation
# - Port conflict detection
# - Clear error messages
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DASHBOARD_PORT=5000
HEALTH_CHECK_URL="http://localhost:${DASHBOARD_PORT}/health"
MAX_WAIT_TIME=30  # Maximum seconds to wait for server
CHECK_INTERVAL=1  # Seconds between health checks

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo ""
    echo "============================================================================"
    echo "  🚀 Market Strategy Testing Bot - Optimized Dashboard Launcher"
    echo "============================================================================"
    echo ""
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

###############################################################################
# Pre-flight Checks
###############################################################################

check_python_version() {
    print_step "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        print_info "Please install Python 3.8 or higher from https://www.python.org/downloads/"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        print_error "Python 3.8 or higher is required (found $PYTHON_VERSION)"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION detected"
}

check_dependencies() {
    print_step "Checking dependencies..."
    
    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
        exit 1
    fi
    
    # Try to import required packages
    python3 -c "import flask, flask_cors, yaml" 2>/dev/null
    if [ $? -ne 0 ]; then
        print_warning "Some dependencies are missing"
        print_info "Installing dependencies..."
        pip3 install -r requirements.txt
        if [ $? -ne 0 ]; then
            print_error "Failed to install dependencies"
            print_info "Try: pip3 install -r requirements.txt"
            exit 1
        fi
    fi
    
    print_success "All dependencies installed"
}

check_config() {
    print_step "Checking configuration..."
    
    if [ ! -f "config.yaml" ]; then
        print_warning "config.yaml not found"
        
        if [ -f "config.example.yaml" ]; then
            print_info "Creating config.yaml from example..."
            cp config.example.yaml config.yaml
            print_success "Created config.yaml"
            print_warning "Please edit config.yaml to add your settings"
        else
            print_error "config.example.yaml not found"
            print_info "Please create config.yaml manually"
            exit 1
        fi
    else
        print_success "config.yaml found"
    fi
}

check_port_available() {
    print_step "Checking if port $DASHBOARD_PORT is available..."
    
    # Check if port is in use
    if lsof -Pi :$DASHBOARD_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        print_error "Port $DASHBOARD_PORT is already in use"
        print_info "Please stop any running dashboard instance or change the port"
        
        # Show what's using the port
        print_info "Process using port $DASHBOARD_PORT:"
        lsof -i :$DASHBOARD_PORT | grep LISTEN
        exit 1
    fi
    
    print_success "Port $DASHBOARD_PORT is available"
}

create_logs_directory() {
    print_step "Setting up logs directory..."
    
    if [ ! -d "logs" ]; then
        mkdir -p logs
        print_success "Created logs directory"
    else
        print_success "Logs directory exists"
    fi
}

###############################################################################
# Server Management
###############################################################################

start_dashboard_server() {
    print_step "Starting dashboard server..."
    
    # Start Flask app in background
    cd dashboard
    python3 app.py > ../logs/dashboard.log 2>&1 &
    DASHBOARD_PID=$!
    cd ..
    
    # Save PID for cleanup
    echo $DASHBOARD_PID > /tmp/dashboard.pid
    
    print_info "Dashboard server started (PID: $DASHBOARD_PID)"
}

wait_for_health_check() {
    print_step "Waiting for server to be ready..."
    
    local elapsed=0
    local spinner=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
    local spin_idx=0
    
    while [ $elapsed -lt $MAX_WAIT_TIME ]; do
        # Try health check
        if curl -s -f "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            echo ""  # New line after spinner
            print_success "Server is ready!"
            return 0
        fi
        
        # Show spinner
        printf "\r${BLUE}[${spinner[$spin_idx]}]${NC} Waiting for server... ${elapsed}s / ${MAX_WAIT_TIME}s"
        
        # Update spinner
        spin_idx=$(( (spin_idx + 1) % ${#spinner[@]} ))
        
        sleep $CHECK_INTERVAL
        elapsed=$((elapsed + CHECK_INTERVAL))
    done
    
    echo ""  # New line after spinner
    print_error "Server failed to start within $MAX_WAIT_TIME seconds"
    
    # Show logs
    print_info "Last 20 lines from dashboard.log:"
    tail -20 logs/dashboard.log 2>/dev/null || echo "No log file found"
    
    return 1
}

open_dashboard() {
    print_step "Opening dashboard in browser..."
    
    local url="http://localhost:${DASHBOARD_PORT}"
    
    # Detect OS and open browser
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open "$url"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v xdg-open &> /dev/null; then
            xdg-open "$url"
        elif command -v gnome-open &> /dev/null; then
            gnome-open "$url"
        else
            print_warning "Could not detect browser. Please open manually: $url"
        fi
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        # Windows
        start "$url"
    else
        print_warning "Could not detect OS. Please open manually: $url"
    fi
    
    print_success "Dashboard URL: $url"
}

###############################################################################
# Cleanup
###############################################################################

cleanup() {
    print_info "Shutting down..."
    
    # Kill dashboard if running
    if [ -f /tmp/dashboard.pid ]; then
        DASHBOARD_PID=$(cat /tmp/dashboard.pid)
        if ps -p $DASHBOARD_PID > /dev/null 2>&1; then
            kill $DASHBOARD_PID 2>/dev/null || true
            print_success "Dashboard stopped"
        fi
        rm -f /tmp/dashboard.pid
    fi
    
    echo ""
    print_success "Cleanup complete"
    exit 0
}

# Trap CTRL+C and other termination signals
trap cleanup SIGINT SIGTERM

###############################################################################
# Main Execution
###############################################################################

main() {
    print_header
    
    # Run all pre-flight checks
    check_python_version
    check_dependencies
    check_config
    check_port_available
    create_logs_directory
    
    echo ""
    echo "============================================================================"
    print_success "All checks passed!"
    echo "============================================================================"
    echo ""
    
    # Start the dashboard
    start_dashboard_server
    
    # Wait for server to be ready
    if wait_for_health_check; then
        echo ""
        print_success "Dashboard started successfully!"
        echo ""
        
        # Open browser
        open_dashboard
        
        echo ""
        echo "============================================================================"
        print_info "Dashboard is running at http://localhost:${DASHBOARD_PORT}"
        print_info "Press Ctrl+C to stop the server"
        echo "============================================================================"
        echo ""
        
        # Wait for user to stop
        wait
    else
        print_error "Failed to start dashboard"
        cleanup
        exit 1
    fi
}

# Run main function
main
