from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.db.session import Base
from datetime import datetime
from typing import Optional

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    stripe_customer_id = Column(String, nullable=False, index=True)
    stripe_subscription_id = Column(String, unique=True, index=True)
    stripe_price_id = Column(String)
    
    plan = Column(String, nullable=False)  # free/starter/professional/team
    status = Column(String, nullable=False)  # active/trialing/cancelled/past_due/incomplete
    billing_cycle = Column(String, default='monthly')  # monthly/yearly
    
    trial_start = Column(DateTime)
    trial_end = Column(DateTime)
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    cancelled_at = Column(DateTime)
    
    # Team-specific fields
    seats = Column(Integer, default=1)
    seats_used = Column(Integer, default=1)
    
    # Metadata
    extra_data = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subscription")
    usage_records = relationship("UsageRecord", back_populates="subscription")
    invoices = relationship("Invoice", back_populates="subscription")


class UsageRecord(Base):
    __tablename__ = "usage_records"
    
    id = Column(Integer, primary_key=True)
    subscription_id = Column(String, ForeignKey('subscriptions.id'), nullable=False)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    metric = Column(String, nullable=False)  # trades/api_calls/storage_mb
    count = Column(Integer, default=0)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    subscription = relationship("Subscription", back_populates="usage_records")
    user = relationship("User", back_populates="usage_records")


class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(String, primary_key=True)
    subscription_id = Column(String, ForeignKey('subscriptions.id'), nullable=False)
    stripe_invoice_id = Column(String, unique=True)
    
    amount = Column(Float, nullable=False)
    currency = Column(String, default='usd')
    status = Column(String, nullable=False)  # draft/open/paid/void/uncollectible
    
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    paid_at = Column(DateTime)
    invoice_pdf = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    subscription = relationship("Subscription", back_populates="invoices")


class PlanLimits(Base):
    __tablename__ = "plan_limits"
    
    id = Column(Integer, primary_key=True)
    plan = Column(String, unique=True, nullable=False)
    
    max_trades_per_month = Column(Integer)
    max_portfolios = Column(Integer)
    data_retention_days = Column(Integer)
    max_api_calls_per_day = Column(Integer)
    max_team_members = Column(Integer, default=1)
    
    # Feature flags
    has_advanced_analytics = Column(Boolean, default=False)
    has_api_access = Column(Boolean, default=False)
    has_export_features = Column(Boolean, default=False)
    has_team_features = Column(Boolean, default=False)
    has_priority_support = Column(Boolean, default=False)
    has_white_label = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# Helper functions
def get_plan_limits(plan: str) -> dict:
    """Get limits for a specific plan"""
    limits = {
        'free': {
            'max_trades_per_month': 10,
            'max_portfolios': 1,
            'data_retention_days': 7,
            'max_api_calls_per_day': 0,
            'max_team_members': 1,
            'has_advanced_analytics': False,
            'has_api_access': False,
            'has_export_features': False,
            'has_team_features': False,
            'has_priority_support': False,
            'has_white_label': False
        },
        'starter': {
            'max_trades_per_month': 100,
            'max_portfolios': 1,
            'data_retention_days': 30,
            'max_api_calls_per_day': 0,
            'max_team_members': 1,
            'has_advanced_analytics': False,
            'has_api_access': False,
            'has_export_features': False,
            'has_team_features': False,
            'has_priority_support': False,
            'has_white_label': False
        },
        'professional': {
            'max_trades_per_month': None,  # Unlimited
            'max_portfolios': 5,
            'data_retention_days': None,  # Unlimited
            'max_api_calls_per_day': 1000,
            'max_team_members': 1,
            'has_advanced_analytics': True,
            'has_api_access': True,
            'has_export_features': True,
            'has_team_features': False,
            'has_priority_support': True,
            'has_white_label': False
        },
        'team': {
            'max_trades_per_month': None,
            'max_portfolios': None,
            'data_retention_days': None,
            'max_api_calls_per_day': 10000,
            'max_team_members': 5,
            'has_advanced_analytics': True,
            'has_api_access': True,
            'has_export_features': True,
            'has_team_features': True,
            'has_priority_support': True,
            'has_white_label': True
        }
    }
    
    return limits.get(plan, limits['free'])