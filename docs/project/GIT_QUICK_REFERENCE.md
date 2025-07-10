# 🎯 TradeSense Git Quick Reference

## 🚀 Daily Commands

```bash
# Start your day
git pull origin main              # Get latest changes

# Make changes and commit
./git-workflow.sh                 # Option 1 for standard commit

# Quick status check
git status --short               # Or: git st (with aliases)

# View recent changes
git log --oneline -5            # Last 5 commits
```

## 📝 Commit Format

```
type(scope): subject

Types: feat|fix|docs|style|refactor|test|chore
```

### Examples:
- `feat(auth): add login endpoint`
- `fix(analytics): correct drawdown calculation`
- `docs: update API documentation`

## 🌳 Branch Commands

```bash
# Create feature branch
git checkout -b feature/my-feature

# Or use workflow
./git-workflow.sh → Option 4

# Switch branches
git checkout main
git checkout develop

# List branches
git branch -a
```

## 🏷️ Version Release

```bash
# Create a release
./git-workflow.sh → Option 2

# Version bumps:
# v1.2.3 → v1.2.4 (patch - bug fixes)
# v1.2.3 → v1.3.0 (minor - new features)
# v1.2.3 → v2.0.0 (major - breaking changes)
```

## 🛡️ Protected Files

**NEVER directly modify:**
- `COMPLETE_SAAS_ARCHITECTURE_GUIDE/*`
- `PROTECTED_FILES.md`
- `project-rules.md`
- `README.md`
- `README_DEV.md`

**To modify:** Get approval → Create issue → Make PR

## 🚨 Emergency Commands

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard all local changes
git reset --hard HEAD

# Recover deleted file
git checkout HEAD -- filename

# View all actions (recovery)
git reflog
```

## ⚡ Aliases (if installed)

| Alias | Command | Description |
|-------|---------|-------------|
| `git st` | `status --short` | Quick status |
| `git cm` | `commit -m` | Quick commit |
| `git lg` | Pretty log | Visual history |
| `git last` | Last commit details | What changed |
| `git undo` | Undo last commit | Keep changes |
| `git protected` | Show protected files | Safety check |

## 🔄 Sync Commands

```bash
# Get latest without merging
git fetch origin

# Pull and merge
git pull origin main

# Push changes
git push origin branch-name

# Push with tags
git push origin main --tags
```

## 📋 Workflow Options

1. **Standard Commit** - Daily work
2. **Version Release** - Tagged releases  
3. **Hotfix** - Emergency fixes
4. **Feature Branch** - New features
5. **Show History** - View logs
6. **Setup Hooks** - Install automation
7. **Validate** - Check project
8. **Rollback** - Emergency undo

## ⚠️ Pre-commit Checks

Automatic checks:
- ✓ Protected file warnings
- ✓ Merge conflict detection
- ✓ Python syntax validation
- ✓ Sensitive data scanning
- ✓ Large file warnings

## 💡 Pro Tips

1. **Commit often** - Small, logical changes
2. **Write good messages** - Future you will thank you
3. **Branch for features** - Keep main clean
4. **Tag releases** - Track versions properly
5. **Check before push** - `git log --oneline -3`
6. **Use the workflow** - `./git-workflow.sh`

---
**Help:** `./git-workflow.sh` | **Docs:** `GIT_WORKFLOW_GUIDE.md`
