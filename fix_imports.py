#!/usr/bin/env python3
"""Fix import paths after restructuring to src/backend/"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern to match imports starting with 'from backend.' or 'import backend.'
    patterns = [
        (r'from backend\.', 'from '),
        (r'import backend\.', 'import '),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Only write if content changed
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    """Fix all Python imports in src/backend/"""
    backend_dir = Path('/home/tarigelamin/Desktop/tradesense/src/backend')
    
    if not backend_dir.exists():
        print(f"Error: Backend directory not found at {backend_dir}")
        return
    
    fixed_count = 0
    total_count = 0
    
    # Find all Python files
    for py_file in backend_dir.rglob('*.py'):
        total_count += 1
        if fix_imports_in_file(py_file):
            fixed_count += 1
            print(f"✓ Fixed: {py_file.relative_to(backend_dir)}")
    
    print(f"\n📊 Summary: Fixed {fixed_count} out of {total_count} Python files")

if __name__ == "__main__":
    main()