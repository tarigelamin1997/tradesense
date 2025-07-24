#!/bin/bash
# Setup script for secret scanning and pre-commit hooks

echo "🔒 Setting up secret scanning and security tools..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate 2>/dev/null

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install development requirements
echo "📦 Installing security and development tools..."
pip install -r requirements-dev.txt

# Install pre-commit hooks
echo "🔨 Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type commit-msg

# Create initial secrets baseline
echo "🔍 Creating secrets baseline..."
detect-secrets scan --all-files > .secrets.baseline

# Create bandit configuration
echo "📝 Creating bandit configuration..."
cat > .bandit << EOF
[bandit]
exclude: /test,/tests,/venv,/frontend/node_modules
skips: B101
EOF

# Run initial security scan
echo "🔍 Running initial security scan..."
echo "Checking for secrets..."
detect-secrets scan --all-files

echo "Checking Python code security..."
if [ -d "src/backend" ]; then
    bandit -r src/backend/ -f json -o security-report.json || true
fi

# Create GitHub Actions workflow
echo "📝 Creating GitHub Actions security workflow..."
mkdir -p .github/workflows

cat > .github/workflows/security-scan.yml << 'EOF'
name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  secrets-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install detect-secrets
      run: |
        pip install detect-secrets
    
    - name: Run secrets scan
      run: |
        detect-secrets scan --all-files --force-use-all-plugins

  python-security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install security tools
      run: |
        pip install bandit safety pip-audit
    
    - name: Run bandit
      run: |
        bandit -r src/backend/ -f json -o bandit-report.json || true
    
    - name: Check dependencies
      run: |
        safety check || true
        pip-audit || true

  js-security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
    
    - name: Install dependencies
      working-directory: ./frontend
      run: npm ci
    
    - name: Run npm audit
      working-directory: ./frontend
      run: npm audit --production || true
    
    - name: Run ESLint security
      working-directory: ./frontend
      run: |
        npm install -D eslint eslint-plugin-security
        npx eslint --ext .js,.jsx,.ts,.tsx,.svelte src/ || true
EOF

echo "✅ Security setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Review and commit .secrets.baseline file"
echo "2. Run 'pre-commit run --all-files' to test hooks"
echo "3. Commit all security configuration files"
echo "4. Enable GitHub secret scanning in repository settings"
echo ""
echo "🔒 Your repository is now protected against accidental secret commits!"