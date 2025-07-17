"""Add feedback tables

Revision ID: add_feedback_tables
Revises: 
Create Date: 2024-01-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_feedback_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create feedback_patterns table first (referenced by feedback)
    op.create_table('feedback_patterns',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('pattern_signature', sa.String(), nullable=False),
        sa.Column('pattern_type', sa.String(), nullable=False),
        sa.Column('occurrences', sa.Integer(), nullable=True),
        sa.Column('affected_users', sa.Integer(), nullable=True),
        sa.Column('first_seen', sa.DateTime(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pattern_signature')
    )
    op.create_index(op.f('ix_feedback_patterns_pattern_signature'), 'feedback_patterns', ['pattern_signature'], unique=False)
    op.create_index(op.f('ix_feedback_patterns_pattern_type'), 'feedback_patterns', ['pattern_type'], unique=False)

    # Create main feedback table
    op.create_table('feedback',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('screen_resolution', sa.String(), nullable=True),
        sa.Column('subscription_tier', sa.String(), nullable=True),
        sa.Column('previous_pages', sa.Text(), nullable=True),
        sa.Column('last_actions', sa.Text(), nullable=True),
        sa.Column('error_logs', sa.Text(), nullable=True),
        sa.Column('expected_behavior', sa.Text(), nullable=True),
        sa.Column('actual_behavior', sa.Text(), nullable=True),
        sa.Column('screenshot', sa.Text(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('assigned_to', sa.String(), nullable=True),
        sa.Column('pattern_id', sa.String(), nullable=True),
        sa.Column('duplicate_count', sa.Integer(), nullable=True),
        sa.Column('affected_users', sa.Integer(), nullable=True),
        sa.Column('first_reported_at', sa.DateTime(), nullable=True),
        sa.Column('last_reported_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pattern_id'], ['feedback_patterns.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedback_created_at'), 'feedback', ['created_at'], unique=False)
    op.create_index(op.f('ix_feedback_pattern_id'), 'feedback', ['pattern_id'], unique=False)
    op.create_index(op.f('ix_feedback_severity'), 'feedback', ['severity'], unique=False)
    op.create_index(op.f('ix_feedback_status'), 'feedback', ['status'], unique=False)
    op.create_index(op.f('ix_feedback_type'), 'feedback', ['type'], unique=False)
    op.create_index(op.f('ix_feedback_url'), 'feedback', ['url'], unique=False)
    op.create_index(op.f('ix_feedback_user_id'), 'feedback', ['user_id'], unique=False)

    # Create feedback_impact table
    op.create_table('feedback_impact',
        sa.Column('feedback_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('impact_score', sa.Integer(), nullable=True),
        sa.Column('churn_risk', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['feedback_id'], ['feedback.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('feedback_id', 'user_id')
    )
    op.create_index(op.f('ix_feedback_impact_impact_score'), 'feedback_impact', ['impact_score'], unique=False)
    op.create_index(op.f('ix_feedback_impact_user_id'), 'feedback_impact', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_feedback_impact_user_id'), table_name='feedback_impact')
    op.drop_index(op.f('ix_feedback_impact_impact_score'), table_name='feedback_impact')
    op.drop_table('feedback_impact')
    op.drop_index(op.f('ix_feedback_user_id'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_url'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_type'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_status'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_severity'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_pattern_id'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_created_at'), table_name='feedback')
    op.drop_table('feedback')
    op.drop_index(op.f('ix_feedback_patterns_pattern_type'), table_name='feedback_patterns')
    op.drop_index(op.f('ix_feedback_patterns_pattern_signature'), table_name='feedback_patterns')
    op.drop_table('feedback_patterns')