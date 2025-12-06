"""Add sort_order column to categories, brands and device models

Revision ID: add_sort_order_202512
Revises: 08baed149111
Create Date: 2025-12-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_sort_order_202512'
down_revision: Union[str, None] = '08baed149111'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем колонку sort_order в таблицу categories
    op.add_column('categories', sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'))
    
    # Добавляем колонку sort_order в таблицу accessory_brands
    op.add_column('accessory_brands', sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'))
    
    # Добавляем колонку sort_order в таблицу device_brands
    op.add_column('device_brands', sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'))
    
    # Добавляем колонку sort_order в таблицу device_models
    op.add_column('device_models', sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    op.drop_column('device_models', 'sort_order')
    op.drop_column('device_brands', 'sort_order')
    op.drop_column('accessory_brands', 'sort_order')
    op.drop_column('categories', 'sort_order')

