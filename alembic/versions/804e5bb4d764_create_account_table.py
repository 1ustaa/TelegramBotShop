"""create account table

Revision ID: 804e5bb4d764
Revises: 684aa1c4b322
Create Date: 2025-11-10 22:05:41.701706

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '804e5bb4d764'
down_revision: Union[str, None] = '684aa1c4b322'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
