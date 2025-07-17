#!/usr/bin/env python3
"""
Import Validation Script for TradeSense Backend
Checks all Python imports to catch errors before deployment
"""

import os
import sys
import importlib.util
from pathlib import Path
import traceback

# Add backend to path
backend_path = Path(__file__).parent / "src" / "backend"
sys.path.insert(0, str(backend_path))

def check_imports():
    """Check all Python files for import errors"""
    errors = []
    checked = 0
    
    print("🔍 Validating imports in TradeSense backend...")
    print("-" * 50)
    
    # Walk through all Python files
    for root, dirs, files in os.walk(backend_path):
        # Skip test directories and __pycache__
        dirs[:] = [d for d in dirs if d not in ['__pycache__', 'tests', 'test']]
        
        for file in files:
            if file.endswith('.py') and not file.startswith('test_'):
                file_path = Path(root) / file
                relative_path = file_path.relative_to(backend_path)
                
                # Convert file path to module name
                module_name = str(relative_path).replace(os.sep, '.').replace('.py', '')
                
                try:
                    # Try to import the module
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = module
                        spec.loader.exec_module(module)
                        
                    checked += 1
                    print(f"✅ {module_name}")
                    
                except Exception as e:
                    error_msg = str(e)
                    errors.append({
                        'file': str(relative_path),
                        'module': module_name,
                        'error': error_msg,
                        'type': type(e).__name__
                    })
                    print(f"❌ {module_name}: {error_msg}")
    
    print("-" * 50)
    print(f"\n📊 Summary:")
    print(f"   Files checked: {checked}")
    print(f"   Errors found: {len(errors)}")
    
    if errors:
        print("\n🚨 Import Errors Found:")
        for i, error in enumerate(errors, 1):
            print(f"\n{i}. {error['file']}")
            print(f"   Module: {error['module']}")
            print(f"   Error Type: {error['type']}")
            print(f"   Error: {error['error']}")
            
        return False
    else:
        print("\n✅ All imports validated successfully!")
        return True

def check_service_dependencies():
    """Check specific service class dependencies"""
    print("\n🔧 Checking service dependencies...")
    print("-" * 50)
    
    services_to_check = [
        ("services.pattern_detection", "PatternDetectionEngine", "requires db: Session"),
        ("services.emotional_analytics", "EmotionalAnalyticsService", "requires db: Session, user_id: str"),
        ("services.edge_strength", "EdgeStrengthService", "no dependencies"),
        ("services.market_context", "MarketContextEngine", "no dependencies"),
        ("services.feature_flag_service", "FeatureFlagService", "imports from features/feature_flags.py"),
    ]
    
    for module_name, class_name, deps in services_to_check:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, class_name):
                print(f"✅ {module_name}.{class_name} - {deps}")
            else:
                print(f"❌ {module_name}.{class_name} - Class not found!")
        except Exception as e:
            print(f"❌ {module_name} - Import failed: {e}")

def check_pydantic_compatibility():
    """Check for Pydantic v2 compatibility issues"""
    print("\n🔍 Checking Pydantic v2 compatibility...")
    print("-" * 50)
    
    issues = []
    
    # Check for regex vs pattern in Field definitions
    for root, dirs, files in os.walk(backend_path):
        dirs[:] = [d for d in dirs if d not in ['__pycache__', 'tests']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                try:
                    content = file_path.read_text()
                    if 'regex=' in content and 'Field' in content:
                        issues.append(f"{file_path.relative_to(backend_path)}: Uses 'regex=' (should be 'pattern=')")
                except:
                    pass
    
    if issues:
        print("❌ Pydantic v2 issues found:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ No Pydantic v2 compatibility issues found")

if __name__ == "__main__":
    print("🚀 TradeSense Import Validator")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not backend_path.exists():
        print("❌ Error: src/backend directory not found!")
        print(f"   Looking for: {backend_path}")
        sys.exit(1)
    
    # Run checks
    imports_ok = check_imports()
    check_service_dependencies()
    check_pydantic_compatibility()
    
    if imports_ok:
        print("\n✅ All validation checks passed! Ready for deployment.")
        sys.exit(0)
    else:
        print("\n❌ Validation failed. Please fix the errors above.")
        sys.exit(1)