# TradeSense Project Structure - Post Reorganization

```
tradesense/
│
├── 📁 src/                           # Source code
│   └── backend/                      # FastAPI backend application
│       ├── alembic/                  # Database migrations
│       ├── analytics/                # Analytics modules
│       ├── api/                      # API endpoints
│       │   ├── deps.py              # Dependencies
│       │   ├── health/              # Health check endpoints
│       │   ├── v1/                  # API v1 endpoints
│       │   │   ├── accounts/
│       │   │   ├── analytics/
│       │   │   ├── auth/
│       │   │   ├── critique/
│       │   │   ├── emotions/
│       │   │   ├── features/
│       │   │   ├── journal/
│       │   │   ├── leaderboard/
│       │   │   ├── market_data/
│       │   │   ├── mental_map/
│       │   │   ├── milestones/
│       │   │   ├── notes/
│       │   │   ├── patterns/
│       │   │   ├── playbooks/
│       │   │   ├── portfolio/
│       │   │   ├── reflections/
│       │   │   ├── reviews/
│       │   │   ├── strategies/
│       │   │   ├── strategy_lab/
│       │   │   ├── tags/
│       │   │   ├── trades/
│       │   │   ├── uploads/
│       │   │   └── users/
│       │   └── websocket/           # WebSocket endpoints
│       ├── core/                    # Core functionality
│       │   ├── config.py
│       │   ├── security.py
│       │   ├── middleware.py
│       │   └── db/
│       ├── models/                  # Database models
│       ├── services/                # Business logic services
│       ├── tests/                   # Backend tests
│       └── main.py                  # Application entry point
│
├── 📁 frontend/                      # React/Next.js frontend
│   ├── src/
│   │   ├── components/              # React components
│   │   ├── pages/                   # Next.js pages
│   │   ├── services/                # API client services
│   │   ├── stores/                  # State management
│   │   ├── hooks/                   # Custom React hooks
│   │   ├── lib/                     # Utility libraries
│   │   ├── styles/                  # CSS/styling
│   │   └── types/                   # TypeScript types
│   ├── public/                      # Static assets
│   └── package.json
│
├── 📁 docs/                          # Documentation
│   ├── architecture/                # Architecture documentation
│   │   └── COMPLETE_SAAS_ARCHITECTURE_GUIDE/
│   │       ├── ARCHITECTURE_STRATEGY.md
│   │       ├── MASTER_IMPLEMENTATION_ROADMAP/
│   │       └── SECTION_*.md files
│   └── project/                     # Project documentation
│       ├── FILE_INVENTORY.md        # Complete file movement log
│       ├── MIGRATION_HISTORY.md     # Streamlit to full-stack journey
│       ├── PROTECTED_FILES.md       # Protected files list
│       ├── project-rules.md         # Project rules
│       └── README.md                # Original README
│
├── 📁 tests/                         # Test files
│   ├── test_api.py
│   ├── test_api_comprehensive.py
│   ├── test_api_detailed.py
│   ├── test_auth_login.py
│   ├── test_auth_minimal.py
│   ├── test_endpoint.py
│   ├── test_fpdf.py
│   └── test_public.py
│
├── 📁 scripts/                       # Utility scripts
│   ├── git-workflow.sh              # Git workflow automation
│   ├── setup-git-workflow.sh        # Git setup script
│   ├── setup_dev.py                 # Development setup
│   ├── start_dev.py                 # Start development
│   └── sync-with-main-and-tag.sh   # Sync script
│
├── 📁 data/                          # Data files
│   ├── samples/                     # Sample data
│   │   └── futures_sample.csv
│   ├── tradesense.db                # Main database
│   ├── test_tradesense.db           # Test database
│   ├── tradesense.db-shm            # SQLite shared memory
│   └── tradesense.db-wal            # SQLite write-ahead log
│
├── 📁 config/                        # Configuration files
│   ├── alembic.ini                  # Alembic configuration
│   ├── .replit                      # Replit configuration
│   └── replit.nix                   # Replit Nix config
│
├── 📁 backups/                       # Backup archives
│   ├── tradesense_backup_*.tar.gz   # Full project backups
│   ├── backend_backup.tar.gz        # Backend backup
│   ├── frontend_backup.tar.gz       # Frontend backup
│   ├── databases_backup.tar.gz      # Database backup
│   ├── streamlit_legacy_backup.tar.gz # Streamlit backup
│   └── assets_backup.tar.gz         # Assets backup
│
├── 📁 files-to-delete/               # Legacy files for review
│   ├── streamlit-legacy/            # 61 Streamlit files
│   │   ├── app.py                   # Main Streamlit app
│   │   ├── pages/                   # Streamlit pages
│   │   ├── core/                    # Core components
│   │   ├── visuals/                 # Visualization components
│   │   └── [50+ other .py files]
│   ├── old-scripts/                 # Deprecated scripts
│   │   └── [Various old scripts]
│   └── needs-review/                # Files needing review
│       ├── api_endpoints.py         # Flask API
│       └── payment.py               # Payment system
│
├── 📁 [Legacy Directories - To Review]
│   ├── analytics/                   # Old analytics (empty?)
│   ├── app/                         # Old app structure
│   ├── attached_assets/             # Large assets (18MB)
│   ├── connectors/                  # Data connectors
│   ├── core/                        # Old core (empty after move)
│   ├── data_import/                 # Data import tools
│   ├── documentation/               # Old documentation
│   ├── infra/                       # Infrastructure files
│   ├── logs/                        # Log files
│   ├── metrics/                     # Metrics tracking
│   └── visuals/                     # Old visuals (empty after move)
│
├── 📄 Root Files (Essential Only)
│   ├── .env.example                 # Environment template
│   ├── .gitignore                   # Git ignore rules
│   ├── .python-version              # Python version
│   ├── LICENSE                      # MIT License
│   ├── requirements.txt             # Python dependencies
│   ├── core-requirements.txt        # Core dependencies
│   ├── dev-requirements.txt         # Dev dependencies
│   ├── runtime.txt                  # Runtime specification
│   ├── package.json                 # Node.js dependencies
│   ├── package-lock.json            # Node.js lock file
│   ├── FINAL_REVIEW.md              # Restructuring summary
│   ├── PR_DESCRIPTION.md            # PR description
│   └── validate_restructure.sh      # Validation script
│
└── 📁 .git/                          # Git repository
    └── [Git internal files]
```

## Summary Statistics

- **Total Python files in backend**: 199 files
- **Streamlit legacy files**: 61 files (staged for deletion)
- **Documentation files**: 34 markdown files
- **Test files**: 27 test files (8 in root tests/ + 19 in backend)
- **Root directory**: Reduced from 100+ files to 13 essential files

## Key Achievements

1. **Clear Separation**: Backend, frontend, and documentation are clearly separated
2. **Clean Root**: Only essential configuration files remain in root
3. **Preserved History**: All files moved, not deleted - full git history preserved
4. **Comprehensive Documentation**: Complete tracking of all movements
5. **Ready for Production**: Structure follows modern full-stack best practices

## Next Steps

1. Review and remove legacy directories (analytics/, app/, etc.)
2. Delete files in `files-to-delete/` after team approval
3. Update CI/CD pipelines to match new structure
4. Update deployment scripts for new paths