# 🚀 TradeSense Git Workflow Guide

> Complete Git strategy and best practices for the TradeSense project

## 📋 Table of Contents
1. [Quick Start](#quick-start)
2. [Git Workflow System](#git-workflow-system)
3. [Branching Strategy](#branching-strategy)
4. [Commit Guidelines](#commit-guidelines)
5. [Version Management](#version-management)
6. [Protected Files Workflow](#protected-files-workflow)
7. [Emergency Procedures](#emergency-procedures)
8. [CI/CD Integration](#cicd-integration)

## 🏃 Quick Start

### Initial Setup
```bash
# 1. Make the workflow script executable
chmod +x git-workflow.sh

# 2. Install pre-commit hook
cp .git/hooks/pre-commit.example .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# 3. Configure git
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### Daily Workflow
```bash
# For regular commits
./git-workflow.sh
# Select option 1 (Standard commit)

# For releases
./git-workflow.sh
# Select option 2 (Version release)
```

## 🔄 Git Workflow System

### Main Features
- **Protected file checking** - Warns before modifying architecture docs
- **Pre-commit validation** - Syntax checks, merge conflicts, large files
- **Semantic versioning** - Automated version bumping
- **Changelog generation** - Automatic CHANGELOG.md updates
- **Multiple workflows** - Standard, release, hotfix, feature

### Workflow Options

#### 1. Standard Commit
Best for: Daily development, bug fixes, small changes
```bash
./git-workflow.sh → Option 1
```
- Runs pre-commit checks
- Validates protected files
- Creates optional backup
- Pushes to current branch

#### 2. Version Release
Best for: Production releases, milestones
```bash
./git-workflow.sh → Option 2
```
- Shows changes since last release
- Semantic version bumping (major.minor.patch)
- Updates CHANGELOG.md
- Creates annotated tags
- Pushes tags to origin

#### 3. Hotfix Workflow
Best for: Critical production fixes
```bash
./git-workflow.sh → Option 3
```
- Creates hotfix branch
- Fast-track to production
- Merges back to main and develop

#### 4. Feature Branch
Best for: New features, large changes
```bash
./git-workflow.sh → Option 4
```
- Creates feature branches
- Manages feature lifecycle
- Handles merging back to main

## 🌳 Branching Strategy

### Branch Types

```
main (production)
├── develop (integration)
├── feature/add-authentication
├── feature/improve-analytics
├── hotfix/fix-critical-bug
└── release/v1.2.0
```

### Branch Rules

| Branch | Purpose | Naming | Merge To |
|--------|---------|--------|----------|
| `main` | Production code | - | - |
| `develop` | Integration branch | - | main |
| `feature/*` | New features | feature/description | develop |
| `hotfix/*` | Emergency fixes | hotfix/description | main & develop |
| `release/*` | Release prep | release/v1.2.0 | main & develop |

### Protected Branches
- `main` - Requires PR and review
- `develop` - Requires PR
- Tags - Cannot be deleted

## 📝 Commit Guidelines

### Conventional Commits
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, semicolons, etc)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes
- `build`: Build system changes
- `revert`: Revert previous commit

### Examples
```bash
# Feature
feat(auth): add JWT authentication

# Bug fix
fix(analytics): correct calculation in drawdown metric

# Documentation
docs: update API endpoints in README

# With scope and body
feat(payments): integrate Stripe payment processing

- Add Stripe SDK
- Implement payment flow
- Add webhook handlers

Closes #123
```

### Commit Rules
1. **Subject line**: 50 characters max, imperative mood
2. **Body**: 72 characters per line, explain what and why
3. **Footer**: Reference issues, breaking changes

## 🏷️ Version Management

### Semantic Versioning
Format: `vMAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes

### Version Workflow
```bash
# Current: v1.2.3

# Bug fix → v1.2.4
./git-workflow.sh → Option 2 → Patch

# New feature → v1.3.0
./git-workflow.sh → Option 2 → Minor

# Breaking change → v2.0.0
./git-workflow.sh → Option 2 → Major
```

### Release Checklist
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped appropriately
- [ ] Create release tag
- [ ] Deploy to production
- [ ] Create GitHub release

## 🛡️ Protected Files Workflow

### Never Directly Modify
```
COMPLETE_SAAS_ARCHITECTURE_GUIDE/
├── All architecture documents
├── Strategy documents
└── Implementation guides
```

### Modification Process
1. **Discuss** - Create issue explaining needed changes
2. **Approve** - Get team consensus
3. **Branch** - Create specific branch for changes
4. **Document** - Explain changes in commit
5. **Review** - Mandatory PR review
6. **Merge** - With full documentation

### If You Must Modify Protected Files
```bash
# 1. Create specific branch
git checkout -b update-architecture-docs

# 2. Make changes carefully
# Edit files...

# 3. Commit with detailed explanation
git commit -m "docs(architecture): update Section 6A for new collaboration tools

- Updated team collaboration guidelines to include Slack integration
- Added new workflow diagrams
- Approved by: @teamlead in issue #456"

# 4. Create PR for review
```

## 🚨 Emergency Procedures

### Accidental Commit to Main
```bash
# DO NOT PUSH!
# Reset to previous commit
git reset --soft HEAD~1

# Create proper branch
git checkout -b proper-branch-name
git commit -m "your message"
```

### Already Pushed Mistakes
```bash
# Create revert commit (safe)
git revert HEAD
git push

# Or use workflow emergency rollback
./git-workflow.sh → Option 8
```

### Lost Work Recovery
```bash
# Check reflog
git reflog

# Recover lost commit
git checkout <commit-hash>
```

### Protected File Accidentally Deleted
```bash
# Restore from main
git checkout main -- PROTECTED_FILES.md

# Restore entire directory
git checkout main -- COMPLETE_SAAS_ARCHITECTURE_GUIDE/
```

## 🔄 CI/CD Integration

### Pre-push Checks
```yaml
# .github/workflows/pre-merge.yml
- Check protected files
- Run tests
- Validate Python syntax
- Check dependencies
- Lint code
```

### Release Pipeline
```yaml
# Triggered by version tags
on:
  push:
    tags:
      - 'v*'
```

### Deployment Gates
1. All tests must pass
2. No protected file violations
3. Changelog updated
4. Version tag valid

## 📊 Git Aliases (Optional)

Add to `~/.gitconfig`:
```ini
[alias]
    # Useful shortcuts
    st = status --short
    cm = commit -m
    co = checkout
    br = branch
    
    # View pretty log
    lg = log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit
    
    # Show files changed in last commit
    last = log -1 HEAD --stat
    
    # Undo last commit (keep changes)
    undo = reset HEAD~1 --mixed
    
    # Show protected files status
    protected = !git status --short | grep -E 'COMPLETE_SAAS_ARCHITECTURE_GUIDE/|PROTECTED_FILES.md|project-rules.md'
```

## 🎯 Best Practices

### Do's ✅
- Use the workflow script for all commits
- Write clear, descriptive commit messages
- Create feature branches for new work
- Tag releases properly
- Keep protected files sacred
- Run tests before committing
- Update documentation with code

### Don'ts ❌
- Don't commit directly to main
- Don't force push to shared branches
- Don't commit sensitive data
- Don't ignore pre-commit warnings
- Don't modify protected files without approval
- Don't skip changelog updates for releases
- Don't use generic commit messages

## 🆘 Getting Help

### Common Issues

**Q: Pre-commit hook not running?**
```bash
chmod +x .git/hooks/pre-commit
```

**Q: Can't push to main?**
- This is intentional! Use feature branches

**Q: Merge conflicts with protected files?**
- Always favor the existing version
- Discuss changes in PR

**Q: Need to break the rules?**
- Document why in commit message
- Get explicit approval
- Update this guide if needed

---

**Remember**: Good Git practices = Happy team + Stable project 🎉

Last Updated: July 9, 2025
