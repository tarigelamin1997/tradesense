# Section 1: Foundation Implementation Plan

## Executive Summary
**Objective**: Establish a secure, organized, and maintainable foundation for the TradeSense SaaS transformation.  
**Duration**: 5-7 days  
**Priority**: CRITICAL - Must complete before any other sections  
**Risk Level**: High (security-critical changes, but low business disruption)

---

## Section 1A: Critical Security Fixes

### Overview
- **Objective**: Fix 15+ hardcoded secrets and authentication vulnerabilities
- **Duration**: 1-2 days
- **Priority**: URGENT - Security vulnerabilities must be fixed immediately
- **Files Affected**: ~10-15 configuration and authentication files

### Current Security Issues Identified
```python
# CRITICAL ISSUES FOUND:
1. backend/core/config.py - Hardcoded secrets
   - secret_key: str = "your-secret-key-here"
   - jwt_secret: str = "your-secret-key-here"
   - alpha_vantage_api_key: str = "demo"

2. Multiple authentication systems
   - /auth.py (Streamlit auth)
   - /backend/api/v1/auth/ (FastAPI auth)
   - Inconsistent security implementations

3. Debug mode enabled in production
   - debug: bool = True

4. No environment variable validation
```

### Implementation Steps

#### Step 1A.1: Create Secure Environment Configuration
**Create**: `.env.template`
```bash
# Security Configuration
SECRET_KEY=
JWT_SECRET_KEY=
DATABASE_URL=postgresql://user:password@localhost/tradesense

# API Keys
ALPHA_VANTAGE_API_KEY=
STRIPE_API_KEY=
STRIPE_WEBHOOK_SECRET=

# Email Configuration
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=

# Environment
ENVIRONMENT=development
DEBUG=False

# Security Settings
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:3000
SESSION_TIMEOUT_MINUTES=30
```

**Create**: `.env.development` (for local development)
```bash
# Copy from .env.template and fill with development values
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-change-in-production
DATABASE_URL=sqlite:///./tradesense_dev.db
ENVIRONMENT=development
DEBUG=True
```

#### Step 1A.2: Update Configuration Management
**Update**: `backend/core/config.py`
```python
import os
from typing import List, Optional
from pydantic import BaseSettings, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings with environment variable validation.
    
    Security: All sensitive values MUST come from environment variables.
    """
    
    # Application Settings
    app_name: str = "TradeSense"
    environment: str = os.getenv("ENVIRONMENT", "production")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Security Settings - REQUIRED
    secret_key: str = os.getenv("SECRET_KEY", "")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "")
    
    # API Keys
    alpha_vantage_api_key: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")
    stripe_api_key: Optional[str] = os.getenv("STRIPE_API_KEY")
    stripe_webhook_secret: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    # Email Settings
    smtp_host: Optional[str] = os.getenv("SMTP_HOST")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: Optional[str] = os.getenv("SMTP_USERNAME")
    smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD")
    
    # CORS Settings
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "").split(",")
    
    # Session Settings
    session_timeout_minutes: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    
    @validator("secret_key", "jwt_secret_key", "database_url")
    def validate_required_fields(cls, v, field):
        if not v:
            raise ValueError(f"{field.name} is required and must be set in environment variables")
        return v
    
    @validator("secret_key", "jwt_secret_key")
    def validate_not_default(cls, v, field):
        default_values = ["your-secret-key-here", "change-me", "dev-secret", ""]
        if v.lower() in default_values:
            raise ValueError(f"{field.name} contains default/insecure value. Please set a secure value.")
        return v
    
    @validator("debug")
    def validate_debug_in_production(cls, v, values):
        if values.get("environment") == "production" and v:
            raise ValueError("DEBUG cannot be True in production environment")
        return v
    
    class Config:
        case_sensitive = False
        env_file = ".env"

# Create settings instance
settings = Settings()

# Validate on import
if settings.environment == "production":
    if not settings.secret_key or len(settings.secret_key) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters in production")
    if not settings.jwt_secret_key or len(settings.jwt_secret_key) < 32:
        raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")
```

#### Step 1A.3: Create Secret Generation Script
**Create**: `scripts/generate_secrets.py`
```python
#!/usr/bin/env python3
"""
Generate secure secrets for TradeSense configuration.
Run this to create secure random secrets for your environment.
"""

import secrets
import string
import sys

def generate_secret_key(length=64):
    """Generate a secure secret key."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    # Remove problematic characters for environment variables
    alphabet = alphabet.replace('"', '').replace("'", '').replace('\\', '')
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def main():
    print("TradeSense Secret Generator")
    print("=" * 50)
    print("\nAdd these to your .env file:\n")
    
    # Generate secrets
    secret_key = generate_secret_key(64)
    jwt_secret = generate_secret_key(64)
    
    print(f"SECRET_KEY={secret_key}")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    
    print("\n" + "=" * 50)
    print("WARNING: Generate new secrets for each environment (dev, staging, prod)")
    print("Never commit these secrets to version control!")

if __name__ == "__main__":
    main()
```

#### Step 1A.4: Update Authentication Security
**Update**: `backend/api/v1/auth/service.py`
```python
import os
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

from backend.core.config import settings
from backend.core.security import verify_password, get_password_hash

class AuthService:
    """Secure authentication service with proper secret management."""
    
    def __init__(self):
        # Validate JWT secret on initialization
        if not settings.jwt_secret_key:
            raise ValueError("JWT_SECRET_KEY not configured")
        
        self.jwt_secret = settings.jwt_secret_key
        self.jwt_algorithm = settings.jwt_algorithm
        self.jwt_expiration = timedelta(minutes=settings.jwt_expiration_minutes)
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token with expiration."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + self.jwt_expiration
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.jwt_secret, 
            algorithm=self.jwt_algorithm
        )
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=[self.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
```

#### Step 1A.5: Remove All Hardcoded Secrets
**Script**: `scripts/security_scanner.py`
```python
#!/usr/bin/env python3
"""
Scan codebase for hardcoded secrets and security issues.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# Patterns to detect hardcoded secrets
SECRET_PATTERNS = [
    (r'(secret|key|password|token)\s*[:=]\s*["\'][\w\-]{8,}["\']', 'Hardcoded secret'),
    (r'["\']your-secret-key-here["\']', 'Default secret key'),
    (r'["\']demo["\']', 'Demo API key'),
    (r'debug\s*[:=]\s*True', 'Debug mode enabled'),
    (r'sqlite:///', 'SQLite database URL'),
]

EXCLUDE_DIRS = {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}
EXCLUDE_FILES = {'.env.template', 'security_scanner.py'}

def scan_file(filepath: Path) -> List[Tuple[int, str, str]]:
    """Scan a single file for security issues."""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                for pattern, issue_type in SECRET_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append((line_num, issue_type, line.strip()))
    except Exception as e:
        print(f"Error scanning {filepath}: {e}")
    
    return issues

def scan_directory(root_dir: str = '.') -> Dict[str, List]:
    """Scan directory tree for security issues."""
    all_issues = {}
    
    for root, dirs, files in os.walk(root_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if file.endswith('.py') and file not in EXCLUDE_FILES:
                filepath = Path(root) / file
                issues = scan_file(filepath)
                
                if issues:
                    all_issues[str(filepath)] = issues
    
    return all_issues

def main():
    print("TradeSense Security Scanner")
    print("=" * 50)
    
    issues = scan_directory()
    
    if not issues:
        print("\n✅ No security issues found!")
    else:
        print(f"\n❌ Found security issues in {len(issues)} files:\n")
        
        for filepath, file_issues in issues.items():
            print(f"\n{filepath}:")
            for line_num, issue_type, line in file_issues:
                print(f"  Line {line_num} - {issue_type}")
                print(f"    {line[:80]}...")

if __name__ == "__main__":
    main()
```

### Validation Checklist for 1A
- [ ] All hardcoded secrets removed from codebase
- [ ] Environment variables properly configured
- [ ] `.env.template` created with all required variables
- [ ] Security scanner returns no issues
- [ ] JWT implementation uses environment secrets
- [ ] Debug mode disabled for production
- [ ] Password hashing implemented correctly
- [ ] No default values in production config

---

## Section 1B: File Organization and Cleanup

### Overview
- **Objective**: Remove 67 duplicate files and organize 50+ scattered root files
- **Duration**: 1 day
- **Priority**: HIGH - Enables all subsequent work
- **Files Affected**: 117+ files to move/delete

### Implementation Steps

#### Step 1B.1: Remove Duplicate Files
**Script**: `scripts/remove_duplicates.py`
```python
#!/usr/bin/env python3
"""
Remove all duplicate files from attached_assets directory.
"""

import os
import shutil
from pathlib import Path

# List of duplicate files to remove (from analysis)
DUPLICATE_FILES = [
    "attached_assets/app_1750507825480.py",
    "attached_assets/auth_1750459073164.py",
    "attached_assets/requirements_1750469243176.txt",
    "attached_assets/analytics_1750507825479.py",
    # Add all 67 files here...
]

def remove_duplicates(dry_run=True):
    """Remove duplicate files with safety checks."""
    removed = []
    errors = []
    
    for filepath in DUPLICATE_FILES:
        path = Path(filepath)
        
        if path.exists():
            if dry_run:
                print(f"Would remove: {filepath}")
            else:
                try:
                    if path.is_file():
                        os.remove(path)
                    else:
                        shutil.rmtree(path)
                    removed.append(filepath)
                    print(f"✅ Removed: {filepath}")
                except Exception as e:
                    errors.append((filepath, str(e)))
                    print(f"❌ Error removing {filepath}: {e}")
        else:
            print(f"⚠️  Not found: {filepath}")
    
    return removed, errors

def main():
    print("TradeSense Duplicate File Remover")
    print("=" * 50)
    
    # First, do a dry run
    print("\nDRY RUN - No files will be deleted:")
    remove_duplicates(dry_run=True)
    
    response = input("\nProceed with deletion? (yes/no): ")
    
    if response.lower() == 'yes':
        print("\nRemoving duplicate files...")
        removed, errors = remove_duplicates(dry_run=False)
        
        print(f"\n✅ Removed {len(removed)} files")
        if errors:
            print(f"❌ {len(errors)} errors occurred")

if __name__ == "__main__":
    main()
```

#### Step 1B.2: Organize Root Files
**Script**: `scripts/organize_files.py`
```python
#!/usr/bin/env python3
"""
Organize scattered root files into proper directory structure.
"""

import os
import shutil
from pathlib import Path

# File organization mapping
FILE_MOVES = {
    # Authentication & User Management
    "auth.py": "backend/api/v1/auth/legacy_auth.py",
    "admin_dashboard.py": "backend/api/v1/admin/dashboard.py",
    "user_engagement.py": "backend/services/user_engagement_service.py",
    
    # Trading & Analytics
    "analytics.py": "backend/api/v1/analytics/legacy_analytics.py",
    "data_validation.py": "backend/core/validation/data_validator.py",
    "performance_monitoring.py": "backend/services/monitoring/performance_monitor.py",
    
    # Integrations
    "affiliate_integration.py": "backend/integrations/affiliate/service.py",
    "crypto_integration.py": "backend/integrations/crypto/service.py",
    "partner_management.py": "backend/api/v1/partners/service.py",
    
    # Infrastructure
    "bug_bounty_system.py": "backend/services/security/bug_bounty.py",
    "email_scheduler.py": "backend/services/notifications/email_scheduler.py",
    "health_monitoring.py": "backend/core/monitoring/health_check.py",
    "load_balancer.py": "backend/infrastructure/load_balancer.py",
    "scheduling_system.py": "backend/services/scheduling/system.py",
    
    # Social Features
    "social_features.py": "backend/api/v1/social/features.py",
}

def create_directories():
    """Create necessary directory structure."""
    directories = set()
    for new_path in FILE_MOVES.values():
        directory = os.path.dirname(new_path)
        directories.add(directory)
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def organize_files(dry_run=True):
    """Move files to organized structure."""
    moved = []
    errors = []
    
    for old_path, new_path in FILE_MOVES.items():
        if os.path.exists(old_path):
            if dry_run:
                print(f"Would move: {old_path} → {new_path}")
            else:
                try:
                    shutil.move(old_path, new_path)
                    moved.append((old_path, new_path))
                    print(f"✅ Moved: {old_path} → {new_path}")
                except Exception as e:
                    errors.append((old_path, str(e)))
                    print(f"❌ Error moving {old_path}: {e}")
    
    return moved, errors

def main():
    print("TradeSense File Organizer")
    print("=" * 50)
    
    # Create directory structure
    print("\nCreating directory structure...")
    create_directories()
    
    # Dry run first
    print("\nDRY RUN - No files will be moved:")
    organize_files(dry_run=True)
    
    response = input("\nProceed with file organization? (yes/no): ")
    
    if response.lower() == 'yes':
        print("\nOrganizing files...")
        moved, errors = organize_files(dry_run=False)
        
        print(f"\n✅ Moved {len(moved)} files")
        if errors:
            print(f"❌ {len(errors)} errors occurred")

if __name__ == "__main__":
    main()
```

#### Step 1B.3: Update Import Statements
**Script**: `scripts/update_imports.py`
```python
#!/usr/bin/env python3
"""
Update import statements after file reorganization.
"""

import os
import re
from pathlib import Path

# Import mappings
IMPORT_UPDATES = {
    r'from auth import': 'from backend.api.v1.auth.legacy_auth import',
    r'import auth': 'import backend.api.v1.auth.legacy_auth as auth',
    r'from analytics import': 'from backend.api.v1.analytics.legacy_analytics import',
    r'import analytics': 'import backend.api.v1.analytics.legacy_analytics as analytics',
    # Add more mappings...
}

def update_imports_in_file(filepath: Path):
    """Update imports in a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for old_import, new_import in IMPORT_UPDATES.items():
            content = re.sub(old_import, new_import, content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"Error updating {filepath}: {e}")
        return False
    
    return False

def update_all_imports():
    """Update imports in all Python files."""
    updated_files = []
    
    for root, dirs, files in os.walk('.'):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'venv'}]
        
        for file in files:
            if file.endswith('.py'):
                filepath = Path(root) / file
                if update_imports_in_file(filepath):
                    updated_files.append(str(filepath))
                    print(f"✅ Updated imports in: {filepath}")
    
    return updated_files

def main():
    print("TradeSense Import Updater")
    print("=" * 50)
    
    print("\nUpdating import statements...")
    updated = update_all_imports()
    
    print(f"\n✅ Updated {len(updated)} files")

if __name__ == "__main__":
    main()
```

### Validation Checklist for 1B
- [ ] All 67 duplicate files removed
- [ ] Attached_assets directory cleaned
- [ ] Root directory files < 10 (only essential files)
- [ ] Proper directory structure created
- [ ] All imports updated and working
- [ ] No broken imports in application
- [ ] Git status shows expected changes

---

## Section 1C: Dependency Management

### Overview
- **Objective**: Consolidate requirements, remove duplicates, pin versions
- **Duration**: 1 day
- **Priority**: HIGH - Prevents version conflicts
- **Files Affected**: 5+ requirements files

### Implementation Steps

#### Step 1C.1: Consolidate Requirements Files
**Create**: `requirements/base.txt`
```txt
# Core Framework
fastapi==0.104.1
streamlit==1.28.2
uvicorn[standard]==0.24.0

# Database
sqlalchemy==2.0.23
alembic==1.12.1
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Authentication & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pydantic[email]==2.5.0

# Data Processing
pandas==2.1.3
numpy==1.26.2
openpyxl==3.1.2
xlrd==2.0.1

# Visualization
plotly==5.18.0
matplotlib==3.8.2
seaborn==0.13.0

# API & Integration
httpx==0.25.2
aiohttp==3.9.1
requests==2.31.0

# Utilities
python-dotenv==1.0.0
pyyaml==6.0.1
```

**Create**: `requirements/dev.txt`
```txt
# Include base requirements
-r base.txt

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Development Tools
black==23.11.0
flake8==6.1.0
mypy==1.7.1
pre-commit==3.5.0

# Documentation
mkdocs==1.5.3
mkdocs-material==9.4.14
```

**Create**: `requirements/prod.txt`
```txt
# Include base requirements
-r base.txt

# Production-specific
gunicorn==21.2.0
redis==5.0.1
celery==5.3.4

# Monitoring
sentry-sdk==1.38.0
prometheus-client==0.19.0
```

#### Step 1C.2: Remove Duplicate Dependencies
**Script**: `scripts/analyze_dependencies.py`
```python
#!/usr/bin/env python3
"""
Analyze and fix dependency issues.
"""

import subprocess
import sys
from collections import defaultdict

def get_installed_packages():
    """Get list of installed packages with versions."""
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'list', '--format=freeze'],
        capture_output=True,
        text=True
    )
    
    packages = {}
    for line in result.stdout.strip().split('\n'):
        if '==' in line:
            name, version = line.split('==')
            packages[name.lower()] = version
    
    return packages

def analyze_requirements_files():
    """Analyze all requirements files for issues."""
    files = [
        'requirements.txt',
        'dev-requirements.txt',
        'requirements/base.txt',
        'requirements/dev.txt',
        'requirements/prod.txt'
    ]
    
    all_deps = defaultdict(list)
    
    for file in files:
        try:
            with open(file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('-r'):
                        if '==' in line:
                            pkg, version = line.split('==')
                            all_deps[pkg.lower()].append((file, version))
                        elif '>=' in line or '<=' in line:
                            # Handle other version specifiers
                            parts = re.split(r'[><=]+', line)
                            if parts:
                                all_deps[parts[0].lower()].append((file, line))
        except FileNotFoundError:
            print(f"File not found: {file}")
    
    # Find duplicates and conflicts
    duplicates = {}
    conflicts = {}
    
    for pkg, occurrences in all_deps.items():
        if len(occurrences) > 1:
            versions = set(v for _, v in occurrences)
            if len(versions) > 1:
                conflicts[pkg] = occurrences
            else:
                duplicates[pkg] = occurrences
    
    return duplicates, conflicts

def main():
    print("TradeSense Dependency Analyzer")
    print("=" * 50)
    
    # Analyze requirements files
    print("\nAnalyzing requirements files...")
    duplicates, conflicts = analyze_requirements_files()
    
    if conflicts:
        print("\n❌ Version conflicts found:")
        for pkg, occurrences in conflicts.items():
            print(f"\n{pkg}:")
            for file, version in occurrences:
                print(f"  - {file}: {version}")
    
    if duplicates:
        print("\n⚠️  Duplicate packages found:")
        for pkg, occurrences in duplicates.items():
            print(f"\n{pkg}:")
            for file, version in occurrences:
                print(f"  - {file}: {version}")
    
    if not conflicts and not duplicates:
        print("\n✅ No dependency issues found!")

if __name__ == "__main__":
    main()
```

### Validation Checklist for 1C
- [ ] Single source of truth for dependencies
- [ ] All packages have pinned versions
- [ ] No duplicate packages
- [ ] No version conflicts
- [ ] Development dependencies separated
- [ ] Production optimizations included
- [ ] pip install runs without errors

---

## Section 1D: Database Migration Preparation

### Overview
- **Objective**: Prepare for PostgreSQL migration from SQLite
- **Duration**: 1-2 days
- **Priority**: HIGH - Foundation for multi-tenancy
- **Risk**: MEDIUM - Requires careful data migration planning

### Implementation Steps

#### Step 1D.1: Document Current Schema
**Script**: `scripts/extract_schema.py`
```python
#!/usr/bin/env python3
"""
Extract current SQLite schema for migration planning.
"""

import sqlite3
import json
from pathlib import Path

def extract_schema(db_path: str):
    """Extract complete schema from SQLite database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    schema = {
        'tables': {},
        'indexes': [],
        'triggers': []
    }
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for (table_name,) in tables:
        if table_name.startswith('sqlite_'):
            continue
            
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        # Get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table_name});")
        foreign_keys = cursor.fetchall()
        
        schema['tables'][table_name] = {
            'columns': [
                {
                    'name': col[1],
                    'type': col[2],
                    'not_null': bool(col[3]),
                    'default': col[4],
                    'primary_key': bool(col[5])
                }
                for col in columns
            ],
            'foreign_keys': [
                {
                    'column': fk[3],
                    'references_table': fk[2],
                    'references_column': fk[4]
                }
                for fk in foreign_keys
            ]
        }
    
    # Get indexes
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index';")
    indexes = cursor.fetchall()
    schema['indexes'] = [{'name': idx[0], 'sql': idx[1]} for idx in indexes if idx[1]]
    
    conn.close()
    return schema

def main():
    print("TradeSense Schema Extractor")
    print("=" * 50)
    
    db_path = "tradesense.db"  # Adjust path as needed
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    print(f"\nExtracting schema from: {db_path}")
    schema = extract_schema(db_path)
    
    # Save schema
    with open('database_schema.json', 'w') as f:
        json.dump(schema, f, indent=2)
    
    print(f"\n✅ Schema extracted to database_schema.json")
    print(f"   Tables: {len(schema['tables'])}")
    print(f"   Indexes: {len(schema['indexes'])}")

if __name__ == "__main__":
    main()
```

#### Step 1D.2: Create PostgreSQL Migration Scripts
**Create**: `migrations/001_initial_postgresql_schema.sql`
```sql
-- TradeSense PostgreSQL Schema
-- Generated from SQLite schema analysis

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS trading;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Users table (multi-tenant ready)
CREATE TABLE auth.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    INDEX idx_users_email (email),
    INDEX idx_users_username (username),
    INDEX idx_users_active (is_active)
);

-- Trading accounts
CREATE TABLE trading.accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    broker VARCHAR(100),
    account_type VARCHAR(50),
    currency VARCHAR(3) DEFAULT 'USD',
    initial_balance DECIMAL(15,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_accounts_user (user_id)
);

-- Trades table
CREATE TABLE trading.trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    account_id UUID REFERENCES trading.accounts(id),
    symbol VARCHAR(20) NOT NULL,
    entry_price DECIMAL(15,6) NOT NULL,
    exit_price DECIMAL(15,6),
    quantity DECIMAL(15,6) NOT NULL,
    trade_type VARCHAR(10) NOT NULL CHECK (trade_type IN ('BUY', 'SELL', 'LONG', 'SHORT')),
    entry_time TIMESTAMP WITH TIME ZONE NOT NULL,
    exit_time TIMESTAMP WITH TIME ZONE,
    confidence_score INTEGER CHECK (confidence_score BETWEEN 1 AND 10),
    notes TEXT,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_trades_user (user_id),
    INDEX idx_trades_symbol (symbol),
    INDEX idx_trades_entry_time (entry_time DESC)
);

-- Create update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trades_updated_at BEFORE UPDATE ON trading.trades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

#### Step 1D.3: Create Migration Tool
**Create**: `scripts/migrate_to_postgresql.py`
```python
#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL.
"""

import sqlite3
import asyncio
import asyncpg
from datetime import datetime
import json

async def migrate_data():
    """Migrate data from SQLite to PostgreSQL."""
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect('tradesense.db')
    sqlite_conn.row_factory = sqlite3.Row
    
    # Connect to PostgreSQL
    pg_conn = await asyncpg.connect(
        'postgresql://user:password@localhost/tradesense'
    )
    
    try:
        # Migrate users
        print("Migrating users...")
        users = sqlite_conn.execute("SELECT * FROM users").fetchall()
        
        for user in users:
            await pg_conn.execute("""
                INSERT INTO auth.users (
                    email, username, password_hash, first_name, last_name,
                    is_active, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (email) DO NOTHING
            """, 
                user['email'], user['username'], user['password_hash'],
                user['first_name'], user['last_name'], user['is_active'],
                datetime.fromisoformat(user['created_at'])
            )
        
        print(f"✅ Migrated {len(users)} users")
        
        # Migrate trades
        print("Migrating trades...")
        # Similar migration for trades...
        
    finally:
        sqlite_conn.close()
        await pg_conn.close()

def main():
    print("TradeSense Database Migration")
    print("=" * 50)
    
    print("\n⚠️  This will migrate data from SQLite to PostgreSQL")
    response = input("Continue? (yes/no): ")
    
    if response.lower() == 'yes':
        asyncio.run(migrate_data())

if __name__ == "__main__":
    main()
```

### Validation Checklist for 1D
- [ ] Current schema fully documented
- [ ] PostgreSQL schema created
- [ ] Migration scripts tested
- [ ] Data integrity verified
- [ ] Rollback plan documented
- [ ] Performance benchmarks established

---

## Overall Section 1 Validation

### Pre-Implementation Checklist
- [ ] Full backup of current codebase
- [ ] Development environment set up
- [ ] Team briefed on changes
- [ ] Rollback procedures documented

### Post-Implementation Validation
- [ ] All security vulnerabilities fixed
- [ ] No hardcoded secrets in codebase
- [ ] File structure organized and clean
- [ ] Dependencies consolidated and conflict-free
- [ ] Database migration plan ready
- [ ] All tests passing
- [ ] Application runs without errors

### Success Metrics
- **Security Issues**: 15+ → 0
- **Duplicate Files**: 67 → 0
- **Root Level Files**: 50+ → <10
- **Dependency Conflicts**: Multiple → 0
- **Test Coverage**: Baseline established

---

## Implementation Schedule

### Day 1: Security Fixes (1A)
- Morning: Environment setup and secret generation
- Afternoon: Update all configuration files
- Evening: Security validation and testing

### Day 2: File Organization (1B)
- Morning: Remove duplicates
- Afternoon: Organize files into proper structure
- Evening: Update imports and validate

### Day 3: Dependencies (1C)
- Morning: Consolidate requirements
- Afternoon: Resolve conflicts
- Evening: Test installation process

### Day 4-5: Database Preparation (1D)
- Day 4: Schema extraction and documentation
- Day 5: Migration script creation and testing

### Day 6-7: Integration Testing
- Full system testing
- Performance benchmarking
- Documentation updates

---

## Risk Mitigation

### Backup Strategy
```bash
# Before starting implementation
git checkout -b backup/pre-section-1
git push origin backup/pre-section-1

# Create feature branch
git checkout -b feature/section-1-foundation
```

### Rollback Procedures
```bash
# If issues arise, rollback to backup
git checkout backup/pre-section-1

# Or revert specific changes
git revert <commit-hash>
```

### Communication Plan
- Daily status updates to stakeholders
- Immediate notification of blocking issues
- End-of-section review meeting

---

## Next Steps

After completing Section 1:
1. Run comprehensive test suite
2. Document all changes
3. Create pull request for review
4. Plan Section 2 implementation
5. Update progress tracker

This foundation work is critical for the success of the entire transformation. Take time to do it right!
