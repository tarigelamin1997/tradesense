# 🔒 Security Setup Guide

This guide helps you set up comprehensive security measures to prevent accidental secret commits.

## Quick Setup

1. **Run the automated setup script:**
   ```bash
   ./setup-secret-scanning.sh
   ```

2. **Manual setup (if script fails):**
   ```bash
   # Install Python dependencies
   pip install -r requirements-dev.txt
   
   # Install pre-commit hooks
   pre-commit install
   pre-commit install --hook-type commit-msg
   
   # Create initial secrets baseline
   detect-secrets scan --all-files > .secrets.baseline
   
   # Test the hooks
   pre-commit run --all-files
   ```

## What's Protected

### 1. **Enhanced .gitignore**
- Blocks common secret file patterns
- Prevents committing of .env files
- Excludes SSH keys, certificates, and tokens
- Ignores cloud provider credentials

### 2. **Pre-commit Hooks**
- **detect-secrets**: Scans for API keys, tokens, passwords
- **bandit**: Python security linting
- **eslint-security**: JavaScript security checks
- **private-key detection**: Blocks SSH/GPG keys
- **large file prevention**: Blocks files >1MB

### 3. **GitHub Actions**
- Automated security scans on every push
- Daily scheduled security audits
- Dependency vulnerability checks
- License compliance verification

### 4. **Environment Variables**
- Comprehensive documentation
- Example files without real secrets
- Best practices guide

## Testing Security

### Test Secret Detection
```bash
# This should be blocked:
echo "aws_access_key_id = AKIAIOSFODNN7EXAMPLE" > test.txt
git add test.txt
git commit -m "test" # Should fail!
```

### Scan Existing Code
```bash
# Full repository scan
detect-secrets scan --all-files

# Check specific file
detect-secrets scan path/to/file.py
```

### Update Secrets Baseline
```bash
# After reviewing and fixing issues
detect-secrets scan --all-files > .secrets.baseline
```

## Common Issues

### False Positives
If detect-secrets flags something that's not actually a secret:

1. Review the finding
2. If it's safe, add to baseline:
   ```bash
   detect-secrets scan --update .secrets.baseline
   ```

### Pre-commit Fails
```bash
# Skip hooks temporarily (use sparingly!)
git commit --no-verify -m "message"

# Fix and re-run
pre-commit run --all-files
```

### Performance Issues
For large repos, exclude directories:
```yaml
# In .pre-commit-config.yaml
exclude: |
  (?x)^(
    frontend/node_modules/|
    venv/|
    .*\.min\.js
  )$
```

## Best Practices

### 1. **Never Hardcode Secrets**
```python
# ❌ Bad
API_KEY = "sk-1234567890abcdef"

# ✅ Good
API_KEY = os.getenv("API_KEY")
```

### 2. **Use Environment Files Correctly**
```bash
# Development
cp .env.example .env
# Edit .env with your values

# Production
# Use secret management service
```

### 3. **Rotate Secrets Regularly**
- Set calendar reminders
- Use short-lived tokens when possible
- Audit access logs

### 4. **Emergency Response**
If a secret is accidentally committed:

1. **Immediately rotate the secret**
2. **Remove from history:**
   ```bash
   # Use BFG Repo-Cleaner
   bfg --delete-files file-with-secret.txt
   git push --force
   ```
3. **Notify team members**
4. **Update .gitignore**

## Additional Resources

- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [Pre-commit Documentation](https://pre-commit.com/)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

## Maintenance

- Review `.secrets.baseline` monthly
- Update security tools quarterly
- Run `pip install --upgrade` for tools
- Check for new secret patterns

---

Remember: **When in doubt, don't commit!** It's better to be safe than sorry.