"""change to users table

Revision ID: 6b997e8a7688
Revises: a52c03a45b4c
Create Date: 2025-12-01 09:03:58.462504

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b997e8a7688'
down_revision: Union[str, Sequence[str], None] = 'a52c03a45b4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
