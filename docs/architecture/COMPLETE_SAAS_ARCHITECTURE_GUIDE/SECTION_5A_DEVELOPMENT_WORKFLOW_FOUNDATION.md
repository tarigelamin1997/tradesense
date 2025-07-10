# Section 5A: Development Workflow Foundation
*Extracted from ARCHITECTURE_STRATEGY_PART4.md*

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

