"""merge heads
Revision ID: 1a45e659df84
Revises: 6e54bf5d0e31, add_billing_tables
Create Date: 2025-07-14 11:59:24.356494
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1a45e659df84'
down_revision: Union[str, Sequence[str], None] = ('6e54bf5d0e31', 'add_billing_tables')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    pass

def downgrade() -> None:
    """Downgrade schema."""
    pass
