"""
Enhanced subscription management service for TradeSense.
Handles Stripe subscriptions, billing, and payment processing.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import stripe
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.db.session import get_db
from models.user import User
from services.email_service import email_service
from analytics import track_subscription_event

stripe.api_key = settings.stripe_api_key or os.getenv('STRIPE_SECRET_KEY')


class SubscriptionService:
    """Manages subscription lifecycle and billing."""
    
    def __init__(self):
        self.stripe = stripe
        self.plans = {
            "free": {
                "name": "Free",
                "price": 0,
                "features": ["100 trades/month", "Basic analytics", "Email support"]
            },
            "pro": {
                "name": "Pro",
                "price": 49.99,
                "stripe_price_id": settings.STRIPE_PRO_PRICE_ID,
                "features": ["Unlimited trades", "Advanced analytics", "Priority support", "API access"]
            },
            "premium": {
                "name": "Premium",
                "price": 99.99,
                "stripe_price_id": settings.STRIPE_PREMIUM_PRICE_ID,
                "features": ["Everything in Pro", "Real-time alerts", "Custom reports", "Phone support"]
            }
        }
    
    async def create_checkout_session(
        self,
        user: User,
        plan: str,
        success_url: str,
        cancel_url: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create a Stripe checkout session for subscription."""
        if plan not in ["pro", "premium"]:
            raise ValueError("Invalid subscription plan")
        
        # Get or create Stripe customer
        customer_id = await self._get_or_create_customer(user, db)
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer=customer_id,
            line_items=[{
                "price": self.plans[plan]["stripe_price_id"],
                "quantity": 1
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": str(user.id),
                "plan": plan
            },
            subscription_data={
                "trial_period_days": 14 if not user.has_had_trial else 0,
                "metadata": {
                    "user_id": str(user.id)
                }
            },
            allow_promotion_codes=True,
            billing_address_collection="required"
        )
        
        # Track checkout started
        await track_subscription_event(
            user_id=str(user.id),
            event="checkout_started",
            plan=plan,
            price=self.plans[plan]["price"]
        )
        
        return {
            "checkout_url": session.url,
            "session_id": session.id
        }
    
    async def create_customer_portal_session(
        self,
        user: User,
        return_url: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create a Stripe customer portal session."""
        customer_id = await self._get_or_create_customer(user, db)
        
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url
        )
        
        return {
            "portal_url": session.url
        }
    
    async def handle_checkout_completed(
        self,
        session_id: str,
        db: AsyncSession
    ) -> bool:
        """Handle successful checkout completion."""
        try:
            # Retrieve session from Stripe
            session = stripe.checkout.Session.retrieve(
                session_id,
                expand=["subscription", "customer"]
            )
            
            if session.payment_status != "paid":
                return False
            
            user_id = session.metadata.get("user_id")
            plan = session.metadata.get("plan")
            
            # Update user subscription
            await db.execute(
                text("""
                    UPDATE users 
                    SET subscription_tier = :plan,
                        subscription_status = 'active',
                        stripe_customer_id = :customer_id,
                        stripe_subscription_id = :subscription_id,
                        subscription_started_at = NOW(),
                        has_had_trial = TRUE
                    WHERE id = :user_id
                """),
                {
                    "plan": plan,
                    "customer_id": session.customer.id,
                    "subscription_id": session.subscription.id,
                    "user_id": user_id
                }
            )
            
            # Store payment record
            await self._record_payment(
                db,
                user_id=user_id,
                amount=session.amount_total / 100,  # Convert from cents
                currency=session.currency,
                stripe_payment_intent_id=session.payment_intent,
                description=f"{plan.capitalize()} subscription"
            )
            
            await db.commit()
            
            # Send confirmation email
            user_result = await db.execute(
                text("SELECT email, full_name FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            )
            user_data = user_result.first()
            
            if user_data:
                await email_service.send_subscription_confirmation(
                    email=user_data.email,
                    name=user_data.full_name,
                    plan=plan
                )
            
            # Track subscription started
            await track_subscription_event(
                user_id=user_id,
                event="started",
                plan=plan,
                price=self.plans[plan]["price"]
            )
            
            return True
            
        except Exception as e:
            print(f"Error handling checkout completion: {e}")
            return False
    
    async def handle_subscription_updated(
        self,
        subscription_id: str,
        db: AsyncSession
    ) -> bool:
        """Handle subscription update from Stripe."""
        try:
            # Retrieve subscription from Stripe
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Find user by subscription ID
            user_result = await db.execute(
                text("SELECT id, subscription_tier FROM users WHERE stripe_subscription_id = :sub_id"),
                {"sub_id": subscription_id}
            )
            user = user_result.first()
            
            if not user:
                return False
            
            # Determine new plan from price ID
            new_plan = self._get_plan_from_price_id(subscription.items.data[0].price.id)
            old_plan = user.subscription_tier
            
            # Update subscription status
            status = "active" if subscription.status == "active" else subscription.status
            
            await db.execute(
                text("""
                    UPDATE users 
                    SET subscription_tier = :plan,
                        subscription_status = :status
                    WHERE id = :user_id
                """),
                {
                    "plan": new_plan,
                    "status": status,
                    "user_id": user.id
                }
            )
            
            await db.commit()
            
            # Track subscription change
            if old_plan != new_plan:
                event = "upgraded" if self._is_upgrade(old_plan, new_plan) else "downgraded"
                await track_subscription_event(
                    user_id=str(user.id),
                    event=event,
                    plan=new_plan,
                    price=self.plans[new_plan]["price"]
                )
            
            return True
            
        except Exception as e:
            print(f"Error handling subscription update: {e}")
            return False
    
    async def handle_subscription_deleted(
        self,
        subscription_id: str,
        db: AsyncSession
    ) -> bool:
        """Handle subscription cancellation."""
        try:
            # Find user by subscription ID
            user_result = await db.execute(
                text("""
                    SELECT id, email, full_name, subscription_tier 
                    FROM users 
                    WHERE stripe_subscription_id = :sub_id
                """),
                {"sub_id": subscription_id}
            )
            user = user_result.first()
            
            if not user:
                return False
            
            # Update user to free tier
            await db.execute(
                text("""
                    UPDATE users 
                    SET subscription_tier = 'free',
                        subscription_status = 'cancelled',
                        subscription_ended_at = NOW()
                    WHERE id = :user_id
                """),
                {"user_id": user.id}
            )
            
            await db.commit()
            
            # Send cancellation email
            await email_service.send_subscription_cancelled(
                email=user.email,
                name=user.full_name
            )
            
            # Track cancellation
            await track_subscription_event(
                user_id=str(user.id),
                event="cancelled",
                plan="free",
                price=0
            )
            
            return True
            
        except Exception as e:
            print(f"Error handling subscription deletion: {e}")
            return False
    
    async def handle_invoice_payment_failed(
        self,
        invoice_id: str,
        db: AsyncSession
    ) -> bool:
        """Handle failed payment."""
        try:
            # Retrieve invoice from Stripe
            invoice = stripe.Invoice.retrieve(invoice_id)
            
            # Find user by customer ID
            user_result = await db.execute(
                text("""
                    SELECT id, email, full_name 
                    FROM users 
                    WHERE stripe_customer_id = :customer_id
                """),
                {"customer_id": invoice.customer}
            )
            user = user_result.first()
            
            if not user:
                return False
            
            # Update subscription status
            await db.execute(
                text("""
                    UPDATE users 
                    SET subscription_status = 'past_due'
                    WHERE id = :user_id
                """),
                {"user_id": user.id}
            )
            
            # Record failed payment
            await self._record_payment(
                db,
                user_id=str(user.id),
                amount=invoice.amount_due / 100,
                currency=invoice.currency,
                status="failed",
                description="Failed subscription payment"
            )
            
            await db.commit()
            
            # Send payment failed email
            await email_service.send_payment_failed(
                email=user.email,
                name=user.full_name,
                amount=invoice.amount_due / 100,
                retry_date=(datetime.utcnow() + timedelta(days=3)).strftime("%B %d, %Y")
            )
            
            return True
            
        except Exception as e:
            print(f"Error handling failed payment: {e}")
            return False
    
    async def get_subscription_details(
        self,
        user: User
    ) -> Dict[str, Any]:
        """Get detailed subscription information."""
        if not user.stripe_subscription_id:
            return {
                "plan": "free",
                "status": "active",
                "features": self.plans["free"]["features"]
            }
        
        try:
            subscription = stripe.Subscription.retrieve(user.stripe_subscription_id)
            
            # Get upcoming invoice
            upcoming_invoice = None
            if subscription.status == "active":
                try:
                    upcoming_invoice = stripe.Invoice.upcoming(
                        customer=user.stripe_customer_id
                    )
                except:
                    pass
            
            return {
                "plan": user.subscription_tier,
                "status": subscription.status,
                "features": self.plans[user.subscription_tier]["features"],
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "upcoming_invoice": {
                    "amount": upcoming_invoice.amount_due / 100,
                    "date": datetime.fromtimestamp(upcoming_invoice.period_end)
                } if upcoming_invoice else None
            }
            
        except Exception as e:
            print(f"Error getting subscription details: {e}")
            return {
                "plan": user.subscription_tier,
                "status": user.subscription_status,
                "features": self.plans[user.subscription_tier]["features"]
            }
    
    async def cancel_subscription(
        self,
        user: User,
        reason: Optional[str] = None,
        feedback: Optional[str] = None,
        db: AsyncSession = None
    ) -> bool:
        """Cancel a user's subscription."""
        if not user.stripe_subscription_id:
            return False
        
        try:
            # Cancel at period end
            subscription = stripe.Subscription.modify(
                user.stripe_subscription_id,
                cancel_at_period_end=True,
                cancellation_details={
                    "comment": f"Reason: {reason}. Feedback: {feedback}" if reason else None
                }
            )
            
            # Store cancellation feedback
            if db and (reason or feedback):
                await db.execute(
                    text("""
                        INSERT INTO subscription_cancellations 
                        (user_id, reason, feedback, scheduled_date)
                        VALUES (:user_id, :reason, :feedback, :scheduled_date)
                    """),
                    {
                        "user_id": user.id,
                        "reason": reason,
                        "feedback": feedback,
                        "scheduled_date": datetime.fromtimestamp(subscription.current_period_end)
                    }
                )
                await db.commit()
            
            # Send confirmation email
            await email_service.send_cancellation_scheduled(
                email=user.email,
                name=user.full_name,
                end_date=datetime.fromtimestamp(subscription.current_period_end)
            )
            
            return True
            
        except Exception as e:
            print(f"Error canceling subscription: {e}")
            return False
    
    async def reactivate_subscription(
        self,
        user: User
    ) -> bool:
        """Reactivate a cancelled subscription."""
        if not user.stripe_subscription_id:
            return False
        
        try:
            # Remove cancellation
            stripe.Subscription.modify(
                user.stripe_subscription_id,
                cancel_at_period_end=False
            )
            
            # Send confirmation email
            await email_service.send_subscription_reactivated(
                email=user.email,
                name=user.full_name
            )
            
            return True
            
        except Exception as e:
            print(f"Error reactivating subscription: {e}")
            return False
    
    async def change_subscription_plan(
        self,
        user: User,
        new_plan: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Change user's subscription plan."""
        if new_plan not in ["pro", "premium"]:
            raise ValueError("Invalid subscription plan")
        
        if not user.stripe_subscription_id:
            # Create new subscription
            return await self.create_checkout_session(
                user, new_plan,
                f"{settings.FRONTEND_URL}/subscription/success",
                f"{settings.FRONTEND_URL}/subscription/cancel",
                db
            )
        
        try:
            # Get current subscription
            subscription = stripe.Subscription.retrieve(user.stripe_subscription_id)
            
            # Update subscription
            updated_subscription = stripe.Subscription.modify(
                user.stripe_subscription_id,
                items=[{
                    "id": subscription["items"]["data"][0].id,
                    "price": self.plans[new_plan]["stripe_price_id"]
                }],
                proration_behavior="create_prorations"
            )
            
            # Update user record
            await db.execute(
                text("""
                    UPDATE users 
                    SET subscription_tier = :plan
                    WHERE id = :user_id
                """),
                {"plan": new_plan, "user_id": user.id}
            )
            await db.commit()
            
            # Track plan change
            event = "upgraded" if self._is_upgrade(user.subscription_tier, new_plan) else "downgraded"
            await track_subscription_event(
                user_id=str(user.id),
                event=event,
                plan=new_plan,
                price=self.plans[new_plan]["price"]
            )
            
            return {
                "success": True,
                "new_plan": new_plan,
                "effective_immediately": True
            }
            
        except Exception as e:
            print(f"Error changing subscription plan: {e}")
            raise
    
    async def apply_coupon(
        self,
        user: User,
        coupon_code: str
    ) -> Dict[str, Any]:
        """Apply a coupon to user's subscription."""
        if not user.stripe_customer_id:
            raise ValueError("No customer record found")
        
        try:
            # Validate coupon
            coupon = stripe.Coupon.retrieve(coupon_code)
            
            if not coupon.valid:
                return {
                    "success": False,
                    "error": "Invalid or expired coupon"
                }
            
            # Apply to customer
            stripe.Customer.modify(
                user.stripe_customer_id,
                coupon=coupon_code
            )
            
            return {
                "success": True,
                "discount": {
                    "percent_off": coupon.percent_off,
                    "amount_off": coupon.amount_off / 100 if coupon.amount_off else None,
                    "duration": coupon.duration,
                    "duration_in_months": coupon.duration_in_months
                }
            }
            
        except stripe.error.InvalidRequestError:
            return {
                "success": False,
                "error": "Invalid coupon code"
            }
        except Exception as e:
            print(f"Error applying coupon: {e}")
            raise
    
    async def get_payment_history(
        self,
        user: User,
        db: AsyncSession,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get user's payment history."""
        result = await db.execute(
            text("""
                SELECT 
                    id, amount, currency, status,
                    description, created_at,
                    stripe_payment_intent_id
                FROM payments
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"user_id": user.id, "limit": limit}
        )
        
        payments = []
        for row in result:
            payments.append({
                "id": str(row.id),
                "amount": float(row.amount),
                "currency": row.currency,
                "status": row.status,
                "description": row.description,
                "date": row.created_at.isoformat(),
                "receipt_url": await self._get_receipt_url(row.stripe_payment_intent_id) if row.stripe_payment_intent_id else None
            })
        
        return payments
    
    async def get_upcoming_invoice(
        self,
        user: User
    ) -> Optional[Dict[str, Any]]:
        """Get upcoming invoice details."""
        if not user.stripe_customer_id:
            return None
        
        try:
            invoice = stripe.Invoice.upcoming(customer=user.stripe_customer_id)
            
            return {
                "amount": invoice.amount_due / 100,
                "currency": invoice.currency,
                "date": datetime.fromtimestamp(invoice.period_end),
                "items": [
                    {
                        "description": item.description,
                        "amount": item.amount / 100
                    }
                    for item in invoice.lines.data
                ]
            }
        except:
            return None
    
    # Helper methods
    async def _get_or_create_customer(
        self,
        user: User,
        db: AsyncSession
    ) -> str:
        """Get or create Stripe customer for user."""
        if user.stripe_customer_id:
            return user.stripe_customer_id
        
        # Create new customer
        customer = stripe.Customer.create(
            email=user.email,
            name=user.full_name,
            metadata={"user_id": str(user.id)}
        )
        
        # Update user record
        await db.execute(
            text("""
                UPDATE users 
                SET stripe_customer_id = :customer_id 
                WHERE id = :user_id
            """),
            {"customer_id": customer.id, "user_id": user.id}
        )
        await db.commit()
        
        return customer.id
    
    async def _record_payment(
        self,
        db: AsyncSession,
        user_id: str,
        amount: float,
        currency: str,
        status: str = "completed",
        stripe_payment_intent_id: Optional[str] = None,
        description: Optional[str] = None
    ):
        """Record payment in database."""
        await db.execute(
            text("""
                INSERT INTO payments (
                    user_id, amount, currency, status,
                    stripe_payment_intent_id, description
                ) VALUES (
                    :user_id, :amount, :currency, :status,
                    :payment_intent_id, :description
                )
            """),
            {
                "user_id": user_id,
                "amount": amount,
                "currency": currency,
                "status": status,
                "payment_intent_id": stripe_payment_intent_id,
                "description": description
            }
        )
    
    def _get_plan_from_price_id(self, price_id: str) -> str:
        """Get plan name from Stripe price ID."""
        for plan_name, plan_info in self.plans.items():
            if plan_info.get("stripe_price_id") == price_id:
                return plan_name
        return "free"
    
    def _is_upgrade(self, old_plan: str, new_plan: str) -> bool:
        """Check if plan change is an upgrade."""
        plan_hierarchy = {"free": 0, "pro": 1, "premium": 2}
        return plan_hierarchy.get(new_plan, 0) > plan_hierarchy.get(old_plan, 0)
    
    async def _get_receipt_url(self, payment_intent_id: str) -> Optional[str]:
        """Get receipt URL for a payment."""
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if payment_intent.charges.data:
                return payment_intent.charges.data[0].receipt_url
        except:
            pass
        return None


# Initialize subscription service
subscription_service = SubscriptionService()