# 📋 TradeSense GitHub Repository Restructuring Plan

> **For Claude Code**: This is a detailed plan to restructure the TradeSense repository. Follow each section carefully and ask for clarification if needed.

## 🛡️ CRITICAL: Protected Files & Directories

**These must NEVER be deleted or have their content modified:**
```
COMPLETE_SAAS_ARCHITECTURE_GUIDE/
├── All 18 architecture documents
└── MASTER_IMPLEMENTATION_ROADMAP/

PROTECTED_FILES.md
project-rules.md
README.md
README_DEV.md
```

**These can be MOVED but not deleted or modified:**
```
git-workflow.sh
GIT_WORKFLOW_GUIDE.md
GIT_QUICK_REFERENCE.md
setup-git-workflow.sh
```

## 📁 Target Repository Structure

```
tradesense/
├── .github/                      # GitHub-specific files
│   ├── workflows/                # CI/CD pipelines
│   │   ├── ci.yml               # Continuous integration
│   │   ├── release.yml          # Release automation
│   │   └── tests.yml            # Test automation
│   ├── ISSUE_TEMPLATE/          # Issue templates
│   │   ├── bug_report.md        # Bug report template
│   │   ├── feature_request.md   # Feature request template
│   │   └── config.yml           # Issue template chooser
│   ├── pull_request_template.md # PR template
│   ├── CODEOWNERS              # Code ownership
│   ├── dependabot.yml          # Dependency updates
│   └── FUNDING.yml             # Sponsorship info (optional)
│
├── docs/                        # All documentation
│   ├── architecture/           # MOVE COMPLETE_SAAS_ARCHITECTURE_GUIDE here
│   │   └── [all architecture files]
│   ├── api/                    # API documentation
│   │   └── README.md          # API overview
│   ├── guides/                 # User and developer guides
│   │   ├── GIT_WORKFLOW_GUIDE.md     # MOVE from root
│   │   ├── GIT_QUICK_REFERENCE.md    # MOVE from root
│   │   └── development-setup.md       # New: setup guide
│   └── project/                # Project documentation
│       ├── PROTECTED_FILES.md  # MOVE from root
│       └── project-rules.md    # MOVE from root
│
├── src/                        # Source code
│   ├── app/                    # MOVE app.py and related files
│   ├── core/                   # MOVE core functionality
│   ├── services/               # MOVE services/
│   ├── models/                 # MOVE models/
│   ├── routers/               # MOVE routers/
│   ├── utils/                 # Utility functions
│   └── __init__.py
│
├── tests/                      # Test files
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   ├── fixtures/              # Test fixtures
│   └── conftest.py           # Pytest configuration
│
├── scripts/                    # Utility scripts
│   ├── git-workflow.sh        # MOVE from root
│   ├── setup-git-workflow.sh  # MOVE from root
│   └── setup-dev.sh          # New: development setup script
│
├── config/                     # Configuration files
│   ├── .env.example           # Example environment variables
│   └── settings.py            # MOVE if exists
│
├── data/                       # Data files
│   └── sample_data/           # MOVE sample_data/
│
├── assets/                     # Static assets
│   ├── images/               # Images for docs/readme
│   └── diagrams/             # Architecture diagrams
│
├── .gitignore                 # UPDATE with new structure
├── README.md                  # UPDATE with new structure
├── README_DEV.md             # Keep in root
├── LICENSE                    # Create if not exists
├── requirements.txt           # Keep in root
├── requirements-dev.txt       # Create for dev dependencies
├── setup.py                   # Create for package installation
├── pyproject.toml            # Modern Python project config
└── CHANGELOG.md              # Keep in root
```

## 📝 Step-by-Step Execution Plan

### Phase 1: Setup & Backup
```bash
# 1. Create backup branch
git checkout -b backup-before-restructure-$(date +%Y%m%d)
git push origin backup-before-restructure-$(date +%Y%m%d)

# 2. Create feature branch
git checkout -b feature/repository-restructure

# 3. Create directory structure
mkdir -p .github/{workflows,ISSUE_TEMPLATE}
mkdir -p docs/{architecture,api,guides,project}
mkdir -p src/{app,core,services,models,routers,utils}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p scripts config data assets/{images,diagrams}
```

### Phase 2: Move Protected Documentation
```bash
# CRITICAL: Move, don't delete and recreate!
# 1. Move architecture guide (preserve git history)
git mv COMPLETE_SAAS_ARCHITECTURE_GUIDE docs/architecture/

# 2. Move project documentation
git mv PROTECTED_FILES.md docs/project/
git mv project-rules.md docs/project/

# 3. Move git guides
git mv GIT_WORKFLOW_GUIDE.md docs/guides/
git mv GIT_QUICK_REFERENCE.md docs/guides/
```

### Phase 3: Move Application Code
```bash
# Move main application files
git mv app.py src/app/
git mv startup.py src/app/  # if exists

# Move directories
git mv core/* src/core/  # if exists
git mv services/* src/services/
git mv models/* src/models/
git mv routers/* src/routers/

# Move other Python files to appropriate locations
# [Claude Code: Identify and move remaining .py files]
```

### Phase 4: Move Scripts and Data
```bash
# Move scripts
git mv git-workflow.sh scripts/
git mv setup-git-workflow.sh scripts/
git mv git-version.sh scripts/  # if still exists

# Move sample data
git mv sample_data data/  # if exists
```

### Phase 5: Create GitHub Files

#### `.github/workflows/ci.yml`
```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    - name: Run tests
      run: pytest
    - name: Check protected files
      run: |
        # Verify protected files exist
        test -f docs/project/PROTECTED_FILES.md
        test -d docs/architecture/COMPLETE_SAAS_ARCHITECTURE_GUIDE
```

#### `.github/ISSUE_TEMPLATE/bug_report.md`
```markdown
---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g. Windows, Mac, Linux]
 - Python version: [e.g. 3.11]
 - Version: [e.g. v1.0.0]
```

#### `.github/CODEOWNERS`
```
# Project documentation owners
/docs/project/ @tarigelamin
/docs/architecture/COMPLETE_SAAS_ARCHITECTURE_GUIDE/ @tarigelamin

# Code owners
/src/ @tarigelamin
```

### Phase 6: Update Configuration Files

#### Update `.gitignore`
```gitignore
# Add new patterns
.github/workflows/local/
docs/architecture/COMPLETE_SAAS_ARCHITECTURE_GUIDE/.backup/
scripts/*.log

# Keep existing patterns
[existing content]
```

#### Create `pyproject.toml`
```toml
[project]
name = "tradesense"
version = "0.1.0"
description = "Trading analytics and risk management platform"
readme = "README.md"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]

[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
```

### Phase 7: Update Import Paths

**Critical: Update all Python imports to reflect new structure**
```python
# Old imports
from services.auth_service import AuthService
from models.user import User

# New imports
from src.services.auth_service import AuthService
from src.models.user import User
```

### Phase 8: Update Documentation

#### Update README.md
Add new repository structure section:
```markdown
## 📁 Repository Structure

\```
tradesense/
├── .github/          # GitHub Actions and templates
├── docs/             # All documentation
│   ├── architecture/ # System architecture (PROTECTED)
│   ├── api/         # API documentation
│   ├── guides/      # User guides
│   └── project/     # Project rules (PROTECTED)
├── src/             # Source code
├── tests/           # Test suite
├── scripts/         # Utility scripts
└── config/          # Configuration
\```

See [docs/guides/](docs/guides/) for detailed guides.
```

### Phase 9: Create Migration Guide

#### Create `MIGRATION.md` in root
```markdown
# Repository Restructure Migration Guide

Date: [Current Date]

## Files Moved

| Old Location | New Location | Notes |
|--------------|--------------|-------|
| `/COMPLETE_SAAS_ARCHITECTURE_GUIDE/` | `/docs/architecture/COMPLETE_SAAS_ARCHITECTURE_GUIDE/` | Preserved with history |
| `/PROTECTED_FILES.md` | `/docs/project/PROTECTED_FILES.md` | Preserved with history |
| `/app.py` | `/src/app/app.py` | Update imports |
| ... | ... | ... |

## Import Updates Required
[List all import changes needed]

## Rollback Instructions
```bash
git checkout backup-before-restructure-[date]
```
```

## ✅ Validation Checklist

After restructuring, verify:

- [ ] All files in PROTECTED_FILES.md still exist
- [ ] Python imports are updated and working
- [ ] `pytest` runs successfully
- [ ] Application starts without errors
- [ ] Git history is preserved for moved files
- [ ] README.md reflects new structure
- [ ] No accidental deletions occurred

## 🚨 If Something Goes Wrong

```bash
# Quick rollback
git checkout main
git branch -D feature/repository-restructure

# Restore from backup
git checkout backup-before-restructure-[date]
```

## 📋 Claude Code Instructions

1. **Read this entire document first**
2. **Check PROTECTED_FILES.md before starting**
3. **Execute phases in order**
4. **Use `git mv` not `mv` to preserve history**
5. **Test after each phase**
6. **Create MIGRATION.md as you go**
7. **Ask if anything is unclear**

## 🎯 Success Criteria

- Clean, professional repository structure
- All protected files intact
- Working application
- Improved organization
- GitHub best practices implemented
- Clear documentation of changes

---

**Remember**: The goal is organization, not modification. Preserve all functionality while improving structure.
