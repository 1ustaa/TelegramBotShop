"""add_unique_constraint_to_products

Revision ID: 08baed149111
Revises: refactor_accessories_202511
Create Date: 2025-11-24 12:06:47.981695

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08baed149111'
down_revision: Union[str, None] = 'refactor_accessories_202511'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Сначала удаляем дубликаты, оставляя только записи с наименьшим id
    op.execute("""
        DELETE FROM products
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM products
            GROUP BY category_id, accessory_brand_id, device_model_id, series_id, color_id, variation
        )
    """)
    
    # Добавляем уникальный constraint на комбинацию полей продукта
    op.create_unique_constraint(
        'uq_product_combination',
        'products',
        ['category_id', 'accessory_brand_id', 'device_model_id', 'series_id', 'color_id', 'variation']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем уникальный constraint
    op.drop_constraint('uq_product_combination', 'products', type_='unique')
