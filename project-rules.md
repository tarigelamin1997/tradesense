# 📜 TradeSense Project Development Rules & Guidelines

> 🔒 **Critical**: This document governs all development on the TradeSense project.  
> All contributors (human and AI) must read and follow these rules.

## 🛡️ Protected Files & Documentation

### Absolute Protection List
The following files/directories have **MAXIMUM PROTECTION** status:
- `COMPLETE_SAAS_ARCHITECTURE_GUIDE/` - All 18 architecture documents + subdirectories
- `PROTECTED_FILES.md` - The protection manifest itself
- `project-rules.md` - This file
- `README.md` - Main project documentation
- `README_DEV.md` - Developer guide

**See `PROTECTED_FILES.md` for the complete list.**

### Protection Rules
1. **NEVER** delete protected files without written approval in an issue/PR
2. **ALWAYS** check `PROTECTED_FILES.md` before any cleanup operation
3. **BACKUP** before touching any protected file
4. **DOCUMENT** any changes to protected files in commit messages

## 🤖 AI Assistant Guidelines (Claude Code, GitHub Copilot, etc.)

### When Working with AI Assistants
1. **Always mention protected files** when giving general prompts like "clean up" or "reorganize"
2. **Be specific** about what can and cannot be touched
3. **Review changes** before accepting AI suggestions
4. **Save session context** when switching between AI assistants

### AI Assistant Rules
- Check `PROTECTED_FILES.md` before any file operations
- Ask for clarification on ambiguous requests
- Preserve all documentation unless explicitly told to remove it
- Focus on code files for cleanup, not documentation
- Never remove files matching protected patterns (`*architecture*`, `*plan*`, etc.)

## ✅ Core Development Rules

### 1. Respect Existing Structure
- **DO NOT** restructure, rename, or move files without approval
- **DO NOT** flatten directory structures (keep `core/`, `app/`, etc.)
- **KEEP** working files as-is until modularization is agreed upon

### 2. No Auto-Deletions or Mass Overwrites
Before any deletion:
- ✓ Get approval in writing
- ✓ Explain why it's needed
- ✓ Create a backup branch
- ✓ Document what was removed

### 3. Gradual & Measured Changes
```bash
# ❌ BAD: Big bang refactor
git add -A && git commit -m "Refactored everything"

# ✅ GOOD: Incremental changes
git add auth.py && git commit -m "Extract auth logic to separate module"
git add app.py && git commit -m "Update app.py to use new auth module"
```

### 4. Every Change Must Be Reversible
```bash
# Before major changes
git checkout -b backup-$(date +%Y%m%d)-feature-name
git push origin backup-$(date +%Y%m%d)-feature-name

# Quick rollback if needed
git checkout main
```

## 📦 Dependency Management

### Rules for Dependencies
1. **All packages** must be in `requirements.txt` with pinned versions
2. **No runtime installs** in `.replit` or application code
3. **Test locally** with `pip install -r requirements.txt` before pushing
4. **Document** any special installation requirements

### Adding a New Package
```bash
# 1. Install and test
pip install package-name==1.2.3

# 2. Add to requirements.txt with comment
echo "package-name==1.2.3  # Used for: brief description" >> requirements.txt

# 3. Test clean install
pip install -r requirements.txt

# 4. Commit with clear message
git add requirements.txt
git commit -m "Add package-name==1.2.3 for [feature/purpose]"
```

## 🔧 Development Workflows

### Feature Development
1. **Plan** - Document in issue/discussion first
2. **Branch** - Create feature branch from main
3. **Develop** - Make incremental commits
4. **Test** - Ensure nothing breaks
5. **Document** - Update relevant docs
6. **Review** - Self-review or peer review
7. **Merge** - Clean merge to main

### Refactoring Workflow
1. **Identify** - What needs refactoring and why
2. **Proposal** - Create refactoring plan
3. **Backup** - Create backup branch
4. **Refactor** - Small, testable chunks
5. **Validate** - Each step must work
6. **Document** - Update architecture docs if needed

## 🚨 Conflict Resolution

### Git Conflicts
```bash
# When conflicts occur
git status                    # See conflicted files
git diff                      # Review conflicts

# For protected files - ALWAYS favor preservation
git checkout --theirs PROTECTED_FILES.md  # Keep existing protected file

# For code conflicts - Review carefully
# Open file, resolve manually, then:
git add <resolved-file>
git commit
```

### Architecture Conflicts
1. **Stop** - Don't proceed with conflicting changes
2. **Document** - Create issue explaining the conflict
3. **Discuss** - Get team consensus
4. **Update** - Modify architecture docs FIRST
5. **Implement** - Then make code changes

### Decision Making
- **Minor changes** (< 50 lines): Dev discretion with good commit message
- **Medium changes** (50-500 lines): Create PR for review
- **Major changes** (> 500 lines or architectural): Require issue + discussion + approval

## 🏗️ Replit-Specific Rules

### Protected Replit Files
```python
# ⚠️ WARNING: This file is production-critical.
# Do not refactor, delete, or modularize without explicit approval.
# Read project-rules.md before making changes.
```

Add this banner to:
- `app.py`
- `startup.py`
- `.replit`
- `replit.nix`
- `core/app_factory.py`

### Replit Config Changes
1. **Never** modify `.replit` or `replit.nix` without testing
2. **Always** keep a backup of working config
3. **Document** any config changes in comments
4. **Test** in a fresh Repl if possible

## 📝 Documentation Standards

### When to Update Docs
- **ALWAYS** when changing architecture
- **ALWAYS** when adding/removing features
- **ALWAYS** when changing APIs
- **WHEN NEEDED** for bug fixes

### Documentation Hierarchy
1. `COMPLETE_SAAS_ARCHITECTURE_GUIDE/` - Architecture decisions
2. `README.md` - User-facing documentation
3. `README_DEV.md` - Developer documentation
4. `PROTECTED_FILES.md` - File protection manifest
5. Code comments - Implementation details

## 🎯 Final Checklist

Before any commit, ask yourself:
- [ ] Did I check `PROTECTED_FILES.md`?
- [ ] Are my changes incremental and reversible?
- [ ] Did I update relevant documentation?
- [ ] Will this break existing functionality?
- [ ] Is my commit message clear and descriptive?
- [ ] Did I test the changes?

## 📌 Golden Rules

1. **Preserve** > Refactor
2. **Document** > Assume
3. **Ask** > Guess
4. **Backup** > Regret
5. **Test** > Hope

---

**Remember**: We're building a production system. Every file has a purpose, every line has a history, and every change has consequences. Respect what exists, improve what needs improving, and always leave the codebase better than you found it.

**Last Updated**: July 9, 2025  
**Enforced By**: All TradeSense Contributors  
**Questions?** Create an issue or check existing documentation first.
