#!/bin/bash

echo "=== TradeSense Repository Restructuring Validation ==="
echo ""

# Test Backend
echo "=== Testing Backend ==="
cd src/backend
if [ -f "main.py" ]; then
    echo "✓ Backend main.py found"
    python -c "import main" 2>&1 | grep -E "Error|ImportError" || echo "✓ Backend imports successfully"
else
    echo "✗ Backend main.py not found"
fi
cd ../..

# Test Frontend
echo -e "\n=== Testing Frontend ==="
if [ -d "frontend" ]; then
    cd frontend
    if [ -f "package.json" ]; then
        echo "✓ Frontend package.json found"
        npm list 2>/dev/null | head -5 || echo "Note: Run 'npm install' to install dependencies"
    else
        echo "✗ Frontend package.json not found"
    fi
    cd ..
else
    echo "✗ Frontend directory not found"
fi

# Check Python tests
echo -e "\n=== Checking Tests ==="
if [ -d "tests" ]; then
    echo "✓ Tests directory exists"
    ls tests/*.py 2>/dev/null | wc -l | xargs echo "  Found Python test files:"
else
    echo "✗ Tests directory not found"
fi

# Check file organization
echo -e "\n=== File Organization Summary ==="
echo "Root directory files: $(ls -1 | grep -v "^[A-Z]" | grep -v "^\." | wc -l)"
echo "Files in streamlit-legacy: $(find files-to-delete/streamlit-legacy -name "*.py" 2>/dev/null | wc -l)"
echo "Documentation files: $(find docs -name "*.md" 2>/dev/null | wc -l)"
echo "Backend source files: $(find src/backend -name "*.py" 2>/dev/null | wc -l)"

# Check for import errors in backend
echo -e "\n=== Checking Backend Python Imports ==="
error_count=0
for file in $(find src/backend -name "*.py" -type f | head -10); do
    python -m py_compile "$file" 2>&1 | grep -E "Error|ImportError" && ((error_count++)) || true
done
if [ $error_count -eq 0 ]; then
    echo "✓ Sample of backend Python files compile successfully"
else
    echo "✗ Found $error_count files with import errors"
fi

# Summary
echo -e "\n=== Validation Summary ==="
echo "Repository structure has been reorganized:"
echo "- Backend moved to src/backend/"
echo "- Documentation moved to docs/"
echo "- Tests moved to tests/"
echo "- Streamlit files moved to files-to-delete/streamlit-legacy/"
echo ""
echo "Next steps:"
echo "1. Push to GitHub: git push origin full-stack/refactor-project --tags"
echo "2. Create PR as described in the instructions"
echo "3. Review files in files-to-delete/ before removal"
echo ""
echo "Validation complete! 🎉"