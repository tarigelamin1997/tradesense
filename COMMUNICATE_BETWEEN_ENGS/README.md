# Engineering Communication Directory

This directory facilitates communication between different engineering teams when cross-functional issues arise.

## Purpose

When one engineer encounters blockers or issues that require another engineer's expertise, they create detailed notes here instead of blocking their own work.

## File Naming Convention

```
NOTES-FROM-[ROLE]-TO-[ROLE]-[YYYYMMDD-HHMMSS].md
```

Examples:
- `NOTES-FROM-DEVOPS-TO-FRONTEND-20250124-163300.md`
- `NOTES-FROM-BACKEND-TO-DEVOPS-20250124-170000.md`
- `NOTES-FROM-FRONTEND-TO-BACKEND-20250124-180000.md`

## Roles

- **DEVOPS**: Infrastructure, CI/CD, deployments, monitoring
- **BACKEND**: API services, databases, business logic
- **FRONTEND**: UI/UX, client-side code, build issues
- **SECURITY**: Security vulnerabilities, authentication issues
- **QA**: Testing, quality assurance, bug reports

## Template

```markdown
# [Brief Issue Title]

**From**: [Your Role]  
**To**: [Target Role]  
**Date**: [YYYY-MM-DD HH:MM:SS]  
**Priority**: [LOW/MEDIUM/HIGH/CRITICAL]

## Issue Summary
[1-2 sentence summary]

## Details
[Detailed description of the issue]

## Impact
[How this blocks your work]

## Required Actions
1. [Action 1]
2. [Action 2]

## How to Test/Verify
[Steps to reproduce or verify the fix]
```

## Process

1. **Creating Issues**: When blocked, create a detailed note file
2. **Resolution**: The responsible engineer addresses the issue and updates the file
3. **Completion**: Mark as RESOLVED in the filename or content
4. **Archival**: Move resolved issues to an `archived/` subdirectory monthly

## Current Active Issues

- ✅ Frontend build errors blocking Vercel deployment
- ✅ Backend service configuration recommendations

---

This system ensures engineers can continue working without waiting for immediate responses while maintaining clear communication about cross-functional dependencies.