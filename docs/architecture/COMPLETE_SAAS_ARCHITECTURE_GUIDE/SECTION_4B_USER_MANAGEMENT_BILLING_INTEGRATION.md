# Section 4B: User Management & Billing Integration
*Extracted from ARCHITECTURE_STRATEGY_PART2.md*

---

## SECTION 4B: USER MANAGEMENT & BILLING INTEGRATION

### Strategic Overview

User management and billing integration form the **commercial backbone** of the TradeSense v2.7.0 SaaS platform. This section details the comprehensive architecture for managing user lifecycles, subscription models, payment processing, and usage-based billing that enables scalable revenue generation from **$29/month starter plans to $50,000+/year enterprise contracts**.

The architecture implements a **state machine-driven user lifecycle**, **flexible subscription models**, **multi-provider payment processing**, and **real-time usage tracking**—all designed to support rapid business growth while maintaining operational efficiency and compliance.

---

### User Lifecycle Management

#### Comprehensive State Machine Design

The user lifecycle is managed through a sophisticated state machine with **13 distinct states** and **18 transition events**, ensuring consistent user management across all scenarios:

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Callable
from datetime import datetime

class UserState(Enum):
    """Comprehensive user lifecycle states"""
    
    # Registration states
    PENDING_REGISTRATION = "pending_registration"  # Email sent, not confirmed
    PENDING_APPROVAL = "pending_approval"          # Awaiting admin approval
    
    # Active states
    TRIAL = "trial"                               # In trial period
    ACTIVE = "active"                             # Paid, active subscription
    
    # Restricted states
    SUSPENDED = "suspended"                       # Admin suspended
    PAYMENT_FAILED = "payment_failed"             # Payment issue
    GRACE_PERIOD = "grace_period"                 # Payment grace period
    OVER_LIMIT = "over_limit"                     # Usage limit exceeded
    
    # Inactive states
    DEACTIVATED = "deactivated"                   # User deactivated
    DISABLED = "disabled"                         # Admin disabled
    CHURNED = "churned"                          # Subscription cancelled
    
    # Final states
    DELETED = "deleted"                           # Soft deleted
    PURGED = "purged"                            # GDPR compliant purge

class UserLifecycleEvent(Enum):
    """User lifecycle transition events"""
    
    # Registration events
    EMAIL_VERIFIED = "email_verified"
    ADMIN_APPROVED = "admin_approved"
    ADMIN_REJECTED = "admin_rejected"
    
    # Subscription events
    TRIAL_STARTED = "trial_started"
    TRIAL_ENDED = "trial_ended"
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_RENEWED = "subscription_renewed"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    
    # Payment events
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"
    GRACE_PERIOD_ENDED = "grace_period_ended"
    
    # Administrative events
    USER_SUSPENDED = "user_suspended"
    USER_REACTIVATED = "user_reactivated"
    USER_DISABLED = "user_disabled"
    
    # Usage events
    LIMIT_EXCEEDED = "limit_exceeded"
    LIMIT_RESET = "limit_reset"
    
    # Deletion events
    DELETION_REQUESTED = "deletion_requested"
    PURGE_SCHEDULED = "purge_scheduled"

@dataclass
class StateTransition:
    """Defines valid state transitions"""
    
    from_state: UserState
    event: UserLifecycleEvent
    to_state: UserState
    conditions: List[Callable] = field(default_factory=list)
    actions: List[Callable] = field(default_factory=list)
    notifications: List[str] = field(default_factory=list)
    requires_approval: bool = False

class UserLifecycleStateMachine:
    """Manages user state transitions with business rules"""
    
    def __init__(self):
        self._transitions = self._define_transitions()
        self._state_handlers = self._define_state_handlers()
    
    def _define_transitions(self) -> Dict[Tuple[UserState, UserLifecycleEvent], StateTransition]:
        """Define all valid state transitions"""
        
        transitions = [
            # Registration flow
            StateTransition(
                from_state=UserState.PENDING_REGISTRATION,
                event=UserLifecycleEvent.EMAIL_VERIFIED,
                to_state=UserState.TRIAL,
                conditions=[self._is_auto_approval_enabled],
                actions=[
                    self._create_trial_subscription,
                    self._send_welcome_email,
                    self._track_conversion
                ],
                notifications=["user_activated", "trial_started"]
            ),
            
            StateTransition(
                from_state=UserState.PENDING_REGISTRATION,
                event=UserLifecycleEvent.EMAIL_VERIFIED,
                to_state=UserState.PENDING_APPROVAL,
                conditions=[self._requires_admin_approval],
                actions=[self._notify_admins],
                notifications=["approval_required"]
            ),
            
            # Trial to paid conversion
            StateTransition(
                from_state=UserState.TRIAL,
                event=UserLifecycleEvent.SUBSCRIPTION_CREATED,
                to_state=UserState.ACTIVE,
                conditions=[self._has_valid_payment_method],
                actions=[
                    self._charge_subscription,
                    self._upgrade_features,
                    self._send_upgrade_confirmation
                ],
                notifications=["subscription_activated", "payment_processed"]
            ),
            
            # Payment failure handling
            StateTransition(
                from_state=UserState.ACTIVE,
                event=UserLifecycleEvent.PAYMENT_FAILED,
                to_state=UserState.PAYMENT_FAILED,
                actions=[
                    self._disable_premium_features,
                    self._send_payment_failed_email,
                    self._schedule_retry
                ],
                notifications=["payment_failed", "features_restricted"]
            ),
            
            StateTransition(
                from_state=UserState.PAYMENT_FAILED,
                event=UserLifecycleEvent.PAYMENT_SUCCEEDED,
                to_state=UserState.ACTIVE,
                actions=[
                    self._restore_features,
                    self._clear_payment_flags,
                    self._send_payment_success_email
                ],
                notifications=["payment_recovered", "features_restored"]
            ),
            
            # Grace period management
            StateTransition(
                from_state=UserState.PAYMENT_FAILED,
                event=UserLifecycleEvent.GRACE_PERIOD_ENDED,
                to_state=UserState.CHURNED,
                conditions=[self._grace_period_expired],
                actions=[
                    self._cancel_subscription,
                    self._disable_all_features,
                    self._send_churn_email,
                    self._trigger_win_back_campaign
                ],
                notifications=["user_churned", "subscription_cancelled"]
            ),
            
            # Administrative actions
            StateTransition(
                from_state=UserState.ACTIVE,
                event=UserLifecycleEvent.USER_SUSPENDED,
                to_state=UserState.SUSPENDED,
                requires_approval=True,
                actions=[
                    self._log_suspension_reason,
                    self._disable_access,
                    self._notify_user_suspension
                ],
                notifications=["user_suspended", "admin_action"]
            ),
            
            # Deletion flow
            StateTransition(
                from_state=UserState.ACTIVE,
                event=UserLifecycleEvent.DELETION_REQUESTED,
                to_state=UserState.DELETED,
                conditions=[self._can_delete_user],
                actions=[
                    self._anonymize_personal_data,
                    self._retain_legal_records,
                    self._schedule_purge
                ],
                notifications=["deletion_initiated", "purge_scheduled"]
            ),
            
            # Add remaining transitions...
        ]
        
        # Build transition map
        transition_map = {}
        for transition in transitions:
            key = (transition.from_state, transition.event)
            transition_map[key] = transition
        
        return transition_map
    
    async def handle_event(
        self,
        user: User,
        event: UserLifecycleEvent,
        context: Dict[str, Any]
    ) -> TransitionResult:
        """Process lifecycle event for user"""
        
        current_state = user.lifecycle_state
        transition_key = (current_state, event)
        
        # Check if transition is valid
        if transition_key not in self._transitions:
            return TransitionResult(
                success=False,
                error=f"Invalid transition: {current_state} + {event}"
            )
        
        transition = self._transitions[transition_key]
        
        # Check conditions
        for condition in transition.conditions:
            if not await condition(user, context):
                return TransitionResult(
                    success=False,
                    error=f"Condition failed for transition"
                )
        
        # Check approval requirements
        if transition.requires_approval and not context.get("approved_by"):
            return TransitionResult(
                success=False,
                error="Transition requires administrative approval",
                requires_approval=True
            )
        
        # Execute pre-transition actions
        for action in transition.actions:
            await action(user, context)
        
        # Update user state
        old_state = user.lifecycle_state
        user.lifecycle_state = transition.to_state
        user.lifecycle_updated_at = datetime.utcnow()
        
        # Log transition
        await self._log_transition(
            user=user,
            from_state=old_state,
            to_state=transition.to_state,
            event=event,
            context=context
        )
        
        # Send notifications
        for notification in transition.notifications:
            await self._send_notification(
                notification_type=notification,
                user=user,
                context=context
            )
        
        return TransitionResult(
            success=True,
            from_state=old_state,
            to_state=transition.to_state,
            notifications_sent=transition.notifications
        )
```

#### User Registration and Onboarding

```python
@dataclass
class RegistrationRequest:
    """User registration data"""
    
    # Required fields
    email: str
    password: str
    tenant_id: str
    
    # Optional profile
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    phone_number: Optional[str] = None
    
    # Marketing attribution
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    referral_code: Optional[str] = None
    
    # Consent tracking
    terms_accepted: bool = False
    marketing_consent: bool = False
    
    # Registration method
    registration_method: str = "email"  # email, google, microsoft, saml
    oauth_provider: Optional[str] = None
    
    # Device/location info
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timezone: Optional[str] = None

class UserRegistrationService:
    """Comprehensive user registration service"""
    
    def __init__(
        self,
        user_repository: UserRepository,
        email_service: EmailService,
        tenant_service: TenantService,
        lifecycle_machine: UserLifecycleStateMachine
    ):
        self._user_repo = user_repository
        self._email_service = email_service
        self._tenant_service = tenant_service
        self._lifecycle = lifecycle_machine
    
    async def register_user(
        self,
        request: RegistrationRequest
    ) -> RegistrationResult:
        """Complete user registration flow"""
        
        # Validate tenant
        tenant = await self._tenant_service.get_by_id(request.tenant_id)
        if not tenant or tenant.status != TenantStatus.ACTIVE:
            raise InvalidTenantError("Invalid or inactive tenant")
        
        # Validate registration against tenant policies
        await self._validate_registration(request, tenant)
        
        # Check for existing user
        existing = await self._user_repo.find_by_email(
            email=request.email,
            tenant_id=request.tenant_id
        )
        if existing:
            raise UserAlreadyExistsError("User already registered")
        
        # Create user record
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=request.tenant_id,
            email=request.email,
            email_normalized=request.email.lower(),
            password_hash=await self._hash_password(request.password),
            
            # Profile
            first_name=request.first_name,
            last_name=request.last_name,
            company_name=request.company_name,
            phone_number=request.phone_number,
            
            # State
            lifecycle_state=UserState.PENDING_REGISTRATION,
            email_verified=False,
            
            # Attribution
            registration_source={
                "method": request.registration_method,
                "utm_source": request.utm_source,
                "utm_medium": request.utm_medium,
                "utm_campaign": request.utm_campaign,
                "referral_code": request.referral_code
            },
            
            # Consent
            terms_accepted_at=datetime.utcnow() if request.terms_accepted else None,
            marketing_consent=request.marketing_consent,
            
            # Metadata
            created_at=datetime.utcnow(),
            last_login_at=None,
            login_count=0
        )
        
        # Save user
        await self._user_repo.create(user)
        
        # Send verification email
        if request.registration_method == "email":
            await self._send_verification_email(user)
        
        # Auto-verify for OAuth registrations
        if request.registration_method in ["google", "microsoft"]:
            await self._lifecycle.handle_event(
                user=user,
                event=UserLifecycleEvent.EMAIL_VERIFIED,
                context={"auto_verified": True}
            )
        
        # Track registration
        await self._track_registration(user, request)
        
        return RegistrationResult(
            user_id=user.id,
            requires_email_verification=request.registration_method == "email",
            trial_days=tenant.trial_duration_days
        )
    
    async def _validate_registration(
        self,
        request: RegistrationRequest,
        tenant: Tenant
    ) -> None:
        """Validate registration against policies"""
        
        # Email domain restrictions
        if tenant.allowed_email_domains:
            domain = request.email.split("@")[1]
            if domain not in tenant.allowed_email_domains:
                raise RegistrationNotAllowedError(
                    f"Email domain {domain} not allowed"
                )
        
        # Password policies
        if request.password:
            password_policy = tenant.security_config.get("password_policy", {})
            
            if len(request.password) < password_policy.get("min_length", 8):
                raise WeakPasswordError("Password too short")
            
            if password_policy.get("require_uppercase", True):
                if not any(c.isupper() for c in request.password):
                    raise WeakPasswordError("Password must contain uppercase")
            
            if password_policy.get("require_special", True):
                if not any(c in "!@#$%^&*" for c in request.password):
                    raise WeakPasswordError("Password must contain special character")
        
        # Rate limiting
        registrations_today = await self._count_recent_registrations(
            ip_address=request.ip_address
        )
        if registrations_today > 10:
            raise RateLimitExceededError("Too many registration attempts")
        
        # Required fields based on tenant config
        required_fields = tenant.registration_config.get("required_fields", [])
        for field in required_fields:
            if not getattr(request, field, None):
                raise MissingRequiredFieldError(f"Field {field} is required")
```

### Subscription Management

#### Flexible Subscription Models

```python
from decimal import Decimal
from typing import List, Optional, Dict, Any

@dataclass
class SubscriptionPlan:
    """Comprehensive subscription plan definition"""
    
    # Identification
    id: str
    name: str
    description: str
    
    # Pricing
    base_price: Decimal
    billing_period: BillingPeriod  # monthly, yearly
    currency: str = "USD"
    
    # Pricing model
    pricing_model: PricingModel  # flat, usage, tiered, hybrid
    
    # Resource limits
    limits: Dict[str, int] = field(default_factory=dict)
    # {
    #     "users": 10,
    #     "portfolios": 5,
    #     "trades_per_month": 10000,
    #     "api_calls_per_day": 1000,
    #     "storage_gb": 10,
    #     "backtests_per_month": 100
    # }
    
    # Feature access
    features: List[str] = field(default_factory=list)
    # ["basic_analytics", "advanced_charts", "api_access", "team_collaboration"]
    
    # Usage-based pricing tiers
    usage_tiers: Optional[List[UsageTier]] = None
    
    # Add-ons available
    available_addons: List[str] = field(default_factory=list)
    
    # Trial configuration
    trial_days: int = 14
    trial_limits: Optional[Dict[str, int]] = None
    
    # Display configuration
    is_popular: bool = False
    is_enterprise: bool = False
    display_order: int = 0

@dataclass
class UsageTier:
    """Usage-based pricing tier"""
    
    metric: str  # api_calls, storage_gb, trades
    from_amount: int
    to_amount: Optional[int]  # None for unlimited
    unit_price: Decimal
    
    def calculate_cost(self, usage: int) -> Decimal:
        """Calculate cost for usage in this tier"""
        
        if self.to_amount is None:
            # Unlimited tier
            tier_usage = max(0, usage - self.from_amount)
        else:
            # Bounded tier
            tier_usage = max(0, min(usage, self.to_amount) - self.from_amount)
        
        return Decimal(tier_usage) * self.unit_price

# Define subscription plans
SUBSCRIPTION_PLANS = {
    "free": SubscriptionPlan(
        id="free",
        name="Free",
        description="Perfect for getting started",
        base_price=Decimal("0"),
        billing_period=BillingPeriod.MONTHLY,
        pricing_model=PricingModel.FLAT,
        limits={
            "users": 1,
            "portfolios": 1,
            "trades_per_month": 100,
            "api_calls_per_day": 100,
            "storage_gb": 1,
            "backtests_per_month": 10
        },
        features=[
            "basic_analytics",
            "portfolio_tracking",
            "manual_trade_entry",
            "basic_reports"
        ],
        trial_days=0  # No trial for free plan
    ),
    
    "starter": SubscriptionPlan(
        id="starter",
        name="Starter",
        description="For individual traders",
        base_price=Decimal("29"),
        billing_period=BillingPeriod.MONTHLY,
        pricing_model=PricingModel.FLAT,
        limits={
            "users": 1,
            "portfolios": 3,
            "trades_per_month": 1000,
            "api_calls_per_day": 1000,
            "storage_gb": 5,
            "backtests_per_month": 50
        },
        features=[
            "advanced_analytics",
            "real_time_sync",
            "broker_integration",
            "custom_indicators",
            "email_alerts",
            "api_access"
        ],
        available_addons=["extra_portfolio", "extra_storage"],
        trial_days=14
    ),
    
    "professional": SubscriptionPlan(
        id="professional",
        name="Professional",
        description="For serious traders",
        base_price=Decimal("99"),
        billing_period=BillingPeriod.MONTHLY,
        pricing_model=PricingModel.HYBRID,
        limits={
            "users": 3,
            "portfolios": 10,
            "trades_per_month": 10000,
            "api_calls_per_day": 5000,
            "storage_gb": 20,
            "backtests_per_month": 200
        },
        features=[
            "ai_insights",
            "advanced_risk_analytics",
            "multi_broker_sync",
            "automated_strategies",
            "priority_support",
            "advanced_api",
            "webhook_integrations"
        ],
        usage_tiers=[
            UsageTier(
                metric="api_calls",
                from_amount=5000,
                to_amount=10000,
                unit_price=Decimal("0.01")
            ),
            UsageTier(
                metric="api_calls",
                from_amount=10000,
                to_amount=None,
                unit_price=Decimal("0.005")
            )
        ],
        is_popular=True,
        trial_days=14
    ),
    
    "business": SubscriptionPlan(
        id="business",
        name="Business",
        description="For trading teams",
        base_price=Decimal("199"),
        billing_period=BillingPeriod.MONTHLY,
        pricing_model=PricingModel.HYBRID,
        limits={
            "users": 10,
            "portfolios": 50,
            "trades_per_month": 50000,
            "api_calls_per_day": 20000,
            "storage_gb": 100,
            "backtests_per_month": 1000
        },
        features=[
            "team_collaboration",
            "role_based_access",
            "audit_trails",
            "compliance_reports",
            "custom_branding",
            "dedicated_account_manager",
            "sla_guarantee",
            "phone_support"
        ],
        available_addons=["extra_user", "dedicated_server", "custom_integration"],
        trial_days=30
    ),
    
    "enterprise": SubscriptionPlan(
        id="enterprise",
        name="Enterprise",
        description="Custom solutions for large organizations",
        base_price=Decimal("0"),  # Custom pricing
        billing_period=BillingPeriod.YEARLY,
        pricing_model=PricingModel.CUSTOM,
        limits={},  # No hard limits
        features=[
            "unlimited_everything",
            "white_label",
            "custom_features",
            "on_premise_option",
            "dedicated_infrastructure",
            "24_7_support",
            "custom_sla",
            "training_included"
        ],
        is_enterprise=True
    )
}

class SubscriptionService:
    """Manages subscription lifecycle"""
    
    async def create_subscription(
        self,
        user: User,
        plan_id: str,
        payment_method_id: Optional[str] = None,
        trial_override_days: Optional[int] = None
    ) -> Subscription:
        """Create new subscription for user"""
        
        plan = SUBSCRIPTION_PLANS.get(plan_id)
        if not plan:
            raise InvalidPlanError(f"Plan {plan_id} not found")
        
        # Check if user can subscribe to plan
        await self._validate_subscription_eligibility(user, plan)
        
        # Calculate trial end date
        trial_days = trial_override_days or plan.trial_days
        trial_end_date = None
        if trial_days > 0:
            trial_end_date = datetime.utcnow() + timedelta(days=trial_days)
        
        # Create subscription
        subscription = Subscription(
            id=str(uuid.uuid4()),
            user_id=user.id,
            tenant_id=user.tenant_id,
            plan_id=plan.id,
            
            # Status
            status=SubscriptionStatus.TRIALING if trial_end_date else SubscriptionStatus.ACTIVE,
            
            # Billing
            current_period_start=datetime.utcnow(),
            current_period_end=self._calculate_period_end(plan.billing_period),
            trial_end=trial_end_date,
            
            # Payment
            payment_method_id=payment_method_id,
            
            # Usage limits
            usage_limits=plan.limits.copy(),
            
            # Features
            enabled_features=plan.features.copy(),
            
            # Metadata
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save subscription
        await self._subscription_repo.create(subscription)
        
        # Initialize usage tracking
        await self._initialize_usage_tracking(subscription)
        
        # Update user state
        await self._lifecycle.handle_event(
            user=user,
            event=UserLifecycleEvent.SUBSCRIPTION_CREATED,
            context={"subscription_id": subscription.id}
        )
        
        # Send confirmation
        await self._send_subscription_confirmation(user, subscription, plan)
        
        return subscription
```

### Payment Processing

#### Multi-Provider Payment Integration

```python
class PaymentProvider(Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    PADDLE = "paddle"

@dataclass
class PaymentIntent:
    """Payment processing intent"""
    
    id: str
    provider: PaymentProvider
    amount: Decimal
    currency: str
    
    # Customer info
    customer_id: str
    payment_method_id: str
    
    # Status
    status: PaymentStatus
    
    # Provider-specific data
    provider_intent_id: str
    provider_response: Dict[str, Any]
    
    # Metadata
    description: str
    metadata: Dict[str, str]
    created_at: datetime

class PaymentService:
    """Unified payment processing service"""
    
    def __init__(self, providers: Dict[PaymentProvider, PaymentProviderInterface]):
        self._providers = providers
        self._webhook_processor = WebhookProcessor()
    
    async def process_payment(
        self,
        user: User,
        amount: Decimal,
        currency: str,
        payment_method_id: str,
        description: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> PaymentResult:
        """Process payment through configured provider"""
        
        # Get user's payment provider
        provider = await self._get_user_payment_provider(user)
        
        # Create payment intent
        intent = PaymentIntent(
            id=str(uuid.uuid4()),
            provider=provider,
            amount=amount,
            currency=currency,
            customer_id=user.payment_customer_id,
            payment_method_id=payment_method_id,
            status=PaymentStatus.PENDING,
            description=description,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )
        
        # Process through provider
        try:
            provider_impl = self._providers[provider]
            result = await provider_impl.charge(
                customer_id=intent.customer_id,
                amount=intent.amount,
                currency=intent.currency,
                payment_method_id=intent.payment_method_id,
                description=intent.description,
                metadata=intent.metadata
            )
            
            # Update intent
            intent.status = PaymentStatus.SUCCEEDED
            intent.provider_intent_id = result.transaction_id
            intent.provider_response = result.raw_response
            
            # Save payment record
            await self._save_payment_record(intent, user)
            
            # Update subscription if applicable
            if metadata and metadata.get("subscription_id"):
                await self._update_subscription_payment(
                    subscription_id=metadata["subscription_id"],
                    payment_intent=intent
                )
            
            return PaymentResult(
                success=True,
                payment_id=intent.id,
                transaction_id=result.transaction_id
            )
            
        except PaymentError as e:
            # Handle payment failure
            intent.status = PaymentStatus.FAILED
            intent.provider_response = {"error": str(e)}
            
            await self._save_payment_record(intent, user)
            
            # Handle specific error types
            if isinstance(e, InsufficientFundsError):
                await self._handle_insufficient_funds(user, intent)
            elif isinstance(e, CardExpiredError):
                await self._handle_expired_card(user, intent)
            elif isinstance(e, FraudDetectedError):
                await self._handle_fraud_detection(user, intent)
            
            raise

class StripePaymentProvider(PaymentProviderInterface):
    """Stripe payment provider implementation"""
    
    def __init__(self, api_key: str, webhook_secret: str):
        stripe.api_key = api_key
        self._webhook_secret = webhook_secret
    
    async def charge(
        self,
        customer_id: str,
        amount: Decimal,
        currency: str,
        payment_method_id: str,
        description: str,
        metadata: Dict[str, str]
    ) -> ProviderPaymentResult:
        """Process payment through Stripe"""
        
        try:
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                customer=customer_id,
                amount=int(amount * 100),  # Convert to cents
                currency=currency.lower(),
                payment_method=payment_method_id,
                description=description,
                metadata=metadata,
                confirm=True,
                off_session=True,
                error_on_requires_action=True
            )
            
            return ProviderPaymentResult(
                transaction_id=intent.id,
                status="succeeded",
                raw_response=intent.to_dict()
            )
            
        except stripe.error.CardError as e:
            error_code = e.error.code
            
            if error_code == "insufficient_funds":
                raise InsufficientFundsError(str(e))
            elif error_code == "expired_card":
                raise CardExpiredError(str(e))
            elif error_code == "card_declined":
                raise CardDeclinedError(str(e))
            else:
                raise PaymentError(f"Card error: {str(e)}")
                
        except stripe.error.RateLimitError:
            raise PaymentProviderError("Rate limit exceeded, please retry")
            
        except stripe.error.InvalidRequestError as e:
            raise PaymentError(f"Invalid request: {str(e)}")
            
        except stripe.error.AuthenticationError:
            raise PaymentProviderError("Authentication failed")
            
        except stripe.error.APIConnectionError:
            raise PaymentProviderError("Network error, please retry")
            
        except stripe.error.StripeError as e:
            raise PaymentProviderError(f"Payment failed: {str(e)}")
    
    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: Optional[int] = None
    ) -> ProviderSubscriptionResult:
        """Create Stripe subscription"""
        
        subscription_data = {
            "customer": customer_id,
            "items": [{"price": price_id}],
            "payment_behavior": "default_incomplete",
            "expand": ["latest_invoice.payment_intent"]
        }
        
        if trial_days:
            subscription_data["trial_period_days"] = trial_days
        
        subscription = stripe.Subscription.create(**subscription_data)
        
        return ProviderSubscriptionResult(
            subscription_id=subscription.id,
            status=subscription.status,
            current_period_end=datetime.fromtimestamp(
                subscription.current_period_end
            ),
            raw_response=subscription.to_dict()
        )
```

### Usage Tracking and Metering

#### Real-Time Usage Tracking

```python
@dataclass
class UsageEvent:
    """Individual usage event"""
    
    id: str
    tenant_id: str
    user_id: str
    
    # Event details
    metric_type: str  # api_calls, storage_bytes, trades_processed
    quantity: Decimal
    timestamp: datetime
    
    # Context
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    operation: Optional[str] = None
    
    # Technical metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    api_key_id: Optional[str] = None
    
    # Billing context
    subscription_id: Optional[str] = None
    billable: bool = True
    
    # Processing
    processed: bool = False
    aggregated: bool = False

class UsageTrackingService:
    """Real-time usage tracking and aggregation"""
    
    def __init__(
        self,
        event_store: EventStore,
        redis_client: Redis,
        time_series_db: TimeSeriesDB
    ):
        self._event_store = event_store
        self._redis = redis_client
        self._tsdb = time_series_db
        self._aggregator = UsageAggregator()
    
    async def track_usage(
        self,
        user_id: str,
        metric_type: str,
        quantity: Decimal,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track usage event asynchronously"""
        
        # Get user and subscription context
        user = await self._get_user(user_id)
        subscription = await self._get_active_subscription(user_id)
        
        # Create usage event
        event = UsageEvent(
            id=str(uuid.uuid4()),
            tenant_id=user.tenant_id,
            user_id=user_id,
            metric_type=metric_type,
            quantity=quantity,
            timestamp=datetime.utcnow(),
            subscription_id=subscription.id if subscription else None,
            billable=subscription.plan.pricing_model != PricingModel.FLAT,
            **context or {}
        )
        
        # Store event
        await self._event_store.append(event)
        
        # Update real-time counters
        await self._update_realtime_usage(event)
        
        # Check usage limits
        await self._check_usage_limits(user, subscription, event)
        
        # Queue for aggregation
        await self._queue_for_aggregation(event)
    
    async def _update_realtime_usage(self, event: UsageEvent) -> None:
        """Update real-time usage counters in Redis"""
        
        # Daily counter
        daily_key = f"usage:{event.tenant_id}:{event.user_id}:{event.metric_type}:daily:{datetime.utcnow().date()}"
        await self._redis.incrbyfloat(daily_key, float(event.quantity))
        await self._redis.expire(daily_key, 86400 * 2)  # 2 days TTL
        
        # Monthly counter
        month_key = f"usage:{event.tenant_id}:{event.user_id}:{event.metric_type}:monthly:{datetime.utcnow().strftime('%Y-%m')}"
        await self._redis.incrbyfloat(month_key, float(event.quantity))
        await self._redis.expire(month_key, 86400 * 35)  # 35 days TTL
        
        # Update time series
        await self._tsdb.write(
            metric=f"usage.{event.metric_type}",
            value=float(event.quantity),
            tags={
                "tenant_id": event.tenant_id,
                "user_id": event.user_id,
                "subscription_id": event.subscription_id or "none"
            },
            timestamp=event.timestamp
        )
    
    async def _check_usage_limits(
        self,
        user: User,
        subscription: Optional[Subscription],
        event: UsageEvent
    ) -> None:
        """Check if usage exceeds limits"""
        
        if not subscription:
            return
        
        # Get limit for metric
        limit_key = self._map_metric_to_limit(event.metric_type)
        limit = subscription.usage_limits.get(limit_key)
        
        if not limit:
            return  # No limit for this metric
        
        # Get current usage
        period = self._get_limit_period(limit_key)
        current_usage = await self.get_usage_for_period(
            user_id=user.id,
            metric_type=event.metric_type,
            period=period
        )
        
        # Check if exceeded
        if current_usage > limit:
            # Calculate overage percentage
            overage_pct = ((current_usage - limit) / limit) * 100
            
            # Trigger different actions based on overage
            if overage_pct < 10:
                # Soft limit - just notify
                await self._send_usage_warning(user, limit_key, current_usage, limit)
            elif overage_pct < 25:
                # Approaching hard limit
                await self._send_usage_alert(user, limit_key, current_usage, limit)
                await self._notify_account_manager(user, subscription)
            else:
                # Hard limit exceeded
                await self._handle_limit_exceeded(user, subscription, limit_key)
    
    async def get_usage_summary(
        self,
        user_id: str,
        period: UsagePeriod
    ) -> UsageSummary:
        """Get usage summary for billing period"""
        
        subscription = await self._get_active_subscription(user_id)
        
        # Aggregate usage by metric
        usage_by_metric = {}
        costs_by_metric = {}
        
        for metric_type in TRACKED_METRICS:
            # Get usage amount
            usage = await self.get_usage_for_period(
                user_id=user_id,
                metric_type=metric_type,
                period=period
            )
            usage_by_metric[metric_type] = usage
            
            # Calculate cost if applicable
            if subscription and subscription.plan.pricing_model != PricingModel.FLAT:
                cost = await self._calculate_usage_cost(
                    subscription=subscription,
                    metric_type=metric_type,
                    usage=usage
                )
                costs_by_metric[metric_type] = cost
        
        # Calculate totals
        total_cost = sum(costs_by_metric.values())
        
        return UsageSummary(
            user_id=user_id,
            period_start=period.start,
            period_end=period.end,
            usage_by_metric=usage_by_metric,
            costs_by_metric=costs_by_metric,
            total_cost=total_cost,
            subscription_id=subscription.id if subscription else None,
            generated_at=datetime.utcnow()
        )
```

### Billing and Invoicing

#### Automated Billing System

```python
class BillingService:
    """Comprehensive billing and invoicing service"""
    
    def __init__(
        self,
        subscription_service: SubscriptionService,
        payment_service: PaymentService,
        usage_service: UsageTrackingService,
        invoice_service: InvoiceService
    ):
        self._subscriptions = subscription_service
        self._payments = payment_service
        self._usage = usage_service
        self._invoices = invoice_service
    
    async def process_billing_cycle(
        self,
        subscription: Subscription
    ) -> BillingResult:
        """Process complete billing cycle for subscription"""
        
        try:
            # Calculate charges
            charges = await self._calculate_subscription_charges(subscription)
            
            # Create invoice
            invoice = await self._invoices.create_invoice(
                subscription=subscription,
                charges=charges,
                period_start=subscription.current_period_start,
                period_end=subscription.current_period_end
            )
            
            # Process payment
            payment_result = await self._payments.process_payment(
                user=subscription.user,
                amount=invoice.total_amount,
                currency=invoice.currency,
                payment_method_id=subscription.payment_method_id,
                description=f"Invoice {invoice.number}",
                metadata={
                    "subscription_id": subscription.id,
                    "invoice_id": invoice.id
                }
            )
            
            # Update invoice status
            invoice.status = InvoiceStatus.PAID
            invoice.paid_at = datetime.utcnow()
            invoice.payment_id = payment_result.payment_id
            await self._invoices.update(invoice)
            
            # Update subscription period
            await self._update_subscription_period(subscription)
            
            # Send invoice
            await self._send_invoice_email(subscription.user, invoice)
            
            return BillingResult(
                success=True,
                invoice_id=invoice.id,
                payment_id=payment_result.payment_id,
                next_billing_date=subscription.current_period_end
            )
            
        except PaymentError as e:
            # Handle payment failure
            await self._handle_billing_failure(subscription, e)
            raise
    
    async def _calculate_subscription_charges(
        self,
        subscription: Subscription
    ) -> List[InvoiceLineItem]:
        """Calculate all charges for subscription"""
        
        charges = []
        plan = SUBSCRIPTION_PLANS[subscription.plan_id]
        
        # Base subscription charge
        charges.append(
            InvoiceLineItem(
                description=f"{plan.name} Plan - {plan.billing_period.value}",
                quantity=1,
                unit_price=plan.base_price,
                amount=plan.base_price,
                type=LineItemType.SUBSCRIPTION
            )
        )
        
        # Calculate usage-based charges
        if plan.pricing_model in [PricingModel.USAGE, PricingModel.HYBRID]:
            usage_charges = await self._calculate_usage_charges(
                subscription=subscription,
                plan=plan
            )
            charges.extend(usage_charges)
        
        # Add-on charges
        for addon in subscription.active_addons:
            addon_charge = await self._calculate_addon_charge(addon)
            charges.append(addon_charge)
        
        # Apply discounts
        discounts = await self._calculate_discounts(subscription, charges)
        charges.extend(discounts)
        
        # Calculate taxes
        taxes = await self._calculate_taxes(subscription, charges)
        charges.extend(taxes)
        
        return charges
    
    async def _calculate_usage_charges(
        self,
        subscription: Subscription,
        plan: SubscriptionPlan
    ) -> List[InvoiceLineItem]:
        """Calculate usage-based charges"""
        
        charges = []
        
        # Get usage for billing period
        usage_summary = await self._usage.get_usage_summary(
            user_id=subscription.user_id,
            period=UsagePeriod(
                start=subscription.current_period_start,
                end=subscription.current_period_end
            )
        )
        
        # Calculate charges for each metric
        for metric, usage_amount in usage_summary.usage_by_metric.items():
            # Check if metric has usage pricing
            if not plan.usage_tiers:
                continue
            
            metric_tiers = [t for t in plan.usage_tiers if t.metric == metric]
            if not metric_tiers:
                continue
            
            # Calculate tiered pricing
            total_cost = Decimal("0")
            remaining_usage = usage_amount
            
            for tier in sorted(metric_tiers, key=lambda t: t.from_amount):
                if remaining_usage <= 0:
                    break
                
                tier_cost = tier.calculate_cost(remaining_usage)
                if tier_cost > 0:
                    total_cost += tier_cost
                    
                    # Track tier usage for invoice details
                    tier_usage = min(
                        remaining_usage,
                        (tier.to_amount or remaining_usage) - tier.from_amount
                    )
                    
                    charges.append(
                        InvoiceLineItem(
                            description=f"{metric.replace('_', ' ').title()} - Tier {tier.from_amount}-{tier.to_amount or 'unlimited'}",
                            quantity=tier_usage,
                            unit_price=tier.unit_price,
                            amount=tier_cost,
                            type=LineItemType.USAGE,
                            metadata={
                                "metric": metric,
                                "tier_from": tier.from_amount,
                                "tier_to": tier.to_amount
                            }
                        )
                    )
                
                if tier.to_amount:
                    remaining_usage = max(0, remaining_usage - (tier.to_amount - tier.from_amount))
        
        return charges
    
    async def handle_payment_method_update(
        self,
        user: User,
        payment_method_id: str
    ) -> None:
        """Handle payment method update with retry logic"""
        
        # Update user's default payment method
        await self._update_default_payment_method(user, payment_method_id)
        
        # Check for failed payments to retry
        failed_invoices = await self._invoices.get_failed_invoices(user.id)
        
        for invoice in failed_invoices:
            try:
                # Retry payment
                payment_result = await self._payments.process_payment(
                    user=user,
                    amount=invoice.total_amount,
                    currency=invoice.currency,
                    payment_method_id=payment_method_id,
                    description=f"Retry: Invoice {invoice.number}",
                    metadata={
                        "invoice_id": invoice.id,
                        "retry": "true"
                    }
                )
                
                # Update invoice
                invoice.status = InvoiceStatus.PAID
                invoice.paid_at = datetime.utcnow()
                await self._invoices.update(invoice)
                
                # Reactivate subscription if needed
                subscription = await self._subscriptions.get_by_id(
                    invoice.subscription_id
                )
                if subscription.status == SubscriptionStatus.PAST_DUE:
                    await self._reactivate_subscription(subscription)
                    
            except PaymentError:
                # Continue with next invoice
                continue
```

### Section 4B Summary

The user management and billing integration architecture provides a **production-ready foundation** for SaaS operations with:

- **Sophisticated State Machine**: 13 user states with 18 transition events ensuring consistent lifecycle management
- **Flexible Subscription Models**: Support for flat-rate, usage-based, tiered, and hybrid pricing models
- **Multi-Provider Payments**: Stripe and PayPal integration with extensible architecture
- **Real-Time Usage Tracking**: Comprehensive metering with Redis caching and time-series storage
- **Automated Billing**: Complete billing cycle automation with retry logic and dunning management
- **Enterprise Features**: Team management, SSO integration, and white-label support

This architecture enables TradeSense to scale from individual traders paying $29/month to enterprise clients with $50,000+ annual contracts while maintaining operational efficiency and delivering excellent user experience.