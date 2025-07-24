#!/bin/bash

# TradeSense Repository Structure Fix Script
# This script flattens the repository structure by removing nested git repositories

set -e  # Exit on error

echo "🔧 TradeSense Repository Structure Fix"
echo "====================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the project root
if [ ! -d "services" ]; then
    print_error "This script must be run from the project root directory"
    exit 1
fi

# Create backup directory
BACKUP_DIR="repository_backup_$(date +%Y%m%d_%H%M%S)"
print_status "Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# List of services with their own git repositories
SERVICES_WITH_GIT=(
    "ai"
    "analytics"
    "billing"
    "market-data"
    "trading"
)

# Step 1: Document current state
print_status "Documenting current repository state..."
echo "Repository State - $(date)" > "$BACKUP_DIR/repository_state.txt"
echo "=========================" >> "$BACKUP_DIR/repository_state.txt"

for service in "${SERVICES_WITH_GIT[@]}"; do
    if [ -d "services/$service/.git" ]; then
        echo "" >> "$BACKUP_DIR/repository_state.txt"
        echo "Service: $service" >> "$BACKUP_DIR/repository_state.txt"
        cd "services/$service"
        echo "Current branch: $(git branch --show-current)" >> "../../$BACKUP_DIR/repository_state.txt"
        echo "Last commit: $(git log -1 --oneline)" >> "../../$BACKUP_DIR/repository_state.txt"
        echo "Status:" >> "../../$BACKUP_DIR/repository_state.txt"
        git status --short >> "../../$BACKUP_DIR/repository_state.txt"
        cd ../..
    fi
done

print_success "Repository state documented"

# Step 2: Check for uncommitted changes
print_status "Checking for uncommitted changes in service repositories..."
UNCOMMITTED_CHANGES=false

for service in "${SERVICES_WITH_GIT[@]}"; do
    if [ -d "services/$service/.git" ]; then
        cd "services/$service"
        if [ -n "$(git status --porcelain)" ]; then
            print_warning "Uncommitted changes found in $service"
            UNCOMMITTED_CHANGES=true
        fi
        cd ../..
    fi
done

if [ "$UNCOMMITTED_CHANGES" = true ]; then
    print_error "Uncommitted changes found in service repositories"
    echo ""
    read -p "Do you want to continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Aborting..."
        exit 1
    fi
fi

# Step 3: Create full backup
print_status "Creating full backup of services directory..."
cp -r services "$BACKUP_DIR/"
print_success "Backup created at $BACKUP_DIR/services"

# Step 4: Remove .git directories
print_status "Removing nested .git directories..."

for service in "${SERVICES_WITH_GIT[@]}"; do
    if [ -d "services/$service/.git" ]; then
        print_status "Removing .git from services/$service"
        rm -rf "services/$service/.git"
        print_success "Removed .git from $service"
    fi
done

# Step 5: Add all service files to main repository
print_status "Adding all service files to main repository..."
git add services/

# Step 6: Check what will be committed
print_status "Files to be added to main repository:"
git status --short services/ | head -20
echo "..."
echo ""

# Step 7: Create commit
print_status "Creating commit..."
cat > "$BACKUP_DIR/commit_message.txt" << EOF
fix: Flatten repository structure for proper CI/CD

- Remove nested git repositories from services
- All services now tracked in main repository
- Fixes deployment issues with gateway and other services
- Enables proper change detection in CI/CD pipeline

Previous service states documented in: $BACKUP_DIR/repository_state.txt

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
EOF

# Step 8: Summary
echo ""
echo "====================================="
echo -e "${GREEN}Repository Structure Fix Complete!${NC}"
echo "====================================="
echo ""
print_success "All nested .git directories removed"
print_success "All service files added to main repository"
print_success "Backup created at: $BACKUP_DIR"
echo ""
print_status "Next steps:"
echo "  1. Review the changes with: git status"
echo "  2. Commit the changes with: git commit -F $BACKUP_DIR/commit_message.txt"
echo "  3. Push to trigger CI/CD: git push origin main"
echo ""
print_warning "If you need to rollback:"
echo "  1. Run: git reset --hard HEAD"
echo "  2. Restore from backup: cp -r $BACKUP_DIR/services/* services/"
echo ""

# Create rollback script
cat > "$BACKUP_DIR/rollback.sh" << 'EOF'
#!/bin/bash
echo "Rolling back repository structure changes..."
git reset --hard HEAD
cp -r services/* ../services/
echo "Rollback complete!"
EOF

chmod +x "$BACKUP_DIR/rollback.sh"
print_success "Rollback script created at: $BACKUP_DIR/rollback.sh"