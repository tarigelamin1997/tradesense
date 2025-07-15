import stripe
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.billing import Subscription, UsageRecord, Invoice, get_plan_limits
from models.user import User
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

# Stripe Price IDs (to be set in environment variables)
PRICE_IDS = {
    'starter': {
        'monthly': os.getenv('STRIPE_PRICE_STARTER_MONTHLY'),
        'yearly': os.getenv('STRIPE_PRICE_STARTER_YEARLY')
    },
    'professional': {
        'monthly': os.getenv('STRIPE_PRICE_PROFESSIONAL_MONTHLY'),
        'yearly': os.getenv('STRIPE_PRICE_PROFESSIONAL_YEARLY')
    },
    'team': {
        'monthly': os.getenv('STRIPE_PRICE_TEAM_MONTHLY'),
        'yearly': os.getenv('STRIPE_PRICE_TEAM_YEARLY')
    }
}

class StripeService:
    @staticmethod
    def create_customer(user: User) -> str:
        """Create a Stripe customer for a user"""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.username,
                metadata={
                    'user_id': str(user.id),
                    'username': user.username
                }
            )
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {str(e)}")
            raise

    @staticmethod
    def create_checkout_session(
        user_id: int,
        price_id: str,
        success_url: str,
        cancel_url: str,
        db: Session,
        trial_days: int = 14
    ) -> str:
        """Create a Stripe checkout session"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Get or create Stripe customer
            if user.stripe_customer_id:
                customer_id = user.stripe_customer_id
            else:
                customer_id = StripeService.create_customer(user)
                user.stripe_customer_id = customer_id
                db.commit()
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                subscription_data={
                    'trial_period_days': trial_days,
                    'metadata': {
                        'user_id': str(user_id)
                    }
                },
                metadata={
                    'user_id': str(user_id)
                }
            )
            
            return session.url
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session: {str(e)}")
            raise

    @staticmethod
    def create_portal_session(user_id: int, return_url: str, db: Session) -> str:
        """Create a Stripe billing portal session"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.stripe_customer_id:
                raise ValueError("User or customer not found")
            
            session = stripe.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url=return_url,
            )
            
            return session.url
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create portal session: {str(e)}")
            raise

    @staticmethod
    def cancel_subscription(subscription_id: str, cancel_at_period_end: bool = True) -> Dict[str, Any]:
        """Cancel a Stripe subscription"""
        try:
            if cancel_at_period_end:
                # Cancel at the end of the current billing period
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                # Cancel immediately
                subscription = stripe.Subscription.delete(subscription_id)
            
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {str(e)}")
            raise

    @staticmethod
    def update_subscription(subscription_id: str, new_price_id: str) -> Dict[str, Any]:
        """Update a subscription to a different plan"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Update the subscription
            updated_subscription = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': subscription['items']['data'][0].id,
                    'price': new_price_id,
                }],
                proration_behavior='create_prorations',
            )
            
            return updated_subscription
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update subscription: {str(e)}")
            raise

    @staticmethod
    def handle_webhook(payload: bytes, sig_header: str, db: Session) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise ValueError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid signature")
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            StripeService._handle_checkout_completed(session, db)
            
        elif event['type'] == 'customer.subscription.created':
            subscription = event['data']['object']
            StripeService._handle_subscription_created(subscription, db)
            
        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            StripeService._handle_subscription_updated(subscription, db)
            
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            StripeService._handle_subscription_deleted(subscription, db)
            
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            StripeService._handle_invoice_paid(invoice, db)
            
        elif event['type'] == 'invoice.payment_failed':
            invoice = event['data']['object']
            StripeService._handle_invoice_failed(invoice, db)
        
        return {"status": "success"}

    @staticmethod
    def _handle_checkout_completed(session: Dict[str, Any], db: Session):
        """Handle successful checkout"""
        user_id = int(session['metadata']['user_id'])
        customer_id = session['customer']
        subscription_id = session['subscription']
        
        # Update user's Stripe customer ID
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.stripe_customer_id = customer_id
            db.commit()

    @staticmethod
    def _handle_subscription_created(subscription: Dict[str, Any], db: Session):
        """Handle new subscription creation"""
        user_id = int(subscription['metadata'].get('user_id', 0))
        if not user_id:
            # Try to find user by customer ID
            user = db.query(User).filter(User.stripe_customer_id == subscription['customer']).first()
            if user:
                user_id = user.id
            else:
                logger.error(f"User not found for subscription {subscription['id']}")
                return
        
        # Determine plan from price ID
        price_id = subscription['items']['data'][0]['price']['id']
        plan = StripeService._get_plan_from_price_id(price_id)
        billing_cycle = 'yearly' if 'yearly' in price_id.lower() else 'monthly'
        
        # Create or update subscription record
        sub = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription['id']
        ).first()
        
        if not sub:
            sub = Subscription(
                id=subscription['id'],
                user_id=user_id,
                stripe_customer_id=subscription['customer'],
                stripe_subscription_id=subscription['id'],
                stripe_price_id=price_id,
                plan=plan,
                billing_cycle=billing_cycle
            )
            db.add(sub)
        
        # Update subscription details
        sub.status = subscription['status']
        sub.current_period_start = datetime.fromtimestamp(subscription['current_period_start'])
        sub.current_period_end = datetime.fromtimestamp(subscription['current_period_end'])
        
        if subscription.get('trial_start'):
            sub.trial_start = datetime.fromtimestamp(subscription['trial_start'])
        if subscription.get('trial_end'):
            sub.trial_end = datetime.fromtimestamp(subscription['trial_end'])
        
        db.commit()

    @staticmethod
    def _handle_subscription_updated(subscription: Dict[str, Any], db: Session):
        """Handle subscription updates"""
        sub = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription['id']
        ).first()
        
        if sub:
            # Update plan if price changed
            price_id = subscription['items']['data'][0]['price']['id']
            plan = StripeService._get_plan_from_price_id(price_id)
            
            sub.stripe_price_id = price_id
            sub.plan = plan
            sub.status = subscription['status']
            sub.cancel_at_period_end = subscription['cancel_at_period_end']
            sub.current_period_start = datetime.fromtimestamp(subscription['current_period_start'])
            sub.current_period_end = datetime.fromtimestamp(subscription['current_period_end'])
            
            if subscription.get('canceled_at'):
                sub.cancelled_at = datetime.fromtimestamp(subscription['canceled_at'])
            
            db.commit()

    @staticmethod
    def _handle_subscription_deleted(subscription: Dict[str, Any], db: Session):
        """Handle subscription cancellation"""
        sub = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription['id']
        ).first()
        
        if sub:
            sub.status = 'cancelled'
            sub.cancelled_at = datetime.now()
            db.commit()

    @staticmethod
    def _handle_invoice_paid(invoice: Dict[str, Any], db: Session):
        """Handle successful invoice payment"""
        # Record invoice
        inv = Invoice(
            id=invoice['id'],
            subscription_id=invoice['subscription'],
            stripe_invoice_id=invoice['id'],
            amount=invoice['amount_paid'] / 100,  # Convert from cents
            currency=invoice['currency'],
            status='paid',
            period_start=datetime.fromtimestamp(invoice['period_start']),
            period_end=datetime.fromtimestamp(invoice['period_end']),
            paid_at=datetime.fromtimestamp(invoice['status_transitions']['paid_at']),
            invoice_pdf=invoice.get('invoice_pdf')
        )
        db.add(inv)
        db.commit()

    @staticmethod
    def _handle_invoice_failed(invoice: Dict[str, Any], db: Session):
        """Handle failed invoice payment"""
        # Update subscription status
        sub = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == invoice['subscription']
        ).first()
        
        if sub:
            sub.status = 'past_due'
            db.commit()
        
        # TODO: Send email notification to user

    @staticmethod
    def _get_plan_from_price_id(price_id: str) -> str:
        """Determine plan name from Stripe price ID"""
        for plan, prices in PRICE_IDS.items():
            if price_id in prices.values():
                return plan
        return 'free'

    @staticmethod
    def check_usage_limits(user_id: int, metric: str, db: Session) -> tuple[bool, Optional[str]]:
        """Check if user has exceeded usage limits"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found"
        
        # Get user's subscription
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status.in_(['active', 'trialing'])
        ).first()
        
        plan = subscription.plan if subscription else 'free'
        limits = get_plan_limits(plan)
        
        # Check specific metric
        if metric == 'trades':
            # Count trades this month
            current_period_start = subscription.current_period_start if subscription else datetime.now().replace(day=1)
            
            usage = db.query(UsageRecord).filter(
                UsageRecord.user_id == user_id,
                UsageRecord.metric == 'trades',
                UsageRecord.period_start >= current_period_start
            ).first()
            
            if usage and limits['max_trades_per_month']:
                if usage.count >= limits['max_trades_per_month']:
                    return False, f"Monthly trade limit ({limits['max_trades_per_month']}) reached. Upgrade to continue."
        
        elif metric == 'api_calls':
            # Count API calls today
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            usage = db.query(UsageRecord).filter(
                UsageRecord.user_id == user_id,
                UsageRecord.metric == 'api_calls',
                UsageRecord.period_start >= today_start
            ).first()
            
            if usage and limits['max_api_calls_per_day']:
                if usage.count >= limits['max_api_calls_per_day']:
                    return False, f"Daily API call limit ({limits['max_api_calls_per_day']}) reached. Try again tomorrow."
        
        elif metric == 'portfolios':
            # Count user's portfolios
            # TODO: Implement portfolio counting
            pass
        
        return True, None

    @staticmethod
    def record_usage(user_id: int, metric: str, count: int, db: Session):
        """Record usage for billing purposes"""
        # Determine period based on metric
        if metric == 'trades':
            # Monthly period
            period_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        else:
            # Daily period
            period_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1) - timedelta(seconds=1)
        
        # Get user's subscription
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status.in_(['active', 'trialing'])
        ).first()
        
        # Find or create usage record
        usage = db.query(UsageRecord).filter(
            UsageRecord.user_id == user_id,
            UsageRecord.metric == metric,
            UsageRecord.period_start == period_start
        ).first()
        
        if usage:
            usage.count += count
        else:
            usage = UsageRecord(
                subscription_id=subscription.id if subscription else None,
                user_id=user_id,
                metric=metric,
                count=count,
                period_start=period_start,
                period_end=period_end
            )
            db.add(usage)
        
        db.commit()