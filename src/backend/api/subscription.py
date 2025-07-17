"""
Subscription API endpoints for TradeSense.
Handles billing, plan changes, and payment management.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.db.session import get_db
from app.models.user import User
from src.backend.services.subscription_service import subscription_service
from src.backend.analytics import track_feature_usage

router = APIRouter(prefix="/api/v1/subscription", tags=["subscription"])


class CheckoutRequest(BaseModel):
    plan: str
    success_url: str
    cancel_url: str


class ChangePlanRequest(BaseModel):
    new_plan: str


class CancelSubscriptionRequest(BaseModel):
    reason: Optional[str] = None
    feedback: Optional[str] = None


class ApplyCouponRequest(BaseModel):
    coupon_code: str


@router.get("/current")
async def get_current_subscription(
    current_user: User = Depends(get_current_user)
):
    """Get current subscription details."""
    try:
        details = await subscription_service.get_subscription_details(current_user)
        
        # Track feature usage
        await track_feature_usage(
            str(current_user.id),
            "view_subscription_details"
        )
        
        return details
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans")
async def get_subscription_plans():
    """Get available subscription plans."""
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "currency": "USD",
                "interval": "month",
                "features": subscription_service.plans["free"]["features"],
                "limits": {
                    "trades_per_month": 100,
                    "api_calls_per_day": 100
                }
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 49.99,
                "currency": "USD",
                "interval": "month",
                "features": subscription_service.plans["pro"]["features"],
                "limits": {
                    "trades_per_month": -1,  # Unlimited
                    "api_calls_per_day": 1000
                },
                "popular": True
            },
            {
                "id": "premium",
                "name": "Premium",
                "price": 99.99,
                "currency": "USD",
                "interval": "month",
                "features": subscription_service.plans["premium"]["features"],
                "limits": {
                    "trades_per_month": -1,  # Unlimited
                    "api_calls_per_day": 10000
                }
            }
        ]
    }


@router.post("/checkout")
async def create_checkout_session(
    checkout_data: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a Stripe checkout session."""
    try:
        result = await subscription_service.create_checkout_session(
            user=current_user,
            plan=checkout_data.plan,
            success_url=checkout_data.success_url,
            cancel_url=checkout_data.cancel_url,
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customer-portal")
async def create_customer_portal_session(
    return_url: str = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a Stripe customer portal session."""
    try:
        result = await subscription_service.create_customer_portal_session(
            user=current_user,
            return_url=return_url,
            db=db
        )
        
        # Track portal access
        await track_feature_usage(
            str(current_user.id),
            "access_customer_portal"
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/change-plan")
async def change_subscription_plan(
    plan_data: ChangePlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change subscription plan."""
    try:
        result = await subscription_service.change_subscription_plan(
            user=current_user,
            new_plan=plan_data.new_plan,
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel")
async def cancel_subscription(
    cancel_data: CancelSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel subscription at end of billing period."""
    try:
        success = await subscription_service.cancel_subscription(
            user=current_user,
            reason=cancel_data.reason,
            feedback=cancel_data.feedback,
            db=db
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="No active subscription found")
        
        return {"message": "Subscription will be cancelled at the end of the billing period"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reactivate")
async def reactivate_subscription(
    current_user: User = Depends(get_current_user)
):
    """Reactivate a cancelled subscription."""
    try:
        success = await subscription_service.reactivate_subscription(current_user)
        
        if not success:
            raise HTTPException(status_code=400, detail="No cancelled subscription found")
        
        return {"message": "Subscription reactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply-coupon")
async def apply_coupon(
    coupon_data: ApplyCouponRequest,
    current_user: User = Depends(get_current_user)
):
    """Apply a coupon code to subscription."""
    try:
        result = await subscription_service.apply_coupon(
            user=current_user,
            coupon_code=coupon_data.coupon_code
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payment-history")
async def get_payment_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's payment history."""
    try:
        payments = await subscription_service.get_payment_history(
            user=current_user,
            db=db,
            limit=limit
        )
        
        return {
            "payments": payments,
            "total": len(payments)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upcoming-invoice")
async def get_upcoming_invoice(
    current_user: User = Depends(get_current_user)
):
    """Get upcoming invoice details."""
    try:
        invoice = await subscription_service.get_upcoming_invoice(current_user)
        
        if not invoice:
            return {"message": "No upcoming invoice"}
        
        return invoice
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage")
async def get_subscription_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current usage against subscription limits."""
    try:
        # Get current month usage
        from sqlalchemy import text
        
        # Trade count
        trade_count_result = await db.execute(
            text("""
                SELECT COUNT(*) as count
                FROM trades
                WHERE user_id = :user_id
                AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
            """),
            {"user_id": current_user.id}
        )
        trade_count = trade_count_result.scalar() or 0
        
        # API calls today
        api_calls_result = await db.execute(
            text("""
                SELECT COUNT(*) as count
                FROM api_requests
                WHERE user_id = :user_id
                AND created_at >= CURRENT_DATE
            """),
            {"user_id": current_user.id}
        )
        api_calls = api_calls_result.scalar() or 0
        
        # Get plan limits
        plan = current_user.subscription_tier
        limits = {
            "free": {"trades_per_month": 100, "api_calls_per_day": 100},
            "pro": {"trades_per_month": -1, "api_calls_per_day": 1000},
            "premium": {"trades_per_month": -1, "api_calls_per_day": 10000}
        }
        
        plan_limits = limits.get(plan, limits["free"])
        
        return {
            "plan": plan,
            "usage": {
                "trades": {
                    "current": trade_count,
                    "limit": plan_limits["trades_per_month"],
                    "unlimited": plan_limits["trades_per_month"] == -1,
                    "percentage": 0 if plan_limits["trades_per_month"] == -1 else (trade_count / plan_limits["trades_per_month"] * 100)
                },
                "api_calls": {
                    "current": api_calls,
                    "limit": plan_limits["api_calls_per_day"],
                    "unlimited": plan_limits["api_calls_per_day"] == -1,
                    "percentage": 0 if plan_limits["api_calls_per_day"] == -1 else (api_calls / plan_limits["api_calls_per_day"] * 100)
                }
            },
            "period": {
                "trades": "monthly",
                "api_calls": "daily"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Webhook endpoints (called by Stripe)
@router.post("/webhook")
async def stripe_webhook(
    request: dict,
    stripe_signature: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Handle Stripe webhook events."""
    # In production, verify webhook signature
    # endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    # stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    
    event_type = request.get("type")
    
    try:
        if event_type == "checkout.session.completed":
            session_id = request["data"]["object"]["id"]
            await subscription_service.handle_checkout_completed(session_id, db)
            
        elif event_type == "customer.subscription.updated":
            subscription_id = request["data"]["object"]["id"]
            await subscription_service.handle_subscription_updated(subscription_id, db)
            
        elif event_type == "customer.subscription.deleted":
            subscription_id = request["data"]["object"]["id"]
            await subscription_service.handle_subscription_deleted(subscription_id, db)
            
        elif event_type == "invoice.payment_failed":
            invoice_id = request["data"]["object"]["id"]
            await subscription_service.handle_invoice_payment_failed(invoice_id, db)
        
        return {"received": True}
        
    except Exception as e:
        print(f"Webhook error: {e}")
        # Return 200 to acknowledge receipt even if processing failed
        return {"received": True, "error": str(e)}