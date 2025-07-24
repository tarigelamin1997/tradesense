"""Add OAuth tables

Revision ID: add_oauth_tables_20250124
Revises: add_mfa_tables_20250124
Create Date: 2025-01-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_oauth_tables_20250124'
down_revision = 'add_mfa_tables_20250124'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_oauth_accounts table
    op.create_table('user_oauth_accounts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('provider_user_id', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('picture', sa.Text(), nullable=True),
        sa.Column('locale', sa.String(10), nullable=True),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('provider', 'provider_user_id', name='unique_provider_account')
    )
    op.create_index(op.f('ix_user_oauth_accounts_user_id'), 'user_oauth_accounts', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_oauth_accounts_provider'), 'user_oauth_accounts', ['provider'], unique=False)
    op.create_index(op.f('ix_user_oauth_accounts_email'), 'user_oauth_accounts', ['email'], unique=False)

    # Add OAuth-related columns to users table if they don't exist
    try:
        op.add_column('users', sa.Column('created_via_oauth', sa.Boolean(), nullable=False, server_default='false'))
        op.add_column('users', sa.Column('oauth_provider', sa.String(50), nullable=True))
        op.add_column('users', sa.Column('has_password', sa.Boolean(), nullable=False, server_default='true'))
        op.add_column('users', sa.Column('avatar_url', sa.Text(), nullable=True))
        op.add_column('users', sa.Column('full_name', sa.String(255), nullable=True))
    except:
        pass  # Columns might already exist

    # Create oauth_state_tokens table for CSRF protection
    op.create_table('oauth_state_tokens',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('state', sa.String(255), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('action', sa.String(20), nullable=False, server_default='login'),
        sa.Column('redirect_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('state')
    )
    op.create_index(op.f('ix_oauth_state_tokens_state'), 'oauth_state_tokens', ['state'], unique=True)
    op.create_index(op.f('ix_oauth_state_tokens_expires_at'), 'oauth_state_tokens', ['expires_at'], unique=False)

    # Create oauth_login_history table for security tracking
    op.create_table('oauth_login_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_oauth_login_history_user_id'), 'oauth_login_history', ['user_id'], unique=False)
    op.create_index(op.f('ix_oauth_login_history_created_at'), 'oauth_login_history', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_table('oauth_login_history')
    op.drop_table('oauth_state_tokens')
    op.drop_table('user_oauth_accounts')
    
    # Remove OAuth columns from users table
    try:
        op.drop_column('users', 'full_name')
        op.drop_column('users', 'avatar_url')
        op.drop_column('users', 'has_password')
        op.drop_column('users', 'oauth_provider')
        op.drop_column('users', 'created_via_oauth')
    except:
        pass  # Columns might not exist