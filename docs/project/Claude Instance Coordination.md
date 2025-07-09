# Claude Instance Coordination Guide

## Work Package Distribution

### Claude Instance 1: Security Lead
**Branch**: `feature/section-1a-security`
**Start**: Immediately
**Duration**: 2 days

#### Deliverables:
1. **Environment Configuration**
   - `.env.template` (complete template)
   - `.env.example` (with dummy values)
   - `backend/core/config.py` (refactored)
   - `scripts/generate_secrets.py`
   - `scripts/security_scanner.py`

2. **Authentication Updates**
   - `backend/api/v1/auth/` (all files updated)
   - Remove ALL hardcoded secrets
   - Implement proper JWT with env vars

3. **Security Documentation**
   - `docs/security_setup.md`
   - List of all changes made
   - Validation checklist

#### Do NOT Touch:
- Database models (Instance 3's responsibility)
- File movements (Instance 2's responsibility)
- Import statements (unless for security modules)

---

### Claude Instance 2: Organization Lead
**Branch**: `feature/section-1b-cleanup`
**Start**: Immediately (parallel with Instance 1)
**Duration**: 2 days

#### Deliverables:
1. **File Cleanup**
   - Delete all files in `attached_assets/`
   - Move root files to proper locations
   - Create new directory structure

2. **Import Updates**
   - Update ALL import statements
   - Create import mapping document
   - Test all imports work

3. **Dependency Management**
   - Consolidate all requirements files
   - Create `requirements/` directory structure
   - Resolve version conflicts

#### Do NOT Touch:
- Security configurations (Instance 1's responsibility)
- Database files (Instance 3's responsibility)
- Business logic (only move files, don't modify)

---

### Claude Instance 3: Database Lead
**Branch**: `feature/section-1d-database`
**Start**: After getting Instance 1's config updates
**Duration**: 2-3 days

#### Deliverables:
1. **Schema Documentation**
   - Complete current schema analysis
   - `docs/database_schema.md`
   - Entity relationship diagrams

2. **PostgreSQL Migration**
   - `migrations/001_initial_schema.sql`
   - `migrations/002_add_indexes.sql`
   - Multi-tenant schema design

3. **Migration Tools**
   - `scripts/migrate_to_postgresql.py`
   - `scripts/backup_sqlite.py`
   - Data validation scripts

#### Do NOT Touch:
- Application code (only database layer)
- File organization (Instance 2's responsibility)
- Non-database configurations

---

## Communication Protocol

### File Handoffs
```yaml
Instance 1 → Instance 3:
  - Updated config.py with database settings
  - Environment variable names for DB

Instance 2 → All:
  - New file locations mapping
  - Updated import paths document

Instance 3 → All:
  - New database model locations
  - Migration instructions
```

### Conflict Resolution
1. **Import Conflicts**: Instance 2 has final say
2. **Config Conflicts**: Instance 1 has final say
3. **Model Location**: Instance 2 decides, Instance 3 implements

---

## Integration Checklist

### After All Instances Complete:
- [ ] All branches can be merged without conflicts
- [ ] Application starts without errors
- [ ] All tests pass
- [ ] No hardcoded secrets remain
- [ ] File structure is clean
- [ ] Database migrations ready

### Integration Order:
1. Merge Instance 1 (security) first
2. Merge Instance 2 (cleanup) second
3. Merge Instance 3 (database) last

---

## Success Criteria

### Instance 1 Success:
- Security scanner shows 0 issues
- All secrets from environment
- Authentication working with new config

### Instance 2 Success:
- Zero files in attached_assets/
- Less than 10 files in root
- All imports working

### Instance 3 Success:
- Complete schema documented
- PostgreSQL migrations tested
- Multi-tenant structure ready
