"""add variations table

Revision ID: add_variations_202512
Revises: refactor_accessories_202511
Create Date: 2025-12-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_variations_202512'
down_revision: Union[str, None] = 'refactor_accessories_202511'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add variations table."""
    
    from sqlalchemy import inspect
    
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()
    
    # 1. Создаем таблицу вариаций
    if 'variations' not in existing_tables:
        op.create_table(
            'variations',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
    
    # 2. Создаем временную таблицу для хранения данных из старого поля variation
    # Извлекаем уникальные значения вариаций из products
    connection = op.get_bind()
    
    # Проверяем, есть ли столбец variation в products
    existing_columns = [col['name'] for col in inspector.get_columns('products')]
    
    if 'variation' in existing_columns and 'variation_id' not in existing_columns:
        # Получаем уникальные вариации
        result = connection.execute(sa.text(
            "SELECT DISTINCT variation FROM products WHERE variation IS NOT NULL AND variation != ''"
        ))
        unique_variations = [row[0] for row in result]
        
        # Вставляем их в таблицу variations
        if unique_variations:
            for variation_name in unique_variations:
                connection.execute(
                    sa.text("INSERT INTO variations (name) VALUES (:name)"),
                    {"name": variation_name}
                )
        
        # 3. Добавляем новый столбец variation_id в products
        op.add_column('products', sa.Column('variation_id', sa.Integer(), nullable=True))
        
        # 4. Создаем внешний ключ
        op.create_foreign_key(
            'fk_products_variation_id',
            'products', 'variations',
            ['variation_id'], ['id']
        )
        
        # 5. Мигрируем данные из старого столбца variation в variation_id
        if unique_variations:
            for variation_name in unique_variations:
                # Получаем id вариации
                result = connection.execute(
                    sa.text("SELECT id FROM variations WHERE name = :name"),
                    {"name": variation_name}
                )
                variation_id = result.scalar()
                
                # Обновляем products
                connection.execute(
                    sa.text("UPDATE products SET variation_id = :vid WHERE variation = :vname"),
                    {"vid": variation_id, "vname": variation_name}
                )
        
        # 6. Удаляем старый constraint если он существует
        try:
            op.drop_constraint('uq_product_combination', 'products', type_='unique')
        except Exception:
            pass  # Constraint может не существовать
        
        # 7. Удаляем старый столбец variation
        op.drop_column('products', 'variation')
        
        # 8. Создаем новый unique constraint
        op.create_unique_constraint(
            'uq_product_combination',
            'products',
            ['category_id', 'accessory_brand_id', 'device_model_id', 'series_id', 'variation_id', 'color_id']
        )


def downgrade() -> None:
    """Downgrade schema to remove variations table."""
    
    from sqlalchemy import inspect
    
    bind = op.get_bind()
    inspector = inspect(bind)
    connection = op.get_bind()
    
    # 1. Удаляем новый constraint
    try:
        op.drop_constraint('uq_product_combination', 'products', type_='unique')
    except Exception:
        pass
    
    # 2. Добавляем обратно столбец variation
    op.add_column('products', sa.Column('variation', sa.String(length=200), nullable=True))
    
    # 3. Мигрируем данные обратно из variation_id в variation
    result = connection.execute(sa.text(
        """
        SELECT p.id, v.name 
        FROM products p 
        JOIN variations v ON p.variation_id = v.id 
        WHERE p.variation_id IS NOT NULL
        """
    ))
    
    for product_id, variation_name in result:
        connection.execute(
            sa.text("UPDATE products SET variation = :vname WHERE id = :pid"),
            {"vname": variation_name, "pid": product_id}
        )
    
    # 4. Удаляем внешний ключ и столбец variation_id
    try:
        op.drop_constraint('fk_products_variation_id', 'products', type_='foreignkey')
    except Exception:
        pass
    
    op.drop_column('products', 'variation_id')
    
    # 5. Восстанавливаем старый constraint
    op.create_unique_constraint(
        'uq_product_combination',
        'products',
        ['category_id', 'accessory_brand_id', 'device_model_id', 'series_id', 'color_id', 'variation']
    )
    
    # 6. Удаляем таблицу variations
    op.drop_table('variations')

