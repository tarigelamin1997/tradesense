# Git Workflow for Parallel Claude Development

## Initial Setup (You do this once)

```bash
# 1. Create a backup of current state
git checkout main
git pull origin main
git checkout -b backup/pre-section-1-$(date +%Y%m%d)
git push origin backup/pre-section-1-$(date +%Y%m%d)

# 2. Create a base branch for Section 1
git checkout main
git checkout -b feature/section-1-foundation
git push origin feature/section-1-foundation

# 3. Create individual branches for each Claude instance
git checkout -b feature/section-1a-security
git push origin feature/section-1a-security

git checkout feature/section-1-foundation
git checkout -b feature/section-1b-cleanup
git push origin feature/section-1b-cleanup

git checkout feature/section-1-foundation
git checkout -b feature/section-1d-database
git push origin feature/section-1d-database
```

## Daily Workflow for Each Claude Instance

### For Claude Instance 1 (Security)
```bash
# Day 1 - Start of work
git checkout feature/section-1a-security
git pull origin feature/section-1a-security

# After implementing changes
git add .
git commit -m "Security: Remove hardcoded secrets from config.py"
git push origin feature/section-1a-security

# Create incremental commits
git add backend/core/config.py
git commit -m "Security: Add environment validation to config"

git add scripts/security_scanner.py
git commit -m "Security: Add security scanning script"

git push origin feature/section-1a-security
```

### For Claude Instance 2 (Cleanup)
```bash
# Start work
git checkout feature/section-1b-cleanup
git pull origin feature/section-1b-cleanup

# After removing duplicates
git rm attached_assets/*
git commit -m "Cleanup: Remove all duplicate files from attached_assets"

# After moving files
git add .
git commit -m "Cleanup: Reorganize root files into proper structure"

git push origin feature/section-1b-cleanup
```

### For Claude Instance 3 (Database)
```bash
# Start work (may need to wait for config updates)
git checkout feature/section-1d-database
git pull origin feature/section-1d-database

# Optionally merge security changes if needed
git merge origin/feature/section-1a-security

# Make database changes
git add migrations/
git commit -m "Database: Add PostgreSQL migration scripts"

git push origin feature/section-1d-database
```

## Integration Strategy

### Day 3-4: Progressive Integration

```bash
# 1. First, merge security changes to foundation
git checkout feature/section-1-foundation
git pull origin feature/section-1-foundation
git merge origin/feature/section-1a-security
# Resolve any conflicts
git push origin feature/section-1-foundation

# 2. Then merge cleanup changes
git merge origin/feature/section-1b-cleanup
# Resolve any conflicts (likely import paths)
git push origin feature/section-1-foundation

# 3. Finally merge database changes
git merge origin/feature/section-1d-database
# Resolve any conflicts
git push origin feature/section-1-foundation

# 4. Test the integrated changes
# Run application, run tests, verify everything works

# 5. Create PR to main
# Go to GitHub and create a Pull Request from feature/section-1-foundation to main
```

## Conflict Resolution Guide

### Common Conflicts and Solutions

#### 1. Import Path Conflicts
```python
# Instance 1 might have:
from backend.core.config import settings

# Instance 2 might move config.py, causing:
from backend.config.settings import settings

# Resolution: Accept Instance 2's file organization
```

#### 2. Config File Conflicts
```python
# Instance 1 modifies config.py for security
# Instance 3 modifies config.py for database

# Resolution: Merge both changes:
class Settings(BaseSettings):
    # Instance 1's security settings
    secret_key: str = os.getenv("SECRET_KEY", "")
    
    # Instance 3's database settings
    database_url: str = os.getenv("DATABASE_URL", "")
```

#### 3. Requirements Conflicts
```txt
# Instance 1 adds security packages
# Instance 2 reorganizes requirements
# Instance 3 adds database packages

# Resolution: Let Instance 2 organize, then add others' packages
```

## Validation Checkpoints

### After Each Claude Completes:
```bash
# 1. Check the branch builds
git checkout feature/section-1x-xxx
python -m pip install -r requirements.txt
python backend/main.py  # Should start without errors

# 2. Run security check (after Instance 1)
python scripts/security_scanner.py

# 3. Check file structure (after Instance 2)
find attached_assets/ -type f | wc -l  # Should be 0
ls | wc -l  # Root files should be < 10

# 4. Check migrations (after Instance 3)
alembic upgrade head  # Should run without errors
```

## Emergency Procedures

### If Something Goes Wrong:
```bash
# 1. Don't panic! You have backups

# 2. Reset a branch if needed
git checkout feature/section-1x-xxx
git reset --hard origin/feature/section-1-foundation

# 3. Or start fresh from backup
git checkout backup/pre-section-1-$(date +%Y%m%d)
git checkout -b feature/section-1x-xxx-retry

# 4. Cherry-pick good commits
git cherry-pick <commit-hash-of-good-change>
```

## Communication Templates

### Daily Status Update
```markdown
## Claude Instance X Status - Day Y

### Completed:
- [ ] Task 1
- [ ] Task 2

### Blockers:
- Need Instance Y to complete Z first

### Files Modified:
- `path/to/file1.py` - Description of changes
- `path/to/file2.py` - Description of changes

### Commits:
- `abc123` - Commit message
- `def456` - Commit message

### Tomorrow's Plan:
- Will work on...
```

### Handoff Communication
```markdown
## Handoff from Instance X to Instance Y

### What I Changed:
- Moved config.py to backend/core/
- Updated all imports in these files: [list]

### What You Need to Know:
- New import path is: `from backend.core.config import settings`
- Database URL env var is now: `DATABASE_URL`

### Don't Touch These Files:
- [List of files that shouldn't be modified]
```
