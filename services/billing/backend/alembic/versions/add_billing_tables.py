"""add billing tables

Revision ID: add_billing_tables
Revises: 
Create Date: 2025-01-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_billing_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create subscriptions table
    op.create_table('subscriptions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('stripe_customer_id', sa.String(), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(), nullable=True),
        sa.Column('stripe_price_id', sa.String(), nullable=True),
        sa.Column('plan', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('billing_cycle', sa.String(), nullable=True),
        sa.Column('trial_start', sa.DateTime(), nullable=True),
        sa.Column('trial_end', sa.DateTime(), nullable=True),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('seats', sa.Integer(), nullable=True),
        sa.Column('seats_used', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_stripe_customer_id'), 'subscriptions', ['stripe_customer_id'], unique=False)
    op.create_index(op.f('ix_subscriptions_stripe_subscription_id'), 'subscriptions', ['stripe_subscription_id'], unique=True)

    # Create usage_records table
    op.create_table('usage_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('metric', sa.String(), nullable=False),
        sa.Column('count', sa.Integer(), nullable=True),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create invoices table
    op.create_table('invoices',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('subscription_id', sa.String(), nullable=False),
        sa.Column('stripe_invoice_id', sa.String(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=True),
        sa.Column('period_end', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('invoice_pdf', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_invoice_id')
    )

    # Create plan_limits table
    op.create_table('plan_limits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan', sa.String(), nullable=False),
        sa.Column('max_trades_per_month', sa.Integer(), nullable=True),
        sa.Column('max_portfolios', sa.Integer(), nullable=True),
        sa.Column('data_retention_days', sa.Integer(), nullable=True),
        sa.Column('max_api_calls_per_day', sa.Integer(), nullable=True),
        sa.Column('max_team_members', sa.Integer(), nullable=True),
        sa.Column('has_advanced_analytics', sa.Boolean(), nullable=True),
        sa.Column('has_api_access', sa.Boolean(), nullable=True),
        sa.Column('has_export_features', sa.Boolean(), nullable=True),
        sa.Column('has_team_features', sa.Boolean(), nullable=True),
        sa.Column('has_priority_support', sa.Boolean(), nullable=True),
        sa.Column('has_white_label', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan')
    )

    # Add stripe_customer_id to users table
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_stripe_customer_id'), 'users', ['stripe_customer_id'], unique=True)

    # Insert default plan limits
    op.execute("""
        INSERT INTO plan_limits (plan, max_trades_per_month, max_portfolios, data_retention_days, 
                                max_api_calls_per_day, max_team_members, has_advanced_analytics, 
                                has_api_access, has_export_features, has_team_features, 
                                has_priority_support, has_white_label)
        VALUES 
        ('free', 10, 1, 7, 0, 1, false, false, false, false, false, false),
        ('starter', 100, 1, 30, 0, 1, false, false, false, false, false, false),
        ('professional', NULL, 5, NULL, 1000, 1, true, true, true, false, true, false),
        ('team', NULL, NULL, NULL, 10000, 5, true, true, true, true, true, true)
    """)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_stripe_customer_id'), table_name='users')
    op.drop_column('users', 'stripe_customer_id')
    op.drop_table('plan_limits')
    op.drop_table('invoices')
    op.drop_table('usage_records')
    op.drop_index(op.f('ix_subscriptions_stripe_subscription_id'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_stripe_customer_id'), table_name='subscriptions')
    op.drop_table('subscriptions')