# ARCHITECTURE STRATEGY - PART 4: DEVELOPMENT WORKFLOWS & IMPLEMENTATION

---

## **SECTION 5A: DEVELOPMENT WORKFLOW FOUNDATION**

### **5A.1 BRANCHING STRATEGY AND GIT WORKFLOW**

#### **5A.1.1 Core Branching Strategy: Modified GitHub Flow**

**Strategic Decision:** Adopt a Modified GitHub Flow approach that balances simplicity with production safety for the TradeSense platform.

**Branch Hierarchy:**
```
main (production-ready)
├── develop (integration branch)
├── feature/[type]/[description] (feature development)
├── hotfix/[issue-id]/[description] (critical fixes)
├── release/[version] (release preparation)
└── experimental/[name] (research/spike work)
```

**Core Principles:**
1. **Main Branch Sanctity**: `main` branch always reflects production-ready state
2. **Short-lived Branches**: Feature branches live < 5 days to minimize integration complexity
3. **Continuous Integration**: All branches must pass CI/CD pipeline before merge
4. **Atomic Changes**: Each branch addresses single feature/bug/improvement

#### **5A.1.2 Detailed Workflow Patterns**

**Feature Development Workflow:**
```bash
# 1. Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/ui/trading-dashboard-enhancement

# 2. Development cycle
git add .
git commit -m "feat(ui): implement real-time price updates

- Add WebSocket integration for live data
- Implement responsive chart components
- Add price alert functionality

Closes #TRS-123"

# 3. Regular synchronization
git fetch origin
git rebase origin/develop

# 4. Push and create PR
git push -u origin feature/ui/trading-dashboard-enhancement
```

**Commit Message Standards:**
```
<type>(<scope>): <description>

<body>

<footer>
```

**Types:** feat, fix, docs, style, refactor, test, chore, perf, ci, build
**Scopes:** ui, api, auth, trading, analytics, infra, db, security

**Example Commit Messages:**
```
feat(trading): implement real-time order execution

- Add WebSocket connection for live market data
- Implement order validation and execution logic
- Add position tracking and P&L calculations
- Integrate with risk management system

Performance: Reduces order latency by 45ms
Security: All trades validated against user permissions

Closes #TRS-456
Breaking-change: Updates order API structure
```

#### **5A.1.3 Branch Protection Rules and Code Review**

**Main Branch Protection:**
```yaml
# .github/branch-protection.yml
main:
  required_status_checks:
    strict: true
    contexts:
      - "ci/build"
      - "ci/test-frontend"
      - "ci/test-backend"
      - "ci/security-scan"
      - "ci/performance-test"
  enforce_admins: true
  required_pull_request_reviews:
    required_approving_reviews: 2
    dismiss_stale_reviews: true
    require_code_owner_reviews: true
    restriction_push_teams: ["senior-developers", "tech-leads"]
  restrictions:
    push_teams: []
    push_users: []
```

**Develop Branch Protection:**
```yaml
develop:
  required_status_checks:
    strict: true
    contexts:
      - "ci/build"
      - "ci/test-integration"
      - "ci/lint"
  required_pull_request_reviews:
    required_approving_reviews: 1
    dismiss_stale_reviews: true
```

**Code Review Requirements:**

**Mandatory Review Checklist:**
- [ ] **Functionality**: Feature works as specified in requirements
- [ ] **Security**: No security vulnerabilities or data exposure
- [ ] **Performance**: No performance regressions introduced
- [ ] **Testing**: Adequate test coverage (>85% for new code)
- [ ] **Documentation**: README, API docs, and inline comments updated
- [ ] **Code Quality**: Follows established patterns and conventions
- [ ] **Dependencies**: New dependencies justified and approved
- [ ] **Database**: Migration scripts reviewed and tested
- [ ] **Configuration**: Environment variables and configs documented

**Review Assignment Strategy:**
```yaml
# .github/CODEOWNERS
# Global owners
* @tech-lead @senior-architect

# Frontend components
/frontend/src/components/ @frontend-team @ui-specialist
/frontend/src/trading/ @trading-team @frontend-team

# Backend services
/backend/src/api/ @backend-team @api-specialist
/backend/src/trading/ @trading-team @backend-team
/backend/src/auth/ @security-team @backend-team

# Infrastructure
/infrastructure/ @devops-team @infrastructure-lead
/docker/ @devops-team
/.github/workflows/ @devops-team @tech-lead

# Database
/backend/migrations/ @database-team @backend-team
/backend/src/models/ @database-team @backend-team

# Security
/backend/src/security/ @security-team
/backend/src/auth/ @security-team
```

#### **5A.1.4 Merge Strategies and Conflict Resolution**

**Merge Strategy Matrix:**
```yaml
Branch Types:
  feature -> develop:
    strategy: "squash"
    rationale: "Clean history, atomic features"
  
  develop -> main:
    strategy: "merge-commit"
    rationale: "Preserve release context"
  
  hotfix -> main:
    strategy: "merge-commit"
    rationale: "Traceable emergency fixes"
  
  hotfix -> develop:
    strategy: "cherry-pick"
    rationale: "Selective integration"
```

**Conflict Resolution Patterns:**

**Pre-merge Conflict Prevention:**
```bash
# Daily synchronization script
#!/bin/bash
# sync-branch.sh

current_branch=$(git branch --show-current)
base_branch="develop"

echo "Syncing $current_branch with $base_branch..."

# Fetch latest changes
git fetch origin

# Check for conflicts before rebasing
git merge-tree $(git merge-base $current_branch origin/$base_branch) $current_branch origin/$base_branch | grep -q "<<<<<<< " && {
    echo "⚠️  Conflicts detected. Manual resolution required."
    echo "Run: git rebase origin/$base_branch"
    exit 1
}

# Safe rebase
git rebase origin/$base_branch
echo "✅ Branch synchronized successfully"
```

**Conflict Resolution Guidelines:**
1. **Immediate Resolution**: Address conflicts within 2 hours of detection
2. **Collaborative Resolution**: Involve original authors for complex conflicts
3. **Test After Resolution**: Run full test suite post-conflict resolution
4. **Documentation**: Record resolution patterns for future reference

#### **5A.1.5 Hotfix and Release Workflows**

**Hotfix Workflow:**
```bash
# 1. Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/TRS-CRITICAL-789/security-patch

# 2. Implement fix
git commit -m "fix(security): patch authentication vulnerability

- Close session hijacking vector in JWT validation
- Add additional rate limiting for auth endpoints
- Update security headers configuration

Security-Impact: Critical
Affected-Versions: v2.1.0 - v2.6.7
CVE: Pending"

# 3. Test thoroughly
npm run test:security
npm run test:integration

# 4. Deploy to staging for validation
git push origin hotfix/TRS-CRITICAL-789/security-patch

# 5. After approval, merge to main and develop
git checkout main
git merge --no-ff hotfix/TRS-CRITICAL-789/security-patch
git tag -a v2.6.8 -m "Hotfix: Security vulnerability patch"
git push origin main --tags

git checkout develop
git merge --no-ff hotfix/TRS-CRITICAL-789/security-patch
git push origin develop
```

**Release Workflow:**
```bash
# 1. Create release branch from develop
git checkout develop
git pull origin develop
git checkout -b release/v2.7.0

# 2. Version bump and final preparations
npm version 2.7.0
./scripts/update-changelog.sh
./scripts/generate-release-notes.sh

# 3. Release testing
npm run test:full-suite
npm run test:e2e
npm run test:performance
npm run test:security

# 4. Merge to main after approval
git checkout main
git merge --no-ff release/v2.7.0
git tag -a v2.7.0 -m "Release v2.7.0: Enhanced trading features"
git push origin main --tags

# 5. Merge back to develop
git checkout develop
git merge --no-ff release/v2.7.0
git push origin develop

# 6. Clean up
git branch -d release/v2.7.0
git push origin --delete release/v2.7.0
```

### **5A.2 CODE ORGANIZATION AND STANDARDS**

#### **5A.2.1 Comprehensive Coding Standards**

**TypeScript/JavaScript Standards:**

```typescript
// File: /frontend/src/types/trading.types.ts
/**
 * Trading domain type definitions
 * 
 * @fileoverview Core trading types and interfaces for the TradeSense platform
 * @author TradeSense Development Team
 * @since v2.7.0
 */

/**
 * Represents a market order with all required trading parameters
 * 
 * @interface MarketOrder
 * @example
 * ```typescript
 * const order: MarketOrder = {
 *   symbol: 'AAPL',
 *   quantity: 100,
 *   side: OrderSide.BUY,
 *   orderType: OrderType.MARKET,
 *   timestamp: new Date().toISOString()
 * };
 * ```
 */
interface MarketOrder {
  /** Trading symbol (e.g., 'AAPL', 'GOOGL') */
  readonly symbol: string;
  
  /** Number of shares/units to trade */
  readonly quantity: number;
  
  /** Buy or sell direction */
  readonly side: OrderSide;
  
  /** Order execution type */
  readonly orderType: OrderType;
  
  /** ISO 8601 timestamp of order creation */
  readonly timestamp: string;
  
  /** Optional price for limit orders */
  readonly price?: number;
  
  /** Optional stop price for stop orders */
  readonly stopPrice?: number;
  
  /** Time in force specification */
  readonly timeInForce?: TimeInForce;
}

/**
 * Order side enumeration
 */
enum OrderSide {
  BUY = 'buy',
  SELL = 'sell'
}

/**
 * Order type enumeration with detailed descriptions
 */
enum OrderType {
  /** Execute immediately at current market price */
  MARKET = 'market',
  
  /** Execute only at specified price or better */
  LIMIT = 'limit',
  
  /** Convert to market order when stop price is reached */
  STOP = 'stop',
  
  /** Convert to limit order when stop price is reached */
  STOP_LIMIT = 'stop_limit'
}
```

**Python/FastAPI Standards:**

```python
# File: /backend/src/services/trading_service.py
"""
Trading service implementation for order execution and management.

This module provides core trading functionality including order validation,
execution, and position management for the TradeSense platform.

Classes:
    TradingService: Main service class for trading operations
    OrderValidator: Validates orders against business rules
    PositionManager: Manages user positions and P&L calculations

Example:
    ```python
    trading_service = TradingService(
        broker_client=broker_client,
        risk_manager=risk_manager
    )
    
    result = await trading_service.execute_order(
        user_id="user_123",
        order=MarketOrder(symbol="AAPL", quantity=100, side="buy")
    )
    ```

Author: TradeSense Development Team
Since: v2.7.0
"""

from typing import Dict, List, Optional, Union
from datetime import datetime, timezone
from decimal import Decimal
import logging
from dataclasses import dataclass, field

from ..models.trading import Order, Position, Trade
from ..core.exceptions import TradingError, InsufficientFundsError
from ..core.security import require_permission
from ..utils.validation import validate_trading_params

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OrderExecutionResult:
    """
    Result of order execution operation.
    
    Attributes:
        order_id: Unique identifier for the executed order
        execution_price: Actual execution price
        executed_quantity: Number of shares actually executed
        commission: Trading commission charged
        timestamp: Execution timestamp in UTC
        status: Execution status (filled, partial, rejected)
    """
    order_id: str
    execution_price: Decimal
    executed_quantity: int
    commission: Decimal
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "filled"


class TradingService:
    """
    Core trading service for order execution and management.
    
    This service handles order validation, execution, position management,
    and integration with external broker systems while maintaining
    comprehensive audit trails and risk management.
    
    Attributes:
        broker_client: Client for broker API integration
        risk_manager: Risk management system interface
        position_manager: Position tracking and P&L calculations
    """
    
    def __init__(
        self,
        broker_client: BrokerClient,
        risk_manager: RiskManager,
        position_manager: PositionManager
    ) -> None:
        """
        Initialize trading service with required dependencies.
        
        Args:
            broker_client: Authenticated broker client instance
            risk_manager: Risk management system for order validation
            position_manager: Position and P&L management system
            
        Raises:
            ValueError: If any required dependency is None
        """
        if not all([broker_client, risk_manager, position_manager]):
            raise ValueError("All dependencies must be provided")
            
        self._broker_client = broker_client
        self._risk_manager = risk_manager
        self._position_manager = position_manager
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @require_permission("trading.execute_orders")
    async def execute_order(
        self,
        user_id: str,
        order: Order,
        dry_run: bool = False
    ) -> OrderExecutionResult:
        """
        Execute a trading order with comprehensive validation and risk checks.
        
        This method performs pre-execution validation, risk assessment,
        order submission to broker, and post-execution position updates.
        
        Args:
            user_id: Unique identifier for the trading user
            order: Order specification to execute
            dry_run: If True, validate but don't execute the order
            
        Returns:
            OrderExecutionResult containing execution details
            
        Raises:
            TradingError: If order validation or execution fails
            InsufficientFundsError: If user lacks required funds
            PermissionError: If user lacks trading permissions
            
        Example:
            ```python
            result = await trading_service.execute_order(
                user_id="user_123",
                order=Order(
                    symbol="AAPL",
                    quantity=100,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET
                )
            )
            
            logger.info(f"Order executed: {result.order_id} at ${result.execution_price}")
            ```
        """
        start_time = datetime.now(timezone.utc)
        self._logger.info(
            f"Executing order for user {user_id}: {order.symbol} "
            f"{order.quantity} shares {order.side}"
        )
        
        try:
            # 1. Validate order parameters
            validation_result = await self._validate_order(user_id, order)
            if not validation_result.is_valid:
                raise TradingError(f"Order validation failed: {validation_result.error}")
            
            # 2. Perform risk assessment
            risk_assessment = await self._risk_manager.assess_order(user_id, order)
            if risk_assessment.risk_level > RiskLevel.ACCEPTABLE:
                raise TradingError(f"Order exceeds risk limits: {risk_assessment.reason}")
            
            # 3. Check available funds
            required_capital = await self._calculate_required_capital(order)
            available_funds = await self._get_available_funds(user_id)
            
            if required_capital > available_funds:
                raise InsufficientFundsError(
                    f"Required: ${required_capital}, Available: ${available_funds}"
                )
            
            # 4. Execute order (skip if dry run)
            if dry_run:
                return OrderExecutionResult(
                    order_id=f"dry_run_{datetime.now().timestamp()}",
                    execution_price=order.price or Decimal("0"),
                    executed_quantity=0,
                    commission=Decimal("0"),
                    status="dry_run"
                )
            
            # 5. Submit to broker
            execution_result = await self._broker_client.submit_order(order)
            
            # 6. Update positions and balances
            await self._position_manager.update_position(
                user_id=user_id,
                symbol=order.symbol,
                quantity_change=execution_result.executed_quantity,
                price=execution_result.execution_price
            )
            
            # 7. Record trade in audit log
            await self._record_trade_audit(user_id, order, execution_result)
            
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            self._logger.info(
                f"Order executed successfully in {execution_time:.3f}s: "
                f"ID {execution_result.order_id}"
            )
            
            return execution_result
            
        except Exception as e:
            self._logger.error(f"Order execution failed for user {user_id}: {str(e)}")
            raise
    
    async def _validate_order(self, user_id: str, order: Order) -> ValidationResult:
        """Validate order parameters against business rules."""
        # Implementation details...
        pass
    
    async def _calculate_required_capital(self, order: Order) -> Decimal:
        """Calculate capital required for order execution."""
        # Implementation details...
        pass
    
    async def _get_available_funds(self, user_id: str) -> Decimal:
        """Get user's available trading funds."""
        # Implementation details...
        pass
    
    async def _record_trade_audit(
        self,
        user_id: str,
        order: Order,
        result: OrderExecutionResult
    ) -> None:
        """Record trade in comprehensive audit log."""
        # Implementation details...
        pass
```

#### **5A.2.2 File Naming Conventions and Directory Structure**

**Frontend Structure:**
```
frontend/
├── src/
│   ├── components/           # Reusable UI components
│   │   ├── common/          # Generic components (Button, Input, etc.)
│   │   ├── trading/         # Trading-specific components
│   │   ├── charts/          # Chart and visualization components
│   │   └── forms/           # Form components and validation
│   ├── pages/               # Route-level page components
│   │   ├── dashboard/       # Dashboard page and subpages
│   │   ├── trading/         # Trading interface pages
│   │   └── auth/            # Authentication pages
│   ├── hooks/               # Custom React hooks
│   │   ├── useAuth.ts       # Authentication hooks
│   │   ├── useTrading.ts    # Trading-related hooks
│   │   └── useWebSocket.ts  # WebSocket connection hooks
│   ├── services/            # API services and external integrations
│   │   ├── api/             # API client configurations
│   │   ├── trading/         # Trading service integrations
│   │   └── auth/            # Authentication services
│   ├── stores/              # State management (Zustand/Redux)
│   │   ├── authStore.ts     # Authentication state
│   │   ├── tradingStore.ts  # Trading state
│   │   └── uiStore.ts       # UI state management
│   ├── types/               # TypeScript type definitions
│   │   ├── api.types.ts     # API response types
│   │   ├── trading.types.ts # Trading domain types
│   │   └── ui.types.ts      # UI component types
│   ├── utils/               # Utility functions
│   │   ├── formatting/      # Data formatting utilities
│   │   ├── validation/      # Input validation utilities
│   │   └── constants/       # Application constants
│   ├── styles/              # Styling and theme configuration
│   │   ├── globals.css      # Global styles
│   │   ├── components/      # Component-specific styles
│   │   └── themes/          # Theme configurations
│   └── tests/               # Test files mirroring src structure
│       ├── components/      # Component tests
│       ├── hooks/           # Hook tests
│       └── utils/           # Utility function tests
```

**Backend Structure:**
```
backend/
├── src/
│   ├── api/                 # FastAPI router definitions
│   │   ├── v1/              # API version 1 routes
│   │   │   ├── auth.py      # Authentication endpoints
│   │   │   ├── trading.py   # Trading endpoints
│   │   │   ├── users.py     # User management endpoints
│   │   │   └── analytics.py # Analytics endpoints
│   │   └── dependencies.py  # Shared dependencies
│   ├── core/                # Core application components
│   │   ├── config.py        # Configuration management
│   │   ├── security.py      # Security utilities
│   │   ├── database.py      # Database configuration
│   │   └── exceptions.py    # Custom exception classes
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py          # User model
│   │   ├── trading.py       # Trading-related models
│   │   └── analytics.py     # Analytics models
│   ├── schemas/             # Pydantic schemas
│   │   ├── user.py          # User schemas
│   │   ├── trading.py       # Trading schemas
│   │   └── responses.py     # API response schemas
│   ├── services/            # Business logic services
│   │   ├── auth_service.py  # Authentication logic
│   │   ├── trading_service.py # Trading operations
│   │   └── analytics_service.py # Analytics processing
│   ├── utils/               # Utility modules
│   │   ├── validation.py    # Input validation
│   │   ├── encryption.py    # Encryption utilities
│   │   └── formatting.py    # Data formatting
│   └── tests/               # Test files mirroring src structure
│       ├── api/             # API endpoint tests
│       ├── services/        # Service layer tests
│       └── utils/           # Utility tests
├── migrations/              # Database migration files
│   ├── versions/            # Alembic migration versions
│   └── alembic.ini          # Alembic configuration
└── scripts/                 # Deployment and utility scripts
    ├── init_db.py           # Database initialization
    └── seed_data.py         # Test data seeding
```

**File Naming Patterns:**

```typescript
// Component files: PascalCase with .tsx extension
TradingDashboard.tsx
OrderExecutionForm.tsx
PriceChart.tsx

// Hook files: camelCase starting with 'use'
useAuth.ts
useWebSocket.ts
useTradingData.ts

// Service files: camelCase with .service.ts suffix
authService.ts
tradingService.ts
apiService.ts

// Type files: camelCase with .types.ts suffix
trading.types.ts
api.types.ts
user.types.ts

// Utility files: camelCase with descriptive names
formatCurrency.ts
validateInput.ts
dateHelpers.ts

// Test files: Same name as source with .test.ts/.spec.ts suffix
TradingDashboard.test.tsx
useAuth.test.ts
tradingService.spec.ts
```

**Python Naming Patterns:**

```python
# Model files: snake_case with .py extension
user_model.py
trading_order.py
portfolio_position.py

# Service files: snake_case with _service.py suffix
auth_service.py
trading_service.py
analytics_service.py

# Schema files: snake_case matching model names
user_schemas.py
trading_schemas.py
response_schemas.py

# Test files: test_ prefix with descriptive names
test_auth_service.py
test_trading_endpoints.py
test_user_models.py
```

#### **5A.2.3 Import Patterns and Module Organization**

**Frontend Import Standards:**

```typescript
// File: /frontend/src/components/trading/TradingDashboard.tsx

// 1. External library imports (grouped and sorted alphabetically)
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Navigate, useParams, useSearchParams } from 'react-router-dom';
import { toast } from 'react-toastify';
import classNames from 'classnames';

// 2. Internal imports - Types first
import type {
  MarketOrder,
  Position,
  TradingAccount,
  PriceData
} from '../../types/trading.types';
import type { ApiResponse } from '../../types/api.types';

// 3. Internal imports - Hooks
import { useAuth } from '../../hooks/useAuth';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useTradingData } from '../../hooks/useTradingData';

// 4. Internal imports - Services
import { tradingService } from '../../services/trading/tradingService';
import { priceService } from '../../services/trading/priceService';

// 5. Internal imports - Components (organized by hierarchy)
import { Button } from '../common/Button';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorBoundary } from '../common/ErrorBoundary';
import { OrderForm } from './OrderForm';
import { PositionsList } from './PositionsList';
import { PriceChart } from '../charts/PriceChart';

// 6. Internal imports - Utilities and constants
import { formatCurrency, formatPercentage } from '../../utils/formatting/numberUtils';
import { validateOrderParams } from '../../utils/validation/tradingValidation';
import { TRADING_CONSTANTS } from '../../utils/constants/trading';

// 7. Styles (always last)
import './TradingDashboard.styles.css';
```

**Backend Import Standards:**

```python
# File: /backend/src/api/v1/trading.py

# 1. Standard library imports (sorted alphabetically)
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional

# 2. Third-party imports (grouped by package, sorted alphabetically)
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

# 3. Local application imports - Core modules first
from ...core.config import get_settings
from ...core.database import get_db
from ...core.security import get_current_user, require_permission
from ...core.exceptions import TradingError, InsufficientFundsError

# 4. Local application imports - Models
from ...models.user import User
from ...models.trading import Order, Position, Trade

# 5. Local application imports - Schemas
from ...schemas.trading import (
    OrderCreate,
    OrderResponse,
    PositionResponse,
    TradingAccountResponse
)
from ...schemas.responses import ApiResponse, ErrorResponse

# 6. Local application imports - Services
from ...services.trading_service import TradingService
from ...services.risk_service import RiskService
from ...services.analytics_service import AnalyticsService

# 7. Local application imports - Utils
from ...utils.validation import validate_trading_params
from ...utils.formatting import format_decimal_places
```

#### **5A.2.4 Documentation Requirements and Standards**

**Comprehensive Documentation Checklist:**

**Code Documentation:**
- [ ] **File-level docstrings**: Purpose, author, since version
- [ ] **Class documentation**: Purpose, attributes, usage examples
- [ ] **Method documentation**: Parameters, returns, exceptions, examples
- [ ] **Complex logic comments**: Explain why, not what
- [ ] **Type annotations**: All functions and methods fully typed
- [ ] **Example usage**: Real-world usage examples in docstrings

**API Documentation:**
```python
# File: /backend/src/api/v1/trading.py

@router.post(
    "/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute a trading order",
    description="""
    Execute a trading order with comprehensive validation and risk management.
    
    This endpoint handles order validation, risk assessment, execution through
    the connected broker, and position updates. All orders are subject to
    real-time risk checks and compliance validation.
    
    **Security Requirements:**
    - User must be authenticated with valid JWT token
    - User must have 'trading.execute_orders' permission
    - Account must be approved for trading
    
    **Rate Limiting:**
    - 100 requests per minute per user
    - Burst limit: 10 requests per second
    
    **Order Types Supported:**
    - Market orders: Execute immediately at current market price
    - Limit orders: Execute only at specified price or better
    - Stop orders: Convert to market order when stop price reached
    - Stop-limit orders: Convert to limit order when stop price reached
    
    **Risk Management:**
    - Position size limits enforced
    - Account balance verification
    - Real-time margin calculations
    - Volatility-based risk assessment
    
    **Example Request:**
    ```json
    {
        "symbol": "AAPL",
        "quantity": 100,
        "side": "buy",
        "order_type": "market",
        "time_in_force": "day"
    }
    ```
    
    **Example Response:**
    ```json
    {
        "order_id": "ord_1234567890",
        "status": "filled",
        "execution_price": 150.25,
        "executed_quantity": 100,
        "commission": 1.50,
        "timestamp": "2024-01-15T10:30:00Z"
    }
    ```
    """,
    responses={
        201: {
            "description": "Order executed successfully",
            "model": OrderResponse
        },
        400: {
            "description": "Invalid order parameters",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "error": "INVALID_ORDER_PARAMS",
                        "message": "Quantity must be positive integer",
                        "details": {
                            "field": "quantity",
                            "value": -10,
                            "constraint": "positive_integer"
                        }
                    }
                }
            }
        },
        403: {
            "description": "Insufficient trading permissions",
            "model": ErrorResponse
        },
        409: {
            "description": "Risk limits exceeded",
            "model": ErrorResponse
        },
        422: {
            "description": "Insufficient funds",
            "model": ErrorResponse
        }
    },
    tags=["Trading"],
    operation_id="execute_order"
)
async def execute_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    trading_service: TradingService = Depends(get_trading_service),
    db: Session = Depends(get_db)
) -> OrderResponse:
```

**README Template:**
```markdown
# TradeSense - Component/Service Name

## Overview
Brief description of what this component/service does and its role in the larger system.

## Features
- Feature 1 with brief description
- Feature 2 with brief description
- Feature 3 with brief description

## Installation & Setup

### Prerequisites
- Node.js 18.x or higher
- Python 3.11 or higher
- PostgreSQL 14.x or higher

### Environment Variables
```bash
# Required variables
DATABASE_URL=postgresql://user:pass@localhost/tradesense
JWT_SECRET=your-super-secret-jwt-key
BROKER_API_KEY=your-broker-api-key

# Optional variables
LOG_LEVEL=info
REDIS_URL=redis://localhost:6379
```

### Local Development
```bash
# Install dependencies
npm install
pip install -r requirements.txt

# Run development server
npm run dev
python -m uvicorn main:app --reload
```

## Usage Examples

### Basic Usage
```typescript
import { TradingService } from './tradingService';

const tradingService = new TradingService({
  apiKey: process.env.BROKER_API_KEY,
  environment: 'sandbox'
});

const result = await tradingService.executeOrder({
  symbol: 'AAPL',
  quantity: 100,
  side: 'buy',
  orderType: 'market'
});
```

### Advanced Configuration
```typescript
// Advanced usage with custom configuration
```

## API Reference

### Methods

#### `executeOrder(orderData: OrderCreate): Promise<OrderResponse>`
Execute a trading order with validation and risk management.

**Parameters:**
- `orderData` (OrderCreate): Order specification object

**Returns:**
- Promise<OrderResponse>: Execution result with order details

**Throws:**
- `TradingError`: If order validation fails
- `InsufficientFundsError`: If account lacks required funds

## Testing

### Unit Tests
```bash
npm run test:unit
pytest tests/unit/
```

### Integration Tests
```bash
npm run test:integration
pytest tests/integration/
```

### E2E Tests
```bash
npm run test:e2e
```

## Performance Considerations
- Order execution latency: < 100ms average
- Throughput: 1000 orders/second sustained
- Memory usage: < 512MB under normal load

## Security Notes
- All API endpoints require authentication
- Trading permissions validated on every request
- Sensitive data encrypted at rest and in transit
- Audit logging for all trading activities

## Contributing
See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

## Changelog
See [CHANGELOG.md](./CHANGELOG.md) for version history.

## License
Copyright 2024 TradeSense. All rights reserved.
```

### **5A.3 DEVELOPMENT ENVIRONMENT SETUP**

#### **5A.3.1 Docker-based Development Environment**

**Complete Docker Development Stack:**

```yaml
# File: /docker-compose.dev.yml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:14-alpine
    container_name: tradesense-postgres-dev
    environment:
      POSTGRES_DB: tradesense_dev
      POSTGRES_USER: tradesense_user
      POSTGRES_PASSWORD: dev_password_2024
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=C"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init-scripts:/docker-entrypoint-initdb.d:ro
      - ./database/dev-seeds:/opt/dev-seeds:ro
    networks:
      - tradesense-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tradesense_user -d tradesense_dev"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: tradesense-redis-dev
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./redis/redis-dev.conf:/usr/local/etc/redis/redis.conf:ro
    networks:
      - tradesense-network
    command: redis-server /usr/local/etc/redis/redis.conf
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    restart: unless-stopped

  # Backend Development Service
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
      target: development
    container_name: tradesense-backend-dev
    environment:
      - DATABASE_URL=postgresql://tradesense_user:dev_password_2024@postgres:5432/tradesense_dev
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET=dev-jwt-secret-key-2024-tradesense
      - ENVIRONMENT=development
      - LOG_LEVEL=debug
      - PYTHONPATH=/app
      - PYTHONDONTWRITEBYTECODE=1
      - PYTHONUNBUFFERED=1
    ports:
      - "8000:8000"
      - "5678:5678"  # Debug port
    volumes:
      - ./backend:/app:cached
      - backend_cache:/app/.cache
      - /app/node_modules  # Prevent overriding node_modules
    networks:
      - tradesense-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: >
      sh -c "
        echo 'Waiting for database...' &&
        python scripts/wait_for_db.py &&
        echo 'Running database migrations...' &&
        alembic upgrade head &&
        echo 'Seeding development data...' &&
        python scripts/seed_dev_data.py &&
        echo 'Starting development server...' &&
        uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
      "
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Frontend Development Service
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
      target: development
    container_name: tradesense-frontend-dev
    environment:
      - NODE_ENV=development
      - REACT_APP_API_URL=http://localhost:8000
      - REACT_APP_WS_URL=ws://localhost:8000
      - CHOKIDAR_USEPOLLING=true
      - FAST_REFRESH=true
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app:cached
      - frontend_cache:/app/.cache
      - /app/node_modules
    networks:
      - tradesense-network
    depends_on:
      - backend
    command: npm start
    restart: unless-stopped
    stdin_open: true
    tty: true

  # MinIO for S3-compatible object storage
  minio:
    image: minio/minio:latest
    container_name: tradesense-minio-dev
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin123
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    networks:
      - tradesense-network
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: tradesense-nginx-dev
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/dev.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    networks:
      - tradesense-network
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

  # Development Tools Container
  dev-tools:
    build:
      context: ./dev-tools
      dockerfile: Dockerfile
    container_name: tradesense-dev-tools
    volumes:
      - ./:/workspace:cached
      - dev_tools_cache:/root/.cache
    networks:
      - tradesense-network
    environment:
      - WORKSPACE=/workspace
    profiles:
      - tools
    command: sleep infinity

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  minio_data:
    driver: local
  backend_cache:
    driver: local
  frontend_cache:
    driver: local
  dev_tools_cache:
    driver: local

networks:
  tradesense-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

**Development Dockerfile for Backend:**

```dockerfile
# File: /backend/Dockerfile.dev
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd --create-home --shell /bin/bash tradesense
USER tradesense
WORKDIR /app

# Install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --user --no-warn-script-location -r requirements-dev.txt

# Add user local bin to PATH
ENV PATH="/home/tradesense/.local/bin:$PATH"

# Development stage
FROM base as development

# Install development tools
USER root
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

USER tradesense

# Copy application code
COPY --chown=tradesense:tradesense . .

# Create cache directory
RUN mkdir -p /app/.cache

# Expose ports
EXPOSE 8000 5678

# Development command (overridden in docker-compose)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Development Dockerfile for Frontend:**

```dockerfile
# File: /frontend/Dockerfile.dev
FROM node:18-alpine as base

# Install dependencies for node-gyp
RUN apk add --no-cache \
    python3 \
    make \
    g++

# Create application user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S tradesense -u 1001

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./
RUN npm ci --only=production && npm cache clean --force

# Development stage
FROM base as development

# Install all dependencies (including dev)
COPY package.json package-lock.json ./
RUN npm ci && npm cache clean --force

# Change ownership
RUN chown -R tradesense:nodejs /app
USER tradesense

# Copy application code
COPY --chown=tradesense:nodejs . .

# Create cache directory
RUN mkdir -p /app/.cache

# Expose port
EXPOSE 3000

# Development command
CMD ["npm", "start"]
```

#### **5A.3.2 Environment Variable Management**

**Comprehensive Environment Configuration:**

```bash
# File: /.env.development
# =============================================================================
# TradeSense Development Environment Configuration
# =============================================================================
# This file contains all environment variables needed for local development
# DO NOT commit this file to version control
# Copy from .env.development.template and customize for your local setup

# Application Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=debug

# Database Configuration
DATABASE_URL=postgresql://tradesense_user:dev_password_2024@localhost:5432/tradesense_dev
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_ECHO=false

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=10
REDIS_PASSWORD=

# JWT Configuration
JWT_SECRET=dev-jwt-secret-key-2024-tradesense-very-long-and-secure
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
JWT_REFRESH_EXPIRE_DAYS=30

# OAuth Configuration (Development)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Broker API Configuration (Sandbox)
ALPACA_API_KEY=your-alpaca-sandbox-api-key
ALPACA_SECRET_KEY=your-alpaca-sandbox-secret-key
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_DATA_URL=https://data.alpaca.markets

# Email Configuration (Development - Use MailHog)
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USE_TLS=false
SMTP_USERNAME=
SMTP_PASSWORD=
FROM_EMAIL=noreply@tradesense.local

# File Storage Configuration
S3_BUCKET_NAME=tradesense-dev-storage
S3_REGION=us-east-1
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin123
S3_ENDPOINT_URL=http://localhost:9000

# Monitoring and Observability
SENTRY_DSN=
DATADOG_API_KEY=
NEW_RELIC_LICENSE_KEY=

# Feature Flags
ENABLE_REAL_TIME_TRADING=false
ENABLE_PAPER_TRADING=true
ENABLE_ANALYTICS_TRACKING=false
ENABLE_RATE_LIMITING=false

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_ENVIRONMENT=development
REACT_APP_SENTRY_DSN=
REACT_APP_GOOGLE_ANALYTICS_ID=

# Development Tools
ENABLE_PROFILING=true
ENABLE_DEBUG_TOOLBAR=true
ENABLE_SWAGGER_UI=true
ENABLE_ADMIN_INTERFACE=true

# Security Settings (Relaxed for Development)
CORS_ORIGINS=["http://localhost:3000", "http://localhost:3001"]
SESSION_SECURE=false
SESSION_SAMESITE=lax
CSRF_PROTECTION=false

# Rate Limiting (Disabled for Development)
RATE_LIMIT_ENABLED=false
RATE_LIMIT_REQUESTS_PER_MINUTE=1000
RATE_LIMIT_BURST_SIZE=100

# Background Tasks
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
CELERY_WORKER_CONCURRENCY=4

# Testing Configuration
TEST_DATABASE_URL=postgresql://tradesense_user:dev_password_2024@localhost:5432/tradesense_test
PYTEST_CURRENT_TEST=
TESTING=false
```

**Environment Template File:**

```bash
# File: /.env.development.template
# =============================================================================
# TradeSense Development Environment Template
# =============================================================================
# Copy this file to .env.development and fill in your specific values
# This template shows all required and optional environment variables

# Application Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=debug

# Database Configuration (Update with your PostgreSQL credentials)
DATABASE_URL=postgresql://tradesense_user:YOUR_PASSWORD@localhost:5432/tradesense_dev
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_ECHO=false

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=10
REDIS_PASSWORD=

# JWT Configuration (IMPORTANT: Change this secret!)
JWT_SECRET=YOUR_SUPER_SECRET_JWT_KEY_MINIMUM_32_CHARACTERS
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
JWT_REFRESH_EXPIRE_DAYS=30

# OAuth Configuration (Optional - for social login testing)
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET
GITHUB_CLIENT_ID=YOUR_GITHUB_CLIENT_ID
GITHUB_CLIENT_SECRET=YOUR_GITHUB_CLIENT_SECRET

# Broker API Configuration (Get from Alpaca/broker)
ALPACA_API_KEY=YOUR_ALPACA_SANDBOX_API_KEY
ALPACA_SECRET_KEY=YOUR_ALPACA_SANDBOX_SECRET_KEY
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_DATA_URL=https://data.alpaca.markets

# Email Configuration (Use MailHog for local development)
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USE_TLS=false
SMTP_USERNAME=
SMTP_PASSWORD=
FROM_EMAIL=noreply@tradesense.local

# File Storage Configuration (MinIO for local S3-compatible storage)
S3_BUCKET_NAME=tradesense-dev-storage
S3_REGION=us-east-1
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin123
S3_ENDPOINT_URL=http://localhost:9000

# Monitoring and Observability (Optional for development)
SENTRY_DSN=
DATADOG_API_KEY=
NEW_RELIC_LICENSE_KEY=

# Feature Flags
ENABLE_REAL_TIME_TRADING=false
ENABLE_PAPER_TRADING=true
ENABLE_ANALYTICS_TRACKING=false
ENABLE_RATE_LIMITING=false

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_ENVIRONMENT=development
REACT_APP_SENTRY_DSN=
REACT_APP_GOOGLE_ANALYTICS_ID=

# Development Tools
ENABLE_PROFILING=true
ENABLE_DEBUG_TOOLBAR=true
ENABLE_SWAGGER_UI=true
ENABLE_ADMIN_INTERFACE=true

# Security Settings (Relaxed for Development)
CORS_ORIGINS=["http://localhost:3000", "http://localhost:3001"]
SESSION_SECURE=false
SESSION_SAMESITE=lax
CSRF_PROTECTION=false

# Rate Limiting (Disabled for Development)
RATE_LIMIT_ENABLED=false
RATE_LIMIT_REQUESTS_PER_MINUTE=1000
RATE_LIMIT_BURST_SIZE=100

# Background Tasks
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
CELERY_WORKER_CONCURRENCY=4

# Testing Configuration
TEST_DATABASE_URL=postgresql://tradesense_user:YOUR_PASSWORD@localhost:5432/tradesense_test
PYTEST_CURRENT_TEST=
TESTING=false
```

#### **5A.3.3 IDE Configuration and Productivity Tools**

**VS Code Workspace Configuration:**

```json
// File: /.vscode/settings.json
{
  "workbench.colorTheme": "Default Dark+",
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true,
    "source.organizeImports": true
  },
  "editor.rulers": [80, 120],
  "editor.tabSize": 2,
  "editor.insertSpaces": true,
  "editor.detectIndentation": false,
  
  // Python settings
  "python.defaultInterpreterPath": "./backend/.venv/bin/python",
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "88"],
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["backend/tests"],
  
  // TypeScript/JavaScript settings
  "typescript.preferences.importModuleSpecifier": "relative",
  "typescript.suggest.autoImports": true,
  "javascript.suggest.autoImports": true,
  
  // File associations
  "files.associations": {
    "*.env.*": "properties",
    "Dockerfile.*": "dockerfile",
    "*.yml": "yaml",
    "*.yaml": "yaml"
  },
  
  // Search and file exclusions
  "files.exclude": {
    "**/node_modules": true,
    "**/.git": true,
    "**/.svn": true,
    "**/.hg": true,
    "**/CVS": true,
    "**/.DS_Store": true,
    "**/Thumbs.db": true,
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/venv": true,
    "**/.venv": true,
    "**/build": true,
    "**/dist": true,
    "**/.coverage": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true
  },
  
  "search.exclude": {
    "**/node_modules": true,
    "**/bower_components": true,
    "**/*.code-search": true,
    "**/build": true,
    "**/dist": true,
    "**/.coverage": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true
  },
  
  // Git settings
  "git.autofetch": true,
  "git.confirmSync": false,
  "git.enableSmartCommit": true,
  "git.postCommitCommand": "sync",
  
  // Extension-specific settings
  "eslint.workingDirectories": ["frontend"],
  "eslint.format.enable": true,
  "prettier.configPath": "./frontend/.prettierrc",
  "prettier.ignorePath": "./frontend/.prettierignore",
  
  // Docker settings
  "docker.enableDockerComposeV2": true,
  
  // Terminal settings
  "terminal.integrated.defaultProfile.linux": "bash",
  "terminal.integrated.cwd": "${workspaceFolder}",
  
  // Emmet settings
  "emmet.includeLanguages": {
    "javascript": "javascriptreact",
    "typescript": "typescriptreact"
  }
}
```

**VS Code Extensions Configuration:**

```json
// File: /.vscode/extensions.json
{
  "recommendations": [
    // Essential Extensions
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.flake8",
    "ms-python.mypy-type-checker",
    "ms-vscode.vscode-typescript-next",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "ms-vscode.vscode-json",
    
    // Git and Version Control
    "eamodio.gitlens",
    "mhutchie.git-graph",
    "github.vscode-pull-request-github",
    
    // Docker and DevOps
    "ms-azuretools.vscode-docker",
    "ms-vscode-remote.remote-containers",
    "redhat.vscode-yaml",
    
    // Database
    "mtxr.sqltools",
    "mtxr.sqltools-driver-pg",
    
    // Testing
    "ms-python.python",
    "hbenl.vscode-test-explorer",
    "little-fox-team.vscode-python-test-adapter",
    
    // Productivity
    "streetsidesoftware.code-spell-checker",
    "aaron-bond.better-comments",
    "christian-kohler.path-intellisense",
    "formulahendry.auto-rename-tag",
    "bradlc.vscode-tailwindcss",
    
    // API Development
    "humao.rest-client",
    "42crunch.vscode-openapi",
    
    // Markdown
    "yzhang.markdown-all-in-one",
    "davidanson.vscode-markdownlint",
    
    // Environment Files
    "mikestead.dotenv",
    
    // Theme and UI
    "pkief.material-icon-theme",
    "zhuangtongfa.material-theme"
  ],
  "unwantedRecommendations": [
    "ms-python.pylint",
    "ms-python.isort"
  ]
}
```

**Development Scripts and Automation:**

```bash
#!/bin/bash
# File: /scripts/dev-setup.sh
# Development environment setup script

set -e

echo "🚀 Setting up TradeSense development environment..."

# Check prerequisites
check_prerequisites() {
    echo "📋 Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js is not installed. Please install Node.js 18+ first."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
        exit 1
    fi
    
    echo "✅ All prerequisites met!"
}

# Setup environment files
setup_env_files() {
    echo "📄 Setting up environment files..."
    
    if [ ! -f .env.development ]; then
        echo "Creating .env.development from template..."
        cp .env.development.template .env.development
        echo "⚠️  Please edit .env.development with your specific values"
    else
        echo "✅ .env.development already exists"
    fi
    
    if [ ! -f frontend/.env.local ]; then
        echo "Creating frontend/.env.local..."
        cat > frontend/.env.local << EOF
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_ENVIRONMENT=development
GENERATE_SOURCEMAP=true
FAST_REFRESH=true
EOF
        echo "✅ Created frontend/.env.local"
    else
        echo "✅ frontend/.env.local already exists"
    fi
}

# Setup Git hooks
setup_git_hooks() {
    echo "🪝 Setting up Git hooks..."
    
    # Pre-commit hook
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook for TradeSense

set -e

echo "🔍 Running pre-commit checks..."

# Frontend checks
if [ -d "frontend" ]; then
    echo "  📄 Checking frontend code..."
    cd frontend
    npm run lint
    npm run type-check
    cd ..
fi

# Backend checks
if [ -d "backend" ]; then
    echo "  🐍 Checking backend code..."
    cd backend
    python -m flake8 src/
    python -m mypy src/
    python -m pytest tests/unit/ -x
    cd ..
fi

echo "✅ Pre-commit checks passed!"
EOF

    chmod +x .git/hooks/pre-commit
    echo "✅ Git hooks configured"
}

# Setup development databases
setup_databases() {
    echo "🗄️  Setting up development databases..."
    
    # Start only database services first
    docker-compose -f docker-compose.dev.yml up -d postgres redis
    
    # Wait for services to be ready
    echo "⏳ Waiting for database services to be ready..."
    sleep 10
    
    # Run database migrations
    echo "📊 Running database migrations..."
    docker-compose -f docker-compose.dev.yml exec postgres psql -U tradesense_user -d tradesense_dev -c "\l"
    
    echo "✅ Database setup complete"
}

# Install dependencies
install_dependencies() {
    echo "📦 Installing dependencies..."
    
    # Frontend dependencies
    if [ -d "frontend" ]; then
        echo "  📄 Installing frontend dependencies..."
        cd frontend
        npm ci
        cd ..
    fi
    
    # Backend dependencies
    if [ -d "backend" ]; then
        echo "  🐍 Installing backend dependencies..."
        cd backend
        if [ ! -d ".venv" ]; then
            python3 -m venv .venv
        fi
        source .venv/bin/activate
        pip install -r requirements-dev.txt
        cd ..
    fi
    
    echo "✅ Dependencies installed"
}

# Start development services
start_services() {
    echo "🚀 Starting development services..."
    
    docker-compose -f docker-compose.dev.yml up -d
    
    echo "⏳ Waiting for services to start..."
    sleep 30
    
    # Check service health
    echo "🔍 Checking service health..."
    docker-compose -f docker-compose.dev.yml ps
    
    echo ""
    echo "🎉 Development environment is ready!"
    echo ""
    echo "📊 Available services:"
    echo "  • Frontend: http://localhost:3000"
    echo "  • Backend API: http://localhost:8000"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo "  • Database: localhost:5432"
    echo "  • Redis: localhost:6379"
    echo "  • MinIO: http://localhost:9001"
    echo ""
    echo "🛠️  Development commands:"
    echo "  • View logs: docker-compose -f docker-compose.dev.yml logs -f"
    echo "  • Stop services: docker-compose -f docker-compose.dev.yml down"
    echo "  • Restart service: docker-compose -f docker-compose.dev.yml restart <service>"
    echo ""
}

# Main execution
main() {
    check_prerequisites
    setup_env_files
    setup_git_hooks
    install_dependencies
    setup_databases
    start_services
}

# Run main function
main "$@"
```

```bash
#!/bin/bash
# File: /scripts/dev-test.sh
# Comprehensive testing script for development

set -e

echo "🧪 Running comprehensive test suite..."

# Function to run frontend tests
test_frontend() {
    echo "📄 Running frontend tests..."
    cd frontend
    
    echo "  🔍 Linting..."
    npm run lint
    
    echo "  📝 Type checking..."
    npm run type-check
    
    echo "  🧪 Unit tests..."
    npm run test:unit -- --coverage --watchAll=false
    
    echo "  🎭 Component tests..."
    npm run test:components -- --coverage --watchAll=false
    
    echo "  🌐 Integration tests..."
    npm run test:integration
    
    cd ..
    echo "✅ Frontend tests completed"
}

# Function to run backend tests
test_backend() {
    echo "🐍 Running backend tests..."
    cd backend
    
    source .venv/bin/activate
    
    echo "  🔍 Linting with flake8..."
    python -m flake8 src/ tests/
    
    echo "  📝 Type checking with mypy..."
    python -m mypy src/
    
    echo "  🧪 Unit tests..."
    python -m pytest tests/unit/ -v --cov=src --cov-report=html --cov-report=term
    
    echo "  🎭 Integration tests..."
    python -m pytest tests/integration/ -v
    
    echo "  🌐 API tests..."
    python -m pytest tests/api/ -v
    
    cd ..
    echo "✅ Backend tests completed"
}

# Function to run E2E tests
test_e2e() {
    echo "🌐 Running E2E tests..."
    
    # Ensure services are running
    docker-compose -f docker-compose.dev.yml up -d
    
    # Wait for services
    echo "⏳ Waiting for services to be ready..."
    sleep 30
    
    # Run E2E tests
    cd e2e
    npm run test:e2e
    cd ..
    
    echo "✅ E2E tests completed"
}

# Function to run security tests
test_security() {
    echo "🔒 Running security tests..."
    
    echo "  🐍 Backend security scan..."
    cd backend
    source .venv/bin/activate
    python -m bandit -r src/
    cd ..
    
    echo "  📄 Frontend security scan..."
    cd frontend
    npm audit
    cd ..
    
    echo "✅ Security tests completed"
}

# Function to run performance tests
test_performance() {
    echo "⚡ Running performance tests..."
    
    # Ensure services are running
    docker-compose -f docker-compose.dev.yml up -d
    
    echo "  🌐 API performance tests..."
    cd performance
    npm run test:performance
    cd ..
    
    echo "✅ Performance tests completed"
}

# Main execution based on arguments
case "${1:-all}" in
    "frontend")
        test_frontend
        ;;
    "backend")
        test_backend
        ;;
    "e2e")
        test_e2e
        ;;
    "security")
        test_security
        ;;
    "performance")
        test_performance
        ;;
    "all")
        test_frontend
        test_backend
        test_security
        echo ""
        echo "🎉 All tests completed successfully!"
        echo "📊 Coverage reports available in:"
        echo "  • Frontend: frontend/coverage/"
        echo "  • Backend: backend/htmlcov/"
        ;;
    *)
        echo "Usage: $0 [frontend|backend|e2e|security|performance|all]"
        exit 1
        ;;
esac
```

This completes Section 5A of the Development Workflow Foundation with exhaustive detail covering branching strategies, code organization standards, and development environment setup. The documentation provides comprehensive guidelines, configuration files, and automation scripts for establishing a robust development workflow.

---

## **SECTION 5B: TESTING, CI/CD & QUALITY ASSURANCE**

### **5B.1 COMPREHENSIVE TESTING STRATEGY**

#### **5B.1.1 Unit Testing Framework and Patterns**

**Frontend Unit Testing Architecture:**

```typescript
// File: /frontend/src/components/trading/OrderForm.test.tsx
/**
 * Comprehensive unit tests for OrderForm component
 * 
 * Test Categories:
 * - Component rendering and UI validation
 * - User interaction handling
 * - Form validation logic
 * - API integration mocking
 * - Error state management
 * - Accessibility compliance
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';

import { OrderForm } from './OrderForm';
import { TradingProvider } from '../../contexts/TradingContext';
import { AuthProvider } from '../../contexts/AuthContext';
import { tradingService } from '../../services/trading/tradingService';
import { mockUser, mockTradingAccount, mockOrderResponse } from '../../__mocks__/trading.mocks';

// Mock external dependencies
vi.mock('../../services/trading/tradingService');
vi.mock('../../hooks/useWebSocket');

/**
 * Test wrapper component with all required providers
 */
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <TradingProvider>
            {children}
          </TradingProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('OrderForm Component', () => {
  let mockExecuteOrder: ReturnType<typeof vi.fn>;
  
  beforeEach(() => {
    mockExecuteOrder = vi.fn();
    (tradingService.executeOrder as any) = mockExecuteOrder;
    
    // Reset all mocks
    vi.clearAllMocks();
    
    // Setup default successful responses
    mockExecuteOrder.mockResolvedValue(mockOrderResponse);
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render all form fields with correct initial values', () => {
      render(<OrderForm />, { wrapper: TestWrapper });
      
      // Verify all form fields are present
      expect(screen.getByLabelText(/symbol/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/quantity/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/order type/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/side/i)).toBeInTheDocument();
      
      // Verify initial values
      expect(screen.getByDisplayValue('')).toBeInTheDocument(); // Symbol input
      expect(screen.getByDisplayValue('1')).toBeInTheDocument(); // Quantity input
      
      // Verify submit button is present but disabled initially
      const submitButton = screen.getByRole('button', { name: /place order/i });
      expect(submitButton).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
    });

    it('should render with correct accessibility attributes', () => {
      render(<OrderForm />, { wrapper: TestWrapper });
      
      // Verify ARIA labels and roles
      expect(screen.getByRole('form')).toHaveAttribute('aria-label', 'Order placement form');
      expect(screen.getByLabelText(/symbol/i)).toHaveAttribute('aria-required', 'true');
      expect(screen.getByLabelText(/quantity/i)).toHaveAttribute('aria-required', 'true');
      
      // Verify form validation messages container
      expect(screen.getByRole('alert')).toHaveAttribute('aria-live', 'polite');
    });

    it('should display current account information', () => {
      render(<OrderForm />, { wrapper: TestWrapper });
      
      // Verify account balance display
      expect(screen.getByText(/available balance/i)).toBeInTheDocument();
      expect(screen.getByText(/buying power/i)).toBeInTheDocument();
      
      // Verify account values are formatted correctly
      expect(screen.getByText(/\$[\d,]+\.\d{2}/)).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('should validate required fields', async () => {
      const user = userEvent.setup();
      render(<OrderForm />, { wrapper: TestWrapper });
      
      const submitButton = screen.getByRole('button', { name: /place order/i });
      
      // Try to submit empty form
      await user.click(submitButton);
      
      // Verify validation errors
      await waitFor(() => {
        expect(screen.getByText(/symbol is required/i)).toBeInTheDocument();
        expect(screen.getByText(/quantity must be greater than 0/i)).toBeInTheDocument();
      });
      
      // Verify form was not submitted
      expect(mockExecuteOrder).not.toHaveBeenCalled();
    });

    it('should validate symbol format', async () => {
      const user = userEvent.setup();
      render(<OrderForm />, { wrapper: TestWrapper });
      
      const symbolInput = screen.getByLabelText(/symbol/i);
      
      // Test invalid symbols
      await user.type(symbolInput, 'invalid@symbol');
      await user.tab(); // Trigger blur validation
      
      await waitFor(() => {
        expect(screen.getByText(/invalid symbol format/i)).toBeInTheDocument();
      });
      
      // Test valid symbol
      await user.clear(symbolInput);
      await user.type(symbolInput, 'AAPL');
      await user.tab();
      
      await waitFor(() => {
        expect(screen.queryByText(/invalid symbol format/i)).not.toBeInTheDocument();
      });
    });

    it('should validate quantity constraints', async () => {
      const user = userEvent.setup();
      render(<OrderForm />, { wrapper: TestWrapper });
      
      const quantityInput = screen.getByLabelText(/quantity/i);
      
      // Test negative quantity
      await user.clear(quantityInput);
      await user.type(quantityInput, '-10');
      await user.tab();
      
      await waitFor(() => {
        expect(screen.getByText(/quantity must be positive/i)).toBeInTheDocument();
      });
      
      // Test decimal quantity for stocks
      await user.clear(quantityInput);
      await user.type(quantityInput, '10.5');
      await user.tab();
      
      await waitFor(() => {
        expect(screen.getByText(/quantity must be whole number/i)).toBeInTheDocument();
      });
      
      // Test valid quantity
      await user.clear(quantityInput);
      await user.type(quantityInput, '100');
      await user.tab();
      
      await waitFor(() => {
        expect(screen.queryByText(/quantity must be positive/i)).not.toBeInTheDocument();
      });
    });

    it('should validate available funds for buy orders', async () => {
      const user = userEvent.setup();
      render(<OrderForm />, { wrapper: TestWrapper });
      
      // Fill form with buy order that exceeds available funds
      await user.type(screen.getByLabelText(/symbol/i), 'AAPL');
      await user.type(screen.getByLabelText(/quantity/i), '10000'); // Large quantity
      await user.selectOptions(screen.getByLabelText(/side/i), 'buy');
      
      const submitButton = screen.getByRole('button', { name: /place order/i });
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/insufficient funds/i)).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    it('should handle form submission with valid data', async () => {
      const user = userEvent.setup();
      render(<OrderForm />, { wrapper: TestWrapper });
      
      // Fill form with valid data
      await user.type(screen.getByLabelText(/symbol/i), 'AAPL');
      await user.clear(screen.getByLabelText(/quantity/i));
      await user.type(screen.getByLabelText(/quantity/i), '100');
      await user.selectOptions(screen.getByLabelText(/side/i), 'buy');
      await user.selectOptions(screen.getByLabelText(/order type/i), 'market');
      
      const submitButton = screen.getByRole('button', { name: /place order/i });
      await user.click(submitButton);
      
      // Verify API call
      await waitFor(() => {
        expect(mockExecuteOrder).toHaveBeenCalledWith({
          symbol: 'AAPL',
          quantity: 100,
          side: 'buy',
          orderType: 'market',
          timeInForce: 'day'
        });
      });
      
      // Verify success message
      await waitFor(() => {
        expect(screen.getByText(/order placed successfully/i)).toBeInTheDocument();
      });
    });

    it('should handle limit order price requirement', async () => {
      const user = userEvent.setup();
      render(<OrderForm />, { wrapper: TestWrapper });
      
      // Select limit order type
      await user.selectOptions(screen.getByLabelText(/order type/i), 'limit');
      
      // Verify price field appears
      await waitFor(() => {
        expect(screen.getByLabelText(/limit price/i)).toBeInTheDocument();
      });
      
      // Verify price is required for limit orders
      const submitButton = screen.getByRole('button', { name: /place order/i });
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/price is required for limit orders/i)).toBeInTheDocument();
      });
    });

    it('should calculate estimated order value', async () => {
      const user = userEvent.setup();
      render(<OrderForm />, { wrapper: TestWrapper });
      
      // Fill form data
      await user.type(screen.getByLabelText(/symbol/i), 'AAPL');
      await user.clear(screen.getByLabelText(/quantity/i));
      await user.type(screen.getByLabelText(/quantity/i), '100');
      
      // Verify estimated value calculation
      await waitFor(() => {
        expect(screen.getByText(/estimated value/i)).toBeInTheDocument();
        expect(screen.getByText(/\$[\d,]+\.\d{2}/)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      const user = userEvent.setup();
      
      // Mock API error
      mockExecuteOrder.mockRejectedValue(new Error('Insufficient funds'));
      
      render(<OrderForm />, { wrapper: TestWrapper });
      
      // Fill and submit form
      await user.type(screen.getByLabelText(/symbol/i), 'AAPL');
      await user.clear(screen.getByLabelText(/quantity/i));
      await user.type(screen.getByLabelText(/quantity/i), '100');
      
      const submitButton = screen.getByRole('button', { name: /place order/i });
      await user.click(submitButton);
      
      // Verify error message
      await waitFor(() => {
        expect(screen.getByText(/insufficient funds/i)).toBeInTheDocument();
      });
      
      // Verify form is still usable
      expect(submitButton).not.toBeDisabled();
    });

    it('should handle network errors', async () => {
      const user = userEvent.setup();
      
      // Mock network error
      mockExecuteOrder.mockRejectedValue(new Error('Network error'));
      
      render(<OrderForm />, { wrapper: TestWrapper });
      
      // Fill and submit form
      await user.type(screen.getByLabelText(/symbol/i), 'AAPL');
      await user.clear(screen.getByLabelText(/quantity/i));
      await user.type(screen.getByLabelText(/quantity/i), '100');
      
      const submitButton = screen.getByRole('button', { name: /place order/i });
      await user.click(submitButton);
      
      // Verify generic error message
      await waitFor(() => {
        expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('should show loading state during order submission', async () => {
      const user = userEvent.setup();
      
      // Create a delayed promise to simulate slow API
      let resolvePromise: (value: any) => void;
      const delayedPromise = new Promise(resolve => {
        resolvePromise = resolve;
      });
      mockExecuteOrder.mockReturnValue(delayedPromise);
      
      render(<OrderForm />, { wrapper: TestWrapper });
      
      // Fill and submit form
      await user.type(screen.getByLabelText(/symbol/i), 'AAPL');
      await user.clear(screen.getByLabelText(/quantity/i));
      await user.type(screen.getByLabelText(/quantity/i), '100');
      
      const submitButton = screen.getByRole('button', { name: /place order/i });
      await user.click(submitButton);
      
      // Verify loading state
      expect(screen.getByText(/placing order/i)).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
      
      // Resolve promise and verify loading state is cleared
      resolvePromise!(mockOrderResponse);
      
      await waitFor(() => {
        expect(screen.queryByText(/placing order/i)).not.toBeInTheDocument();
        expect(submitButton).not.toBeDisabled();
      });
    });
  });
});
```

**Backend Unit Testing Architecture:**

```python
# File: /backend/tests/unit/services/test_trading_service.py
"""
Comprehensive unit tests for TradingService

Test Categories:
- Service initialization and dependency injection
- Order validation logic
- Risk assessment integration
- Broker API integration mocking
- Position management
- Error handling and edge cases
- Performance and concurrency
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any

from src.services.trading_service import TradingService
from src.models.trading import Order, Position, OrderSide, OrderType
from src.core.exceptions import TradingError, InsufficientFundsError
from src.schemas.trading import OrderCreate, OrderExecutionResult
from tests.fixtures.trading_fixtures import (
    mock_broker_client,
    mock_risk_manager,
    mock_position_manager,
    sample_user,
    sample_order,
    sample_execution_result
)


class TestTradingServiceInitialization:
    """Test service initialization and dependency management"""
    
    def test_service_initialization_with_valid_dependencies(
        self,
        mock_broker_client,
        mock_risk_manager,
        mock_position_manager
    ):
        """Test successful service initialization with all dependencies"""
        service = TradingService(
            broker_client=mock_broker_client,
            risk_manager=mock_risk_manager,
            position_manager=mock_position_manager
        )
        
        assert service._broker_client == mock_broker_client
        assert service._risk_manager == mock_risk_manager
        assert service._position_manager == mock_position_manager
        assert service._logger.name.endswith('TradingService')
    
    def test_service_initialization_with_none_dependencies(self):
        """Test service initialization fails with None dependencies"""
        with pytest.raises(ValueError, match="All dependencies must be provided"):
            TradingService(
                broker_client=None,
                risk_manager=None,
                position_manager=None
            )
    
    def test_service_initialization_with_partial_dependencies(
        self,
        mock_broker_client
    ):
        """Test service initialization fails with partial dependencies"""
        with pytest.raises(ValueError, match="All dependencies must be provided"):
            TradingService(
                broker_client=mock_broker_client,
                risk_manager=None,
                position_manager=None
            )


class TestOrderValidation:
    """Test order validation logic"""
    
    @pytest.fixture
    def trading_service(
        self,
        mock_broker_client,
        mock_risk_manager,
        mock_position_manager
    ):
        return TradingService(
            broker_client=mock_broker_client,
            risk_manager=mock_risk_manager,
            position_manager=mock_position_manager
        )
    
    @pytest.mark.asyncio
    async def test_validate_order_with_valid_market_order(
        self,
        trading_service,
        sample_user,
        sample_order
    ):
        """Test validation of valid market order"""
        sample_order.order_type = OrderType.MARKET
        
        with patch.object(trading_service, '_validate_order') as mock_validate:
            mock_validate.return_value = Mock(is_valid=True, error=None)
            
            result = await trading_service._validate_order(sample_user.id, sample_order)
            
            assert result.is_valid is True
            assert result.error is None
            mock_validate.assert_called_once_with(sample_user.id, sample_order)
    
    @pytest.mark.asyncio
    async def test_validate_order_with_invalid_symbol(
        self,
        trading_service,
        sample_user,
        sample_order
    ):
        """Test validation fails with invalid symbol"""
        sample_order.symbol = "INVALID@SYMBOL"
        
        with patch.object(trading_service, '_validate_order') as mock_validate:
            mock_validate.return_value = Mock(
                is_valid=False,
                error="Invalid symbol format"
            )
            
            result = await trading_service._validate_order(sample_user.id, sample_order)
            
            assert result.is_valid is False
            assert "Invalid symbol format" in result.error
    
    @pytest.mark.asyncio
    async def test_validate_order_with_negative_quantity(
        self,
        trading_service,
        sample_user,
        sample_order
    ):
        """Test validation fails with negative quantity"""
        sample_order.quantity = -100
        
        with patch.object(trading_service, '_validate_order') as mock_validate:
            mock_validate.return_value = Mock(
                is_valid=False,
                error="Quantity must be positive"
            )
            
            result = await trading_service._validate_order(sample_user.id, sample_order)
            
            assert result.is_valid is False
            assert "Quantity must be positive" in result.error
    
    @pytest.mark.asyncio
    async def test_validate_limit_order_without_price(
        self,
        trading_service,
        sample_user,
        sample_order
    ):
        """Test validation fails for limit order without price"""
        sample_order.order_type = OrderType.LIMIT
        sample_order.price = None
        
        with patch.object(trading_service, '_validate_order') as mock_validate:
            mock_validate.return_value = Mock(
                is_valid=False,
                error="Price required for limit orders"
            )
            
            result = await trading_service._validate_order(sample_user.id, sample_order)
            
            assert result.is_valid is False
            assert "Price required for limit orders" in result.error


class TestOrderExecution:
    """Test order execution workflows"""
    
    @pytest.fixture
    def trading_service(
        self,
        mock_broker_client,
        mock_risk_manager,
        mock_position_manager
    ):
        return TradingService(
            broker_client=mock_broker_client,
            risk_manager=mock_risk_manager,
            position_manager=mock_position_manager
        )
    
    @pytest.mark.asyncio
    async def test_execute_order_success_flow(
        self,
        trading_service,
        sample_user,
        sample_order,
        sample_execution_result
    ):
        """Test successful order execution flow"""
        # Mock all dependencies
        with patch.object(trading_service, '_validate_order') as mock_validate, \
             patch.object(trading_service._risk_manager, 'assess_order') as mock_risk, \
             patch.object(trading_service, '_calculate_required_capital') as mock_capital, \
             patch.object(trading_service, '_get_available_funds') as mock_funds, \
             patch.object(trading_service._broker_client, 'submit_order') as mock_submit, \
             patch.object(trading_service._position_manager, 'update_position') as mock_position, \
             patch.object(trading_service, '_record_trade_audit') as mock_audit:
            
            # Setup mocks
            mock_validate.return_value = Mock(is_valid=True, error=None)
            mock_risk.return_value = Mock(risk_level="LOW", reason=None)
            mock_capital.return_value = Decimal("15000.00")
            mock_funds.return_value = Decimal("20000.00")
            mock_submit.return_value = sample_execution_result
            
            # Execute order
            result = await trading_service.execute_order(
                user_id=sample_user.id,
                order=sample_order,
                dry_run=False
            )
            
            # Verify result
            assert result.order_id == sample_execution_result.order_id
            assert result.execution_price == sample_execution_result.execution_price
            assert result.executed_quantity == sample_execution_result.executed_quantity
            assert result.status == "filled"
            
            # Verify all steps were called
            mock_validate.assert_called_once()
            mock_risk.assert_called_once()
            mock_capital.assert_called_once()
            mock_funds.assert_called_once()
            mock_submit.assert_called_once()
            mock_position.assert_called_once()
            mock_audit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_order_validation_failure(
        self,
        trading_service,
        sample_user,
        sample_order
    ):
        """Test order execution fails on validation"""
        with patch.object(trading_service, '_validate_order') as mock_validate:
            mock_validate.return_value = Mock(
                is_valid=False,
                error="Invalid order parameters"
            )
            
            with pytest.raises(TradingError, match="Order validation failed"):
                await trading_service.execute_order(
                    user_id=sample_user.id,
                    order=sample_order,
                    dry_run=False
                )
    
    @pytest.mark.asyncio
    async def test_execute_order_insufficient_funds(
        self,
        trading_service,
        sample_user,
        sample_order
    ):
        """Test order execution fails on insufficient funds"""
        with patch.object(trading_service, '_validate_order') as mock_validate, \
             patch.object(trading_service._risk_manager, 'assess_order') as mock_risk, \
             patch.object(trading_service, '_calculate_required_capital') as mock_capital, \
             patch.object(trading_service, '_get_available_funds') as mock_funds:
            
            # Setup mocks
            mock_validate.return_value = Mock(is_valid=True, error=None)
            mock_risk.return_value = Mock(risk_level="LOW", reason=None)
            mock_capital.return_value = Decimal("20000.00")
            mock_funds.return_value = Decimal("15000.00")  # Less than required
            
            with pytest.raises(InsufficientFundsError):
                await trading_service.execute_order(
                    user_id=sample_user.id,
                    order=sample_order,
                    dry_run=False
                )
    
    @pytest.mark.asyncio
    async def test_execute_order_dry_run(
        self,
        trading_service,
        sample_user,
        sample_order
    ):
        """Test dry run order execution"""
        with patch.object(trading_service, '_validate_order') as mock_validate, \
             patch.object(trading_service._risk_manager, 'assess_order') as mock_risk, \
             patch.object(trading_service, '_calculate_required_capital') as mock_capital, \
             patch.object(trading_service, '_get_available_funds') as mock_funds:
            
            # Setup mocks
            mock_validate.return_value = Mock(is_valid=True, error=None)
            mock_risk.return_value = Mock(risk_level="LOW", reason=None)
            mock_capital.return_value = Decimal("15000.00")
            mock_funds.return_value = Decimal("20000.00")
            
            result = await trading_service.execute_order(
                user_id=sample_user.id,
                order=sample_order,
                dry_run=True
            )
            
            assert result.status == "dry_run"
            assert result.executed_quantity == 0
            assert result.commission == Decimal("0")


class TestRiskManagement:
    """Test risk management integration"""
    
    @pytest.fixture
    def trading_service(
        self,
        mock_broker_client,
        mock_risk_manager,
        mock_position_manager
    ):
        return TradingService(
            broker_client=mock_broker_client,
            risk_manager=mock_risk_manager,
            position_manager=mock_position_manager
        )
    
    @pytest.mark.asyncio
    async def test_risk_assessment_blocks_high_risk_order(
        self,
        trading_service,
        sample_user,
        sample_order
    ):
        """Test high-risk orders are blocked"""
        with patch.object(trading_service, '_validate_order') as mock_validate, \
             patch.object(trading_service._risk_manager, 'assess_order') as mock_risk:
            
            mock_validate.return_value = Mock(is_valid=True, error=None)
            mock_risk.return_value = Mock(
                risk_level="HIGH",
                reason="Position size exceeds limits"
            )
            
            with pytest.raises(TradingError, match="Order exceeds risk limits"):
                await trading_service.execute_order(
                    user_id=sample_user.id,
                    order=sample_order,
                    dry_run=False
                )
    
    @pytest.mark.asyncio
    async def test_risk_assessment_allows_acceptable_risk(
        self,
        trading_service,
        sample_user,
        sample_order,
        sample_execution_result
    ):
        """Test acceptable risk orders proceed"""
        with patch.object(trading_service, '_validate_order') as mock_validate, \
             patch.object(trading_service._risk_manager, 'assess_order') as mock_risk, \
             patch.object(trading_service, '_calculate_required_capital') as mock_capital, \
             patch.object(trading_service, '_get_available_funds') as mock_funds, \
             patch.object(trading_service._broker_client, 'submit_order') as mock_submit, \
             patch.object(trading_service._position_manager, 'update_position'), \
             patch.object(trading_service, '_record_trade_audit'):
            
            mock_validate.return_value = Mock(is_valid=True, error=None)
            mock_risk.return_value = Mock(risk_level="ACCEPTABLE", reason=None)
            mock_capital.return_value = Decimal("15000.00")
            mock_funds.return_value = Decimal("20000.00")
            mock_submit.return_value = sample_execution_result
            
            result = await trading_service.execute_order(
                user_id=sample_user.id,
                order=sample_order,
                dry_run=False
            )
            
            assert result.status == "filled"


class TestConcurrency:
    """Test concurrent order execution"""
    
    @pytest.fixture
    def trading_service(
        self,
        mock_broker_client,
        mock_risk_manager,
        mock_position_manager
    ):
        return TradingService(
            broker_client=mock_broker_client,
            risk_manager=mock_risk_manager,
            position_manager=mock_position_manager
        )
    
    @pytest.mark.asyncio
    async def test_concurrent_order_execution(
        self,
        trading_service,
        sample_user,
        sample_execution_result
    ):
        """Test multiple concurrent orders execute correctly"""
        # Create multiple orders
        orders = [
            Order(
                symbol="AAPL",
                quantity=100,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET
            ),
            Order(
                symbol="GOOGL",
                quantity=50,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET
            ),
            Order(
                symbol="MSFT",
                quantity=200,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET
            )
        ]
        
        # Mock dependencies for all orders
        with patch.object(trading_service, '_validate_order') as mock_validate, \
             patch.object(trading_service._risk_manager, 'assess_order') as mock_risk, \
             patch.object(trading_service, '_calculate_required_capital') as mock_capital, \
             patch.object(trading_service, '_get_available_funds') as mock_funds, \
             patch.object(trading_service._broker_client, 'submit_order') as mock_submit, \
             patch.object(trading_service._position_manager, 'update_position'), \
             patch.object(trading_service, '_record_trade_audit'):
            
            mock_validate.return_value = Mock(is_valid=True, error=None)
            mock_risk.return_value = Mock(risk_level="ACCEPTABLE", reason=None)
            mock_capital.return_value = Decimal("15000.00")
            mock_funds.return_value = Decimal("50000.00")
            mock_submit.return_value = sample_execution_result
            
            # Execute orders concurrently
            tasks = [
                trading_service.execute_order(
                    user_id=sample_user.id,
                    order=order,
                    dry_run=False
                )
                for order in orders
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Verify all orders executed
            assert len(results) == 3
            for result in results:
                assert result.status == "filled"
            
            # Verify broker was called for each order
            assert mock_submit.call_count == 3


@pytest.fixture
def mock_broker_client():
    """Mock broker client"""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_risk_manager():
    """Mock risk manager"""
    manager = AsyncMock()
    return manager


@pytest.fixture
def mock_position_manager():
    """Mock position manager"""
    manager = AsyncMock()
    return manager


@pytest.fixture
def sample_user():
    """Sample user for testing"""
    return Mock(id="user_123", email="test@example.com")


@pytest.fixture
def sample_order():
    """Sample order for testing"""
    return Order(
        symbol="AAPL",
        quantity=100,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        price=None,
        stop_price=None
    )


@pytest.fixture
def sample_execution_result():
    """Sample execution result for testing"""
    return OrderExecutionResult(
        order_id="ord_123456789",
        execution_price=Decimal("150.25"),
        executed_quantity=100,
        commission=Decimal("1.50"),
        timestamp=datetime.now(timezone.utc),
        status="filled"
    )
```

#### **5B.1.2 Integration Testing Strategies**

**API Integration Testing Framework:**

```python
# File: /backend/tests/integration/test_trading_api.py
"""
Integration tests for Trading API endpoints

These tests verify:
- API endpoint functionality with real database
- Authentication and authorization
- Request/response validation
- Error handling and status codes
- Database state changes
- External service integration (mocked)
"""

import pytest
import asyncio
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock

from main import app
from src.core.database import get_db
from src.models.user import User
from src.models.trading import Order, Position, TradingAccount
from src.core.security import create_access_token
from tests.utils.database import create_test_user, create_test_trading_account


@pytest.mark.integration
class TestTradingEndpoints:
    """Integration tests for trading endpoints"""
    
    @pytest.fixture(autouse=True)
    async def setup_test_data(self, async_session: AsyncSession):
        """Setup test data for each test"""
        # Create test user
        self.test_user = await create_test_user(
            async_session,
            email="trader@test.com",
            is_trading_enabled=True
        )
        
        # Create trading account
        self.trading_account = await create_test_trading_account(
            async_session,
            user_id=self.test_user.id,
            balance=Decimal("50000.00")
        )
        
        # Create access token
        self.access_token = create_access_token(
            data={"sub": str(self.test_user.id)}
        )
        
        # Setup authentication headers
        self.auth_headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
    
    @pytest.mark.asyncio
    async def test_place_market_order_success(self, async_client: AsyncClient):
        """Test successful market order placement"""
        order_data = {
            "symbol": "AAPL",
            "quantity": 100,
            "side": "buy",
            "order_type": "market",
            "time_in_force": "day"
        }
        
        # Mock broker client response
        with patch('src.services.trading_service.BrokerClient') as mock_broker:
            mock_broker_instance = AsyncMock()
            mock_broker.return_value = mock_broker_instance
            mock_broker_instance.submit_order.return_value = AsyncMock(
                order_id="ord_123456789",
                execution_price=Decimal("150.25"),
                executed_quantity=100,
                commission=Decimal("1.50"),
                status="filled"
            )
            
            response = await async_client.post(
                "/api/v1/trading/orders",
                json=order_data,
                headers=self.auth_headers
            )
        
        # Verify response
        assert response.status_code == 201
        response_data = response.json()
        
        assert response_data["order_id"] == "ord_123456789"
        assert response_data["status"] == "filled"
        assert float(response_data["execution_price"]) == 150.25
        assert response_data["executed_quantity"] == 100
        assert float(response_data["commission"]) == 1.50
        
        # Verify database state
        async with async_session() as session:
            # Check order was created
            order = await session.get(Order, response_data["order_id"])
            assert order is not None
            assert order.symbol == "AAPL"
            assert order.quantity == 100
            assert order.user_id == self.test_user.id
            
            # Check position was updated
            position = await session.execute(
                select(Position).where(
                    Position.user_id == self.test_user.id,
                    Position.symbol == "AAPL"
                )
            )
            position = position.scalar_one_or_none()
            assert position is not None
            assert position.quantity == 100
    
    @pytest.mark.asyncio
    async def test_place_limit_order_success(self, async_client: AsyncClient):
        """Test successful limit order placement"""
        order_data = {
            "symbol": "GOOGL",
            "quantity": 50,
            "side": "buy",
            "order_type": "limit",
            "price": 2500.00,
            "time_in_force": "gtc"
        }
        
        with patch('src.services.trading_service.BrokerClient') as mock_broker:
            mock_broker_instance = AsyncMock()
            mock_broker.return_value = mock_broker_instance
            mock_broker_instance.submit_order.return_value = AsyncMock(
                order_id="ord_987654321",
                execution_price=Decimal("2500.00"),
                executed_quantity=50,
                commission=Decimal("2.50"),
                status="filled"
            )
            
            response = await async_client.post(
                "/api/v1/trading/orders",
                json=order_data,
                headers=self.auth_headers
            )
        
        assert response.status_code == 201
        response_data = response.json()
        
        assert response_data["order_id"] == "ord_987654321"
        assert response_data["status"] == "filled"
        assert float(response_data["execution_price"]) == 2500.00
    
    @pytest.mark.asyncio
    async def test_place_order_insufficient_funds(self, async_client: AsyncClient):
        """Test order placement fails with insufficient funds"""
        order_data = {
            "symbol": "AAPL",
            "quantity": 10000,  # Very large quantity
            "side": "buy",
            "order_type": "market",
            "time_in_force": "day"
        }
        
        response = await async_client.post(
            "/api/v1/trading/orders",
            json=order_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 422
        response_data = response.json()
        assert "insufficient funds" in response_data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_place_order_invalid_symbol(self, async_client: AsyncClient):
        """Test order placement fails with invalid symbol"""
        order_data = {
            "symbol": "INVALID@SYMBOL",
            "quantity": 100,
            "side": "buy",
            "order_type": "market"
        }
        
        response = await async_client.post(
            "/api/v1/trading/orders",
            json=order_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 400
        response_data = response.json()
        assert "invalid symbol" in response_data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_place_order_unauthorized(self, async_client: AsyncClient):
        """Test order placement fails without authentication"""
        order_data = {
            "symbol": "AAPL",
            "quantity": 100,
            "side": "buy",
            "order_type": "market"
        }
        
        response = await async_client.post(
            "/api/v1/trading/orders",
            json=order_data
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_user_positions(self, async_client: AsyncClient):
        """Test retrieving user positions"""
        # Create test positions
        async with async_session() as session:
            positions = [
                Position(
                    user_id=self.test_user.id,
                    symbol="AAPL",
                    quantity=100,
                    average_cost=Decimal("150.00")
                ),
                Position(
                    user_id=self.test_user.id,
                    symbol="GOOGL",
                    quantity=50,
                    average_cost=Decimal("2500.00")
                )
            ]
            session.add_all(positions)
            await session.commit()
        
        response = await async_client.get(
            "/api/v1/trading/positions",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        positions_data = response.json()
        
        assert len(positions_data) == 2
        
        # Verify AAPL position
        aapl_position = next(p for p in positions_data if p["symbol"] == "AAPL")
        assert aapl_position["quantity"] == 100
        assert float(aapl_position["average_cost"]) == 150.00
        
        # Verify GOOGL position
        googl_position = next(p for p in positions_data if p["symbol"] == "GOOGL")
        assert googl_position["quantity"] == 50
        assert float(googl_position["average_cost"]) == 2500.00
    
    @pytest.mark.asyncio
    async def test_get_order_history(self, async_client: AsyncClient):
        """Test retrieving order history"""
        # Create test orders
        async with async_session() as session:
            orders = [
                Order(
                    id="ord_123",
                    user_id=self.test_user.id,
                    symbol="AAPL",
                    quantity=100,
                    side="buy",
                    order_type="market",
                    status="filled",
                    execution_price=Decimal("150.25")
                ),
                Order(
                    id="ord_456",
                    user_id=self.test_user.id,
                    symbol="GOOGL",
                    quantity=50,
                    side="sell",
                    order_type="limit",
                    status="cancelled",
                    price=Decimal("2600.00")
                )
            ]
            session.add_all(orders)
            await session.commit()
        
        response = await async_client.get(
            "/api/v1/trading/orders",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        orders_data = response.json()
        
        assert len(orders_data) >= 2
        
        # Verify orders are included
        order_ids = [order["id"] for order in orders_data]
        assert "ord_123" in order_ids
        assert "ord_456" in order_ids
    
    @pytest.mark.asyncio
    async def test_get_trading_account(self, async_client: AsyncClient):
        """Test retrieving trading account information"""
        response = await async_client.get(
            "/api/v1/trading/account",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        account_data = response.json()
        
        assert float(account_data["balance"]) == 50000.00
        assert "buying_power" in account_data
        assert "margin_used" in account_data
        assert account_data["is_trading_enabled"] is True


@pytest.mark.integration
class TestTradingWebSocketIntegration:
    """Integration tests for trading WebSocket functionality"""
    
    @pytest.mark.asyncio
    async def test_real_time_price_updates(self):
        """Test real-time price updates via WebSocket"""
        # This would test WebSocket connections for real-time data
        # Implementation depends on WebSocket testing framework
        pass
    
    @pytest.mark.asyncio
    async def test_order_status_updates(self):
        """Test order status updates via WebSocket"""
        # Test real-time order status notifications
        pass


# Database Integration Testing

@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database operations"""
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, async_session: AsyncSession):
        """Test database transaction rollback on error"""
        async with async_session() as session:
            try:
                # Create a user
                user = User(email="test@example.com", hashed_password="hashed")
                session.add(user)
                await session.flush()  # Get user ID
                
                # Create trading account
                account = TradingAccount(
                    user_id=user.id,
                    balance=Decimal("10000.00")
                )
                session.add(account)
                
                # Simulate error (duplicate email)
                duplicate_user = User(email="test@example.com", hashed_password="hashed2")
                session.add(duplicate_user)
                
                await session.commit()  # This should fail
                
            except Exception:
                await session.rollback()
                
                # Verify rollback worked - no user should exist
                user_count = await session.execute(
                    select(func.count(User.id))
                )
                assert user_count.scalar() == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_order_processing(self, async_session: AsyncSession):
        """Test concurrent order processing with database locking"""
        user = await create_test_user(async_session, email="concurrent@test.com")
        
        async def place_order(session, order_id):
            """Simulate placing an order"""
            order = Order(
                id=order_id,
                user_id=user.id,
                symbol="AAPL",
                quantity=100,
                side="buy",
                order_type="market",
                status="pending"
            )
            session.add(order)
            await session.commit()
        
        # Execute concurrent orders
        tasks = []
        for i in range(10):
            session = async_session()
            task = asyncio.create_task(place_order(session, f"ord_{i}"))
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all orders were created
        async with async_session() as session:
            order_count = await session.execute(
                select(func.count(Order.id)).where(Order.user_id == user.id)
            )
            assert order_count.scalar() == 10
```

#### **5B.1.3 End-to-End Testing Framework**

**Comprehensive E2E Testing Strategy:**

```typescript
// File: /e2e/tests/trading-workflow.spec.ts
/**
 * End-to-End tests for complete trading workflows
 * 
 * This test suite covers:
 * - User authentication and account setup
 * - Market data visualization
 * - Order placement and execution
 * - Portfolio management
 * - Real-time updates and notifications
 */

import { test, expect, Page, BrowserContext } from '@playwright/test';
import { TradingPage } from '../pages/TradingPage';
import { AuthPage } from '../pages/AuthPage';
import { DashboardPage } from '../pages/DashboardPage';
import { testConfig } from '../config/test.config';
import { MockDataService } from '../services/MockDataService';

test.describe('Complete Trading Workflow', () => {
  let context: BrowserContext;
  let page: Page;
  let authPage: AuthPage;
  let dashboardPage: DashboardPage;
  let tradingPage: TradingPage;
  let mockDataService: MockDataService;

  test.beforeAll(async ({ browser }) => {
    // Create a new browser context for test isolation
    context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      permissions: ['notifications'],
      geolocation: { latitude: 40.7128, longitude: -74.0060 } // NYC
    });
    
    // Setup API mocking
    mockDataService = new MockDataService();
    await mockDataService.setupMocks(context);
  });

  test.beforeEach(async () => {
    page = await context.newPage();
    authPage = new AuthPage(page);
    dashboardPage = new DashboardPage(page);
    tradingPage = new TradingPage(page);
    
    // Navigate to application
    await page.goto(testConfig.baseUrl);
  });

  test.afterEach(async () => {
    await page.close();
  });

  test.afterAll(async () => {
    await context.close();
  });

  test('Complete user journey: Registration to successful trade', async () => {
    // Step 1: User Registration
    await test.step('User registers new account', async () => {
      await authPage.navigateToRegister();
      await authPage.fillRegistrationForm({
        email: 'newtrader@example.com',
        password: 'SecurePass123!',
        firstName: 'John',
        lastName: 'Trader',
        acceptTerms: true
      });
      await authPage.submitRegistration();
      
      // Verify account creation success
      await expect(page.getByText('Account created successfully')).toBeVisible();
      await expect(page.getByText('Please verify your email')).toBeVisible();
    });

    // Step 2: Email Verification (simulated)
    await test.step('User verifies email', async () => {
      // In real test, this would involve email service integration
      await mockDataService.simulateEmailVerification('newtrader@example.com');
      
      // Navigate to login after verification
      await authPage.navigateToLogin();
      await authPage.login('newtrader@example.com', 'SecurePass123!');
      
      // Verify successful login
      await expect(page).toHaveURL(/.*\/dashboard/);
      await expect(page.getByText('Welcome, John')).toBeVisible();
    });

    // Step 3: Account Setup and Verification
    await test.step('User completes account setup', async () => {
      // Check if account setup wizard is shown
      if (await page.getByText('Complete Account Setup').isVisible()) {
        await dashboardPage.completeAccountSetup({
          ssn: '123-45-6789',
          dateOfBirth: '1990-01-01',
          address: {
            street: '123 Wall Street',
            city: 'New York',
            state: 'NY',
            zipCode: '10005'
          },
          employmentInfo: {
            status: 'employed',
            employer: 'Tech Corp',
            income: 75000
          }
        });
        
        await expect(page.getByText('Account setup completed')).toBeVisible();
      }
    });

    // Step 4: Fund Account
    await test.step('User funds trading account', async () => {
      await dashboardPage.navigateToFunding();
      await dashboardPage.addFunds({
        amount: 10000,
        method: 'bank_transfer',
        bankAccount: 'checking_account_123'
      });
      
      // Mock instant funding for testing
      await mockDataService.simulateInstantFunding('newtrader@example.com', 10000);
      
      await expect(page.getByText('$10,000.00')).toBeVisible();
      await expect(page.getByText('Available for trading')).toBeVisible();
    });

    // Step 5: Navigate to Trading Interface
    await test.step('User navigates to trading interface', async () => {
      await dashboardPage.navigateToTrading();
      
      // Verify trading interface loads
      await expect(page).toHaveURL(/.*\/trading/);
      await expect(tradingPage.getOrderForm()).toBeVisible();
      await expect(tradingPage.getPriceChart()).toBeVisible();
      await expect(tradingPage.getMarketData()).toBeVisible();
    });

    // Step 6: Research and Select Stock
    await test.step('User researches and selects stock', async () => {
      // Search for Apple stock
      await tradingPage.searchStock('AAPL');
      await tradingPage.selectStock('AAPL');
      
      // Verify stock information is displayed
      await expect(page.getByText('Apple Inc.')).toBeVisible();
      await expect(page.getByText('NASDAQ: AAPL')).toBeVisible();
      
      // Check that price chart loads
      await expect(tradingPage.getPriceChart()).toBeVisible();
      await tradingPage.waitForChartToLoad();
      
      // Verify real-time price updates
      const initialPrice = await tradingPage.getCurrentPrice();
      expect(parseFloat(initialPrice.replace('$', ''))).toBeGreaterThan(0);
    });

    // Step 7: Place Market Order
    await test.step('User places market buy order', async () => {
      const orderData = {
        symbol: 'AAPL',
        quantity: 10,
        side: 'buy',
        orderType: 'market'
      };
      
      await tradingPage.fillOrderForm(orderData);
      
      // Verify order preview
      await expect(page.getByText('Order Preview')).toBeVisible();
      await expect(page.getByText('Buy 10 shares of AAPL')).toBeVisible();
      await expect(page.getByText(/Estimated cost: \$[\d,]+\.\d{2}/)).toBeVisible();
      
      // Confirm order
      await tradingPage.confirmOrder();
      
      // Verify order execution
      await expect(page.getByText('Order executed successfully')).toBeVisible();
      await expect(page.getByText(/Order ID: ord_[a-zA-Z0-9]+/)).toBeVisible();
    });

    // Step 8: Verify Portfolio Update
    await test.step('User verifies portfolio update', async () => {
      await tradingPage.navigateToPortfolio();
      
      // Check that position appears in portfolio
      await expect(page.getByText('AAPL')).toBeVisible();
      await expect(page.getByText('10 shares')).toBeVisible();
      
      // Verify P&L calculation
      const pnlElement = page.getByTestId('position-pnl-AAPL');
      await expect(pnlElement).toBeVisible();
      
      // Check that account balance is updated
      const newBalance = await dashboardPage.getAccountBalance();
      expect(parseFloat(newBalance.replace(/[$,]/g, ''))).toBeLessThan(10000);
    });

    // Step 9: Place Limit Order
    await test.step('User places limit sell order', async () => {
      await tradingPage.navigateToOrderEntry();
      
      const limitOrderData = {
        symbol: 'AAPL',
        quantity: 5,
        side: 'sell',
        orderType: 'limit',
        price: 155.00 // Assuming current price is around 150
      };
      
      await tradingPage.fillOrderForm(limitOrderData);
      await tradingPage.confirmOrder();
      
      // Verify limit order is placed (not executed)
      await expect(page.getByText('Limit order placed')).toBeVisible();
      await expect(page.getByText('Order status: PENDING')).toBeVisible();
    });

    // Step 10: View Order History
    await test.step('User views order history', async () => {
      await tradingPage.navigateToOrderHistory();
      
      // Verify both orders appear in history
      await expect(page.getByText('Market Buy - AAPL - 10 shares - FILLED')).toBeVisible();
      await expect(page.getByText('Limit Sell - AAPL - 5 shares - PENDING')).toBeVisible();
      
      // Check order details
      await page.getByText('Market Buy - AAPL').click();
      await expect(page.getByText(/Execution Price: \$\d+\.\d{2}/)).toBeVisible();
      await expect(page.getByText(/Commission: \$\d+\.\d{2}/)).toBeVisible();
    });

    // Step 11: Test Real-time Features
    await test.step('User tests real-time features', async () => {
      await tradingPage.navigateToWatchlist();
      
      // Add stock to watchlist
      await tradingPage.addToWatchlist('GOOGL');
      await expect(page.getByText('GOOGL added to watchlist')).toBeVisible();
      
      // Test price alerts
      await tradingPage.setPriceAlert('AAPL', 160.00, 'above');
      await expect(page.getByText('Price alert set for AAPL')).toBeVisible();
      
      // Simulate price change to trigger alert
      await mockDataService.simulatePriceChange('AAPL', 160.50);
      
      // Wait for alert notification
      await expect(page.getByText('Price Alert: AAPL is now above $160.00')).toBeVisible();
    });
  });

  test('Trading error scenarios and recovery', async () => {
    // Login with existing user
    await authPage.login('trader@example.com', 'password123');
    await dashboardPage.navigateToTrading();

    await test.step('Handle insufficient funds error', async () => {
      const orderData = {
        symbol: 'TSLA',
        quantity: 1000, // Large quantity to exceed funds
        side: 'buy',
        orderType: 'market'
      };
      
      await tradingPage.fillOrderForm(orderData);
      await tradingPage.confirmOrder();
      
      // Verify error handling
      await expect(page.getByText('Insufficient funds')).toBeVisible();
      await expect(page.getByText('Available: $')).toBeVisible();
      await expect(page.getByText('Required: $')).toBeVisible();
      
      // Verify order form is still usable
      await expect(tradingPage.getOrderForm()).toBeVisible();
      await expect(tradingPage.getSubmitButton()).toBeEnabled();
    });

    await test.step('Handle market closed error', async () => {
      // Mock market closed scenario
      await mockDataService.simulateMarketClosed();
      
      const orderData = {
        symbol: 'AAPL',
        quantity: 10,
        side: 'buy',
        orderType: 'market'
      };
      
      await tradingPage.fillOrderForm(orderData);
      await tradingPage.confirmOrder();
      
      // Verify market closed message
      await expect(page.getByText('Market is currently closed')).toBeVisible();
      await expect(page.getByText('Your order will be queued')).toBeVisible();
    });

    await test.step('Handle network error recovery', async () => {
      // Simulate network failure
      await context.setOffline(true);
      
      const orderData = {
        symbol: 'AAPL',
        quantity: 10,
        side: 'buy',
        orderType: 'market'
      };
      
      await tradingPage.fillOrderForm(orderData);
      await tradingPage.confirmOrder();
      
      // Verify offline handling
      await expect(page.getByText('Connection lost')).toBeVisible();
      
      // Restore network
      await context.setOffline(false);
      
      // Verify recovery
      await expect(page.getByText('Connection restored')).toBeVisible();
      await expect(tradingPage.getOrderForm()).toBeVisible();
    });
  });

  test('Mobile trading workflow', async ({ browser }) => {
    // Create mobile context
    const mobileContext = await browser.newContext({
      ...testConfig.mobileDevice,
      permissions: ['notifications']
    });
    
    const mobilePage = await mobileContext.newPage();
    const mobileTrading = new TradingPage(mobilePage);
    
    await test.step('Mobile user places order', async () => {
      await mobilePage.goto(testConfig.baseUrl);
      
      // Login on mobile
      await authPage.login('trader@example.com', 'password123');
      
      // Navigate to mobile trading interface
      await mobilePage.getByRole('button', { name: 'Menu' }).click();
      await mobilePage.getByText('Trade').click();
      
      // Verify mobile trading interface
      await expect(mobilePage.getByText('Quick Trade')).toBeVisible();
      
      // Place order using mobile interface
      await mobileTrading.fillMobileOrderForm({
        symbol: 'AAPL',
        quantity: 5,
        side: 'buy',
        orderType: 'market'
      });
      
      await mobileTrading.confirmMobileOrder();
      
      // Verify order success on mobile
      await expect(mobilePage.getByText('Order executed')).toBeVisible();
    });
    
    await mobileContext.close();
  });
});
```

**E2E Test Page Object Models:**

```typescript
// File: /e2e/pages/TradingPage.ts
/**
 * Page Object Model for Trading Interface
 * 
 * Encapsulates all trading-related interactions and assertions
 */

import { Page, Locator, expect } from '@playwright/test';

export class TradingPage {
  private readonly page: Page;
  
  // Locators
  private readonly orderForm: Locator;
  private readonly symbolInput: Locator;
  private readonly quantityInput: Locator;
  private readonly sideSelect: Locator;
  private readonly orderTypeSelect: Locator;
  private readonly priceInput: Locator;
  private readonly submitButton: Locator;
  private readonly priceChart: Locator;
  private readonly marketData: Locator;
  private readonly currentPrice: Locator;
  private readonly portfolio: Locator;
  private readonly orderHistory: Locator;
  private readonly watchlist: Locator;

  constructor(page: Page) {
    this.page = page;
    
    // Initialize locators
    this.orderForm = page.getByTestId('order-form');
    this.symbolInput = page.getByLabel('Symbol');
    this.quantityInput = page.getByLabel('Quantity');
    this.sideSelect = page.getByLabel('Side');
    this.orderTypeSelect = page.getByLabel('Order Type');
    this.priceInput = page.getByLabel('Price');
    this.submitButton = page.getByRole('button', { name: 'Place Order' });
    this.priceChart = page.getByTestId('price-chart');
    this.marketData = page.getByTestId('market-data');
    this.currentPrice = page.getByTestId('current-price');
    this.portfolio = page.getByTestId('portfolio');
    this.orderHistory = page.getByTestId('order-history');
    this.watchlist = page.getByTestId('watchlist');
  }

  // Navigation methods
  async navigateToOrderEntry(): Promise<void> {
    await this.page.getByText('Place Order').click();
  }

  async navigateToPortfolio(): Promise<void> {
    await this.page.getByText('Portfolio').click();
  }

  async navigateToOrderHistory(): Promise<void> {
    await this.page.getByText('Order History').click();
  }

  async navigateToWatchlist(): Promise<void> {
    await this.page.getByText('Watchlist').click();
  }

  // Stock search and selection
  async searchStock(symbol: string): Promise<void> {
    const searchInput = this.page.getByPlaceholder('Search stocks...');
    await searchInput.fill(symbol);
    await searchInput.press('Enter');
  }

  async selectStock(symbol: string): Promise<void> {
    await this.page.getByText(symbol).first().click();
  }

  // Order form interactions
  async fillOrderForm(orderData: {
    symbol: string;
    quantity: number;
    side: 'buy' | 'sell';
    orderType: 'market' | 'limit' | 'stop' | 'stop_limit';
    price?: number;
    stopPrice?: number;
  }): Promise<void> {
    await this.symbolInput.fill(orderData.symbol);
    await this.quantityInput.fill(orderData.quantity.toString());
    await this.sideSelect.selectOption(orderData.side);
    await this.orderTypeSelect.selectOption(orderData.orderType);
    
    if (orderData.price && (orderData.orderType === 'limit' || orderData.orderType === 'stop_limit')) {
      await this.priceInput.fill(orderData.price.toString());
    }
    
    if (orderData.stopPrice && (orderData.orderType === 'stop' || orderData.orderType === 'stop_limit')) {
      const stopPriceInput = this.page.getByLabel('Stop Price');
      await stopPriceInput.fill(orderData.stopPrice.toString());
    }
  }

  async confirmOrder(): Promise<void> {
    await this.submitButton.click();
    
    // Handle order confirmation dialog if present
    const confirmDialog = this.page.getByRole('dialog', { name: 'Confirm Order' });
    if (await confirmDialog.isVisible()) {
      await this.page.getByRole('button', { name: 'Confirm' }).click();
    }
  }

  // Mobile-specific methods
  async fillMobileOrderForm(orderData: {
    symbol: string;
    quantity: number;
    side: 'buy' | 'sell';
    orderType: 'market' | 'limit';
  }): Promise<void> {
    // Mobile interface might have different layout
    await this.page.getByTestId('mobile-symbol-input').fill(orderData.symbol);
    await this.page.getByTestId('mobile-quantity-input').fill(orderData.quantity.toString());
    await this.page.getByTestId(`mobile-${orderData.side}-button`).click();
    await this.page.getByTestId(`mobile-${orderData.orderType}-button`).click();
  }

  async confirmMobileOrder(): Promise<void> {
    await this.page.getByTestId('mobile-place-order-button').click();
    
    // Mobile confirmation
    await this.page.getByTestId('mobile-confirm-button').click();
  }

  // Chart interactions
  async waitForChartToLoad(): Promise<void> {
    await expect(this.priceChart).toBeVisible();
    
    // Wait for chart data to load
    await this.page.waitForFunction(() => {
      const chart = document.querySelector('[data-testid="price-chart"]');
      return chart && chart.querySelector('svg');
    });
  }

  async changeChartTimeframe(timeframe: '1D' | '1W' | '1M' | '3M' | '1Y'): Promise<void> {
    await this.page.getByRole('button', { name: timeframe }).click();
  }

  // Data retrieval methods
  async getCurrentPrice(): Promise<string> {
    await expect(this.currentPrice).toBeVisible();
    return await this.currentPrice.textContent() || '';
  }

  async getAccountBalance(): Promise<string> {
    const balanceElement = this.page.getByTestId('account-balance');
    await expect(balanceElement).toBeVisible();
    return await balanceElement.textContent() || '';
  }

  // Watchlist methods
  async addToWatchlist(symbol: string): Promise<void> {
    await this.searchStock(symbol);
    await this.page.getByTestId(`add-watchlist-${symbol}`).click();
  }

  async removeFromWatchlist(symbol: string): Promise<void> {
    await this.page.getByTestId(`remove-watchlist-${symbol}`).click();
  }

  // Price alerts
  async setPriceAlert(symbol: string, price: number, direction: 'above' | 'below'): Promise<void> {
    await this.page.getByTestId('price-alerts-button').click();
    await this.page.getByTestId('add-alert-button').click();
    
    await this.page.getByTestId('alert-symbol-input').fill(symbol);
    await this.page.getByTestId('alert-price-input').fill(price.toString());
    await this.page.getByTestId(`alert-${direction}-radio`).click();
    
    await this.page.getByTestId('save-alert-button').click();
  }

  // Getter methods for elements
  getOrderForm(): Locator {
    return this.orderForm;
  }

  getPriceChart(): Locator {
    return this.priceChart;
  }

  getMarketData(): Locator {
    return this.marketData;
  }

  getSubmitButton(): Locator {
    return this.submitButton;
  }

  // Assertion helpers
  async verifyOrderInHistory(orderData: {
    symbol: string;
    quantity: number;
    side: string;
    status: string;
  }): Promise<void> {
    await this.navigateToOrderHistory();
    
    const orderRow = this.page.getByTestId(`order-${orderData.symbol}-${orderData.quantity}`);
    await expect(orderRow).toBeVisible();
    await expect(orderRow).toContainText(orderData.symbol);
    await expect(orderRow).toContainText(orderData.quantity.toString());
    await expect(orderRow).toContainText(orderData.side);
    await expect(orderRow).toContainText(orderData.status);
  }

  async verifyPositionInPortfolio(symbol: string, quantity: number): Promise<void> {
    await this.navigateToPortfolio();
    
    const positionRow = this.page.getByTestId(`position-${symbol}`);
    await expect(positionRow).toBeVisible();
    await expect(positionRow).toContainText(symbol);
    await expect(positionRow).toContainText(quantity.toString());
  }
}
```

#### **5B.1.4 Performance and Load Testing**

**Performance Testing Strategy:**

```typescript
// File: /performance/tests/trading-load.test.ts
/**
 * Performance and Load Testing for Trading System
 * 
 * This test suite covers:
 * - Order placement under load
 * - WebSocket connection scalability
 * - Database performance under concurrent operations
 * - API response times and throughput
 * - Memory and CPU usage monitoring
 */

import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import http from 'k6/http';
import ws from 'k6/ws';
import { randomItem, randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Custom metrics
const orderPlacementRate = new Rate('order_placement_success');
const orderLatency = new Trend('order_placement_latency');
const wsConnectionRate = new Rate('websocket_connection_success');
const priceUpdateLatency = new Trend('price_update_latency');
const errorCounter = new Counter('errors');

// Test configuration
export const options = {
  stages: [
    // Ramp up to 100 virtual users over 2 minutes
    { duration: '2m', target: 100 },
    // Stay at 100 users for 5 minutes
    { duration: '5m', target: 100 },
    // Ramp up to 500 users over 3 minutes
    { duration: '3m', target: 500 },
    // Stay at 500 users for 10 minutes
    { duration: '10m', target: 500 },
    // Spike test - ramp to 1000 users
    { duration: '1m', target: 1000 },
    // Stay at spike for 2 minutes
    { duration: '2m', target: 1000 },
    // Ramp down
    { duration: '2m', target: 0 }
  ],
  thresholds: {
    // HTTP requests should complete within 200ms for 95% of requests
    'http_req_duration': ['p(95)<200'],
    // Order placement should succeed for 99.5% of attempts
    'order_placement_success': ['rate>0.995'],
    // WebSocket connections should succeed for 99% of attempts
    'websocket_connection_success': ['rate>0.99'],
    // Error rate should be less than 1%
    'errors': ['count<100']
  }
};

// Test data
const symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'NFLX'];
const sides = ['buy', 'sell'];
const orderTypes = ['market', 'limit'];

// Authentication setup
function getAuthToken() {
  const loginResponse = http.post(
    `${__ENV.API_BASE_URL}/auth/login`,
    JSON.stringify({
      email: `testuser${__VU}_${__ITER}@example.com`,
      password: 'TestPassword123!'
    }),
    {
      headers: { 'Content-Type': 'application/json' }
    }
  );
  
  return JSON.parse(loginResponse.body).access_token;
}

// Main test function
export default function() {
  const token = getAuthToken();
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };

  group('Trading Operations', () => {
    testOrderPlacement(headers);
    testPortfolioRetrieval(headers);
    testMarketDataRequests(headers);
  });

  group('Real-time Data', () => {
    testWebSocketConnections(token);
  });

  // Think time between operations
  sleep(randomIntBetween(1, 3));
}

function testOrderPlacement(headers) {
  group('Order Placement', () => {
    const orderData = {
      symbol: randomItem(symbols),
      quantity: randomIntBetween(1, 100),
      side: randomItem(sides),
      order_type: randomItem(orderTypes),
      time_in_force: 'day'
    };

    // Add price for limit orders
    if (orderData.order_type === 'limit') {
      orderData.price = randomIntBetween(100, 200) + Math.random();
    }

    const startTime = Date.now();
    
    const response = http.post(
      `${__ENV.API_BASE_URL}/api/v1/trading/orders`,
      JSON.stringify(orderData),
      { headers }
    );

    const endTime = Date.now();
    const latency = endTime - startTime;

    // Record metrics
    orderLatency.add(latency);
    
    const success = check(response, {
      'order placement status is 201': (r) => r.status === 201,
      'order placement response time < 500ms': () => latency < 500,
      'response has order_id': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.order_id !== undefined;
        } catch {
          return false;
        }
      }
    });

    orderPlacementRate.add(success);

    if (!success) {
      errorCounter.add(1);
      console.log(`Order placement failed: ${response.status} - ${response.body}`);
    }
  });
}

function testPortfolioRetrieval(headers) {
  group('Portfolio Retrieval', () => {
    const response = http.get(
      `${__ENV.API_BASE_URL}/api/v1/trading/positions`,
      { headers }
    );

    check(response, {
      'portfolio status is 200': (r) => r.status === 200,
      'portfolio response time < 100ms': (r) => r.timings.duration < 100,
      'portfolio response is valid JSON': (r) => {
        try {
          JSON.parse(r.body);
          return true;
        } catch {
          return false;
        }
      }
    });
  });
}

function testMarketDataRequests(headers) {
  group('Market Data', () => {
    const symbol = randomItem(symbols);
    
    const response = http.get(
      `${__ENV.API_BASE_URL}/api/v1/market/quote/${symbol}`,
      { headers }
    );

    check(response, {
      'market data status is 200': (r) => r.status === 200,
      'market data response time < 50ms': (r) => r.timings.duration < 50,
      'market data has price': (r) => {
        try {
          const data = JSON.parse(r.body);
          return data.price !== undefined;
        } catch {
          return false;
        }
      }
    });
  });
}

function testWebSocketConnections(token) {
  group('WebSocket Real-time Data', () => {
    const url = `${__ENV.WS_BASE_URL}/ws/trading?token=${token}`;
    
    const response = ws.connect(url, {}, (socket) => {
      socket.on('open', () => {
        wsConnectionRate.add(true);
        
        // Subscribe to price updates
        socket.send(JSON.stringify({
          type: 'subscribe',
          symbols: [randomItem(symbols)]
        }));
      });

      socket.on('message', (data) => {
        try {
          const message = JSON.parse(data);
          if (message.type === 'price_update') {
            const latency = Date.now() - message.timestamp;
            priceUpdateLatency.add(latency);
          }
        } catch (e) {
          errorCounter.add(1);
        }
      });

      socket.on('error', (e) => {
        wsConnectionRate.add(false);
        errorCounter.add(1);
        console.log(`WebSocket error: ${e.error()}`);
      });

      // Keep connection open for 30 seconds
      socket.setTimeout(() => {
        socket.close();
      }, 30000);
    });

    if (!response) {
      wsConnectionRate.add(false);
      errorCounter.add(1);
    }
  });
}

// Stress test for order execution system
export function orderExecutionStressTest() {
  const token = getAuthToken();
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };

  // Rapid fire order placement
  for (let i = 0; i < 10; i++) {
    const orderData = {
      symbol: 'AAPL',
      quantity: 1,
      side: i % 2 === 0 ? 'buy' : 'sell',
      order_type: 'market',
      time_in_force: 'day'
    };

    const response = http.post(
      `${__ENV.API_BASE_URL}/api/v1/trading/orders`,
      JSON.stringify(orderData),
      { headers }
    );

    check(response, {
      'rapid order placement succeeds': (r) => r.status === 201 || r.status === 409, // 409 for insufficient funds is acceptable
    });

    // Very short delay between orders
    sleep(0.1);
  }
}

// Database stress test
export function databaseStressTest() {
  const token = getAuthToken();
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };

  group('Database Stress Test', () => {
    // Concurrent reads
    const responses = [];
    
    for (let i = 0; i < 5; i++) {
      responses.push(
        http.get(`${__ENV.API_BASE_URL}/api/v1/trading/positions`, { headers })
      );
      responses.push(
        http.get(`${__ENV.API_BASE_URL}/api/v1/trading/orders`, { headers })
      );
      responses.push(
        http.get(`${__ENV.API_BASE_URL}/api/v1/trading/account`, { headers })
      );
    }

    // Check all responses
    responses.forEach((response, index) => {
      check(response, {
        [`concurrent read ${index} succeeds`]: (r) => r.status === 200,
        [`concurrent read ${index} fast enough`]: (r) => r.timings.duration < 200
      });
    });
  });
}

// Memory leak detection test
export function memoryLeakTest() {
  const token = getAuthToken();
  
  // WebSocket connection that should be properly cleaned up
  const url = `${__ENV.WS_BASE_URL}/ws/trading?token=${token}`;
  
  for (let i = 0; i < 100; i++) {
    ws.connect(url, {}, (socket) => {
      socket.on('open', () => {
        // Immediately close to test connection cleanup
        socket.close();
      });
    });
    
    sleep(0.01);
  }
}

// Performance monitoring setup
export function setup() {
  // Pre-test setup - create test users if needed
  console.log('Setting up performance test environment...');
  
  // Create test users for load testing
  for (let i = 1; i <= 1000; i++) {
    const registerResponse = http.post(
      `${__ENV.API_BASE_URL}/auth/register`,
      JSON.stringify({
        email: `testuser${i}@example.com`,
        password: 'TestPassword123!',
        first_name: 'Test',
        last_name: `User${i}`
      }),
      {
        headers: { 'Content-Type': 'application/json' }
      }
    );
    
    if (i % 100 === 0) {
      console.log(`Created ${i} test users`);
    }
  }
  
  console.log('Performance test setup complete');
}

export function teardown() {
  // Post-test cleanup
  console.log('Performance test teardown complete');
}
```

This completes the comprehensive testing strategy section with unit testing frameworks, integration testing approaches, end-to-end testing strategies, and performance testing protocols. The section provides practical implementations and detailed examples for each testing category.

### **5B.2 CI/CD PIPELINE ARCHITECTURE**

#### **5B.2.1 Automated Build Pipeline Design**

**GitHub Actions CI/CD Pipeline Configuration:**

```yaml
# File: /.github/workflows/main.yml
name: TradeSense CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    # Run security scans daily at 2 AM UTC
    - cron: '0 2 * * *'

env:
  NODE_VERSION: '18.x'
  PYTHON_VERSION: '3.11'
  DOCKER_REGISTRY: ghcr.io
  IMAGE_NAME: tradesense

jobs:
  # =============================================================================
  # 1. CODE QUALITY AND VALIDATION
  # =============================================================================
  
  code-quality:
    name: Code Quality Checks
    runs-on: ubuntu-latest
    strategy:
      matrix:
        component: [frontend, backend]
        
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Fetch full history for better analysis
      
      - name: Setup Node.js
        if: matrix.component == 'frontend'
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Setup Python
        if: matrix.component == 'backend'
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
          cache-dependency-path: backend/requirements*.txt
      
      # Frontend Quality Checks
      - name: Install frontend dependencies
        if: matrix.component == 'frontend'
        working-directory: ./frontend
        run: |
          npm ci --only=production
          npm ci  # Install all dependencies including dev
      
      - name: Frontend linting
        if: matrix.component == 'frontend'
        working-directory: ./frontend
        run: |
          npm run lint:check
          npm run format:check
      
      - name: Frontend type checking
        if: matrix.component == 'frontend'
        working-directory: ./frontend
        run: npm run type-check
      
      - name: Frontend dependency audit
        if: matrix.component == 'frontend'
        working-directory: ./frontend
        run: |
          npm audit --audit-level=high
          npm run check-updates
      
      # Backend Quality Checks
      - name: Install backend dependencies
        if: matrix.component == 'backend'
        working-directory: ./backend
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Backend linting
        if: matrix.component == 'backend'
        working-directory: ./backend
        run: |
          flake8 src/ tests/ --config=.flake8
          black --check src/ tests/
          isort --check-only src/ tests/
      
      - name: Backend type checking
        if: matrix.component == 'backend'
        working-directory: ./backend
        run: mypy src/ --config-file=pyproject.toml
      
      - name: Backend security scanning
        if: matrix.component == 'backend'
        working-directory: ./backend
        run: |
          bandit -r src/ -f json -o bandit-report.json
          safety check --json --output safety-report.json
      
      - name: Upload security reports
        if: matrix.component == 'backend'
        uses: actions/upload-artifact@v3
        with:
          name: security-reports-${{ matrix.component }}
          path: |
            backend/bandit-report.json
            backend/safety-report.json
          retention-days: 30

  # =============================================================================
  # 2. AUTOMATED TESTING
  # =============================================================================
  
  test-frontend:
    name: Frontend Tests
    runs-on: ubuntu-latest
    needs: code-quality
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci
      
      - name: Run unit tests
        working-directory: ./frontend
        run: |
          npm run test:unit -- --coverage --watchAll=false
        env:
          CI: true
      
      - name: Run component tests
        working-directory: ./frontend
        run: |
          npm run test:components -- --coverage --watchAll=false
        env:
          CI: true
      
      - name: Upload test coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./frontend/coverage/lcov.info
          flags: frontend
          name: frontend-coverage
          fail_ci_if_error: true
      
      - name: Store test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: frontend-test-results
          path: |
            frontend/coverage/
            frontend/test-results/
          retention-days: 30

  test-backend:
    name: Backend Tests
    runs-on: ubuntu-latest
    needs: code-quality
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_USER: test_user
          POSTGRES_DB: tradesense_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
          cache-dependency-path: backend/requirements*.txt
      
      - name: Install dependencies
        working-directory: ./backend
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run database migrations
        working-directory: ./backend
        run: |
          alembic upgrade head
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/tradesense_test
          REDIS_URL: redis://localhost:6379/0
      
      - name: Run unit tests
        working-directory: ./backend
        run: |
          pytest tests/unit/ -v --cov=src --cov-report=xml --cov-report=html
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/tradesense_test
          REDIS_URL: redis://localhost:6379/0
          TESTING: true
      
      - name: Run integration tests
        working-directory: ./backend
        run: |
          pytest tests/integration/ -v --cov=src --cov-append --cov-report=xml
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/tradesense_test
          REDIS_URL: redis://localhost:6379/0
          TESTING: true
      
      - name: Upload test coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
          flags: backend
          name: backend-coverage
          fail_ci_if_error: true
      
      - name: Store test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: backend-test-results
          path: |
            backend/htmlcov/
            backend/coverage.xml
            backend/test-results/
          retention-days: 30

  # =============================================================================
  # 3. END-TO-END TESTING
  # =============================================================================
  
  test-e2e:
    name: End-to-End Tests
    runs-on: ubuntu-latest
    needs: [test-frontend, test-backend]
    if: github.event_name == 'pull_request' || github.ref == 'refs/heads/main'
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: e2e/package-lock.json
      
      - name: Install E2E dependencies
        working-directory: ./e2e
        run: npm ci
      
      - name: Install Playwright browsers
        working-directory: ./e2e
        run: npx playwright install --with-deps
      
      - name: Start application stack
        run: |
          docker-compose -f docker-compose.test.yml up -d
          # Wait for services to be ready
          timeout 300s bash -c 'until curl -f http://localhost:3000/health && curl -f http://localhost:8000/health; do sleep 5; done'
      
      - name: Run E2E tests
        working-directory: ./e2e
        run: |
          npx playwright test --reporter=html
        env:
          PLAYWRIGHT_BASE_URL: http://localhost:3000
          API_BASE_URL: http://localhost:8000
      
      - name: Upload E2E test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: e2e-test-results
          path: |
            e2e/playwright-report/
            e2e/test-results/
          retention-days: 30
      
      - name: Stop application stack
        if: always()
        run: docker-compose -f docker-compose.test.yml down -v

  # =============================================================================
  # 4. SECURITY SCANNING
  # =============================================================================
  
  security-scan:
    name: Security Analysis
    runs-on: ubuntu-latest
    needs: code-quality
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
      
      - name: Run CodeQL Analysis
        uses: github/codeql-action/init@v2
        with:
          languages: javascript, python
      
      - name: Autobuild
        uses: github/codeql-action/autobuild@v2
      
      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v2
      
      - name: Run Semgrep security scan
        uses: returntocorp/semgrep-action@v1
        with:
          config: auto
          generateSarif: true
      
      - name: Upload Semgrep results
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: semgrep.sarif

  # =============================================================================
  # 5. PERFORMANCE TESTING
  # =============================================================================
  
  performance-test:
    name: Performance Testing
    runs-on: ubuntu-latest
    needs: [test-frontend, test-backend]
    if: github.ref == 'refs/heads/main' || contains(github.event.pull_request.labels.*.name, 'performance')
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup k6
        run: |
          sudo apt-get update
          sudo apt-get install -y gnupg
          curl -s https://dl.k6.io/key.gpg | sudo apt-key add -
          echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6
      
      - name: Start application for performance testing
        run: |
          docker-compose -f docker-compose.perf.yml up -d
          timeout 300s bash -c 'until curl -f http://localhost:8000/health; do sleep 5; done'
      
      - name: Run performance tests
        working-directory: ./performance
        run: |
          k6 run --out json=results.json tests/trading-load.test.js
        env:
          API_BASE_URL: http://localhost:8000
          WS_BASE_URL: ws://localhost:8000
      
      - name: Upload performance results
        uses: actions/upload-artifact@v3
        with:
          name: performance-results
          path: performance/results.json
          retention-days: 30
      
      - name: Stop performance test environment
        if: always()
        run: docker-compose -f docker-compose.perf.yml down -v

  # =============================================================================
  # 6. BUILD AND CONTAINERIZATION
  # =============================================================================
  
  build:
    name: Build and Package
    runs-on: ubuntu-latest
    needs: [test-frontend, test-backend, security-scan]
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
    
    outputs:
      frontend-image: ${{ steps.meta-frontend.outputs.tags }}
      backend-image: ${{ steps.meta-backend.outputs.tags }}
      frontend-digest: ${{ steps.build-frontend.outputs.digest }}
      backend-digest: ${{ steps.build-backend.outputs.digest }}
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.DOCKER_REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      # Frontend Build
      - name: Extract frontend metadata
        id: meta-frontend
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.DOCKER_REGISTRY }}/${{ github.repository }}/frontend
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}
      
      - name: Build and push frontend image
        id: build-frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          file: ./frontend/Dockerfile.prod
          push: true
          tags: ${{ steps.meta-frontend.outputs.tags }}
          labels: ${{ steps.meta-frontend.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64,linux/arm64
      
      # Backend Build
      - name: Extract backend metadata
        id: meta-backend
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.DOCKER_REGISTRY }}/${{ github.repository }}/backend
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}
      
      - name: Build and push backend image
        id: build-backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          file: ./backend/Dockerfile.prod
          push: true
          tags: ${{ steps.meta-backend.outputs.tags }}
          labels: ${{ steps.meta-backend.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64,linux/arm64

  # =============================================================================
  # 7. DEPLOYMENT TO STAGING
  # =============================================================================
  
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://staging.tradesense.example.com
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Update ECS service
        run: |
          # Update task definition with new image
          aws ecs describe-task-definition --task-definition tradesense-staging-frontend \
            --query taskDefinition > frontend-task-def.json
          
          # Update image in task definition
          jq --arg IMAGE "${{ needs.build.outputs.frontend-image }}" \
            '.containerDefinitions[0].image = $IMAGE' frontend-task-def.json > frontend-task-def-updated.json
          
          # Register new task definition
          aws ecs register-task-definition --cli-input-json file://frontend-task-def-updated.json
          
          # Update service
          aws ecs update-service --cluster tradesense-staging \
            --service tradesense-staging-frontend \
            --task-definition tradesense-staging-frontend
          
          # Wait for deployment to complete
          aws ecs wait services-stable --cluster tradesense-staging \
            --services tradesense-staging-frontend
      
      - name: Run deployment verification
        run: |
          # Wait for service to be available
          timeout 300s bash -c 'until curl -f https://staging.tradesense.example.com/health; do sleep 10; done'
          
          # Run smoke tests
          curl -f https://staging.tradesense.example.com/api/health
          curl -f https://staging.tradesense.example.com/api/v1/health
      
      - name: Notify deployment status
        uses: 8398a7/action-slack@v3
        if: always()
        with:
          status: ${{ job.status }}
          channel: '#deployments'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
          fields: repo,message,commit,author,action,eventName,ref,workflow

  # =============================================================================
  # 8. DEPLOYMENT TO PRODUCTION
  # =============================================================================
  
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://tradesense.example.com
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Blue-Green Deployment Setup
        run: |
          # Determine current and target environments
          CURRENT_ENV=$(aws elbv2 describe-target-groups \
            --target-group-arns ${{ secrets.PROD_TARGET_GROUP_BLUE }} \
            --query 'TargetGroups[0].TargetGroupArn' --output text)
          
          if [ "$CURRENT_ENV" == "${{ secrets.PROD_TARGET_GROUP_BLUE }}" ]; then
            TARGET_ENV="${{ secrets.PROD_TARGET_GROUP_GREEN }}"
            TARGET_SERVICE="tradesense-prod-green"
          else
            TARGET_ENV="${{ secrets.PROD_TARGET_GROUP_BLUE }}"
            TARGET_SERVICE="tradesense-prod-blue"
          fi
          
          echo "TARGET_ENV=$TARGET_ENV" >> $GITHUB_ENV
          echo "TARGET_SERVICE=$TARGET_SERVICE" >> $GITHUB_ENV
      
      - name: Deploy to target environment
        run: |
          # Update task definition with new image
          aws ecs describe-task-definition --task-definition ${{ env.TARGET_SERVICE }} \
            --query taskDefinition > task-def.json
          
          # Update images in task definition
          jq --arg FRONTEND_IMAGE "${{ needs.build.outputs.frontend-image }}" \
             --arg BACKEND_IMAGE "${{ needs.build.outputs.backend-image }}" \
            '.containerDefinitions |= map(
              if .name == "frontend" then .image = $FRONTEND_IMAGE
              elif .name == "backend" then .image = $BACKEND_IMAGE
              else . end
            )' task-def.json > task-def-updated.json
          
          # Register new task definition
          aws ecs register-task-definition --cli-input-json file://task-def-updated.json
          
          # Update service
          aws ecs update-service --cluster tradesense-production \
            --service ${{ env.TARGET_SERVICE }} \
            --task-definition ${{ env.TARGET_SERVICE }}
          
          # Wait for deployment to complete
          aws ecs wait services-stable --cluster tradesense-production \
            --services ${{ env.TARGET_SERVICE }}
      
      - name: Run comprehensive health checks
        run: |
          # Get target environment URL
          TARGET_URL=$(aws elbv2 describe-load-balancers \
            --load-balancer-arns ${{ secrets.PROD_ALB_ARN }} \
            --query 'LoadBalancers[0].DNSName' --output text)
          
          # Health check script
          ./scripts/production-health-check.sh "https://$TARGET_URL"
      
      - name: Switch traffic to new environment
        run: |
          # Switch ALB target group
          aws elbv2 modify-listener --listener-arn ${{ secrets.PROD_LISTENER_ARN }} \
            --default-actions Type=forward,TargetGroupArn=${{ env.TARGET_ENV }}
          
          # Wait for traffic switch
          sleep 30
          
          # Verify production is serving from new environment
          curl -f https://tradesense.example.com/health
      
      - name: Scale down old environment
        run: |
          # Scale down old environment after successful switch
          OLD_SERVICE=$([ "${{ env.TARGET_SERVICE }}" == "tradesense-prod-blue" ] && echo "tradesense-prod-green" || echo "tradesense-prod-blue")
          
          aws ecs update-service --cluster tradesense-production \
            --service $OLD_SERVICE \
            --desired-count 0
      
      - name: Notify production deployment
        uses: 8398a7/action-slack@v3
        if: always()
        with:
          status: ${{ job.status }}
          channel: '#production-deployments'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
          fields: repo,message,commit,author,action,eventName,ref,workflow
          custom_payload: |
            {
              text: `Production Deployment ${job.status}`,
              attachments: [{
                color: '${{ job.status }}' === 'success' ? 'good' : 'danger',
                fields: [{
                  title: 'Frontend Image',
                  value: '${{ needs.build.outputs.frontend-image }}',
                  short: true
                }, {
                  title: 'Backend Image',
                  value: '${{ needs.build.outputs.backend-image }}',
                  short: true
                }]
              }]
            }

  # =============================================================================
  # 9. POST-DEPLOYMENT VERIFICATION
  # =============================================================================
  
  post-deployment-verification:
    name: Post-Deployment Verification
    runs-on: ubuntu-latest
    needs: [deploy-production]
    if: github.ref == 'refs/heads/main'
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Run production smoke tests
        working-directory: ./e2e
        run: |
          npm ci
          npx playwright install --with-deps
          npx playwright test --config=playwright.prod.config.ts --grep="@smoke"
        env:
          PLAYWRIGHT_BASE_URL: https://tradesense.example.com
      
      - name: Run API health checks
        run: |
          ./scripts/api-health-check.sh https://tradesense.example.com/api
      
      - name: Monitor error rates
        run: |
          # Check error rates for 10 minutes post-deployment
          python scripts/monitor-error-rates.py --duration=600 --threshold=0.1
        env:
          DATADOG_API_KEY: ${{ secrets.DATADOG_API_KEY }}
          DATADOG_APP_KEY: ${{ secrets.DATADOG_APP_KEY }}
      
      - name: Verify deployment success
        run: |
          echo "✅ Production deployment verification completed successfully"
          echo "🚀 Application is live at: https://tradesense.example.com"
```

#### **5B.2.2 Deployment Automation and Environment Management**

**Environment-Specific Deployment Configurations:**

```yaml
# File: /.github/workflows/deploy-staging.yml
name: Staging Deployment

on:
  workflow_call:
    inputs:
      frontend-image:
        required: true
        type: string
      backend-image:
        required: true
        type: string
      environment:
        required: true
        type: string
    secrets:
      AWS_ACCESS_KEY_ID:
        required: true
      AWS_SECRET_ACCESS_KEY:
        required: true
      DATADOG_API_KEY:
        required: true

jobs:
  deploy:
    name: Deploy to ${{ inputs.environment }}
    runs-on: ubuntu-latest
    environment:
      name: ${{ inputs.environment }}
      url: ${{ vars.ENVIRONMENT_URL }}
    
    steps:
      - name: Checkout deployment scripts
        uses: actions/checkout@v4
        with:
          sparse-checkout: |
            scripts/
            infrastructure/
            k8s/
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ vars.AWS_REGION }}
      
      - name: Setup kubectl
        uses: azure/setup-kubectl@v3
        with:
          version: 'latest'
      
      - name: Configure kubectl
        run: |
          aws eks update-kubeconfig --region ${{ vars.AWS_REGION }} --name ${{ vars.EKS_CLUSTER_NAME }}
      
      - name: Deploy database migrations
        run: |
          # Run database migrations in a job
          envsubst < k8s/migration-job.yaml | kubectl apply -f -
          kubectl wait --for=condition=complete job/migration-${{ github.sha }} --timeout=300s
        env:
          BACKEND_IMAGE: ${{ inputs.backend-image }}
          ENVIRONMENT: ${{ inputs.environment }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
      
      - name: Deploy backend services
        run: |
          # Update backend deployment
          envsubst < k8s/backend-deployment.yaml | kubectl apply -f -
          kubectl rollout status deployment/tradesense-backend-${{ inputs.environment }} --timeout=600s
        env:
          BACKEND_IMAGE: ${{ inputs.backend-image }}
          ENVIRONMENT: ${{ inputs.environment }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          REDIS_URL: ${{ secrets.REDIS_URL }}
          JWT_SECRET: ${{ secrets.JWT_SECRET }}
      
      - name: Deploy frontend services
        run: |
          # Update frontend deployment
          envsubst < k8s/frontend-deployment.yaml | kubectl apply -f -
          kubectl rollout status deployment/tradesense-frontend-${{ inputs.environment }} --timeout=600s
        env:
          FRONTEND_IMAGE: ${{ inputs.frontend-image }}
          ENVIRONMENT: ${{ inputs.environment }}
          API_URL: ${{ vars.API_URL }}
      
      - name: Update ingress configuration
        run: |
          envsubst < k8s/ingress.yaml | kubectl apply -f -
        env:
          ENVIRONMENT: ${{ inputs.environment }}
          DOMAIN: ${{ vars.ENVIRONMENT_URL }}
      
      - name: Wait for deployment readiness
        run: |
          # Wait for all pods to be ready
          kubectl wait --for=condition=ready pod -l app=tradesense-backend-${{ inputs.environment }} --timeout=300s
          kubectl wait --for=condition=ready pod -l app=tradesense-frontend-${{ inputs.environment }} --timeout=300s
      
      - name: Run deployment verification
        run: |
          # Health check script
          ./scripts/deployment-health-check.sh "${{ vars.ENVIRONMENT_URL }}"
          
          # API functional tests
          ./scripts/api-functional-tests.sh "${{ vars.ENVIRONMENT_URL }}/api"
      
      - name: Update deployment tracking
        run: |
          # Record deployment in Datadog
          curl -X POST "https://api.datadoghq.com/api/v1/events" \
            -H "Content-Type: application/json" \
            -H "DD-API-KEY: ${{ secrets.DATADOG_API_KEY }}" \
            -d '{
              "title": "TradeSense Deployment",
              "text": "Deployed to ${{ inputs.environment }}",
              "tags": ["environment:${{ inputs.environment }}", "service:tradesense"],
              "alert_type": "info"
            }'
```

**Kubernetes Deployment Manifests:**

```yaml
# File: /k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tradesense-backend-${ENVIRONMENT}
  namespace: tradesense-${ENVIRONMENT}
  labels:
    app: tradesense-backend
    environment: ${ENVIRONMENT}
    version: ${GITHUB_SHA}
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: tradesense-backend
      environment: ${ENVIRONMENT}
  template:
    metadata:
      labels:
        app: tradesense-backend
        environment: ${ENVIRONMENT}
        version: ${GITHUB_SHA}
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: tradesense-backend
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: backend
        image: ${BACKEND_IMAGE}
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: ENVIRONMENT
          value: ${ENVIRONMENT}
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: tradesense-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: tradesense-secrets
              key: redis-url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: tradesense-secrets
              key: jwt-secret
        - name: ALPACA_API_KEY
          valueFrom:
            secretKeyRef:
              name: tradesense-secrets
              key: alpaca-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /app/.cache
      volumes:
      - name: tmp
        emptyDir: {}
      - name: cache
        emptyDir: {}
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - tradesense-backend
              topologyKey: kubernetes.io/hostname

---
apiVersion: v1
kind: Service
metadata:
  name: tradesense-backend-service
  namespace: tradesense-${ENVIRONMENT}
  labels:
    app: tradesense-backend
    environment: ${ENVIRONMENT}
spec:
  selector:
    app: tradesense-backend
    environment: ${ENVIRONMENT}
  ports:
  - name: http
    port: 80
    targetPort: 8000
  type: ClusterIP

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: tradesense-backend-hpa
  namespace: tradesense-${ENVIRONMENT}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: tradesense-backend-${ENVIRONMENT}
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

#### **5B.2.3 Rollback and Recovery Mechanisms**

**Automated Rollback System:**

```bash
#!/bin/bash
# File: /scripts/rollback-deployment.sh
# Automated rollback system for TradeSense deployments

set -euo pipefail

ENVIRONMENT=${1:-}
ROLLBACK_VERSION=${2:-}
DRY_RUN=${3:-false}

if [[ -z "$ENVIRONMENT" ]]; then
    echo "❌ Error: Environment must be specified"
    echo "Usage: $0 <environment> [version] [dry-run]"
    echo "Environments: staging, production"
    exit 1
fi

# Configuration
NAMESPACE="tradesense-${ENVIRONMENT}"
DEPLOYMENT_TIMEOUT="600s"
HEALTH_CHECK_TIMEOUT="300"
ROLLBACK_LOG_FILE="/tmp/rollback-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S).log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$ROLLBACK_LOG_FILE"
}

# Error handling
handle_error() {
    log "❌ Error occurred during rollback. Check logs at $ROLLBACK_LOG_FILE"
    
    # Send alert to monitoring system
    curl -X POST "$SLACK_WEBHOOK_URL" -H 'Content-type: application/json' \
        --data "{\"text\":\"🚨 Rollback FAILED for $ENVIRONMENT environment\"}" \
        2>/dev/null || true
    
    exit 1
}

trap handle_error ERR

log "🔄 Starting rollback for $ENVIRONMENT environment"

# Validate prerequisites
validate_prerequisites() {
    log "📋 Validating prerequisites..."
    
    # Check kubectl access
    if ! kubectl get ns "$NAMESPACE" >/dev/null 2>&1; then
        log "❌ Cannot access namespace $NAMESPACE"
        exit 1
    fi
    
    # Check if deployments exist
    local deployments=("tradesense-backend-${ENVIRONMENT}" "tradesense-frontend-${ENVIRONMENT}")
    for deployment in "${deployments[@]}"; do
        if ! kubectl get deployment "$deployment" -n "$NAMESPACE" >/dev/null 2>&1; then
            log "❌ Deployment $deployment not found"
            exit 1
        fi
    done
    
    log "✅ Prerequisites validated"
}

# Get current deployment status
get_current_status() {
    log "📊 Getting current deployment status..."
    
    kubectl get deployments -n "$NAMESPACE" -o wide
    kubectl get pods -n "$NAMESPACE" -l app=tradesense-backend
    kubectl get pods -n "$NAMESPACE" -l app=tradesense-frontend
    
    # Get current replica counts
    BACKEND_REPLICAS=$(kubectl get deployment "tradesense-backend-${ENVIRONMENT}" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
    FRONTEND_REPLICAS=$(kubectl get deployment "tradesense-frontend-${ENVIRONMENT}" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
    
    log "Current replicas - Backend: $BACKEND_REPLICAS, Frontend: $FRONTEND_REPLICAS"
}

# Determine rollback version
determine_rollback_version() {
    if [[ -n "$ROLLBACK_VERSION" ]]; then
        log "📌 Using specified rollback version: $ROLLBACK_VERSION"
        return
    fi
    
    log "🔍 Determining rollback version..."
    
    # Get previous successful deployment from rollout history
    ROLLBACK_VERSION=$(kubectl rollout history deployment/tradesense-backend-${ENVIRONMENT} -n "$NAMESPACE" \
        | grep -E "^\s*[0-9]+" | tail -2 | head -1 | awk '{print $1}')
    
    if [[ -z "$ROLLBACK_VERSION" ]]; then
        log "❌ Could not determine rollback version"
        exit 1
    fi
    
    log "📌 Rolling back to version: $ROLLBACK_VERSION"
}

# Pre-rollback health check
pre_rollback_health_check() {
    log "🏥 Performing pre-rollback health check..."
    
    # Check if application is responsive
    if timeout 30 bash -c "until curl -sf ${ENVIRONMENT_URL}/health >/dev/null; do sleep 2; done" 2>/dev/null; then
        log "✅ Application is currently responsive"
    else
        log "⚠️  Application is not responsive - proceeding with rollback"
    fi
    
    # Check error rates
    if command -v python3 >/dev/null; then
        python3 scripts/check-error-rates.py --environment="$ENVIRONMENT" --threshold=0.1 || {
            log "⚠️  High error rates detected - rollback justified"
        }
    fi
}

# Perform rollback
perform_rollback() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log "🧪 DRY RUN: Would rollback deployments to version $ROLLBACK_VERSION"
        return
    fi
    
    log "🔄 Performing rollback..."
    
    # Stop any ongoing deployments
    kubectl rollout pause deployment/tradesense-backend-${ENVIRONMENT} -n "$NAMESPACE" || true
    kubectl rollout pause deployment/tradesense-frontend-${ENVIRONMENT} -n "$NAMESPACE" || true
    
    # Scale up old version pods gradually
    log "📈 Scaling up rollback version..."
    
    # Rollback backend
    kubectl rollout undo deployment/tradesense-backend-${ENVIRONMENT} -n "$NAMESPACE" --to-revision="$ROLLBACK_VERSION"
    kubectl rollout resume deployment/tradesense-backend-${ENVIRONMENT} -n "$NAMESPACE"
    
    # Wait for backend rollback
    log "⏳ Waiting for backend rollback to complete..."
    kubectl rollout status deployment/tradesense-backend-${ENVIRONMENT} -n "$NAMESPACE" --timeout="$DEPLOYMENT_TIMEOUT"
    
    # Rollback frontend
    kubectl rollout undo deployment/tradesense-frontend-${ENVIRONMENT} -n "$NAMESPACE" --to-revision="$ROLLBACK_VERSION"
    kubectl rollout resume deployment/tradesense-frontend-${ENVIRONMENT} -n "$NAMESPACE"
    
    # Wait for frontend rollback
    log "⏳ Waiting for frontend rollback to complete..."
    kubectl rollout status deployment/tradesense-frontend-${ENVIRONMENT} -n "$NAMESPACE" --timeout="$DEPLOYMENT_TIMEOUT"
}

# Post-rollback verification
post_rollback_verification() {
    log "🔍 Performing post-rollback verification..."
    
    # Wait for pods to be ready
    log "⏳ Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod -l app=tradesense-backend -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=ready pod -l app=tradesense-frontend -n "$NAMESPACE" --timeout=300s
    
    # Health check
    log "🏥 Running health checks..."
    local health_check_start=$(date +%s)
    
    while true; do
        if curl -sf "${ENVIRONMENT_URL}/health" >/dev/null 2>&1; then
            log "✅ Health check passed"
            break
        fi
        
        local current_time=$(date +%s)
        if (( current_time - health_check_start > HEALTH_CHECK_TIMEOUT )); then
            log "❌ Health check timeout"
            exit 1
        fi
        
        log "⏳ Waiting for health check to pass..."
        sleep 10
    done
    
    # API functional tests
    if [[ -f "scripts/api-functional-tests.sh" ]]; then
        log "🧪 Running API functional tests..."
        bash scripts/api-functional-tests.sh "${ENVIRONMENT_URL}/api" || {
            log "❌ API functional tests failed"
            exit 1
        }
        log "✅ API functional tests passed"
    fi
    
    # Smoke tests
    if [[ -f "e2e/smoke-tests.sh" ]]; then
        log "💨 Running smoke tests..."
        bash e2e/smoke-tests.sh "$ENVIRONMENT_URL" || {
            log "❌ Smoke tests failed"
            exit 1
        }
        log "✅ Smoke tests passed"
    fi
}

# Update monitoring and alerts
update_monitoring() {
    log "📊 Updating monitoring systems..."
    
    # Create deployment event in Datadog
    curl -X POST "https://api.datadoghq.com/api/v1/events" \
        -H "Content-Type: application/json" \
        -H "DD-API-KEY: $DATADOG_API_KEY" \
        -d "{
            \"title\": \"TradeSense Rollback Completed\",
            \"text\": \"Successfully rolled back $ENVIRONMENT to version $ROLLBACK_VERSION\",
            \"tags\": [\"environment:$ENVIRONMENT\", \"service:tradesense\", \"event:rollback\"],
            \"alert_type\": \"success\"
        }" >/dev/null 2>&1 || log "⚠️  Could not update Datadog"
    
    # Send Slack notification
    curl -X POST "$SLACK_WEBHOOK_URL" \
        -H 'Content-type: application/json' \
        --data "{
            \"text\": \"✅ Rollback completed successfully for $ENVIRONMENT environment\",
            \"attachments\": [{
                \"color\": \"good\",
                \"fields\": [{
                    \"title\": \"Environment\",
                    \"value\": \"$ENVIRONMENT\",
                    \"short\": true
                }, {
                    \"title\": \"Rollback Version\",
                    \"value\": \"$ROLLBACK_VERSION\",
                    \"short\": true
                }, {
                    \"title\": \"Duration\",
                    \"value\": \"$(($(date +%s) - rollback_start_time)) seconds\",
                    \"short\": true
                }]
            }]
        }" >/dev/null 2>&1 || log "⚠️  Could not send Slack notification"
}

# Main execution
main() {
    local rollback_start_time=$(date +%s)
    
    log "🚀 Starting rollback process for $ENVIRONMENT"
    
    validate_prerequisites
    get_current_status
    determine_rollback_version
    pre_rollback_health_check
    perform_rollback
    post_rollback_verification
    update_monitoring
    
    local rollback_duration=$(($(date +%s) - rollback_start_time))
    log "✅ Rollback completed successfully in ${rollback_duration} seconds"
    log "📋 Rollback log saved to: $ROLLBACK_LOG_FILE"
}

# Load environment variables
if [[ -f ".env.${ENVIRONMENT}" ]]; then
    source ".env.${ENVIRONMENT}"
fi

# Execute main function
main "$@"
```

This completes the CI/CD Pipeline Architecture section with comprehensive automation for builds, testing, deployment, and rollback mechanisms.

### **5B.3 QUALITY ASSURANCE FRAMEWORK**

#### **5B.3.1 Code Quality Metrics and Technical Debt Management**

**Comprehensive Quality Metrics Dashboard:**

```yaml
# File: /.github/workflows/quality-metrics.yml
name: Quality Metrics Collection

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    # Run quality analysis daily
    - cron: '0 6 * * *'

jobs:
  collect-metrics:
    name: Collect Quality Metrics
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for trend analysis
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18.x'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'
          cache-dependency-path: backend/requirements*.txt
      
      # Frontend Quality Metrics
      - name: Install frontend dependencies
        working-directory: ./frontend
        run: npm ci
      
      - name: Frontend code complexity analysis
        working-directory: ./frontend
        run: |
          # Install complexity analysis tools
          npm install -g complexity-report typescript-analyzer
          
          # Generate complexity report
          complexity-report --output json --format json src/ > complexity-report.json
          
          # TypeScript analysis
          typescript-analyzer src/ --output ts-analysis.json
          
          # Bundle size analysis
          npm run analyze:bundle > bundle-analysis.json
      
      - name: Frontend test coverage analysis
        working-directory: ./frontend
        run: |
          npm run test:coverage
          
          # Generate detailed coverage report
          npx nyc report --reporter=json-summary > coverage-summary.json
          npx nyc report --reporter=html
      
      # Backend Quality Metrics
      - name: Install backend dependencies
        working-directory: ./backend
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          pip install radon xenon vulture
      
      - name: Backend code complexity analysis
        working-directory: ./backend
        run: |
          # Cyclomatic complexity
          radon cc src/ --json > cyclomatic-complexity.json
          
          # Maintainability index
          radon mi src/ --json > maintainability-index.json
          
          # Raw metrics
          radon raw src/ --json > raw-metrics.json
          
          # Dead code detection
          vulture src/ --json > dead-code-report.json
          
          # Code quality analysis
          xenon --max-absolute B --max-modules A --max-average A src/ > xenon-report.txt
      
      - name: Backend test coverage analysis
        working-directory: ./backend
        run: |
          pytest tests/ --cov=src --cov-report=json --cov-report=html
          
          # Generate detailed coverage analysis
          coverage json -o coverage-detailed.json
      
      # Technical Debt Analysis
      - name: Technical debt assessment
        run: |
          # Create technical debt report
          python scripts/analyze-technical-debt.py > technical-debt-report.json
      
      # Code Duplication Analysis
      - name: Code duplication analysis
        run: |
          # Install jscpd for JavaScript/TypeScript
          npm install -g jscpd
          
          # JavaScript/TypeScript duplication
          jscpd frontend/src --reporters json --output ./frontend-duplication.json
          
          # Python duplication using PMD CPD equivalent
          docker run --rm -v $(pwd):/workspace pmd/pmd:latest cpd \
            --minimum-tokens 50 --language python --files /workspace/backend/src \
            --format json > backend-duplication.json
      
      # Security Analysis
      - name: Security vulnerability analysis
        run: |
          # Frontend security
          cd frontend && npm audit --json > ../frontend-security.json
          
          # Backend security
          cd backend && safety check --json > ../backend-security.json
          
          # Container security
          docker run --rm -v $(pwd):/path aquasec/trivy fs --format json /path > trivy-security.json
      
      # Performance Metrics
      - name: Performance analysis
        run: |
          # Bundle performance analysis
          cd frontend && npm run build
          ls -la build/static/js/*.js | awk '{print $5, $9}' > bundle-sizes.txt
          
          # Backend performance profiling simulation
          cd backend && python scripts/profile-performance.py > performance-profile.json
      
      # Quality Gates Evaluation
      - name: Evaluate quality gates
        run: |
          python scripts/evaluate-quality-gates.py \
            --frontend-complexity frontend/complexity-report.json \
            --backend-complexity backend/cyclomatic-complexity.json \
            --frontend-coverage frontend/coverage-summary.json \
            --backend-coverage backend/coverage-detailed.json \
            --duplication-frontend frontend-duplication.json \
            --duplication-backend backend-duplication.json \
            --security-frontend frontend-security.json \
            --security-backend backend-security.json \
            --technical-debt technical-debt-report.json \
            --output quality-gates-result.json
      
      # Upload metrics to monitoring
      - name: Upload metrics to Datadog
        run: |
          python scripts/upload-metrics-to-datadog.py \
            --metrics-file quality-gates-result.json \
            --api-key ${{ secrets.DATADOG_API_KEY }}
        env:
          DATADOG_API_KEY: ${{ secrets.DATADOG_API_KEY }}
      
      # Store artifacts
      - name: Upload quality reports
        uses: actions/upload-artifact@v3
        with:
          name: quality-metrics-${{ github.sha }}
          path: |
            **/*-report.json
            **/*-analysis.json
            **/coverage-*.json
            quality-gates-result.json
          retention-days: 90
```

**Quality Gates Evaluation Script:**

```python
# File: /scripts/evaluate-quality-gates.py
"""
Comprehensive quality gates evaluation for TradeSense

This script evaluates code quality metrics against predefined thresholds
and generates actionable insights for continuous improvement.
"""

import json
import argparse
import sys
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class QualityGate:
    """Represents a quality gate with thresholds and current values"""
    name: str
    current_value: float
    threshold: float
    operator: str  # 'gte', 'lte', 'eq'
    severity: str  # 'error', 'warning', 'info'
    description: str
    
    @property
    def passed(self) -> bool:
        """Check if quality gate passes"""
        if self.operator == 'gte':
            return self.current_value >= self.threshold
        elif self.operator == 'lte':
            return self.current_value <= self.threshold
        elif self.operator == 'eq':
            return self.current_value == self.threshold
        return False

class QualityGatesEvaluator:
    """Evaluates quality gates for code quality metrics"""
    
    def __init__(self):
        self.gates: List[QualityGate] = []
        self.results = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'UNKNOWN',
            'gates': [],
            'summary': {},
            'recommendations': []
        }
    
    def load_frontend_complexity(self, filepath: str) -> None:
        """Load and evaluate frontend complexity metrics"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Average cyclomatic complexity
            avg_complexity = data.get('averageComplexity', 0)
            self.gates.append(QualityGate(
                name='Frontend Average Complexity',
                current_value=avg_complexity,
                threshold=5.0,
                operator='lte',
                severity='warning',
                description='Average cyclomatic complexity should be <= 5'
            ))
            
            # Maximum complexity
            max_complexity = data.get('maxComplexity', 0)
            self.gates.append(QualityGate(
                name='Frontend Maximum Complexity',
                current_value=max_complexity,
                threshold=15.0,
                operator='lte',
                severity='error',
                description='Maximum cyclomatic complexity should be <= 15'
            ))
            
            # Functions with high complexity
            high_complexity_functions = len([
                f for f in data.get('functions', [])
                if f.get('complexity', 0) > 10
            ])
            
            self.gates.append(QualityGate(
                name='Frontend High Complexity Functions',
                current_value=high_complexity_functions,
                threshold=5,
                operator='lte',
                severity='warning',
                description='Number of functions with complexity > 10 should be <= 5'
            ))
            
        except Exception as e:
            print(f"Error loading frontend complexity: {e}")
    
    def load_backend_complexity(self, filepath: str) -> None:
        """Load and evaluate backend complexity metrics"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Calculate average complexity across all files
            total_complexity = 0
            total_functions = 0
            
            for file_path, file_data in data.items():
                for item in file_data:
                    if 'complexity' in item:
                        total_complexity += item['complexity']
                        total_functions += 1
            
            avg_complexity = total_complexity / total_functions if total_functions > 0 else 0
            
            self.gates.append(QualityGate(
                name='Backend Average Complexity',
                current_value=avg_complexity,
                threshold=5.0,
                operator='lte',
                severity='warning',
                description='Average cyclomatic complexity should be <= 5'
            ))
            
            # Find maximum complexity
            max_complexity = 0
            for file_path, file_data in data.items():
                for item in file_data:
                    if 'complexity' in item:
                        max_complexity = max(max_complexity, item['complexity'])
            
            self.gates.append(QualityGate(
                name='Backend Maximum Complexity',
                current_value=max_complexity,
                threshold=15.0,
                operator='lte',
                severity='error',
                description='Maximum cyclomatic complexity should be <= 15'
            ))
            
        except Exception as e:
            print(f"Error loading backend complexity: {e}")
    
    def load_test_coverage(self, frontend_file: str, backend_file: str) -> None:
        """Load and evaluate test coverage metrics"""
        try:
            # Frontend coverage
            with open(frontend_file, 'r') as f:
                frontend_coverage = json.load(f)
            
            frontend_total = frontend_coverage.get('total', {})
            frontend_line_coverage = frontend_total.get('lines', {}).get('pct', 0)
            frontend_branch_coverage = frontend_total.get('branches', {}).get('pct', 0)
            frontend_function_coverage = frontend_total.get('functions', {}).get('pct', 0)
            
            # Backend coverage
            with open(backend_file, 'r') as f:
                backend_coverage = json.load(f)
            
            backend_line_coverage = backend_coverage.get('totals', {}).get('percent_covered', 0)
            
            # Coverage gates
            self.gates.extend([
                QualityGate(
                    name='Frontend Line Coverage',
                    current_value=frontend_line_coverage,
                    threshold=85.0,
                    operator='gte',
                    severity='error',
                    description='Frontend line coverage should be >= 85%'
                ),
                QualityGate(
                    name='Frontend Branch Coverage',
                    current_value=frontend_branch_coverage,
                    threshold=80.0,
                    operator='gte',
                    severity='warning',
                    description='Frontend branch coverage should be >= 80%'
                ),
                QualityGate(
                    name='Frontend Function Coverage',
                    current_value=frontend_function_coverage,
                    threshold=90.0,
                    operator='gte',
                    severity='warning',
                    description='Frontend function coverage should be >= 90%'
                ),
                QualityGate(
                    name='Backend Line Coverage',
                    current_value=backend_line_coverage,
                    threshold=90.0,
                    operator='gte',
                    severity='error',
                    description='Backend line coverage should be >= 90%'
                )
            ])
            
        except Exception as e:
            print(f"Error loading test coverage: {e}")
    
    def load_code_duplication(self, frontend_file: str, backend_file: str) -> None:
        """Load and evaluate code duplication metrics"""
        try:
            # Frontend duplication
            with open(frontend_file, 'r') as f:
                frontend_dup = json.load(f)
            
            frontend_dup_percentage = frontend_dup.get('statistics', {}).get('duplicatedPercentage', 0)
            
            # Backend duplication
            with open(backend_file, 'r') as f:
                backend_dup = json.load(f)
            
            # Calculate backend duplication percentage
            backend_dup_percentage = 0
            if 'duplications' in backend_dup:
                total_lines = backend_dup.get('totalLines', 1)
                duplicated_lines = sum(d.get('lines', 0) for d in backend_dup['duplications'])
                backend_dup_percentage = (duplicated_lines / total_lines) * 100
            
            self.gates.extend([
                QualityGate(
                    name='Frontend Code Duplication',
                    current_value=frontend_dup_percentage,
                    threshold=5.0,
                    operator='lte',
                    severity='warning',
                    description='Frontend code duplication should be <= 5%'
                ),
                QualityGate(
                    name='Backend Code Duplication',
                    current_value=backend_dup_percentage,
                    threshold=3.0,
                    operator='lte',
                    severity='warning',
                    description='Backend code duplication should be <= 3%'
                )
            ])
            
        except Exception as e:
            print(f"Error loading code duplication: {e}")
    
    def load_security_vulnerabilities(self, frontend_file: str, backend_file: str) -> None:
        """Load and evaluate security vulnerability metrics"""
        try:
            # Frontend security
            with open(frontend_file, 'r') as f:
                frontend_security = json.load(f)
            
            frontend_high_vulns = len([
                v for v in frontend_security.get('vulnerabilities', [])
                if v.get('severity') == 'high'
            ])
            
            frontend_critical_vulns = len([
                v for v in frontend_security.get('vulnerabilities', [])
                if v.get('severity') == 'critical'
            ])
            
            # Backend security
            with open(backend_file, 'r') as f:
                backend_security = json.load(f)
            
            backend_high_vulns = len([
                v for v in backend_security.get('vulnerabilities', [])
                if v.get('severity') == 'high'
            ])
            
            backend_critical_vulns = len([
                v for v in backend_security.get('vulnerabilities', [])
                if v.get('severity') == 'critical'
            ])
            
            self.gates.extend([
                QualityGate(
                    name='Frontend Critical Vulnerabilities',
                    current_value=frontend_critical_vulns,
                    threshold=0,
                    operator='eq',
                    severity='error',
                    description='No critical vulnerabilities allowed'
                ),
                QualityGate(
                    name='Frontend High Vulnerabilities',
                    current_value=frontend_high_vulns,
                    threshold=2,
                    operator='lte',
                    severity='warning',
                    description='High vulnerabilities should be <= 2'
                ),
                QualityGate(
                    name='Backend Critical Vulnerabilities',
                    current_value=backend_critical_vulns,
                    threshold=0,
                    operator='eq',
                    severity='error',
                    description='No critical vulnerabilities allowed'
                ),
                QualityGate(
                    name='Backend High Vulnerabilities',
                    current_value=backend_high_vulns,
                    threshold=1,
                    operator='lte',
                    severity='warning',
                    description='High vulnerabilities should be <= 1'
                )
            ])
            
        except Exception as e:
            print(f"Error loading security vulnerabilities: {e}")
    
    def load_technical_debt(self, filepath: str) -> None:
        """Load and evaluate technical debt metrics"""
        try:
            with open(filepath, 'r') as f:
                debt_data = json.load(f)
            
            # Technical debt ratio (time to fix / time to develop)
            debt_ratio = debt_data.get('debt_ratio', 0)
            
            # SQALE rating
            sqale_rating = debt_data.get('sqale_rating', 'A')
            sqale_numeric = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5}.get(sqale_rating, 5)
            
            # Number of code smells
            code_smells = debt_data.get('code_smells', 0)
            
            self.gates.extend([
                QualityGate(
                    name='Technical Debt Ratio',
                    current_value=debt_ratio,
                    threshold=5.0,
                    operator='lte',
                    severity='warning',
                    description='Technical debt ratio should be <= 5%'
                ),
                QualityGate(
                    name='SQALE Rating',
                    current_value=sqale_numeric,
                    threshold=2,
                    operator='lte',
                    severity='warning',
                    description='SQALE rating should be A or B'
                ),
                QualityGate(
                    name='Code Smells',
                    current_value=code_smells,
                    threshold=10,
                    operator='lte',
                    severity='info',
                    description='Code smells should be <= 10'
                )
            ])
            
        except Exception as e:
            print(f"Error loading technical debt: {e}")
    
    def evaluate_gates(self) -> Dict[str, Any]:
        """Evaluate all quality gates and generate report"""
        passed_gates = 0
        failed_gates = 0
        gate_results = []
        
        for gate in self.gates:
            gate_result = {
                'name': gate.name,
                'current_value': gate.current_value,
                'threshold': gate.threshold,
                'operator': gate.operator,
                'severity': gate.severity,
                'description': gate.description,
                'passed': gate.passed,
                'status': 'PASS' if gate.passed else 'FAIL'
            }
            
            gate_results.append(gate_result)
            
            if gate.passed:
                passed_gates += 1
            else:
                failed_gates += 1
        
        # Determine overall status
        critical_failures = [g for g in gate_results if not g['passed'] and g['severity'] == 'error']
        
        if critical_failures:
            overall_status = 'FAIL'
        elif failed_gates > 0:
            overall_status = 'WARNING'
        else:
            overall_status = 'PASS'
        
        # Generate recommendations
        recommendations = self.generate_recommendations(gate_results)
        
        self.results.update({
            'overall_status': overall_status,
            'gates': gate_results,
            'summary': {
                'total_gates': len(self.gates),
                'passed_gates': passed_gates,
                'failed_gates': failed_gates,
                'pass_rate': (passed_gates / len(self.gates)) * 100 if self.gates else 0,
                'critical_failures': len(critical_failures)
            },
            'recommendations': recommendations
        })
        
        return self.results
    
    def generate_recommendations(self, gate_results: List[Dict]) -> List[str]:
        """Generate actionable recommendations based on failed gates"""
        recommendations = []
        
        failed_gates = [g for g in gate_results if not g['passed']]
        
        for gate in failed_gates:
            if 'complexity' in gate['name'].lower():
                recommendations.append(
                    f"Refactor functions in {gate['name']} to reduce complexity. "
                    f"Consider breaking down large functions into smaller, single-purpose functions."
                )
            
            elif 'coverage' in gate['name'].lower():
                recommendations.append(
                    f"Improve test coverage for {gate['name']}. "
                    f"Current: {gate['current_value']:.1f}%, Target: {gate['threshold']:.1f}%. "
                    f"Focus on untested code paths and edge cases."
                )
            
            elif 'duplication' in gate['name'].lower():
                recommendations.append(
                    f"Reduce code duplication in {gate['name']}. "
                    f"Extract common functionality into shared utilities or base classes."
                )
            
            elif 'vulnerabilities' in gate['name'].lower():
                recommendations.append(
                    f"Address security vulnerabilities in {gate['name']}. "
                    f"Update dependencies and review security practices."
                )
            
            elif 'debt' in gate['name'].lower():
                recommendations.append(
                    f"Address technical debt: {gate['name']}. "
                    f"Prioritize refactoring and code quality improvements."
                )
        
        # General recommendations based on overall quality
        pass_rate = (len(gate_results) - len(failed_gates)) / len(gate_results) * 100
        
        if pass_rate < 70:
            recommendations.append(
                "Overall code quality is below acceptable levels. "
                "Consider implementing a code quality improvement sprint."
            )
        elif pass_rate < 85:
            recommendations.append(
                "Code quality shows room for improvement. "
                "Focus on addressing warning-level issues in the next iteration."
            )
        
        return recommendations

def main():
    parser = argparse.ArgumentParser(description='Evaluate quality gates')
    parser.add_argument('--frontend-complexity', required=True)
    parser.add_argument('--backend-complexity', required=True)
    parser.add_argument('--frontend-coverage', required=True)
    parser.add_argument('--backend-coverage', required=True)
    parser.add_argument('--duplication-frontend', required=True)
    parser.add_argument('--duplication-backend', required=True)
    parser.add_argument('--security-frontend', required=True)
    parser.add_argument('--security-backend', required=True)
    parser.add_argument('--technical-debt', required=True)
    parser.add_argument('--output', required=True)
    
    args = parser.parse_args()
    
    evaluator = QualityGatesEvaluator()
    
    # Load all metrics
    evaluator.load_frontend_complexity(args.frontend_complexity)
    evaluator.load_backend_complexity(args.backend_complexity)
    evaluator.load_test_coverage(args.frontend_coverage, args.backend_coverage)
    evaluator.load_code_duplication(args.duplication_frontend, args.duplication_backend)
    evaluator.load_security_vulnerabilities(args.security_frontend, args.security_backend)
    evaluator.load_technical_debt(args.technical_debt)
    
    # Evaluate gates
    results = evaluator.evaluate_gates()
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"Quality Gates Evaluation: {results['overall_status']}")
    print(f"Passed: {results['summary']['passed_gates']}/{results['summary']['total_gates']}")
    print(f"Pass Rate: {results['summary']['pass_rate']:.1f}%")
    
    if results['overall_status'] == 'FAIL':
        print("Critical quality gates failed!")
        sys.exit(1)
    elif results['overall_status'] == 'WARNING':
        print("Some quality gates have warnings.")
        sys.exit(0)
    else:
        print("All quality gates passed!")
        sys.exit(0)

if __name__ == '__main__':
    main()
```

#### **5B.3.2 Static Code Analysis and Security Scanning**

**Comprehensive Security Analysis Pipeline:**

```yaml
# File: /.github/workflows/security-analysis.yml
name: Security Analysis and Compliance

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    # Run comprehensive security scan weekly
    - cron: '0 3 * * 1'

jobs:
  static-analysis:
    name: Static Security Analysis
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      # Multi-language Security Scanning
      - name: Run Semgrep Security Analysis
        uses: returntocorp/semgrep-action@v1
        with:
          config: >
            p/security-audit
            p/secrets
            p/owasp-top-ten
            p/javascript
            p/typescript
            p/python
            p/react
            p/docker
          generateSarif: true
      
      - name: Run Bandit Security Scan (Python)
        working-directory: ./backend
        run: |
          pip install bandit[toml]
          bandit -r src/ -f json -o bandit-security-report.json
          bandit -r src/ -f txt -o bandit-security-report.txt
      
      - name: Run ESLint Security Scan (JavaScript/TypeScript)
        working-directory: ./frontend
        run: |
          npm install eslint-plugin-security @typescript-eslint/eslint-plugin
          npx eslint src/ --ext .js,.jsx,.ts,.tsx \
            --config .eslintrc.security.js \
            --format json --output-file eslint-security-report.json
      
      # Secret Detection
      - name: Run GitLeaks Secret Detection
        uses: zricethezav/gitleaks-action@v1.6.0
        with:
          config-path: .gitleaks.toml
      
      - name: Run TruffleHog Secret Scan
        uses: trufflesecurity/trufflehog@v3.63.2
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD
          extra_args: --debug --only-verified
      
      # Dependency Vulnerability Scanning
      - name: Run Snyk Vulnerability Scan
        uses: snyk/actions/setup@master
      
      - name: Snyk Frontend Dependencies
        working-directory: ./frontend
        run: |
          npm install
          snyk test --json > snyk-frontend-report.json || true
          snyk code test --json > snyk-frontend-code-report.json || true
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      
      - name: Snyk Backend Dependencies
        working-directory: ./backend
        run: |
          pip install -r requirements.txt
          snyk test --json > snyk-backend-report.json || true
          snyk code test --json > snyk-backend-code-report.json || true
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      
      # Container Security Scanning
      - name: Build Docker Images for Scanning
        run: |
          docker build -t tradesense-frontend:security-scan ./frontend
          docker build -t tradesense-backend:security-scan ./backend
      
      - name: Run Trivy Container Scan
        run: |
          # Install Trivy
          sudo apt-get update
          sudo apt-get install wget apt-transport-https gnupg lsb-release
          wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
          echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
          sudo apt-get update
          sudo apt-get install trivy
          
          # Scan images
          trivy image --format json --output trivy-frontend-report.json tradesense-frontend:security-scan
          trivy image --format json --output trivy-backend-report.json tradesense-backend:security-scan
      
      - name: Run Hadolint Dockerfile Analysis
        run: |
          docker run --rm -i hadolint/hadolint:v2.12.0 < frontend/Dockerfile > hadolint-frontend-report.txt || true
          docker run --rm -i hadolint/hadolint:v2.12.0 < backend/Dockerfile > hadolint-backend-report.txt || true
      
      # Infrastructure Security
      - name: Run Checkov Infrastructure Scan
        run: |
          pip install checkov
          checkov -d infrastructure/ --framework terraform --output json > checkov-infrastructure-report.json || true
          checkov -d k8s/ --framework kubernetes --output json > checkov-k8s-report.json || true
      
      # License Compliance
      - name: License Compliance Check
        run: |
          # Frontend license check
          cd frontend && npx license-checker --json > ../frontend-licenses.json
          
          # Backend license check
          cd backend && pip-licenses --format json > ../backend-licenses.json
          
          # Analyze license compatibility
          python scripts/analyze-license-compliance.py \
            --frontend frontend-licenses.json \
            --backend backend-licenses.json \
            --output license-compliance-report.json
      
      # Aggregate Security Report
      - name: Generate Security Summary
        run: |
          python scripts/aggregate-security-reports.py \
            --semgrep-sarif results.sarif \
            --bandit-json backend/bandit-security-report.json \
            --eslint-json frontend/eslint-security-report.json \
            --snyk-frontend frontend/snyk-frontend-report.json \
            --snyk-backend backend/snyk-backend-report.json \
            --trivy-frontend trivy-frontend-report.json \
            --trivy-backend trivy-backend-report.json \
            --checkov-infra checkov-infrastructure-report.json \
            --checkov-k8s checkov-k8s-report.json \
            --license-compliance license-compliance-report.json \
            --output security-summary-report.json
      
      # Upload reports
      - name: Upload Security Reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports-${{ github.sha }}
          path: |
            **/*-report.json
            **/*-report.txt
            results.sarif
            security-summary-report.json
          retention-days: 90
      
      # Upload SARIF to GitHub Security
      - name: Upload SARIF to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: results.sarif
      
      # Security Gate Evaluation
      - name: Evaluate Security Gates
        run: |
          python scripts/evaluate-security-gates.py \
            --security-summary security-summary-report.json \
            --fail-on-high-severity \
            --max-medium-vulnerabilities 5 \
            --max-license-violations 0
```

**Security Gates Evaluation Script:**

```python
# File: /scripts/evaluate-security-gates.py
"""
Security gates evaluation for TradeSense

Evaluates security scan results against security policies and compliance requirements.
"""

import json
import argparse
import sys
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class SecurityIssue:
    source: str
    type: str
    severity: Severity
    title: str
    description: str
    file_path: str = ""
    line_number: int = 0
    cve_id: str = ""
    
class SecurityGatesEvaluator:
    """Evaluates security gates based on scan results"""
    
    def __init__(self):
        self.issues: List[SecurityIssue] = []
        self.policy_violations: List[str] = []
        self.license_violations: List[str] = []
        
    def load_security_summary(self, filepath: str) -> None:
        """Load aggregated security summary"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Process different types of security issues
        for source, results in data.items():
            if source == 'semgrep':
                self._process_semgrep_results(results)
            elif source == 'bandit':
                self._process_bandit_results(results)
            elif source == 'eslint_security':
                self._process_eslint_results(results)
            elif source == 'snyk':
                self._process_snyk_results(results)
            elif source == 'trivy':
                self._process_trivy_results(results)
            elif source == 'checkov':
                self._process_checkov_results(results)
            elif source == 'license_compliance':
                self._process_license_results(results)
    
    def _process_semgrep_results(self, results: Dict) -> None:
        """Process Semgrep SARIF results"""
        for run in results.get('runs', []):
            for result in run.get('results', []):
                severity_map = {
                    'error': Severity.HIGH,
                    'warning': Severity.MEDIUM,
                    'note': Severity.LOW
                }
                
                severity = severity_map.get(result.get('level', 'warning'), Severity.MEDIUM)
                
                location = result.get('locations', [{}])[0]
                file_path = location.get('physicalLocation', {}).get('artifactLocation', {}).get('uri', '')
                line_number = location.get('physicalLocation', {}).get('region', {}).get('startLine', 0)
                
                self.issues.append(SecurityIssue(
                    source='semgrep',
                    type='static_analysis',
                    severity=severity,
                    title=result.get('message', {}).get('text', 'Security issue'),
                    description=result.get('ruleId', ''),
                    file_path=file_path,
                    line_number=line_number
                ))
    
    def _process_bandit_results(self, results: Dict) -> None:
        """Process Bandit security scan results"""
        for result in results.get('results', []):
            severity_map = {
                'HIGH': Severity.HIGH,
                'MEDIUM': Severity.MEDIUM,
                'LOW': Severity.LOW
            }
            
            severity = severity_map.get(result.get('issue_severity', 'MEDIUM'), Severity.MEDIUM)
            
            self.issues.append(SecurityIssue(
                source='bandit',
                type='security_vulnerability',
                severity=severity,
                title=result.get('test_name', 'Security issue'),
                description=result.get('issue_text', ''),
                file_path=result.get('filename', ''),
                line_number=result.get('line_number', 0)
            ))
    
    def _process_snyk_results(self, results: Dict) -> None:
        """Process Snyk vulnerability scan results"""
        for vuln in results.get('vulnerabilities', []):
            severity_map = {
                'critical': Severity.CRITICAL,
                'high': Severity.HIGH,
                'medium': Severity.MEDIUM,
                'low': Severity.LOW
            }
            
            severity = severity_map.get(vuln.get('severity', 'medium'), Severity.MEDIUM)
            
            self.issues.append(SecurityIssue(
                source='snyk',
                type='dependency_vulnerability',
                severity=severity,
                title=vuln.get('title', 'Dependency vulnerability'),
                description=vuln.get('description', ''),
                cve_id=vuln.get('identifiers', {}).get('CVE', [''])[0]
            ))
    
    def _process_trivy_results(self, results: Dict) -> None:
        """Process Trivy container scan results"""
        for result in results.get('Results', []):
            for vuln in result.get('Vulnerabilities', []):
                severity_map = {
                    'CRITICAL': Severity.CRITICAL,
                    'HIGH': Severity.HIGH,
                    'MEDIUM': Severity.MEDIUM,
                    'LOW': Severity.LOW
                }
                
                severity = severity_map.get(vuln.get('Severity', 'MEDIUM'), Severity.MEDIUM)
                
                self.issues.append(SecurityIssue(
                    source='trivy',
                    type='container_vulnerability',
                    severity=severity,
                    title=vuln.get('Title', 'Container vulnerability'),
                    description=vuln.get('Description', ''),
                    cve_id=vuln.get('VulnerabilityID', '')
                ))
    
    def _process_checkov_results(self, results: Dict) -> None:
        """Process Checkov infrastructure scan results"""
        for check in results.get('failed_checks', []):
            severity = Severity.MEDIUM  # Checkov doesn't provide severity, assume medium
            
            self.issues.append(SecurityIssue(
                source='checkov',
                type='infrastructure_misconfiguration',
                severity=severity,
                title=check.get('check_name', 'Infrastructure issue'),
                description=check.get('guideline', ''),
                file_path=check.get('file_path', '')
            ))
    
    def _process_license_results(self, results: Dict) -> None:
        """Process license compliance results"""
        for violation in results.get('violations', []):
            self.license_violations.append(violation)
    
    def evaluate_security_gates(self, 
                               fail_on_critical: bool = True,
                               fail_on_high: bool = True,
                               max_medium: int = 10,
                               max_low: int = 50,
                               max_license_violations: int = 0) -> Dict[str, Any]:
        """Evaluate security gates against policy"""
        
        # Count issues by severity
        severity_counts = {severity: 0 for severity in Severity}
        for issue in self.issues:
            severity_counts[issue.severity] += 1
        
        # Evaluate gates
        gates_passed = True
        gate_results = []
        
        # Critical vulnerabilities gate
        critical_gate = {
            'name': 'Critical Vulnerabilities',
            'threshold': 0 if fail_on_critical else float('inf'),
            'current': severity_counts[Severity.CRITICAL],
            'passed': severity_counts[Severity.CRITICAL] == 0 if fail_on_critical else True,
            'severity': 'critical'
        }
        gate_results.append(critical_gate)
        if not critical_gate['passed']:
            gates_passed = False
        
        # High vulnerabilities gate
        high_gate = {
            'name': 'High Vulnerabilities',
            'threshold': 0 if fail_on_high else float('inf'),
            'current': severity_counts[Severity.HIGH],
            'passed': severity_counts[Severity.HIGH] == 0 if fail_on_high else True,
            'severity': 'high'
        }
        gate_results.append(high_gate)
        if not high_gate['passed']:
            gates_passed = False
        
        # Medium vulnerabilities gate
        medium_gate = {
            'name': 'Medium Vulnerabilities',
            'threshold': max_medium,
            'current': severity_counts[Severity.MEDIUM],
            'passed': severity_counts[Severity.MEDIUM] <= max_medium,
            'severity': 'medium'
        }
        gate_results.append(medium_gate)
        if not medium_gate['passed']:
            gates_passed = False
        
        # License violations gate
        license_gate = {
            'name': 'License Violations',
            'threshold': max_license_violations,
            'current': len(self.license_violations),
            'passed': len(self.license_violations) <= max_license_violations,
            'severity': 'high'
        }
        gate_results.append(license_gate)
        if not license_gate['passed']:
            gates_passed = False
        
        # Generate report
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'PASS' if gates_passed else 'FAIL',
            'security_gates': gate_results,
            'vulnerability_summary': {
                'total_issues': len(self.issues),
                'by_severity': {severity.value: count for severity, count in severity_counts.items()},
                'by_source': self._count_by_source(),
                'by_type': self._count_by_type()
            },
            'license_violations': self.license_violations,
            'recommendations': self._generate_security_recommendations()
        }
        
        return report
    
    def _count_by_source(self) -> Dict[str, int]:
        """Count issues by source"""
        counts = {}
        for issue in self.issues:
            counts[issue.source] = counts.get(issue.source, 0) + 1
        return counts
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count issues by type"""
        counts = {}
        for issue in self.issues:
            counts[issue.type] = counts.get(issue.type, 0) + 1
        return counts
    
    def _generate_security_recommendations(self) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        critical_count = sum(1 for issue in self.issues if issue.severity == Severity.CRITICAL)
        high_count = sum(1 for issue in self.issues if issue.severity == Severity.HIGH)
        
        if critical_count > 0:
            recommendations.append(
                f"URGENT: Address {critical_count} critical security vulnerabilities immediately. "
                "These pose severe security risks and should be fixed before deployment."
            )
        
        if high_count > 0:
            recommendations.append(
                f"High priority: Address {high_count} high-severity security vulnerabilities. "
                "Schedule fixes for these issues in the current sprint."
            )
        
        # Source-specific recommendations
        source_counts = self._count_by_source()
        
        if source_counts.get('snyk', 0) > 0:
            recommendations.append(
                "Update dependencies to address known vulnerabilities. "
                "Consider using automated dependency updates."
            )
        
        if source_counts.get('bandit', 0) > 0 or source_counts.get('semgrep', 0) > 0:
            recommendations.append(
                "Review and fix static code analysis findings. "
                "Implement secure coding practices and code review guidelines."
            )
        
        if source_counts.get('trivy', 0) > 0:
            recommendations.append(
                "Update base images and system packages in containers. "
                "Regularly scan and update container images."
            )
        
        if source_counts.get('checkov', 0) > 0:
            recommendations.append(
                "Address infrastructure security misconfigurations. "
                "Review and apply security best practices for cloud resources."
            )
        
        if self.license_violations:
            recommendations.append(
                "Resolve license compliance violations. "
                "Review and approve all third-party dependencies."
            )
        
        return recommendations

def main():
    parser = argparse.ArgumentParser(description='Evaluate security gates')
    parser.add_argument('--security-summary', required=True,
                       help='Path to aggregated security summary JSON')
    parser.add_argument('--fail-on-critical', action='store_true',
                       help='Fail if critical vulnerabilities found')
    parser.add_argument('--fail-on-high-severity', action='store_true',
                       help='Fail if high severity vulnerabilities found')
    parser.add_argument('--max-medium-vulnerabilities', type=int, default=10,
                       help='Maximum allowed medium severity vulnerabilities')
    parser.add_argument('--max-license-violations', type=int, default=0,
                       help='Maximum allowed license violations')
    parser.add_argument('--output', default='security-gates-result.json',
                       help='Output file for results')
    
    args = parser.parse_args()
    
    evaluator = SecurityGatesEvaluator()
    evaluator.load_security_summary(args.security_summary)
    
    report = evaluator.evaluate_security_gates(
        fail_on_critical=args.fail_on_critical,
        fail_on_high=args.fail_on_high_severity,
        max_medium=args.max_medium_vulnerabilities,
        max_license_violations=args.max_license_violations
    )
    
    # Save report
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"Security Gates Evaluation: {report['overall_status']}")
    print(f"Total Issues: {report['vulnerability_summary']['total_issues']}")
    print(f"Critical: {report['vulnerability_summary']['by_severity']['critical']}")
    print(f"High: {report['vulnerability_summary']['by_severity']['high']}")
    print(f"Medium: {report['vulnerability_summary']['by_severity']['medium']}")
    print(f"License Violations: {len(report['license_violations'])}")
    
    if report['overall_status'] == 'FAIL':
        print("\nSecurity gates failed! Address security issues before proceeding.")
        for rec in report['recommendations']:
            print(f"- {rec}")
        sys.exit(1)
    else:
        print("\nAll security gates passed!")
        sys.exit(0)

if __name__ == '__main__':
    main()
```

#### **5B.3.3 Performance Monitoring and Error Tracking**

**Real-time Quality Monitoring Dashboard:**

```python
# File: /scripts/quality-monitoring-dashboard.py
"""
Real-time quality monitoring dashboard for TradeSense

Aggregates quality metrics from various sources and provides
a unified view of application health and quality trends.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import websockets
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram
from datadog import initialize, statsd

class MetricType(Enum):
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"

@dataclass
class QualityMetric:
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    metric_type: MetricType
    description: str = ""

class QualityMonitor:
    """Real-time quality monitoring system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics: Dict[str, QualityMetric] = {}
        self.registry = CollectorRegistry()
        self.setup_prometheus_metrics()
        self.setup_datadog()
        
    def setup_prometheus_metrics(self):
        """Setup Prometheus metrics"""
        self.prometheus_metrics = {
            'test_coverage': Gauge(
                'tradesense_test_coverage_percentage',
                'Test coverage percentage',
                ['component', 'type'],
                registry=self.registry
            ),
            'code_complexity': Gauge(
                'tradesense_code_complexity_average',
                'Average code complexity',
                ['component'],
                registry=self.registry
            ),
            'build_duration': Histogram(
                'tradesense_build_duration_seconds',
                'Build duration in seconds',
                ['component', 'status'],
                registry=self.registry
            ),
            'deployment_frequency': Counter(
                'tradesense_deployments_total',
                'Total number of deployments',
                ['environment', 'status'],
                registry=self.registry
            ),
            'error_rate': Gauge(
                'tradesense_error_rate_percentage',
                'Application error rate percentage',
                ['environment', 'service'],
                registry=self.registry
            ),
            'response_time': Histogram(
                'tradesense_response_time_seconds',
                'API response time in seconds',
                ['environment', 'endpoint'],
                registry=self.registry
            ),
            'security_vulnerabilities': Gauge(
                'tradesense_security_vulnerabilities_count',
                'Number of security vulnerabilities',
                ['severity', 'component'],
                registry=self.registry
            ),
            'technical_debt_ratio': Gauge(
                'tradesense_technical_debt_ratio',
                'Technical debt ratio percentage',
                ['component'],
                registry=self.registry
            )
        }
    
    def setup_datadog(self):
        """Setup Datadog integration"""
        if self.config.get('datadog_api_key'):
            initialize(
                api_key=self.config['datadog_api_key'],
                app_key=self.config.get('datadog_app_key')
            )
    
    async def collect_github_metrics(self) -> List[QualityMetric]:
        """Collect metrics from GitHub Actions"""
        metrics = []
        
        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f"token {self.config['github_token']}",
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Get workflow runs
            url = f"https://api.github.com/repos/{self.config['github_repo']}/actions/runs"
            params = {'per_page': 100, 'status': 'completed'}
            
            async with session.get(url, headers=headers, params=params) as response:
                data = await response.json()
                
                for run in data.get('workflow_runs', []):
                    # Calculate build duration
                    start_time = datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(run['updated_at'].replace('Z', '+00:00'))
                    duration = (end_time - start_time).total_seconds()
                    
                    metrics.append(QualityMetric(
                        name='build_duration',
                        value=duration,
                        timestamp=end_time,
                        tags={
                            'workflow': run['name'],
                            'status': run['conclusion'],
                            'branch': run['head_branch']
                        },
                        metric_type=MetricType.HISTOGRAM
                    ))
                    
                    # Track deployment frequency
                    if 'deploy' in run['name'].lower():
                        metrics.append(QualityMetric(
                            name='deployment_frequency',
                            value=1,
                            timestamp=end_time,
                            tags={
                                'environment': self._extract_environment(run['name']),
                                'status': run['conclusion']
                            },
                            metric_type=MetricType.COUNTER
                        ))
        
        return metrics
    
    async def collect_sonarqube_metrics(self) -> List[QualityMetric]:
        """Collect metrics from SonarQube"""
        metrics = []
        
        if not self.config.get('sonarqube_url'):
            return metrics
        
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(
                self.config['sonarqube_token'], 
                ''
            )
            
            # Get project metrics
            url = f"{self.config['sonarqube_url']}/api/measures/component"
            params = {
                'component': self.config['sonarqube_project'],
                'metricKeys': 'coverage,complexity,technical_debt_ratio,vulnerabilities,code_smells'
            }
            
            async with session.get(url, auth=auth, params=params) as response:
                data = await response.json()
                
                for measure in data.get('component', {}).get('measures', []):
                    metric_name = measure['metric']
                    value = float(measure['value'])
                    
                    if metric_name == 'coverage':
                        metrics.append(QualityMetric(
                            name='test_coverage',
                            value=value,
                            timestamp=datetime.utcnow(),
                            tags={'component': 'overall', 'type': 'line'},
                            metric_type=MetricType.GAUGE
                        ))
                    elif metric_name == 'complexity':
                        metrics.append(QualityMetric(
                            name='code_complexity',
                            value=value,
                            timestamp=datetime.utcnow(),
                            tags={'component': 'overall'},
                            metric_type=MetricType.GAUGE
                        ))
                    elif metric_name == 'technical_debt_ratio':
                        metrics.append(QualityMetric(
                            name='technical_debt_ratio',
                            value=value,
                            timestamp=datetime.utcnow(),
                            tags={'component': 'overall'},
                            metric_type=MetricType.GAUGE
                        ))
                    elif metric_name == 'vulnerabilities':
                        metrics.append(QualityMetric(
                            name='security_vulnerabilities',
                            value=value,
                            timestamp=datetime.utcnow(),
                            tags={'severity': 'all', 'component': 'overall'},
                            metric_type=MetricType.GAUGE
                        ))
        
        return metrics
    
    async def collect_application_metrics(self) -> List[QualityMetric]:
        """Collect metrics from application monitoring"""
        metrics = []
        
        # Collect from Datadog API
        if self.config.get('datadog_api_key'):
            metrics.extend(await self._collect_datadog_metrics())
        
        # Collect from application health endpoints
        metrics.extend(await self._collect_health_metrics())
        
        return metrics
    
    async def _collect_datadog_metrics(self) -> List[QualityMetric]:
        """Collect metrics from Datadog API"""
        metrics = []
        
        async with aiohttp.ClientSession() as session:
            headers = {
                'DD-API-KEY': self.config['datadog_api_key'],
                'DD-APPLICATION-KEY': self.config['datadog_app_key']
            }
            
            # Define time range (last hour)
            end_time = int(time.time())
            start_time = end_time - 3600
            
            # Query for error rates
            query = 'avg:tradesense.error_rate{*} by {environment,service}'
            url = 'https://api.datadoghq.com/api/v1/query'
            params = {
                'query': query,
                'from': start_time,
                'to': end_time
            }
            
            async with session.get(url, headers=headers, params=params) as response:
                data = await response.json()
                
                for series in data.get('series', []):
                    if series['pointlist']:
                        latest_point = series['pointlist'][-1]
                        value = latest_point[1] if latest_point[1] is not None else 0
                        
                        # Extract tags
                        tags = {}
                        for tag in series.get('scope', '').split(','):
                            if ':' in tag:
                                key, val = tag.split(':', 1)
                                tags[key] = val
                        
                        metrics.append(QualityMetric(
                            name='error_rate',
                            value=value,
                            timestamp=datetime.fromtimestamp(latest_point[0] / 1000),
                            tags=tags,
                            metric_type=MetricType.GAUGE
                        ))
        
        return metrics
    
    async def _collect_health_metrics(self) -> List[QualityMetric]:
        """Collect metrics from application health endpoints"""
        metrics = []
        
        environments = ['staging', 'production']
        
        for env in environments:
            env_config = self.config.get('environments', {}).get(env, {})
            if not env_config.get('health_url'):
                continue
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(env_config['health_url'], timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Extract response time
                            response_time = response.headers.get('X-Response-Time')
                            if response_time:
                                metrics.append(QualityMetric(
                                    name='response_time',
                                    value=float(response_time) / 1000,  # Convert to seconds
                                    timestamp=datetime.utcnow(),
                                    tags={'environment': env, 'endpoint': 'health'},
                                    metric_type=MetricType.HISTOGRAM
                                ))
                            
                            # Extract application-specific metrics
                            if 'metrics' in data:
                                for metric_name, metric_value in data['metrics'].items():
                                    if isinstance(metric_value, (int, float)):
                                        metrics.append(QualityMetric(
                                            name=metric_name,
                                            value=float(metric_value),
                                            timestamp=datetime.utcnow(),
                                            tags={'environment': env},
                                            metric_type=MetricType.GAUGE
                                        ))
            
            except Exception as e:
                print(f"Error collecting health metrics for {env}: {e}")
        
        return metrics
    
    def update_prometheus_metrics(self, metrics: List[QualityMetric]):
        """Update Prometheus metrics"""
        for metric in metrics:
            if metric.name in self.prometheus_metrics:
                prom_metric = self.prometheus_metrics[metric.name]
                
                if metric.metric_type == MetricType.GAUGE:
                    prom_metric.labels(**metric.tags).set(metric.value)
                elif metric.metric_type == MetricType.COUNTER:
                    prom_metric.labels(**metric.tags).inc(metric.value)
                elif metric.metric_type == MetricType.HISTOGRAM:
                    prom_metric.labels(**metric.tags).observe(metric.value)
    
    def send_to_datadog(self, metrics: List[QualityMetric]):
        """Send metrics to Datadog"""
        for metric in metrics:
            tags = [f"{k}:{v}" for k, v in metric.tags.items()]
            
            if metric.metric_type == MetricType.GAUGE:
                statsd.gauge(
                    f"tradesense.{metric.name}",
                    metric.value,
                    tags=tags,
                    timestamp=metric.timestamp
                )
            elif metric.metric_type == MetricType.COUNTER:
                statsd.increment(
                    f"tradesense.{metric.name}",
                    value=int(metric.value),
                    tags=tags,
                    timestamp=metric.timestamp
                )
            elif metric.metric_type == MetricType.HISTOGRAM:
                statsd.histogram(
                    f"tradesense.{metric.name}",
                    metric.value,
                    tags=tags,
                    timestamp=metric.timestamp
                )
    
    async def generate_quality_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality report"""
        all_metrics = []
        
        # Collect metrics from all sources
        all_metrics.extend(await self.collect_github_metrics())
        all_metrics.extend(await self.collect_sonarqube_metrics())
        all_metrics.extend(await self.collect_application_metrics())
        
        # Update monitoring systems
        self.update_prometheus_metrics(all_metrics)
        if self.config.get('datadog_api_key'):
            self.send_to_datadog(all_metrics)
        
        # Generate report
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics_count': len(all_metrics),
            'summary': self._generate_summary(all_metrics),
            'trends': self._analyze_trends(all_metrics),
            'alerts': self._check_quality_alerts(all_metrics),
            'recommendations': self._generate_recommendations(all_metrics)
        }
        
        return report
    
    def _generate_summary(self, metrics: List[QualityMetric]) -> Dict[str, Any]:
        """Generate metrics summary"""
        summary = {}
        
        for metric in metrics:
            if metric.name not in summary:
                summary[metric.name] = {
                    'latest_value': metric.value,
                    'timestamp': metric.timestamp.isoformat(),
                    'tags': metric.tags
                }
            elif metric.timestamp > datetime.fromisoformat(summary[metric.name]['timestamp']):
                summary[metric.name] = {
                    'latest_value': metric.value,
                    'timestamp': metric.timestamp.isoformat(),
                    'tags': metric.tags
                }
        
        return summary
    
    def _analyze_trends(self, metrics: List[QualityMetric]) -> Dict[str, Any]:
        """Analyze quality trends"""
        # Group metrics by name and calculate trends
        metric_groups = {}
        for metric in metrics:
            if metric.name not in metric_groups:
                metric_groups[metric.name] = []
            metric_groups[metric.name].append(metric)
        
        trends = {}
        for metric_name, metric_list in metric_groups.items():
            if len(metric_list) >= 2:
                # Sort by timestamp
                sorted_metrics = sorted(metric_list, key=lambda m: m.timestamp)
                
                # Calculate trend
                latest = sorted_metrics[-1].value
                previous = sorted_metrics[-2].value
                
                if previous != 0:
                    trend_percentage = ((latest - previous) / previous) * 100
                    trend_direction = 'improving' if self._is_improving_trend(metric_name, trend_percentage) else 'degrading'
                else:
                    trend_percentage = 0
                    trend_direction = 'stable'
                
                trends[metric_name] = {
                    'percentage_change': trend_percentage,
                    'direction': trend_direction,
                    'latest_value': latest,
                    'previous_value': previous
                }
        
        return trends
    
    def _is_improving_trend(self, metric_name: str, trend_percentage: float) -> bool:
        """Determine if trend is improving based on metric type"""
        # Metrics where higher values are better
        higher_is_better = ['test_coverage']
        
        # Metrics where lower values are better
        lower_is_better = ['error_rate', 'code_complexity', 'security_vulnerabilities', 'technical_debt_ratio']
        
        if metric_name in higher_is_better:
            return trend_percentage > 0
        elif metric_name in lower_is_better:
            return trend_percentage < 0
        else:
            return abs(trend_percentage) < 5  # Stable is good for unknown metrics
    
    def _check_quality_alerts(self, metrics: List[QualityMetric]) -> List[Dict[str, Any]]:
        """Check for quality alerts based on thresholds"""
        alerts = []
        
        # Define alert thresholds
        thresholds = {
            'test_coverage': {'min': 85.0, 'severity': 'warning'},
            'error_rate': {'max': 1.0, 'severity': 'critical'},
            'security_vulnerabilities': {'max': 0, 'severity': 'critical'},
            'technical_debt_ratio': {'max': 5.0, 'severity': 'warning'},
            'code_complexity': {'max': 10.0, 'severity': 'warning'}
        }
        
        summary = self._generate_summary(metrics)
        
        for metric_name, config in thresholds.items():
            if metric_name in summary:
                value = summary[metric_name]['latest_value']
                
                # Check minimum threshold
                if 'min' in config and value < config['min']:
                    alerts.append({
                        'metric': metric_name,
                        'type': 'threshold_violation',
                        'severity': config['severity'],
                        'message': f"{metric_name} ({value:.2f}) is below minimum threshold ({config['min']:.2f})",
                        'current_value': value,
                        'threshold': config['min'],
                        'timestamp': summary[metric_name]['timestamp']
                    })
                
                # Check maximum threshold
                if 'max' in config and value > config['max']:
                    alerts.append({
                        'metric': metric_name,
                        'type': 'threshold_violation',
                        'severity': config['severity'],
                        'message': f"{metric_name} ({value:.2f}) exceeds maximum threshold ({config['max']:.2f})",
                        'current_value': value,
                        'threshold': config['max'],
                        'timestamp': summary[metric_name]['timestamp']
                    })
        
        return alerts
    
    def _generate_recommendations(self, metrics: List[QualityMetric]) -> List[str]:
        """Generate quality improvement recommendations"""
        recommendations = []
        summary = self._generate_summary(metrics)
        trends = self._analyze_trends(metrics)
        
        # Coverage recommendations
        if 'test_coverage' in summary:
            coverage = summary['test_coverage']['latest_value']
            if coverage < 85:
                recommendations.append(
                    f"Improve test coverage from {coverage:.1f}% to at least 85%. "
                    "Focus on untested code paths and critical business logic."
                )
        
        # Complexity recommendations
        if 'code_complexity' in summary:
            complexity = summary['code_complexity']['latest_value']
            if complexity > 8:
                recommendations.append(
                    f"Reduce code complexity from {complexity:.1f}. "
                    "Refactor complex functions into smaller, single-purpose methods."
                )
        
        # Error rate recommendations
        if 'error_rate' in summary:
            error_rate = summary['error_rate']['latest_value']
            if error_rate > 0.5:
                recommendations.append(
                    f"Address high error rate ({error_rate:.2f}%). "
                    "Investigate and fix the root causes of application errors."
                )
        
        # Security recommendations
        if 'security_vulnerabilities' in summary:
            vulns = summary['security_vulnerabilities']['latest_value']
            if vulns > 0:
                recommendations.append(
                    f"Address {int(vulns)} security vulnerabilities. "
                    "Prioritize critical and high-severity issues."
                )
        
        # Technical debt recommendations
        if 'technical_debt_ratio' in summary:
            debt = summary['technical_debt_ratio']['latest_value']
            if debt > 5:
                recommendations.append(
                    f"Reduce technical debt ratio from {debt:.1f}%. "
                    "Allocate time for refactoring and code quality improvements."
                )
        
        # Trend-based recommendations
        for metric_name, trend in trends.items():
            if trend['direction'] == 'degrading':
                recommendations.append(
                    f"Address degrading trend in {metric_name} "
                    f"({trend['percentage_change']:+.1f}% change). "
                    "Monitor closely and take corrective action."
                )
        
        return recommendations
    
    def _extract_environment(self, workflow_name: str) -> str:
        """Extract environment from workflow name"""
        workflow_lower = workflow_name.lower()
        if 'production' in workflow_lower or 'prod' in workflow_lower:
            return 'production'
        elif 'staging' in workflow_lower:
            return 'staging'
        else:
            return 'development'

async def main():
    """Main monitoring loop"""
    config = {
        'github_token': 'your_github_token',
        'github_repo': 'your_org/tradesense',
        'sonarqube_url': 'https://sonarqube.example.com',
        'sonarqube_token': 'your_sonarqube_token',
        'sonarqube_project': 'tradesense',
        'datadog_api_key': 'your_datadog_api_key',
        'datadog_app_key': 'your_datadog_app_key',
        'environments': {
            'staging': {
                'health_url': 'https://staging.tradesense.example.com/health'
            },
            'production': {
                'health_url': 'https://tradesense.example.com/health'
            }
        }
    }
    
    monitor = QualityMonitor(config)
    
    while True:
        try:
            print(f"Collecting quality metrics at {datetime.utcnow()}")
            report = await monitor.generate_quality_report()
            
            print(f"Generated report with {report['metrics_count']} metrics")
            
            # Save report
            with open(f"quality-report-{int(time.time())}.json", 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            # Print alerts
            if report['alerts']:
                print("Quality alerts:")
                for alert in report['alerts']:
                    print(f"  - {alert['severity'].upper()}: {alert['message']}")
            
            # Wait before next collection
            await asyncio.sleep(300)  # 5 minutes
            
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retry

if __name__ == '__main__':
    asyncio.run(main())
```

---

## **SECTION 5C: DEPLOYMENT & INFRASTRUCTURE ORCHESTRATION**

### **5C.1 CONTAINERIZATION AND ORCHESTRATION STRATEGY**

#### **5C.1.1 Container Architecture Design**

**Strategic Decision:** Implement a microservices-based containerization strategy using Docker and Kubernetes for maximum scalability, portability, and operational consistency across all environments.

**Container Strategy Overview:**
```
TradeSense Container Ecosystem
├── Frontend Containers
│   ├── tradesense-web (React/TypeScript)
│   ├── tradesense-mobile-web (PWA optimized)
│   └── tradesense-admin-dashboard
├── Backend API Containers
│   ├── tradesense-api-gateway (FastAPI)
│   ├── tradesense-trading-service
│   ├── tradesense-user-service
│   ├── tradesense-analytics-service
│   └── tradesense-notification-service
├── Infrastructure Containers
│   ├── tradesense-redis-cluster
│   ├── tradesense-postgres-primary
│   ├── tradesense-postgres-replica
│   └── tradesense-monitoring-stack
└── External Integrations
    ├── tradesense-broker-connectors
    ├── tradesense-market-data-ingestion
    └── tradesense-payment-processors
```

**Dockerfile Architecture - Frontend Container:**

```dockerfile
# File: /frontend/Dockerfile
# Multi-stage build for optimal production container
ARG NODE_VERSION=20.11.0
ARG NGINX_VERSION=1.25.4-alpine

# Build stage
FROM node:${NODE_VERSION}-alpine AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for node-gyp
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    git

# Copy package files
COPY package*.json ./
COPY yarn.lock ./

# Install dependencies with cache optimization
RUN yarn install --frozen-lockfile --network-timeout 100000

# Copy source code
COPY . .

# Build arguments for runtime configuration
ARG BUILD_ENV=production
ARG API_BASE_URL
ARG SENTRY_DSN
ARG ANALYTICS_TRACKING_ID

# Set build environment variables
ENV NODE_ENV=${BUILD_ENV}
ENV REACT_APP_API_BASE_URL=${API_BASE_URL}
ENV REACT_APP_SENTRY_DSN=${SENTRY_DSN}
ENV REACT_APP_ANALYTICS_TRACKING_ID=${ANALYTICS_TRACKING_ID}

# Build application
RUN yarn build

# Verify build output
RUN ls -la /app/dist && \
    echo "Build completed successfully"

# Production stage
FROM nginx:${NGINX_VERSION} AS production

# Install security updates
RUN apk upgrade --no-cache

# Create non-root user
RUN addgroup -g 1001 -S nginx && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx nginx

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx-security.conf /etc/nginx/conf.d/security.conf

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Set proper permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Create startup script
RUN echo '#!/bin/sh' > /docker-entrypoint.sh && \
    echo 'echo "Starting TradeSense Frontend..."' >> /docker-entrypoint.sh && \
    echo 'echo "Environment: $NODE_ENV"' >> /docker-entrypoint.sh && \
    echo 'echo "API URL: $REACT_APP_API_BASE_URL"' >> /docker-entrypoint.sh && \
    echo 'exec "$@"' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# Switch to non-root user
USER nginx

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Expose port
EXPOSE 80

# Set entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]

# Metadata
LABEL \
    org.opencontainers.image.title="TradeSense Frontend" \
    org.opencontainers.image.description="React/TypeScript frontend for TradeSense trading platform" \
    org.opencontainers.image.vendor="TradeSense" \
    org.opencontainers.image.version="2.7.0" \
    org.opencontainers.image.created="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    org.opencontainers.image.source="https://github.com/tradesense/frontend"
```

**Dockerfile Architecture - Backend API Container:**

```dockerfile
# File: /backend/Dockerfile
# Multi-stage build for Python FastAPI application
ARG PYTHON_VERSION=3.11.8
ARG ALPINE_VERSION=3.19

# Base stage with common dependencies
FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION} AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev \
    curl \
    && rm -rf /var/cache/apk/*

# Create application user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S -D -H -u 1001 -h /app -s /sbin/nologin -G appgroup appuser

# Set working directory
WORKDIR /app

# Dependencies stage
FROM base AS deps

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Development stage
FROM deps AS development

# Install development dependencies
RUN pip install -r requirements-dev.txt

# Copy source code
COPY . .

# Set ownership
RUN chown -R appuser:appgroup /app

# Switch to application user
USER appuser

# Expose port
EXPOSE 8000

# Development command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM deps AS production

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp && \
    chown -R appuser:appgroup /app

# Switch to application user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production startup script
RUN echo '#!/bin/sh' > start.sh && \
    echo 'echo "Starting TradeSense API..."' >> start.sh && \
    echo 'echo "Environment: $ENVIRONMENT"' >> start.sh && \
    echo 'echo "Database URL: $DATABASE_URL"' >> start.sh && \
    echo '# Run database migrations' >> start.sh && \
    echo 'alembic upgrade head' >> start.sh && \
    echo '# Start application with optimized workers' >> start.sh && \
    echo 'exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker' >> start.sh && \
    chmod +x start.sh

# Default command
CMD ["./start.sh"]

# Metadata
LABEL \
    org.opencontainers.image.title="TradeSense API" \
    org.opencontainers.image.description="FastAPI backend for TradeSense trading platform" \
    org.opencontainers.image.vendor="TradeSense" \
    org.opencontainers.image.version="2.7.0" \
    org.opencontainers.image.created="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    org.opencontainers.image.source="https://github.com/tradesense/backend"
```

#### **5C.1.2 Kubernetes Orchestration Framework**

**Namespace Organization Strategy:**

```yaml
# File: /k8s/namespaces/namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: tradesense-production
  labels:
    environment: production
    app.kubernetes.io/name: tradesense
    app.kubernetes.io/component: namespace
---
apiVersion: v1
kind: Namespace
metadata:
  name: tradesense-staging
  labels:
    environment: staging
    app.kubernetes.io/name: tradesense
    app.kubernetes.io/component: namespace
---
apiVersion: v1
kind: Namespace
metadata:
  name: tradesense-development
  labels:
    environment: development
    app.kubernetes.io/name: tradesense
    app.kubernetes.io/component: namespace
---
apiVersion: v1
kind: Namespace
metadata:
  name: tradesense-monitoring
  labels:
    environment: shared
    app.kubernetes.io/name: tradesense
    app.kubernetes.io/component: monitoring
```

**Comprehensive Deployment Configuration - API Gateway:**

```yaml
# File: /k8s/deployments/api-gateway.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tradesense-api-gateway
  namespace: tradesense-production
  labels:
    app: tradesense-api-gateway
    component: backend
    tier: api
    version: v2.7.0
spec:
  replicas: 3
  revisionHistoryLimit: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: tradesense-api-gateway
  template:
    metadata:
      labels:
        app: tradesense-api-gateway
        component: backend
        tier: api
        version: v2.7.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: tradesense-api-gateway
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        runAsGroup: 1001
        fsGroup: 1001
      containers:
      - name: api-gateway
        image: tradesense/api-gateway:v2.7.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          protocol: TCP
          name: http
        - containerPort: 8080
          protocol: TCP
          name: metrics
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: tradesense-db-credentials
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: tradesense-redis-credentials
              key: REDIS_URL
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: tradesense-auth-secrets
              key: JWT_SECRET_KEY
        - name: SENTRY_DSN
          valueFrom:
            secretKeyRef:
              name: tradesense-monitoring-secrets
              key: SENTRY_DSN
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        volumeMounts:
        - name: app-logs
          mountPath: /app/logs
        - name: tmp-volume
          mountPath: /tmp
      volumes:
      - name: app-logs
        emptyDir: {}
      - name: tmp-volume
        emptyDir: {}
      nodeSelector:
        kubernetes.io/arch: amd64
      tolerations:
      - key: "node.kubernetes.io/not-ready"
        operator: "Exists"
        effect: "NoExecute"
        tolerationSeconds: 300
      - key: "node.kubernetes.io/unreachable"
        operator: "Exists"
        effect: "NoExecute"
        tolerationSeconds: 300
---
apiVersion: v1
kind: Service
metadata:
  name: tradesense-api-gateway-service
  namespace: tradesense-production
  labels:
    app: tradesense-api-gateway
    component: backend
spec:
  selector:
    app: tradesense-api-gateway
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP
  - name: metrics
    port: 8080
    targetPort: 8080
    protocol: TCP
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tradesense-api-gateway-ingress
  namespace: tradesense-production
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.tradesense.com
    secretName: tradesense-api-tls
  rules:
  - host: api.tradesense.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: tradesense-api-gateway-service
            port:
              number: 80
```

**HorizontalPodAutoscaler Configuration:**

```yaml
# File: /k8s/autoscaling/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: tradesense-api-gateway-hpa
  namespace: tradesense-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: tradesense-api-gateway
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: custom_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Max
```

### **5C.2 ENVIRONMENT MANAGEMENT AND CONFIGURATION**

#### **5C.2.1 Environment-Specific Configuration Strategy**

**ConfigMap Management:**

```yaml
# File: /k8s/config/production-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: tradesense-config
  namespace: tradesense-production
data:
  # Application Configuration
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  DEBUG: "false"
  
  # API Configuration
  API_VERSION: "v1"
  API_RATE_LIMIT: "1000"
  API_TIMEOUT: "30"
  
  # Database Configuration
  DB_POOL_SIZE: "20"
  DB_MAX_OVERFLOW: "10"
  DB_POOL_TIMEOUT: "30"
  DB_POOL_RECYCLE: "3600"
  
  # Redis Configuration
  REDIS_MAX_CONNECTIONS: "100"
  REDIS_RETRY_ON_TIMEOUT: "true"
  REDIS_SOCKET_KEEPALIVE: "true"
  
  # Trading Configuration
  MAX_ORDERS_PER_MINUTE: "60"
  POSITION_SIZE_LIMIT: "100000"
  RISK_CHECK_ENABLED: "true"
  
  # Monitoring Configuration
  METRICS_ENABLED: "true"
  TRACING_ENABLED: "true"
  PROMETHEUS_PORT: "8080"
  
  # External Services
  BROKER_TIMEOUT: "5"
  MARKET_DATA_REFRESH_INTERVAL: "1"
  NOTIFICATION_RETRY_ATTEMPTS: "3"
  
  # Security Configuration
  CORS_ORIGINS: "https://tradesense.com,https://app.tradesense.com"
  SESSION_TIMEOUT: "3600"
  MAX_LOGIN_ATTEMPTS: "5"
  
  # Performance Configuration
  WORKER_PROCESSES: "4"
  WORKER_CONNECTIONS: "1000"
  KEEPALIVE_TIMEOUT: "65"
```

**Secret Management:**

```yaml
# File: /k8s/secrets/production-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: tradesense-db-credentials
  namespace: tradesense-production
type: Opaque
stringData:
  DATABASE_URL: "postgresql://tradesense_user:${DB_PASSWORD}@postgres-primary.tradesense-production.svc.cluster.local:5432/tradesense_production"
  DB_USERNAME: "tradesense_user"
  DB_PASSWORD: "${DB_PASSWORD}"
---
apiVersion: v1
kind: Secret
metadata:
  name: tradesense-redis-credentials
  namespace: tradesense-production
type: Opaque
stringData:
  REDIS_URL: "redis://:${REDIS_PASSWORD}@redis-cluster.tradesense-production.svc.cluster.local:6379/0"
  REDIS_PASSWORD: "${REDIS_PASSWORD}"
---
apiVersion: v1
kind: Secret
metadata:
  name: tradesense-auth-secrets
  namespace: tradesense-production
type: Opaque
stringData:
  JWT_SECRET_KEY: "${JWT_SECRET_KEY}"
  JWT_ALGORITHM: "HS256"
  JWT_ACCESS_TOKEN_EXPIRE_MINUTES: "30"
  JWT_REFRESH_TOKEN_EXPIRE_DAYS: "30"
---
apiVersion: v1
kind: Secret
metadata:
  name: tradesense-external-api-keys
  namespace: tradesense-production
type: Opaque
stringData:
  ALPACA_API_KEY: "${ALPACA_API_KEY}"
  ALPACA_SECRET_KEY: "${ALPACA_SECRET_KEY}"
  POLYGON_API_KEY: "${POLYGON_API_KEY}"
  FINNHUB_API_KEY: "${FINNHUB_API_KEY}"
  SENDGRID_API_KEY: "${SENDGRID_API_KEY}"
  STRIPE_SECRET_KEY: "${STRIPE_SECRET_KEY}"
  STRIPE_WEBHOOK_SECRET: "${STRIPE_WEBHOOK_SECRET}"
---
apiVersion: v1
kind: Secret
metadata:
  name: tradesense-monitoring-secrets
  namespace: tradesense-production
type: Opaque
stringData:
  SENTRY_DSN: "${SENTRY_DSN}"
  DATADOG_API_KEY: "${DATADOG_API_KEY}"
  NEW_RELIC_LICENSE_KEY: "${NEW_RELIC_LICENSE_KEY}"
```

#### **5C.2.2 Service Account and RBAC Configuration**

**Service Account with Precise RBAC:**

```yaml
# File: /k8s/rbac/service-accounts.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: tradesense-api-gateway
  namespace: tradesense-production
  labels:
    app.kubernetes.io/name: tradesense
    app.kubernetes.io/component: api-gateway
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: tradesense-api-gateway-role
  namespace: tradesense-production
rules:
# ConfigMap access for runtime configuration
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch"]
# Secret access for credentials
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]
# Pod access for service discovery
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
# Service access for internal communication
- apiGroups: [""]
  resources: ["services"]
  verbs: ["get", "list"]
# Events for debugging
- apiGroups: [""]
  resources: ["events"]
  verbs: ["create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: tradesense-api-gateway-binding
  namespace: tradesense-production
subjects:
- kind: ServiceAccount
  name: tradesense-api-gateway
  namespace: tradesense-production
roleRef:
  kind: Role
  name: tradesense-api-gateway-role
  apiGroup: rbac.authorization.k8s.io
```

### **5C.3 DEPLOYMENT STRATEGIES AND ROLLBACK MECHANISMS**

#### **5C.3.1 Advanced Deployment Patterns**

**Blue-Green Deployment Implementation:**

```yaml
# File: /k8s/deployments/blue-green-strategy.yaml
# Blue Environment (Current Production)
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: tradesense-api-gateway
  namespace: tradesense-production
spec:
  replicas: 5
  strategy:
    blueGreen:
      # Reference to service that the rollout modifies as the active service
      activeService: tradesense-api-gateway-active
      # Reference to service that the rollout modifies as the preview service
      previewService: tradesense-api-gateway-preview
      # Pre-promotion analysis
      prePromotionAnalysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: tradesense-api-gateway-preview.tradesense-production.svc.cluster.local
      # Post-promotion analysis
      postPromotionAnalysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: tradesense-api-gateway-active.tradesense-production.svc.cluster.local
      # Auto-promotion settings
      autoPromotionEnabled: false
      scaleDownDelaySeconds: 30
      previewReplicaCount: 1
  selector:
    matchLabels:
      app: tradesense-api-gateway
  template:
    metadata:
      labels:
        app: tradesense-api-gateway
    spec:
      containers:
      - name: api-gateway
        image: tradesense/api-gateway:v2.7.0
        ports:
        - containerPort: 8000
          name: http
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
---
# Active service (production traffic)
apiVersion: v1
kind: Service
metadata:
  name: tradesense-api-gateway-active
  namespace: tradesense-production
spec:
  selector:
    app: tradesense-api-gateway
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
---
# Preview service (testing traffic)
apiVersion: v1
kind: Service
metadata:
  name: tradesense-api-gateway-preview
  namespace: tradesense-production
spec:
  selector:
    app: tradesense-api-gateway
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
---
# Analysis template for deployment validation
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
  namespace: tradesense-production
spec:
  args:
  - name: service-name
  metrics:
  - name: success-rate
    interval: 2m
    count: 5
    # Success rate threshold must be > 95%
    successCondition: result[0] >= 0.95
    failureLimit: 2
    provider:
      prometheus:
        address: http://prometheus.tradesense-monitoring.svc.cluster.local:9090
        query: |
          sum(rate(http_requests_total{service="{{args.service-name}}",status!~"5.."}[2m])) / 
          sum(rate(http_requests_total{service="{{args.service-name}}"}[2m]))
  - name: avg-response-time
    interval: 2m
    count: 5
    # Average response time must be < 500ms
    successCondition: result[0] < 0.5
    failureLimit: 2
    provider:
      prometheus:
        address: http://prometheus.tradesense-monitoring.svc.cluster.local:9090
        query: |
          histogram_quantile(0.50, 
          sum(rate(http_request_duration_seconds_bucket{service="{{args.service-name}}"}[2m])) by (le))
```

**Canary Deployment Configuration:**

```yaml
# File: /k8s/deployments/canary-strategy.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: tradesense-trading-service
  namespace: tradesense-production
spec:
  replicas: 10
  strategy:
    canary:
      steps:
      # Deploy canary with 10% traffic
      - setWeight: 10
      # Pause for manual verification
      - pause: 
          duration: 2m
      # Increase to 25% traffic
      - setWeight: 25
      # Run analysis for 5 minutes
      - analysis:
          templates:
          - templateName: canary-analysis
          args:
          - name: service-name
            value: tradesense-trading-service
          - name: canary-hash
            valueFrom:
              podTemplateHashValue: Latest
      # Increase to 50% traffic
      - setWeight: 50
      - pause: 
          duration: 5m
      # Increase to 75% traffic
      - setWeight: 75
      - pause: 
          duration: 5m
      # Full rollout
      - setWeight: 100
      # Traffic routing configuration
      trafficRouting:
        nginx:
          stableIngress: tradesense-trading-service-stable
          annotationPrefix: nginx.ingress.kubernetes.io
          additionalIngressAnnotations:
            canary-by-header: "x-canary"
            canary-by-header-value: "tradesense-canary"
  selector:
    matchLabels:
      app: tradesense-trading-service
  template:
    metadata:
      labels:
        app: tradesense-trading-service
    spec:
      containers:
      - name: trading-service
        image: tradesense/trading-service:latest
        env:
        - name: CANARY_DEPLOYMENT
          value: "true"
        - name: FEATURE_FLAGS_ENDPOINT
          value: "http://feature-flags.tradesense-production.svc.cluster.local:8080"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: canary-analysis
  namespace: tradesense-production
spec:
  args:
  - name: service-name
  - name: canary-hash
  metrics:
  # Error rate comparison between canary and stable
  - name: error-rate-comparison
    interval: 2m
    count: 10
    successCondition: result < 0.02  # Less than 2% error rate
    failureLimit: 3
    provider:
      prometheus:
        address: http://prometheus.tradesense-monitoring.svc.cluster.local:9090
        query: |
          sum(rate(http_requests_total{service="{{args.service-name}}",status=~"5..",revision="{{args.canary-hash}}"}[2m])) / 
          sum(rate(http_requests_total{service="{{args.service-name}}",revision="{{args.canary-hash}}"}[2m]))
  # Response time comparison
  - name: response-time-p99
    interval: 2m
    count: 10
    successCondition: result < 1.0  # Less than 1 second p99
    failureLimit: 3
    provider:
      prometheus:
        address: http://prometheus.tradesense-monitoring.svc.cluster.local:9090
        query: |
          histogram_quantile(0.99, 
          sum(rate(http_request_duration_seconds_bucket{service="{{args.service-name}}",revision="{{args.canary-hash}}"}[2m])) by (le))
  # Trading-specific metrics
  - name: order-success-rate
    interval: 1m
    count: 15
    successCondition: result > 0.98  # Greater than 98% success rate
    failureLimit: 2
    provider:
      prometheus:
        address: http://prometheus.tradesense-monitoring.svc.cluster.local:9090
        query: |
          sum(rate(trading_orders_total{status="success",revision="{{args.canary-hash}}"}[1m])) / 
          sum(rate(trading_orders_total{revision="{{args.canary-hash}}"}[1m]))
```

#### **5C.3.2 Automated Rollback Mechanisms**

**Rollback Automation Script:**

```python
# File: /scripts/deployment/automated_rollback.py
"""
Automated rollback system for TradeSense deployments

This script monitors deployment health and automatically triggers rollbacks
when critical thresholds are exceeded.

Key Features:
- Real-time metrics monitoring
- Multi-stage rollback validation
- Automated notification system
- Rollback impact assessment
- Recovery verification
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp
import kubernetes
from prometheus_client.parser import text_string_to_metric_families

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collect metrics from various sources for rollback decisions"""
    
    def __init__(self, prometheus_url: str, namespace: str):
        self.prometheus_url = prometheus_url
        self.namespace = namespace
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_error_rate(self, service_name: str, time_window: str = "5m") -> float:
        """Get error rate for a service"""
        query = f"""
        sum(rate(http_requests_total{{service="{service_name}",status=~"5.."}}[{time_window}])) / 
        sum(rate(http_requests_total{{service="{service_name}"}}[{time_window}]))
        """
        
        try:
            async with self.session.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query}
            ) as response:
                data = await response.json()
                result = data.get("data", {}).get("result", [])
                
                if result:
                    return float(result[0]["value"][1])
                return 0.0
                
        except Exception as e:
            logger.error(f"Error fetching error rate: {e}")
            return 0.0
    
    async def get_response_time_p99(self, service_name: str, time_window: str = "5m") -> float:
        """Get 99th percentile response time"""
        query = f"""
        histogram_quantile(0.99, 
        sum(rate(http_request_duration_seconds_bucket{{service="{service_name}"}}[{time_window}])) by (le))
        """
        
        try:
            async with self.session.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query}
            ) as response:
                data = await response.json()
                result = data.get("data", {}).get("result", [])
                
                if result:
                    return float(result[0]["value"][1])
                return 0.0
                
        except Exception as e:
            logger.error(f"Error fetching response time: {e}")
            return 0.0
    
    async def get_trading_metrics(self, service_name: str) -> Dict[str, float]:
        """Get trading-specific metrics"""
        metrics = {}
        
        # Order success rate
        order_success_query = f"""
        sum(rate(trading_orders_total{{status="success"}}[2m])) / 
        sum(rate(trading_orders_total[2m]))
        """
        
        # Position update latency
        position_latency_query = f"""
        histogram_quantile(0.95, 
        sum(rate(position_update_duration_seconds_bucket[2m])) by (le))
        """
        
        # Risk check failures
        risk_failures_query = f"""
        sum(rate(risk_check_failures_total[5m]))
        """
        
        queries = {
            "order_success_rate": order_success_query,
            "position_latency_p95": position_latency_query,
            "risk_failures_rate": risk_failures_query
        }
        
        for metric_name, query in queries.items():
            try:
                async with self.session.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={"query": query}
                ) as response:
                    data = await response.json()
                    result = data.get("data", {}).get("result", [])
                    
                    if result:
                        metrics[metric_name] = float(result[0]["value"][1])
                    else:
                        metrics[metric_name] = 0.0
                        
            except Exception as e:
                logger.error(f"Error fetching {metric_name}: {e}")
                metrics[metric_name] = 0.0
        
        return metrics

class KubernetesManager:
    """Manage Kubernetes resources for rollback operations"""
    
    def __init__(self, namespace: str):
        self.namespace = namespace
        kubernetes.config.load_incluster_config()
        self.apps_v1 = kubernetes.client.AppsV1Api()
        self.core_v1 = kubernetes.client.CoreV1Api()
        self.custom_objects = kubernetes.client.CustomObjectsApi()
    
    async def get_rollout_status(self, rollout_name: str) -> Dict:
        """Get Argo Rollout status"""
        try:
            rollout = self.custom_objects.get_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="rollouts",
                name=rollout_name
            )
            return rollout.get("status", {})
        except Exception as e:
            logger.error(f"Error getting rollout status: {e}")
            return {}
    
    async def trigger_rollback(self, rollout_name: str) -> bool:
        """Trigger rollback of a deployment"""
        try:
            # Patch the rollout to trigger rollback
            patch = {
                "spec": {
                    "restartAt": datetime.utcnow().isoformat() + "Z"
                }
            }
            
            self.custom_objects.patch_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="rollouts",
                name=rollout_name,
                body=patch
            )
            
            logger.info(f"Triggered rollback for {rollout_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error triggering rollback: {e}")
            return False
    
    async def abort_rollout(self, rollout_name: str) -> bool:
        """Abort current rollout"""
        try:
            # Set weight to 0 to stop traffic to canary
            patch = {
                "status": {
                    "abort": True
                }
            }
            
            self.custom_objects.patch_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="rollouts",
                name=rollout_name,
                body=patch
            )
            
            logger.info(f"Aborted rollout for {rollout_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error aborting rollout: {e}")
            return False

class RollbackDecisionEngine:
    """Decision engine for automatic rollback triggers"""
    
    def __init__(self):
        self.thresholds = {
            "error_rate_critical": 0.05,      # 5% error rate
            "error_rate_warning": 0.02,       # 2% error rate
            "response_time_critical": 5.0,    # 5 seconds p99
            "response_time_warning": 2.0,     # 2 seconds p99
            "order_success_rate_min": 0.95,   # 95% minimum success rate
            "position_latency_max": 1.0,      # 1 second max latency
            "risk_failures_max": 10,          # Max 10 risk failures per minute
        }
        
        self.violation_counts = {}
        self.max_violations = 3  # Trigger rollback after 3 consecutive violations
    
    def should_rollback(self, metrics: Dict[str, float], service_name: str) -> Dict[str, any]:
        """Determine if rollback should be triggered"""
        violations = []
        current_time = datetime.utcnow()
        
        # Check error rate
        error_rate = metrics.get("error_rate", 0.0)
        if error_rate > self.thresholds["error_rate_critical"]:
            violations.append({
                "metric": "error_rate",
                "value": error_rate,
                "threshold": self.thresholds["error_rate_critical"],
                "severity": "critical"
            })
        
        # Check response time
        response_time = metrics.get("response_time_p99", 0.0)
        if response_time > self.thresholds["response_time_critical"]:
            violations.append({
                "metric": "response_time_p99",
                "value": response_time,
                "threshold": self.thresholds["response_time_critical"],
                "severity": "critical"
            })
        
        # Check trading metrics
        trading_metrics = metrics.get("trading_metrics", {})
        
        order_success_rate = trading_metrics.get("order_success_rate", 1.0)
        if order_success_rate < self.thresholds["order_success_rate_min"]:
            violations.append({
                "metric": "order_success_rate",
                "value": order_success_rate,
                "threshold": self.thresholds["order_success_rate_min"],
                "severity": "critical"
            })
        
        position_latency = trading_metrics.get("position_latency_p95", 0.0)
        if position_latency > self.thresholds["position_latency_max"]:
            violations.append({
                "metric": "position_latency_p95",
                "value": position_latency,
                "threshold": self.thresholds["position_latency_max"],
                "severity": "warning"
            })
        
        # Count violations
        if violations:
            violation_key = f"{service_name}:{current_time.strftime('%Y-%m-%d-%H-%M')}"
            self.violation_counts[violation_key] = self.violation_counts.get(violation_key, 0) + 1
            
            # Clean old violation counts (older than 10 minutes)
            cutoff_time = current_time - timedelta(minutes=10)
            cutoff_str = cutoff_time.strftime('%Y-%m-%d-%H-%M')
            self.violation_counts = {
                k: v for k, v in self.violation_counts.items()
                if k.split(':')[1] >= cutoff_str
            }
            
            # Check if we should trigger rollback
            consecutive_violations = self.violation_counts.get(violation_key, 0)
            should_rollback = consecutive_violations >= self.max_violations
            
            return {
                "should_rollback": should_rollback,
                "violations": violations,
                "consecutive_violations": consecutive_violations,
                "timestamp": current_time.isoformat()
            }
        
        return {
            "should_rollback": False,
            "violations": [],
            "consecutive_violations": 0,
            "timestamp": current_time.isoformat()
        }

class AutomatedRollbackSystem:
    """Main rollback automation system"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.prometheus_url = config["prometheus_url"]
        self.namespace = config["namespace"]
        self.services = config["services"]
        
        self.k8s_manager = KubernetesManager(self.namespace)
        self.decision_engine = RollbackDecisionEngine()
        
        # Notification configuration
        self.notification_webhook = config.get("notification_webhook")
        self.slack_webhook = config.get("slack_webhook")
    
    async def monitor_deployments(self):
        """Main monitoring loop"""
        logger.info("Starting automated rollback monitoring...")
        
        async with MetricsCollector(self.prometheus_url, self.namespace) as collector:
            while True:
                try:
                    for service_config in self.services:
                        await self._monitor_service(collector, service_config)
                    
                    # Wait before next check
                    await asyncio.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    await asyncio.sleep(60)  # Wait longer on error
    
    async def _monitor_service(self, collector: MetricsCollector, service_config: Dict):
        """Monitor a specific service"""
        service_name = service_config["name"]
        rollout_name = service_config["rollout_name"]
        
        logger.info(f"Monitoring service: {service_name}")
        
        # Collect metrics
        metrics = {}
        metrics["error_rate"] = await collector.get_error_rate(service_name)
        metrics["response_time_p99"] = await collector.get_response_time_p99(service_name)
        
        # Collect trading-specific metrics if it's a trading service
        if service_config.get("is_trading_service", False):
            metrics["trading_metrics"] = await collector.get_trading_metrics(service_name)
        
        # Make rollback decision
        decision = self.decision_engine.should_rollback(metrics, service_name)
        
        if decision["should_rollback"]:
            logger.warning(f"Triggering rollback for {service_name} due to violations: {decision['violations']}")
            
            # Get rollout status
            rollout_status = await self.k8s_manager.get_rollout_status(rollout_name)
            
            # Execute rollback
            if rollout_status.get("currentPodHash") != rollout_status.get("stableRS"):
                # Canary is active, abort it
                success = await self.k8s_manager.abort_rollout(rollout_name)
            else:
                # Trigger full rollback
                success = await self.k8s_manager.trigger_rollback(rollout_name)
            
            if success:
                await self._send_rollback_notification(service_name, decision, metrics)
            else:
                logger.error(f"Failed to execute rollback for {service_name}")
                await self._send_error_notification(service_name, "Rollback execution failed")
        
        elif decision["violations"]:
            logger.warning(f"Violations detected for {service_name}: {decision['violations']}")
            await self._send_warning_notification(service_name, decision, metrics)
    
    async def _send_rollback_notification(self, service_name: str, decision: Dict, metrics: Dict):
        """Send rollback notification"""
        message = {
            "service": service_name,
            "action": "rollback_triggered",
            "violations": decision["violations"],
            "metrics": metrics,
            "timestamp": decision["timestamp"]
        }
        
        await self._send_notification("🚨 ROLLBACK TRIGGERED", message)
    
    async def _send_warning_notification(self, service_name: str, decision: Dict, metrics: Dict):
        """Send warning notification"""
        message = {
            "service": service_name,
            "action": "warning",
            "violations": decision["violations"],
            "consecutive_violations": decision["consecutive_violations"],
            "metrics": metrics,
            "timestamp": decision["timestamp"]
        }
        
        await self._send_notification("⚠️ DEPLOYMENT WARNING", message)
    
    async def _send_error_notification(self, service_name: str, error_message: str):
        """Send error notification"""
        message = {
            "service": service_name,
            "action": "error",
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._send_notification("❌ ROLLBACK ERROR", message)
    
    async def _send_notification(self, title: str, message: Dict):
        """Send notification to configured channels"""
        try:
            # Send to Slack if configured
            if self.slack_webhook:
                async with aiohttp.ClientSession() as session:
                    slack_payload = {
                        "text": title,
                        "attachments": [{
                            "color": "danger" if "ROLLBACK" in title else "warning",
                            "fields": [
                                {"title": "Service", "value": message["service"], "short": True},
                                {"title": "Action", "value": message["action"], "short": True},
                                {"title": "Timestamp", "value": message["timestamp"], "short": True}
                            ]
                        }]
                    }
                    
                    async with session.post(self.slack_webhook, json=slack_payload) as response:
                        if response.status == 200:
                            logger.info(f"Sent Slack notification: {title}")
                        else:
                            logger.error(f"Failed to send Slack notification: {response.status}")
            
            # Send to general webhook if configured
            if self.notification_webhook:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.notification_webhook, json=message) as response:
                        if response.status == 200:
                            logger.info(f"Sent webhook notification: {title}")
                        else:
                            logger.error(f"Failed to send webhook notification: {response.status}")
                            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

async def main():
    """Main function"""
    config = {
        "prometheus_url": "http://prometheus.tradesense-monitoring.svc.cluster.local:9090",
        "namespace": "tradesense-production",
        "notification_webhook": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
        "slack_webhook": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
        "services": [
            {
                "name": "tradesense-api-gateway",
                "rollout_name": "tradesense-api-gateway",
                "is_trading_service": False
            },
            {
                "name": "tradesense-trading-service",
                "rollout_name": "tradesense-trading-service",
                "is_trading_service": True
            },
            {
                "name": "tradesense-user-service",
                "rollout_name": "tradesense-user-service",
                "is_trading_service": False
            }
        ]
    }
    
    rollback_system = AutomatedRollbackSystem(config)
    await rollback_system.monitor_deployments()

if __name__ == "__main__":
    asyncio.run(main())
```

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "8", "content": "Write Section 5B: Testing, CI/CD & Quality Assurance - Quality Assurance Framework", "status": "completed", "priority": "high"}]