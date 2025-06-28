
#!/bin/bash

set -e

echo "🔄 TradeSense Rollback Script"
echo "============================"

# Configuration
DATABASE_BACKUP_DIR="./backups"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Stop current services
stop_services() {
    log_info "Stopping current services..."
    
    if [ -f ".backend.pid" ]; then
        BACKEND_PID=$(cat .backend.pid)
        kill $BACKEND_PID 2>/dev/null || true
        rm .backend.pid
        log_info "Backend stopped (PID: $BACKEND_PID)"
    fi
    
    if [ -f ".frontend.pid" ]; then
        FRONTEND_PID=$(cat .frontend.pid)
        kill $FRONTEND_PID 2>/dev/null || true
        rm .frontend.pid
        log_info "Frontend stopped (PID: $FRONTEND_PID)"
    fi
    
    # Fallback: kill all related processes
    pkill -f "python.*main.py" || true
    pkill -f "npm.*dev" || true
    
    log_info "Services stopped ✓"
}

# List available backups
list_backups() {
    log_info "Available database backups:"
    if [ -d "$DATABASE_BACKUP_DIR" ]; then
        ls -la $DATABASE_BACKUP_DIR/*.db 2>/dev/null || log_warn "No backups found"
    else
        log_warn "Backup directory not found"
    fi
}

# Restore database from backup
restore_database() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        log_error "Backup file not specified"
        list_backups
        read -p "Enter backup filename: " backup_file
    fi
    
    if [ ! -f "$DATABASE_BACKUP_DIR/$backup_file" ]; then
        log_error "Backup file not found: $DATABASE_BACKUP_DIR/$backup_file"
        exit 1
    fi
    
    log_info "Restoring database from backup: $backup_file"
    cp "$DATABASE_BACKUP_DIR/$backup_file" "backend/tradesense.db"
    log_info "Database restored ✓"
}

# Git rollback
git_rollback() {
    local commit_hash=$1
    
    if [ -z "$commit_hash" ]; then
        log_info "Recent commits:"
        git log --oneline -10
        read -p "Enter commit hash to rollback to: " commit_hash
    fi
    
    log_info "Rolling back to commit: $commit_hash"
    git checkout $commit_hash
    log_info "Git rollback completed ✓"
}

# Full rollback
full_rollback() {
    log_warn "This will stop services, restore database, and rollback code"
    read -p "Are you sure? (y/N): " confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        log_info "Rollback cancelled"
        exit 0
    fi
    
    stop_services
    
    log_info "Available options:"
    echo "1. Restore database only"
    echo "2. Git rollback only"
    echo "3. Both database and git rollback"
    read -p "Choose option (1-3): " option
    
    case $option in
        1)
            list_backups
            read -p "Enter backup filename: " backup_file
            restore_database "$backup_file"
            ;;
        2)
            git_rollback
            ;;
        3)
            list_backups
            read -p "Enter backup filename: " backup_file
            restore_database "$backup_file"
            git_rollback
            ;;
        *)
            log_error "Invalid option"
            exit 1
            ;;
    esac
    
    log_info "Rollback completed. Run deploy.sh to restart services."
}

# Handle command line arguments
case "$1" in
    "stop")
        stop_services
        ;;
    "list")
        list_backups
        ;;
    "restore")
        restore_database "$2"
        ;;
    "git")
        git_rollback "$2"
        ;;
    "full")
        full_rollback
        ;;
    *)
        echo "Usage: $0 [stop|list|restore|git|full]"
        echo "  stop           - Stop running services"
        echo "  list           - List available database backups"
        echo "  restore <file> - Restore database from backup"
        echo "  git <hash>     - Rollback to git commit"
        echo "  full           - Interactive full rollback"
        exit 1
        ;;
esac
