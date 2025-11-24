"""refactor to accessories model

Revision ID: refactor_accessories_202511
Revises: 804e5bb4d764
Create Date: 2025-11-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'refactor_accessories_202511'
down_revision: Union[str, None] = '804e5bb4d764'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to accessories model."""
    
    from sqlalchemy import inspect
    
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()
    
    # 1. Удаляем внешние ключи и старые таблицы, связанные со смартфонами
    
    # Сначала удаляем зависимые таблицы (только если существуют)
    if 'cart_items' in existing_tables:
        op.drop_table('cart_items')
    if 'order_items' in existing_tables:
        op.drop_table('order_items')
    if 'models_images' in existing_tables:
        op.drop_table('models_images')
    if 'model_variants' in existing_tables:
        op.drop_table('model_variants')
    if 'models' in existing_tables:
        op.drop_table('models')
    if 'manufacturer_category' in existing_tables:
        op.drop_table('manufacturer_category')
    if 'manufacturers' in existing_tables:
        op.drop_table('manufacturers')
    if 'sim_cards' in existing_tables:
        op.drop_table('sim_cards')
    if 'memory_storage' in existing_tables:
        op.drop_table('memory_storage')
    if 'diagonals' in existing_tables:
        op.drop_table('diagonals')
    
    # Обновляем список существующих таблиц
    existing_tables = inspector.get_table_names()
    
    # 2. Создаем новые таблицы для аксессуаров
    
    # Таблица брендов аксессуаров
    if 'accessory_brands' not in existing_tables:
        op.create_table(
            'accessory_brands',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
    
    # Таблица брендов устройств
    if 'device_brands' not in existing_tables:
        op.create_table(
            'device_brands',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
    
    # Таблица моделей устройств
    if 'device_models' not in existing_tables:
        op.create_table(
            'device_models',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('device_brand_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['device_brand_id'], ['device_brands.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Таблица серий
    if 'series' not in existing_tables:
        op.create_table(
            'series',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
    
    # Таблица продуктов
    if 'products' not in existing_tables:
        op.create_table(
            'products',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('variation', sa.String(length=200), nullable=True),
            sa.Column('price', sa.Integer(), nullable=True),
            sa.Column('description', sa.String(length=500), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
            sa.Column('category_id', sa.Integer(), nullable=False),
            sa.Column('accessory_brand_id', sa.Integer(), nullable=False),
            sa.Column('device_model_id', sa.Integer(), nullable=True),
            sa.Column('series_id', sa.Integer(), nullable=True),
            sa.Column('color_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
            sa.ForeignKeyConstraint(['accessory_brand_id'], ['accessory_brands.id'], ),
            sa.ForeignKeyConstraint(['device_model_id'], ['device_models.id'], ),
            sa.ForeignKeyConstraint(['series_id'], ['series.id'], ),
            sa.ForeignKeyConstraint(['color_id'], ['colors.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Таблица изображений продуктов
    if 'product_images' not in existing_tables:
        op.create_table(
            'product_images',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('path', sa.String(), nullable=False),
            sa.Column('is_main', sa.Boolean(), nullable=True, default=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('color_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['color_id'], ['colors.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Обновляем список существующих таблиц снова
    existing_tables = inspector.get_table_names()
    
    # 3. Пересоздаем таблицы корзины и заказов с новыми связями
    
    # Таблица корзины
    if 'cart_items' not in existing_tables:
        op.create_table(
            'cart_items',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('user_id', sa.BigInteger(), nullable=False),
            sa.Column('quantity', sa.Integer(), nullable=True, default=1),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['customers.telegram_id'], ),
            sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Таблица позиций заказов
    if 'order_items' not in existing_tables:
        op.create_table(
            'order_items',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('quantity', sa.Integer(), nullable=True, default=1),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
            sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Создаем индексы (проверяем существование)
    existing_indexes = []
    for table_name in existing_tables:
        indexes = inspector.get_indexes(table_name)
        existing_indexes.extend([idx['name'] for idx in indexes])
    
    if 'ix_order_items_order_id' not in existing_indexes:
        op.create_index('ix_order_items_order_id', 'order_items', ['order_id'])


def downgrade() -> None:
    """Downgrade schema back to smartphone model."""
    
    # Это довольно сложный откат, так как мы меняем всю структуру
    # В реальном проекте лучше создать резервную копию БД перед миграцией
    
    # Удаляем новые таблицы
    op.drop_index('ix_order_items_order_id')
    op.drop_table('order_items')
    op.drop_table('cart_items')
    op.drop_table('product_images')
    op.drop_table('products')
    op.drop_table('series')
    op.drop_table('device_models')
    op.drop_table('device_brands')
    op.drop_table('accessory_brands')
    
    # Восстанавливаем старые таблицы
    # (Здесь нужно добавить код создания старых таблиц, если требуется полный откат)
    # Для краткости пропущено, так как в реальности откат такой большой миграции
    # обычно делается через восстановление резервной копии БД
    pass

