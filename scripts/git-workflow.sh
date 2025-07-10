#!/bin/bash

# ============================================================================
# TradeSense Git Workflow System
# Enhanced version control with protection checks and best practices
# ============================================================================

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
PROTECTED_FILES="PROTECTED_FILES.md"
PROJECT_RULES="project-rules.md"
CHANGELOG="CHANGELOG.md"

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${PURPLE}ℹ $1${NC}"
}

# Check if protected files have been modified
check_protected_files() {
    print_header "Checking Protected Files"
    
    if [ ! -f "$PROTECTED_FILES" ]; then
        print_warning "PROTECTED_FILES.md not found. Skipping protection check."
        return 0
    fi
    
    # Get list of modified files
    modified_files=$(git diff --cached --name-only)
    
    # Check each modified file against protected patterns
    protected_modified=()
    while IFS= read -r file; do
        # Check if file is in COMPLETE_SAAS_ARCHITECTURE_GUIDE
        if [[ "$file" == COMPLETE_SAAS_ARCHITECTURE_GUIDE/* ]]; then
            protected_modified+=("$file")
        fi
        
        # Check against other protected files
        if [[ "$file" == "PROTECTED_FILES.md" || "$file" == "project-rules.md" || "$file" == "README.md" || "$file" == "README_DEV.md" ]]; then
            protected_modified+=("$file")
        fi
    done <<< "$modified_files"
    
    if [ ${#protected_modified[@]} -gt 0 ]; then
        print_warning "The following protected files have been modified:"
        for file in "${protected_modified[@]}"; do
            echo "  - $file"
        done
        echo ""
        read -p "Are you sure you want to commit changes to protected files? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            print_error "Commit cancelled."
            exit 1
        fi
        print_info "Protected file changes approved by user."
    else
        print_success "No protected files modified."
    fi
}

# Validate commit message format
validate_commit_message() {
    local msg="$1"
    
    # Check minimum length
    if [ ${#msg} -lt 10 ]; then
        print_error "Commit message too short (minimum 10 characters)"
        return 1
    fi
    
    # Suggest conventional commit format
    if [[ ! "$msg" =~ ^(feat|fix|docs|style|refactor|test|chore|build|ci|perf|revert): ]]; then
        print_warning "Consider using conventional commit format:"
        echo "  feat:     New feature"
        echo "  fix:      Bug fix"
        echo "  docs:     Documentation changes"
        echo "  style:    Code style changes"
        echo "  refactor: Code refactoring"
        echo "  test:     Test changes"
        echo "  chore:    Maintenance tasks"
        echo ""
        read -p "Continue with current message? (yes/no): " continue_commit
        if [[ "$continue_commit" != "yes" ]]; then
            return 1
        fi
    fi
    
    return 0
}

# Semantic versioning helper
get_next_version() {
    local current_version=$1
    local bump_type=$2
    
    # Remove 'v' prefix if present
    current_version=${current_version#v}
    
    # Split version into components
    IFS='.' read -r major minor patch <<< "$current_version"
    
    case $bump_type in
        "major")
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        "minor")
            minor=$((minor + 1))
            patch=0
            ;;
        "patch")
            patch=$((patch + 1))
            ;;
    esac
    
    echo "v${major}.${minor}.${patch}"
}

# Generate changelog entry
update_changelog() {
    local version=$1
    local description=$2
    local commit_msg=$3
    local date=$(date +"%Y-%m-%d")
    
    if [ ! -f "$CHANGELOG" ]; then
        print_info "Creating CHANGELOG.md"
        cat > "$CHANGELOG" << EOF
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

EOF
    fi
    
    # Create temporary file with new entry
    local temp_file=$(mktemp)
    
    # Write header
    head -n 6 "$CHANGELOG" > "$temp_file"
    
    # Write new version entry
    cat >> "$temp_file" << EOF

## [$version] - $date

### Changed
- $description

### Commit
- $commit_msg

EOF
    
    # Append rest of changelog
    tail -n +7 "$CHANGELOG" >> "$temp_file"
    
    # Replace original file
    mv "$temp_file" "$CHANGELOG"
    print_success "Updated CHANGELOG.md"
}

# Create backup branch
create_backup() {
    local backup_branch="backup-$(date +%Y%m%d-%H%M%S)"
    git branch "$backup_branch"
    print_success "Created backup branch: $backup_branch"
}

# Run pre-commit checks
run_pre_commit_checks() {
    print_header "Running Pre-commit Checks"
    
    # Check for merge conflicts
    if grep -r "<<<<<<< HEAD" . --exclude-dir=.git > /dev/null; then
        print_error "Unresolved merge conflicts found!"
        return 1
    fi
    
    # Check for large files
    large_files=$(find . -type f -size +10M ! -path "./.git/*" 2>/dev/null)
    if [ ! -z "$large_files" ]; then
        print_warning "Large files detected (>10MB):"
        echo "$large_files"
        read -p "Continue with large files? (yes/no): " continue_large
        if [[ "$continue_large" != "yes" ]]; then
            return 1
        fi
    fi
    
    # Check Python syntax if Python files changed
    python_files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)
    if [ ! -z "$python_files" ]; then
        print_info "Checking Python syntax..."
        for file in $python_files; do
            if ! python -m py_compile "$file" 2>/dev/null; then
                print_error "Python syntax error in: $file"
                return 1
            fi
        done
        print_success "Python syntax check passed"
    fi
    
    return 0
}

# ============================================================================
# Main Menu Functions
# ============================================================================

# Standard commit
standard_commit() {
    print_header "Standard Commit"
    
    # Show current status
    echo "Current git status:"
    git status --short
    echo ""
    
    # Run pre-commit checks
    if ! run_pre_commit_checks; then
        print_error "Pre-commit checks failed"
        exit 1
    fi
    
    # Stage files
    read -p "Stage all files? (yes/no/select): " stage_choice
    case $stage_choice in
        "yes")
            git add .
            print_success "All files staged"
            ;;
        "select")
            git add -i
            ;;
        *)
            print_info "No files staged"
            exit 0
            ;;
    esac
    
    # Check protected files
    check_protected_files
    
    # Get commit message
    while true; do
        read -p "Enter commit message: " commit_msg
        if validate_commit_message "$commit_msg"; then
            break
        fi
    done
    
    # Create backup
    read -p "Create backup branch? (yes/no): " create_backup_choice
    if [[ "$create_backup_choice" == "yes" ]]; then
        create_backup
    fi
    
    # Commit
    git commit -m "$commit_msg"
    print_success "Changes committed"
    
    # Push
    read -p "Push to remote? (yes/no): " push_choice
    if [[ "$push_choice" == "yes" ]]; then
        branch=$(git branch --show-current)
        git push origin "$branch"
        print_success "Pushed to origin/$branch"
    fi
}

# Version release
version_release() {
    print_header "Version Release"
    
    # Get latest tag
    latest_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
    print_info "Latest version: $latest_tag"
    
    # Show what's changed since last tag
    echo -e "\nChanges since $latest_tag:"
    git log "$latest_tag"..HEAD --oneline
    echo ""
    
    # Get version bump type
    echo "Version bump type:"
    echo "  1) Major (breaking changes)"
    echo "  2) Minor (new features)"
    echo "  3) Patch (bug fixes)"
    echo "  4) Custom version"
    read -p "Select option (1-4): " bump_choice
    
    case $bump_choice in
        1) new_version=$(get_next_version "$latest_tag" "major") ;;
        2) new_version=$(get_next_version "$latest_tag" "minor") ;;
        3) new_version=$(get_next_version "$latest_tag" "patch") ;;
        4) read -p "Enter custom version (e.g., v1.2.3): " new_version ;;
        *) print_error "Invalid choice"; exit 1 ;;
    esac
    
    print_info "New version will be: $new_version"
    
    # Get release description
    read -p "Enter release description: " release_desc
    
    # Run standard commit first
    standard_commit
    
    # Update changelog
    read -p "Update CHANGELOG.md? (yes/no): " update_changelog_choice
    if [[ "$update_changelog_choice" == "yes" ]]; then
        commit_msg=$(git log -1 --pretty=%B)
        update_changelog "$new_version" "$release_desc" "$commit_msg"
        git add "$CHANGELOG"
        git commit -m "docs: Update CHANGELOG for $new_version"
    fi
    
    # Create and push tag
    git tag -a "$new_version" -m "$release_desc"
    print_success "Created tag: $new_version"
    
    # Push tag
    git push origin "$new_version"
    print_success "Pushed tag to origin"
    
    # Show release summary
    print_header "Release Summary"
    echo "Version: $new_version"
    echo "Description: $release_desc"
    echo "Tag pushed to origin"
}

# Hotfix workflow
hotfix() {
    print_header "Hotfix Workflow"
    
    # Get current branch
    current_branch=$(git branch --show-current)
    
    # Create hotfix branch
    read -p "Enter hotfix name (e.g., fix-critical-bug): " hotfix_name
    hotfix_branch="hotfix/$hotfix_name"
    
    git checkout -b "$hotfix_branch"
    print_success "Created and switched to $hotfix_branch"
    
    print_info "Make your hotfix changes, then run this script again to complete the hotfix"
    echo "Current branch: $hotfix_branch"
}

# Feature branch workflow
feature_branch() {
    print_header "Feature Branch Workflow"
    
    echo "1) Create new feature branch"
    echo "2) Finish feature branch"
    read -p "Select option (1-2): " feature_choice
    
    case $feature_choice in
        1)
            read -p "Enter feature name (e.g., add-authentication): " feature_name
            feature_branch="feature/$feature_name"
            git checkout -b "$feature_branch"
            print_success "Created and switched to $feature_branch"
            ;;
        2)
            current_branch=$(git branch --show-current)
            if [[ ! "$current_branch" =~ ^feature/ ]]; then
                print_error "Not on a feature branch"
                exit 1
            fi
            
            # Run tests if available
            if [ -f "pytest.ini" ] || [ -f "setup.cfg" ] || [ -f "tests/" ]; then
                read -p "Run tests before merging? (yes/no): " run_tests
                if [[ "$run_tests" == "yes" ]]; then
                    pytest || { print_error "Tests failed"; exit 1; }
                fi
            fi
            
            # Merge back to main
            git checkout main
            git merge --no-ff "$current_branch" -m "Merge $current_branch"
            print_success "Merged $current_branch to main"
            
            # Delete feature branch
            read -p "Delete feature branch? (yes/no): " delete_branch
            if [[ "$delete_branch" == "yes" ]]; then
                git branch -d "$current_branch"
                print_success "Deleted $current_branch"
            fi
            ;;
    esac
}

# Show git history
show_history() {
    print_header "Git History"
    
    echo "1) Recent commits (last 10)"
    echo "2) All tags"
    echo "3) Branch graph"
    echo "4) File history"
    echo "5) Search commits"
    read -p "Select option (1-5): " history_choice
    
    case $history_choice in
        1) git log --oneline -10 ;;
        2) git tag -l -n1 ;;
        3) git log --graph --oneline --all --decorate ;;
        4) 
            read -p "Enter filename: " filename
            git log --follow --oneline -- "$filename"
            ;;
        5)
            read -p "Enter search term: " search_term
            git log --grep="$search_term" --oneline
            ;;
    esac
}

# ============================================================================
# Main Script
# ============================================================================

# Check if git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository"
    exit 1
fi

# Show main menu
print_header "TradeSense Git Workflow System"

echo "Select workflow:"
echo "  1) Standard commit"
echo "  2) Version release"
echo "  3) Hotfix"
echo "  4) Feature branch"
echo "  5) Show history"
echo "  6) Setup git hooks"
echo "  7) Validate project"
echo "  8) Emergency rollback"
echo ""
read -p "Enter choice (1-8): " choice

case $choice in
    1) standard_commit ;;
    2) version_release ;;
    3) hotfix ;;
    4) feature_branch ;;
    5) show_history ;;
    6) 
        print_info "Installing git hooks..."
        # This would install pre-commit hooks
        print_info "Git hooks installation not yet implemented"
        ;;
    7)
        print_info "Validating project structure..."
        # Check if all protected files exist
        if [ -f "$PROTECTED_FILES" ]; then
            print_success "PROTECTED_FILES.md exists"
        else
            print_error "PROTECTED_FILES.md missing"
        fi
        
        if [ -f "$PROJECT_RULES" ]; then
            print_success "project-rules.md exists"
        else
            print_error "project-rules.md missing"
        fi
        ;;
    8)
        print_header "Emergency Rollback"
        echo "Recent commits:"
        git log --oneline -5
        echo ""
        read -p "Enter commit hash to rollback to: " rollback_hash
        read -p "Are you SURE? This will create a new commit reverting changes (yes/no): " confirm_rollback
        if [[ "$confirm_rollback" == "yes" ]]; then
            git revert --no-edit HEAD.."$rollback_hash"
            print_success "Rollback complete"
        fi
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac
