"""empty message

Revision ID: ffd80a482778
Revises: c2f0d759fd6b
Create Date: 2025-05-04 16:54:00.576740

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ffd80a482778'
down_revision: Union[str, None] = 'c2f0d759fd6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
