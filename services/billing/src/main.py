import os
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Float, DateTime, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import httpx
import uvicorn
import logging
import stripe
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TradeSense Billing Service",
    description="Subscription and payment management",
    version="1.0.0"
)

# CORS configuration
cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://localhost:8000",
    "https://frontend-og3gd5s4j-tarig-ahmeds-projects.vercel.app",
    "https://frontend-jj8nosjl0-tarig-ahmeds-projects.vercel.app",
    "https://frontend-*.vercel.app",
    "https://*.vercel.app",
    "https://tradesense.vercel.app",
    "https://tradesense-*.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/billing_db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_your_test_key")

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth:8000")

# Price IDs from environment
PRICE_BASIC = os.getenv("STRIPE_PRICE_BASIC", "price_basic_test")
PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "price_pro_test")
PRICE_PREMIUM = os.getenv("STRIPE_PRICE_PREMIUM", "price_premium_test")

# Models
class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    stripe_customer_id = Column(String)
    stripe_subscription_id = Column(String)
    plan = Column(String)  # basic, pro, premium
    status = Column(String)  # active, cancelled, past_due
    current_period_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    stripe_payment_intent_id = Column(String)
    amount = Column(Float)
    currency = Column(String, default="usd")
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Failed to create tables: {e}")

# Pydantic models
class CreateCheckoutSession(BaseModel):
    plan: str  # basic, pro, premium
    success_url: str
    cancel_url: str

class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str

class SubscriptionResponse(BaseModel):
    id: str
    plan: str
    status: str
    current_period_end: datetime
    features: List[str]

class CancelSubscription(BaseModel):
    reason: Optional[str] = None

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth dependency
async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    
    # Verify with auth service
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/auth/verify",
                params={"token": token}
            )
            data = response.json()
            if not data.get("valid"):
                raise HTTPException(status_code=401, detail="Invalid token")
            return data.get("username")
        except:
            raise HTTPException(status_code=503, detail="Auth service unavailable")

# Helper functions
def get_plan_features(plan: str) -> List[str]:
    """Get features for a plan"""
    features = {
        "basic": [
            "100 trades per month",
            "Basic analytics",
            "Portfolio tracking",
            "Email support"
        ],
        "pro": [
            "Unlimited trades",
            "Advanced analytics",
            "Pattern recognition",
            "Real-time market data",
            "Priority support",
            "API access"
        ],
        "premium": [
            "Everything in Pro",
            "AI-powered insights",
            "Custom strategies",
            "Dedicated support",
            "White-label options",
            "Advanced API access"
        ]
    }
    return features.get(plan, [])

def get_price_id(plan: str) -> str:
    """Get Stripe price ID for a plan"""
    prices = {
        "basic": PRICE_BASIC,
        "pro": PRICE_PRO,
        "premium": PRICE_PREMIUM
    }
    return prices.get(plan)

# Routes
@app.get("/")
async def root():
    return {"service": "Billing Service", "status": "operational"}

@app.get("/health")
async def health():
    try:
        # Check database connection
        db = SessionLocal()
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Health check DB error: {e}")
        db_status = "unhealthy"
    
    # Check Stripe
    try:
        stripe.Account.retrieve()
        stripe_status = "healthy"
    except Exception as e:
        logger.error(f"Health check Stripe error: {e}")
        stripe_status = "unhealthy"
    
    status = "healthy" if db_status == "healthy" and stripe_status == "healthy" else "degraded"
    
    return {
        "status": status,
        "database": db_status,
        "stripe": stripe_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/billing/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    data: CreateCheckoutSession,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create a Stripe checkout session"""
    price_id = get_price_id(data.plan)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    try:
        # Create or get Stripe customer
        existing_sub = db.query(Subscription).filter(
            Subscription.user_id == username
        ).first()
        
        if existing_sub and existing_sub.stripe_customer_id:
            customer_id = existing_sub.stripe_customer_id
        else:
            # Create new customer
            customer = stripe.Customer.create(
                metadata={"username": username}
            )
            customer_id = customer.id
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1
            }],
            mode="subscription",
            success_url=data.success_url,
            cancel_url=data.cancel_url,
            metadata={
                "username": username,
                "plan": data.plan
            }
        )
        
        return CheckoutSessionResponse(
            checkout_url=session.url,
            session_id=session.id
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/billing/subscription", response_model=Optional[SubscriptionResponse])
async def get_subscription(
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get current subscription"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == username,
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        return None
    
    return SubscriptionResponse(
        id=subscription.id,
        plan=subscription.plan,
        status=subscription.status,
        current_period_end=subscription.current_period_end,
        features=get_plan_features(subscription.plan)
    )

@app.post("/billing/cancel")
async def cancel_subscription(
    data: CancelSubscription,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Cancel subscription"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == username,
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    try:
        # Cancel in Stripe
        stripe_sub = stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True
        )
        
        # Update database
        subscription.status = "cancelled"
        db.commit()
        
        return {
            "message": "Subscription will be cancelled at period end",
            "period_end": subscription.current_period_end
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/billing/webhook")
async def stripe_webhook(request: dict, db: Session = Depends(get_db)):
    """Handle Stripe webhooks"""
    # In production, verify webhook signature
    event_type = request.get("type")
    
    if event_type == "checkout.session.completed":
        session = request["data"]["object"]
        
        # Create subscription record
        subscription = Subscription(
            id=f"sub_{datetime.utcnow().timestamp()}",
            user_id=session["metadata"]["username"],
            stripe_customer_id=session["customer"],
            stripe_subscription_id=session["subscription"],
            plan=session["metadata"]["plan"],
            status="active",
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        
        db.add(subscription)
        db.commit()
        
    elif event_type == "invoice.payment_succeeded":
        invoice = request["data"]["object"]
        
        # Record payment
        payment = Payment(
            id=f"pay_{datetime.utcnow().timestamp()}",
            user_id=invoice["metadata"].get("username", "unknown"),
            stripe_payment_intent_id=invoice["payment_intent"],
            amount=invoice["amount_paid"] / 100,  # Convert from cents
            status="succeeded"
        )
        
        db.add(payment)
        db.commit()
    
    return {"received": True}

@app.get("/billing/plans")
async def get_plans():
    """Get available plans"""
    return {
        "plans": [
            {
                "id": "basic",
                "name": "Basic",
                "price": 29,
                "currency": "USD",
                "interval": "month",
                "features": get_plan_features("basic")
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 79,
                "currency": "USD",
                "interval": "month",
                "features": get_plan_features("pro"),
                "popular": True
            },
            {
                "id": "premium",
                "name": "Premium",
                "price": 199,
                "currency": "USD",
                "interval": "month",
                "features": get_plan_features("premium")
            }
        ]
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Billing Service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)