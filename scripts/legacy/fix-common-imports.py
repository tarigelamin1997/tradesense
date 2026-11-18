#!/usr/bin/env python3
"""
Script to find and suggest fixes for common import issues
"""

import os
import re
from pathlib import Path

backend_path = Path("src/backend")

print("🔍 Scanning for common import issues...")
print("=" * 50)

issues_found = []

# Pattern 1: Check for imports from api.v1.users.schemas
for root, dirs, files in os.walk(backend_path):
    for file in files:
        if file.endswith('.py'):
            file_path = Path(root) / file
            try:
                content = file_path.read_text()
                
                # Check for wrong User imports
                if 'from api.v1.users.schemas import User' in content:
                    issues_found.append({
                        'file': str(file_path),
                        'issue': 'Imports User from wrong location',
                        'fix': 'Change to: from models.user import User'
                    })
                
                # Check for wrong auth imports
                if 'from core.auth import' in content:
                    issues_found.append({
                        'file': str(file_path),
                        'issue': 'Imports from core.auth (doesn\'t exist)',
                        'fix': 'Change to: from api.deps import'
                    })
                
                # Check for app. prefix imports
                if re.search(r'from app\.', content):
                    issues_found.append({
                        'file': str(file_path),
                        'issue': 'Uses app. prefix in imports',
                        'fix': 'Remove app. prefix from imports'
                    })
                
                # Check for src.backend. prefix imports
                if re.search(r'from src\.backend\.', content):
                    issues_found.append({
                        'file': str(file_path),
                        'issue': 'Uses src.backend. prefix in imports',
                        'fix': 'Remove src.backend. prefix from imports'
                    })
                    
            except Exception as e:
                pass

if issues_found:
    print(f"\n❌ Found {len(issues_found)} potential import issues:\n")
    for i, issue in enumerate(issues_found, 1):
        print(f"{i}. {issue['file']}")
        print(f"   Issue: {issue['issue']}")
        print(f"   Fix: {issue['fix']}")
        print()
else:
    print("\n✅ No common import issues found!")

print("\n💡 Other things to check in Railway logs:")
print("- ModuleNotFoundError: Missing dependencies in requirements.txt")
print("- ImportError with specific function/class names")
print("- AttributeError when accessing imported items")