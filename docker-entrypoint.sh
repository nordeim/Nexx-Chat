#!/bin/bash
# =============================================================================
# Neural Terminal - Docker Entrypoint Script
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# =============================================================================
# Environment Validation
# =============================================================================
validate_environment() {
    log_info "Validating environment..."
    
    # Check required environment variables
    if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
        log_warn "OPENROUTER_API_KEY not set - application will require configuration via UI"
    else
        log_success "OpenRouter API key configured"
    fi
    
    # Ensure data directory exists
    mkdir -p /app/data
    
    # Set proper permissions
    if [[ "$(id -u)" == "1000" ]]; then
        log_info "Running as neural user (UID: 1000)"
    fi
    
    log_success "Environment validation complete"
}

# =============================================================================
# Database Initialization
# =============================================================================
init_database() {
    log_info "Initializing database..."
    
    # Set database path for initialization
    export DATABASE_URL="sqlite:////app/data/neural_terminal.db"
    
    # Run initialization script
    if python /app/scripts/init_db.py 2>/dev/null; then
        log_success "Database initialized successfully"
    else
        log_warn "Database initialization may have issues - continuing anyway"
    fi
    
    # Display database stats
    if [[ -f "/app/data/neural_terminal.db" ]]; then
        local size=$(du -h /app/data/neural_terminal.db | cut -f1)
        log_info "Database file size: ${size}"
    fi
}

# =============================================================================
# Health Check
# =============================================================================
health_check() {
    log_info "Running health check..."
    
    if python /app/scripts/health_check.py --exit-code 2>/dev/null; then
        log_success "Health check passed"
    else
        log_warn "Health check had warnings - check output above"
    fi
}

# =============================================================================
# Start Application
# =============================================================================
start_app() {
    log_info "Starting Neural Terminal..."
    log_info "Streamlit will be available at: http://localhost:${STREAMLIT_SERVER_PORT:-7860}"
    
    # Set PYTHONPATH to include src directory
    export PYTHONPATH=/app/src:${PYTHONPATH:-}
    
    # Run Streamlit
    exec streamlit run /app/app.py \
        --server.port=${STREAMLIT_SERVER_PORT:-7860} \
        --server.address=0.0.0.0 \
        --server.headless=true \
        --server.enableCORS=false \
        --server.enableXsrfProtection=true \
        --browser.gatherUsageStats=false
}

# =============================================================================
# Initialize (one-time setup)
# =============================================================================
cmd_init() {
    log_info "Running initialization..."
    validate_environment
    init_database
    health_check
    log_success "Initialization complete!"
}

# =============================================================================
# Start (default)
# =============================================================================
cmd_start() {
    validate_environment
    init_database
    start_app
}

# =============================================================================
# Health check only
# =============================================================================
cmd_health() {
    health_check
}

# =============================================================================
# Database management
# =============================================================================
cmd_db_init() {
    init_database
}

cmd_db_backup() {
    log_info "Creating database backup..."
    python /app/scripts/init_db.py --backup
}

cmd_db_stats() {
    log_info "Database statistics:"
    python /app/scripts/init_db.py --stats
}

# =============================================================================
# Shell access (for debugging)
# =============================================================================
cmd_shell() {
    log_info "Starting shell..."
    exec /bin/bash
}

# =============================================================================
# Main
# =============================================================================
main() {
    case "${1:-start}" in
        start)
            cmd_start
            ;;
        init)
            cmd_init
            ;;
        health)
            cmd_health
            ;;
        db-init)
            cmd_db_init
            ;;
        db-backup)
            cmd_db_backup
            ;;
        db-stats)
            cmd_db_stats
            ;;
        shell)
            cmd_shell
            ;;
        *)
            log_error "Unknown command: $1"
            echo "Usage: $0 {start|init|health|db-init|db-backup|db-stats|shell}"
            exit 1
            ;;
    esac
}

main "$@"
