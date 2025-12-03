import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from data.model import *
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from config_reader import base_dir, db_link
import os
from sqlalchemy import create_engine

# ==========================================
# АСИНХРОННЫЕ ФУНКЦИИ ДЛЯ БОТА
# ==========================================

async def get_products_for_selection(
    category_id: int = None,
    accessory_brand_id: int = None,
    device_model_id: int = None,
    series_id: int = None,
    color_id: int = None,
    offset: int = None,
    limit: int = None
):
    """
    Получить продукты с фильтрацией по выбранным критериям
    :return: список продуктов
    """
    stmt = select(Products).filter(Products.is_active == True)
    
    if category_id is not None:
        stmt = stmt.filter(Products.category_id == category_id)
    if accessory_brand_id is not None:
        stmt = stmt.filter(Products.accessory_brand_id == accessory_brand_id)
    if device_model_id is not None:
        stmt = stmt.filter(Products.device_model_id == device_model_id)
    if series_id is not None:
        stmt = stmt.filter(Products.series_id == series_id)
    if color_id is not None:
        stmt = stmt.filter(Products.color_id == color_id)
    
    if offset is not None:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(stmt)
        return result.scalars().all()

async def count_products(
    category_id: int = None,
    accessory_brand_id: int = None,
    device_model_id: int = None,
    series_id: int = None,
    color_id: int = None
) -> int:
    """Подсчет количества продуктов с фильтрацией"""
    stmt = select(func.count(Products.id)).filter(Products.is_active == True)
    
    if category_id is not None:
        stmt = stmt.filter(Products.category_id == category_id)
    if accessory_brand_id is not None:
        stmt = stmt.filter(Products.accessory_brand_id == accessory_brand_id)
    if device_model_id is not None:
        stmt = stmt.filter(Products.device_model_id == device_model_id)
    if series_id is not None:
        stmt = stmt.filter(Products.series_id == series_id)
    if color_id is not None:
        stmt = stmt.filter(Products.color_id == color_id)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(stmt)
        count = result.scalar()
    return count or 0

async def get_product_by_id(product_id: int):
    """Получить продукт по ID"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Products).filter(Products.id == product_id)
        )
        return result.scalar()

async def get_product_image(product_id: int, color_id: int = None):
    """Получить изображение продукта"""
    async with AsyncSessionLocal() as session:
        stmt = select(ProductImages).filter(ProductImages.product_id == product_id)
        if color_id:
            stmt = stmt.filter(ProductImages.color_id == color_id)
        stmt = stmt.filter(ProductImages.is_main == True)
        
        result = await session.execute(stmt)
        img_obj = result.scalar()
        
        if img_obj:
            return os.path.join(base_dir, "stock", "devices_images", img_obj.path)
        return None

async def get_product_full_info(product_id: int):
    """Получить полную информацию о продукте для отображения карточки"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Products)
            .options(
                selectinload(Products.category),
                selectinload(Products.accessory_brand),
                selectinload(Products.device_model).selectinload(DeviceModels.device_brand),
                selectinload(Products.series),
                selectinload(Products.variation),
                selectinload(Products.color)
            )
            .filter(Products.id == product_id)
        )
        product = result.scalar()
        
        if not product:
            return None
        
        return {
            "id": product.id,
            "category": product.category.name if product.category else None,
            "accessory_brand": product.accessory_brand.name if product.accessory_brand else None,
            "device_model": str(product.device_model) if product.device_model else None,
            "series": product.series.name if product.series else None,
            "variation": product.variation.name if product.variation else None,
            "color": product.color.name if product.color else None,
            "color_id": product.color_id,
            "price": product.price,
            "description": product.description,
        }

async def get_cart_items(user_id):
    """Получить товары из корзины пользователя"""
    from data.model import Variations
    stmt = (
        select(
            Products.id.label("product_id"),
            Categories.name.label("category"),
            AccessoryBrands.name.label("brand"),
            DeviceModels.name.label("device_model"),
            Series.name.label("series"),
            Variations.name.label("variation"),
            Colors.name.label("color"),
            Products.price,
            (Products.price * CartItems.quantity).label("sum"),
            CartItems.quantity
        )
        .select_from(CartItems)
        .outerjoin(Products, CartItems.product_id == Products.id)
        .outerjoin(Categories, Products.category_id == Categories.id)
        .outerjoin(AccessoryBrands, Products.accessory_brand_id == AccessoryBrands.id)
        .outerjoin(DeviceModels, Products.device_model_id == DeviceModels.id)
        .outerjoin(Series, Products.series_id == Series.id)
        .outerjoin(Variations, Products.variation_id == Variations.id)
        .outerjoin(Colors, Products.color_id == Colors.id)
        .where(CartItems.user_id == user_id)
        .order_by(Categories.name, AccessoryBrands.name)
    )
    async with AsyncSessionLocal() as session:
        result = await session.execute(stmt)
        cart_items = result.mappings().all()
    return cart_items

async def add_new_customer(user_id: int, username: str):
    """Добавить нового пользователя или получить существующего"""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Customers).filter_by(telegram_id=user_id)
            )
            customer = result.scalar()
            if not customer:
                customer = Customers(telegram_id=user_id, username=username)
                session.add(customer)
                await session.commit()
            return customer
        except SQLAlchemyError as e:
            await session.rollback()
            print(f"Ошибка добавления нового пользователя {user_id}: {e}")

async def add_cart_item(product_id: int, user_id: int, quantity: int = 1):
    """Добавить товар в корзину"""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(CartItems).filter_by(user_id=user_id, product_id=product_id)
            )
            cart_item = result.scalar()
            if cart_item:
                cart_item.quantity += quantity
            else:
                cart_item = CartItems(user_id=user_id, product_id=product_id, quantity=quantity)
                session.add(cart_item)
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            print(f"Ошибка добавления товара в корзину {product_id}: {e}")

async def count_cart_sum(user_id):
    """Подсчитать общую сумму корзины"""
    stmt = (
        select(
            func.sum(CartItems.quantity * Products.price).label("total_sum")
        )
        .select_from(CartItems)
        .outerjoin(Products, CartItems.product_id == Products.id)
        .where(CartItems.user_id == user_id)
    )
    async with AsyncSessionLocal() as session:
        result = await session.execute(stmt)
        total = result.scalar()
    return total or 0

async def clear_user_cart(user_id):
    """Очистить корзину пользователя"""
    async with AsyncSessionLocal() as session:
        try:
            stmt = delete(CartItems).where(CartItems.user_id == user_id)
            await session.execute(stmt)
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            print(f"Ошибка очистки корзины пользователя {user_id}: {e}")

async def make_order(user_id, date):
    """Создать заказ из корзины"""
    async with AsyncSessionLocal() as session:
        try:
            total_price = await count_cart_sum(user_id)
            result = await session.execute(
                select(OrderStatuses).where(OrderStatuses.name == "В работе")
            )
            status = result.scalar_one_or_none()
            order = Orders(customer_id=user_id, created_at=date, status=status, total_price=total_price)
            session.add(order)
            await session.flush()
            
            stmt = (
                select(
                    CartItems.quantity,
                    CartItems.product_id
                )
                .select_from(CartItems)
                .where(CartItems.user_id == user_id)
            )
            result = await session.execute(stmt)
            cart_items = result.mappings().all()
            
            if not cart_items:
                print("Корзина пуста — заказ не создан.")
                await session.rollback()
                return None
            
            for cart_item in cart_items:
                order_item = OrderItems(
                    order_id=order.id,
                    quantity=cart_item["quantity"],
                    product_id=cart_item["product_id"]
                )
                session.add(order_item)
            
            await clear_user_cart(user_id)
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            print(f"Ошибка создания заказа: {e}")
            return None
        return order

async def get_admins():
    """Получить список админов"""
    stmt = (
        select(
            Admins.username,
            Admins.id
        ).select_from(Admins)
    )
    async with AsyncSessionLocal() as session:
        result = await session.execute(stmt)
        admins = result.mappings().all()
    return admins

async def get_order_details(order_id):
    """Получить детали заказа"""
    from data.model import Variations
    stmt = (
        select(
            Categories.name.label("category"),
            AccessoryBrands.name.label("brand"),
            DeviceModels.name.label("device_model"),
            Series.name.label("series"),
            Variations.name.label("variation"),
            Colors.name.label("color"),
            Products.price,
            (Products.price * OrderItems.quantity).label("sum"),
            OrderItems.quantity
        )
        .select_from(OrderItems)
        .outerjoin(Products, OrderItems.product_id == Products.id)
        .outerjoin(Categories, Products.category_id == Categories.id)
        .outerjoin(AccessoryBrands, Products.accessory_brand_id == AccessoryBrands.id)
        .outerjoin(DeviceModels, Products.device_model_id == DeviceModels.id)
        .outerjoin(Series, Products.series_id == Series.id)
        .outerjoin(Variations, Products.variation_id == Variations.id)
        .outerjoin(Colors, Products.color_id == Colors.id)
        .where(OrderItems.order_id == order_id)
        .order_by(Categories.name, AccessoryBrands.name)
    )
    async with AsyncSessionLocal() as session:
        result = await session.execute(stmt)
        order_items = result.mappings().all()
    return order_items

# ==========================================
# СИНХРОННЫЕ ФУНКЦИИ ДЛЯ FLASK ADMIN
# ==========================================

# Создаем синхронный движок для Flask
sync_engine = create_engine(db_link, echo=True)
SyncSessionLocal = sessionmaker(bind=sync_engine)

def get_or_create_sync(local_session, model, **kwargs):
    """Получить или создать объект (синхронная версия)"""
    instance = local_session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    instance = model(**kwargs)
    local_session.add(instance)
    local_session.flush()
    return instance
