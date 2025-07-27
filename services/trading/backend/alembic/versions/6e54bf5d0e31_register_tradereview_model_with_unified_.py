"""Register TradeReview model with unified Base

Revision ID: 6e54bf5d0e31
Revises: 3911f13f470b
Create Date: 2025-07-02 21:55:54.148441

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e54bf5d0e31'
down_revision: Union[str, Sequence[str], None] = '3911f13f470b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # No-op: index is created by SQLAlchemy from the model definition
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # No-op: index is dropped with the table by SQLAlchemy
    pass
