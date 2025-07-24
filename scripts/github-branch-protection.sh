#!/bin/bash

# GitHub Branch Protection Setup Script
# Configures branch protection rules for the TradeSense repository

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REPO_OWNER="tarigelamin1997"
REPO_NAME="tradesense"
MAIN_BRANCH="main"
DEVELOP_BRANCH="develop"

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v gh >/dev/null 2>&1; then
        error "GitHub CLI (gh) not installed"
        echo "Install with: brew install gh (macOS) or see https://cli.github.com"
        exit 1
    fi
    
    # Check if authenticated
    if ! gh auth status >/dev/null 2>&1; then
        error "Not authenticated with GitHub"
        echo "Run: gh auth login"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Create branch protection for main branch
protect_main_branch() {
    log "Setting up protection for main branch..."
    
    gh api \
        --method PUT \
        -H "Accept: application/vnd.github+json" \
        "/repos/${REPO_OWNER}/${REPO_NAME}/branches/${MAIN_BRANCH}/protection" \
        --field required_status_checks='
        {
            "strict": true,
            "contexts": [
                "security-scan",
                "test-services",
                "test-frontend"
            ]
        }' \
        --field enforce_admins=false \
        --field required_pull_request_reviews='
        {
            "dismissal_restrictions": {},
            "dismiss_stale_reviews": true,
            "require_code_owner_reviews": true,
            "required_approving_review_count": 1,
            "require_last_push_approval": false
        }' \
        --field restrictions=null \
        --field allow_force_pushes=false \
        --field allow_deletions=false \
        --field block_creations=false \
        --field required_conversation_resolution=true \
        --field lock_branch=false \
        --field allow_fork_syncing=true
    
    success "Main branch protection configured"
}

# Create branch protection for develop branch
protect_develop_branch() {
    log "Setting up protection for develop branch..."
    
    # First, create develop branch if it doesn't exist
    if ! gh api "/repos/${REPO_OWNER}/${REPO_NAME}/branches/${DEVELOP_BRANCH}" >/dev/null 2>&1; then
        log "Creating develop branch..."
        gh api \
            --method POST \
            -H "Accept: application/vnd.github+json" \
            "/repos/${REPO_OWNER}/${REPO_NAME}/git/refs" \
            --field ref="refs/heads/${DEVELOP_BRANCH}" \
            --field sha="$(gh api /repos/${REPO_OWNER}/${REPO_NAME}/git/refs/heads/${MAIN_BRANCH} --jq .object.sha)"
    fi
    
    gh api \
        --method PUT \
        -H "Accept: application/vnd.github+json" \
        "/repos/${REPO_OWNER}/${REPO_NAME}/branches/${DEVELOP_BRANCH}/protection" \
        --field required_status_checks='
        {
            "strict": false,
            "contexts": [
                "test-services",
                "test-frontend"
            ]
        }' \
        --field enforce_admins=false \
        --field required_pull_request_reviews='
        {
            "dismiss_stale_reviews": true,
            "require_code_owner_reviews": false,
            "required_approving_review_count": 1
        }' \
        --field restrictions=null \
        --field allow_force_pushes=false \
        --field allow_deletions=false
    
    success "Develop branch protection configured"
}

# Set up security policies
setup_security_policies() {
    log "Creating security policy..."
    
    mkdir -p .github
    
    cat > .github/SECURITY.md << 'EOF'
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of TradeSense seriously. If you have discovered a security vulnerability, please follow these steps:

### 1. **Do NOT** disclose publicly
Please do not disclose the vulnerability publicly until we have had a chance to address it.

### 2. Contact us
Email: security@tradesense.com

Include:
- Type of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### 3. Response timeline
- **Acknowledgment**: Within 24 hours
- **Initial assessment**: Within 72 hours
- **Resolution timeline**: Depends on severity
  - Critical: 1-3 days
  - High: 1 week
  - Medium: 2 weeks
  - Low: 1 month

### 4. Recognition
We appreciate responsible disclosure and will acknowledge security researchers who help us maintain the security of TradeSense.

## Security Measures

### Code Security
- All code is reviewed before merging
- Dependencies are regularly updated
- Security scanning in CI/CD pipeline
- SAST and DAST testing

### Infrastructure Security
- End-to-end encryption
- Regular security audits
- Intrusion detection
- Access logging and monitoring

### Data Security
- Encryption at rest and in transit
- Regular backups
- GDPR compliant
- PII data minimization

## Security Checklist for Contributors

Before submitting a PR:
- [ ] No hardcoded secrets
- [ ] Input validation implemented
- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] CSRF tokens used
- [ ] Authentication required for sensitive endpoints
- [ ] Rate limiting considered
- [ ] Error messages don't leak sensitive info
- [ ] Dependencies are up to date
- [ ] Security tests pass

## Contact

Security Team: security@tradesense.com
EOF

    success "Security policy created"
}

# Set up dependabot
setup_dependabot() {
    log "Creating Dependabot configuration..."
    
    mkdir -p .github
    
    cat > .github/dependabot.yml << 'EOF'
version: 2
updates:
  # Python dependencies for backend services
  - package-ecosystem: "pip"
    directory: "/services/gateway"
    schedule:
      interval: "weekly"
      day: "monday"
    labels:
      - "dependencies"
      - "python"
    reviewers:
      - "tarigelamin1997"
    open-pull-requests-limit: 5

  - package-ecosystem: "pip"
    directory: "/services/auth"
    schedule:
      interval: "weekly"
      day: "monday"
    labels:
      - "dependencies"
      - "python"
      - "security"
    reviewers:
      - "tarigelamin1997"

  - package-ecosystem: "pip"
    directory: "/services/trading"
    schedule:
      interval: "weekly"
      day: "monday"
    labels:
      - "dependencies"
      - "python"
    reviewers:
      - "tarigelamin1997"

  - package-ecosystem: "pip"
    directory: "/services/analytics"
    schedule:
      interval: "weekly"
      day: "monday"
    labels:
      - "dependencies"
      - "python"
    reviewers:
      - "tarigelamin1997"

  - package-ecosystem: "pip"
    directory: "/services/market-data"
    schedule:
      interval: "weekly"
      day: "monday"
    labels:
      - "dependencies"
      - "python"
    reviewers:
      - "tarigelamin1997"

  - package-ecosystem: "pip"
    directory: "/services/billing"
    schedule:
      interval: "weekly"
      day: "monday"
    labels:
      - "dependencies"
      - "python"
    reviewers:
      - "tarigelamin1997"

  - package-ecosystem: "pip"
    directory: "/services/ai"
    schedule:
      interval: "weekly"
      day: "monday"
    labels:
      - "dependencies"
      - "python"
    reviewers:
      - "tarigelamin1997"

  # Frontend dependencies
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
      day: "monday"
    labels:
      - "dependencies"
      - "javascript"
    reviewers:
      - "tarigelamin1997"
    open-pull-requests-limit: 5

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    labels:
      - "dependencies"
      - "github-actions"
    reviewers:
      - "tarigelamin1997"

  # Docker dependencies
  - package-ecosystem: "docker"
    directory: "/services/gateway"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "docker"
    reviewers:
      - "tarigelamin1997"
EOF

    success "Dependabot configuration created"
}

# Create pull request template
create_pr_template() {
    log "Creating pull request template..."
    
    mkdir -p .github
    
    cat > .github/pull_request_template.md << 'EOF'
## Description
<!-- Provide a brief description of the changes in this PR -->

## Type of Change
<!-- Mark the relevant option with an "x" -->
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring

## Related Issues
<!-- Link to related issues -->
Fixes #(issue number)

## Testing
<!-- Describe the tests you ran to verify your changes -->
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Performance impact assessed

## Checklist
<!-- Mark completed items with an "x" -->
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Security Checklist
<!-- For security-sensitive changes -->
- [ ] No hardcoded secrets or credentials
- [ ] Input validation implemented
- [ ] SQL injection prevention verified
- [ ] XSS protection in place
- [ ] Authentication/authorization properly implemented
- [ ] Sensitive data properly encrypted
- [ ] Security tests added/updated

## Performance Impact
<!-- Describe any performance implications -->
- [ ] Database queries optimized
- [ ] Caching strategy considered
- [ ] Load testing performed (if applicable)
- [ ] No significant performance degradation

## Screenshots (if applicable)
<!-- Add screenshots to help explain your changes -->

## Additional Notes
<!-- Add any additional notes for reviewers -->
EOF

    success "Pull request template created"
}

# Create issue templates
create_issue_templates() {
    log "Creating issue templates..."
    
    mkdir -p .github/ISSUE_TEMPLATE
    
    # Bug report template
    cat > .github/ISSUE_TEMPLATE/bug_report.md << 'EOF'
---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: 'bug'
assignees: ''
---

## Bug Description
<!-- A clear and concise description of what the bug is -->

## To Reproduce
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
<!-- A clear and concise description of what you expected to happen -->

## Actual Behavior
<!-- What actually happened -->

## Screenshots
<!-- If applicable, add screenshots to help explain your problem -->

## Environment
- **Service**: [e.g., Gateway, Auth, Trading]
- **Browser** (if frontend): [e.g., Chrome 120, Safari 17]
- **OS**: [e.g., macOS 14, Ubuntu 22.04]
- **Version**: [e.g., 1.0.0]

## Logs
<!-- Please include relevant log entries -->
```
Paste logs here
```

## Additional Context
<!-- Add any other context about the problem here -->

## Possible Solution
<!-- If you have suggestions on how to fix the bug -->
EOF

    # Feature request template
    cat > .github/ISSUE_TEMPLATE/feature_request.md << 'EOF'
---
name: Feature Request
about: Suggest an idea for this project
title: '[FEATURE] '
labels: 'enhancement'
assignees: ''
---

## Feature Description
<!-- A clear and concise description of the feature -->

## Problem Statement
<!-- Describe the problem this feature would solve -->

## Proposed Solution
<!-- Describe your proposed solution -->

## Alternatives Considered
<!-- Describe any alternative solutions or features you've considered -->

## Implementation Details
<!-- If you have ideas on how to implement this feature -->

## Additional Context
<!-- Add any other context, mockups, or screenshots about the feature request here -->

## Acceptance Criteria
<!-- Define what needs to be done for this feature to be considered complete -->
- [ ] Criteria 1
- [ ] Criteria 2
- [ ] Criteria 3
EOF

    # Security issue template
    cat > .github/ISSUE_TEMPLATE/security_issue.md << 'EOF'
---
name: Security Issue
about: Report a security vulnerability
title: '[SECURITY] '
labels: 'security'
assignees: ''
---

<!-- 
⚠️ IMPORTANT: If this is a security vulnerability, please do NOT create a public issue.
Instead, please email security@tradesense.com with the details.
-->

## Security Issue Type
<!-- Only use this template for general security improvements, not vulnerabilities -->
- [ ] Security hardening suggestion
- [ ] Security documentation improvement
- [ ] Security testing enhancement

## Description
<!-- Describe the security improvement -->

## Current State
<!-- Describe the current security posture -->

## Proposed Improvement
<!-- Describe your suggested security enhancement -->

## Impact
<!-- Describe the security impact of this change -->

## Additional Context
<!-- Add any other context about the security improvement -->
EOF

    success "Issue templates created"
}

# Main setup process
main() {
    log "🔐 Starting GitHub repository security configuration..."
    
    check_prerequisites
    
    echo ""
    log "This script will:"
    echo "  1. Set up branch protection rules"
    echo "  2. Create security policy"
    echo "  3. Configure Dependabot"
    echo "  4. Create PR and issue templates"
    echo ""
    echo "Repository: ${REPO_OWNER}/${REPO_NAME}"
    echo ""
    
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Setup cancelled"
        exit 0
    fi
    
    # Run setup
    protect_main_branch
    protect_develop_branch
    setup_security_policies
    setup_dependabot
    create_pr_template
    create_issue_templates
    
    echo ""
    success "✨ GitHub security configuration complete!"
    
    echo ""
    echo "📋 Next steps:"
    echo "1. Review and commit the created files:"
    echo "   - .github/SECURITY.md"
    echo "   - .github/dependabot.yml"
    echo "   - .github/pull_request_template.md"
    echo "   - .github/ISSUE_TEMPLATE/*.md"
    echo "2. Push changes to GitHub"
    echo "3. Verify branch protection rules in repository settings"
    echo "4. Add team members to CODEOWNERS file"
    echo "5. Configure security alerts in repository settings"
    echo ""
    echo "🔗 Repository settings: https://github.com/${REPO_OWNER}/${REPO_NAME}/settings"
}

# Run main function
main "$@"