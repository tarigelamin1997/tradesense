"""Add MFA tables

Revision ID: add_mfa_tables_20250124
Revises: 
Create Date: 2025-01-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_mfa_tables_20250124'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create mfa_devices table
    op.create_table('mfa_devices',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('device_type', sa.String(50), nullable=False),
        sa.Column('device_name', sa.String(255), nullable=False),
        sa.Column('secret_encrypted', sa.Text(), nullable=True),
        sa.Column('phone_number', sa.String(20), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('disabled_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'device_type', 'status', name='unique_active_device_per_type')
    )
    op.create_index(op.f('ix_mfa_devices_user_id'), 'mfa_devices', ['user_id'], unique=False)
    op.create_index(op.f('ix_mfa_devices_device_type'), 'mfa_devices', ['device_type'], unique=False)
    op.create_index(op.f('ix_mfa_devices_status'), 'mfa_devices', ['status'], unique=False)

    # Create mfa_backup_codes table
    op.create_table('mfa_backup_codes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('code_hash', sa.String(64), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('code_hash')
    )
    op.create_index(op.f('ix_mfa_backup_codes_user_id'), 'mfa_backup_codes', ['user_id'], unique=False)
    op.create_index(op.f('ix_mfa_backup_codes_status'), 'mfa_backup_codes', ['status'], unique=False)

    # Create mfa_verification_codes table
    op.create_table('mfa_verification_codes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('code_hash', sa.String(64), nullable=False),
        sa.Column('method', sa.String(20), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_mfa_verification_codes_user_id'), 'mfa_verification_codes', ['user_id'], unique=False)
    op.create_index(op.f('ix_mfa_verification_codes_expires_at'), 'mfa_verification_codes', ['expires_at'], unique=False)

    # Create mfa_trusted_devices table
    op.create_table('mfa_trusted_devices',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('device_fingerprint', sa.String(64), nullable=False),
        sa.Column('device_name', sa.String(255), nullable=False),
        sa.Column('trust_token', sa.String(64), nullable=False),
        sa.Column('last_ip_address', sa.String(45), nullable=True),
        sa.Column('last_user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_used_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'device_fingerprint')
    )
    op.create_index(op.f('ix_mfa_trusted_devices_user_id'), 'mfa_trusted_devices', ['user_id'], unique=False)
    op.create_index(op.f('ix_mfa_trusted_devices_expires_at'), 'mfa_trusted_devices', ['expires_at'], unique=False)

    # Create mfa_auth_attempts table
    op.create_table('mfa_auth_attempts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('method', sa.String(20), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('attempted_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_mfa_auth_attempts_user_id'), 'mfa_auth_attempts', ['user_id'], unique=False)
    op.create_index(op.f('ix_mfa_auth_attempts_attempted_at'), 'mfa_auth_attempts', ['attempted_at'], unique=False)

    # Create mfa_security_events table
    op.create_table('mfa_security_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_mfa_security_events_user_id'), 'mfa_security_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_mfa_security_events_event_type'), 'mfa_security_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_mfa_security_events_created_at'), 'mfa_security_events', ['created_at'], unique=False)

    # Add MFA columns to users table if they don't exist
    try:
        op.add_column('users', sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='false'))
        op.add_column('users', sa.Column('mfa_methods', postgresql.ARRAY(sa.String()), nullable=True))
    except:
        pass  # Columns might already exist

    # Create view for MFA admin stats
    op.execute("""
        CREATE OR REPLACE VIEW mfa_admin_stats AS
        SELECT 
            COUNT(DISTINCT CASE WHEN mfa_enabled = TRUE THEN id END) as users_with_mfa,
            COUNT(DISTINCT CASE WHEN mfa_enabled = FALSE THEN id END) as users_without_mfa,
            COUNT(DISTINCT CASE WHEN 'totp' = ANY(mfa_methods) THEN id END) as totp_devices,
            COUNT(DISTINCT CASE WHEN 'sms' = ANY(mfa_methods) THEN id END) as sms_devices,
            COUNT(DISTINCT CASE WHEN 'email' = ANY(mfa_methods) THEN id END) as email_devices,
            (SELECT COUNT(DISTINCT user_id) FROM mfa_backup_codes WHERE status = 'active') as users_with_backup_codes,
            (SELECT COUNT(*) FROM mfa_auth_attempts WHERE success = TRUE AND attempted_at > NOW() - INTERVAL '24 hours') as successful_auths_24h,
            (SELECT COUNT(*) FROM mfa_auth_attempts WHERE success = FALSE AND attempted_at > NOW() - INTERVAL '24 hours') as failed_auths_24h
        FROM users;
    """)


def downgrade() -> None:
    # Drop view
    op.execute("DROP VIEW IF EXISTS mfa_admin_stats")
    
    # Drop tables
    op.drop_table('mfa_security_events')
    op.drop_table('mfa_auth_attempts')
    op.drop_table('mfa_trusted_devices')
    op.drop_table('mfa_verification_codes')
    op.drop_table('mfa_backup_codes')
    op.drop_table('mfa_devices')
    
    # Remove MFA columns from users table
    try:
        op.drop_column('users', 'mfa_methods')
        op.drop_column('users', 'mfa_enabled')
    except:
        pass  # Columns might not exist