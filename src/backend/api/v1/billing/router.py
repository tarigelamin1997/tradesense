from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from api.deps import get_current_user
from core.db.session import get_db
from models.user import User

router = APIRouter()

# Default subscription response for development
@router.get("/subscription")
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's subscription"""
    # Return default free subscription for now
    return {
        "id": "sub_free",
        "user_id": current_user.id,
        "plan_id": "free",
        "status": "active",
        "current_period_start": datetime.now().isoformat(),
        "current_period_end": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat()
    }

@router.get("/usage")
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's usage statistics"""
    # Return default usage for now
    return {
        "user_id": current_user.id,
        "period_start": datetime.now().isoformat(),
        "period_end": datetime.now().isoformat(),
        "trades_count": 0,
        "trades_limit": 100,  # Free tier limit
        "api_calls_count": 0,
        "api_calls_limit": 1000
    }

@router.post("/create-checkout-session")
async def create_checkout_session(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe checkout session"""
    # For now, return a mock response
    return {
        "url": f"/payment-success?session_id=mock_{product_id}",
        "session_id": f"mock_{product_id}"
    }

@router.post("/create-portal-session")
async def create_portal_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe customer portal session"""
    # For now, return a mock response
    return {
        "url": "/billing",
        "session_id": "mock_portal_session"
    }