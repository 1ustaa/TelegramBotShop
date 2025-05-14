from httpx import delete
from sqlalchemy.exc import SQLAlchemyError

from data.model import *
from sqlalchemy import select, func, delete, nullsfirst
from config_reader import base_dir
import os

def query_models_variants(model_id: int, color_id:int, variant_id: int=None, offset: int=None, limit: int=None):
    """

    :param model_id: int айди модели устройства
    :param color_id: int айди цвета устройства
    :param variant_id: int айди варианта устройства
    :param offset: int с какой записи выбирать
    :param limit: int ограничение по количеству записей
    :return: все варианты устройств с отбором по модели по цвету
    """
    stmt = (
        select(
            Diagonals.name.label("diagonal"),
            SimCards.name.label("sim"),
            MemoryStorage.name.label("memory"),
            ModelVariants.price.label("price"),
            ModelVariants.id.label("id")
        )
        .select_from(ModelVariants)
        .outerjoin(SimCards, ModelVariants.sim_id == SimCards.id)
        .outerjoin(MemoryStorage, ModelVariants.memory_id == MemoryStorage.id)
        .outerjoin(Diagonals, ModelVariants.diagonal_id == Diagonals.id)
        .filter(
            ModelVariants.model_id == model_id,
            ModelVariants.color_id == color_id,
            ModelVariants.is_active == True)
        .order_by(
            MemoryStorage.quantity,
            SimCards.name)
    )
    if variant_id is not None:
        stmt = stmt.filter(ModelVariants.id == variant_id)
    if offset is not None:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)

    return session.execute(stmt).mappings().all()

def count_models_variants(model_id :int, color_id:int) -> int:
    count = (
        session.query(ModelVariants)
        .filter(
            ModelVariants.model_id == model_id,
            ModelVariants.color_id == color_id
        )
        .count()
    )
    return count

def get_color_model_image(model_id, color_id):
    model = session.get(Models, model_id)
    color = session.get(Colors, color_id)

    model_name = model.name if model else ""
    color_name = color.name if color else ""

    image = ""

    if model and color:
        image = (
            session.query(ModelsImages)
            .filter_by(model_id=model.id, color_id=color.id)
            .first()
        )
        if image:
            image = os.path.join(base_dir, "stock", "devices_images", image.path)

    return model_name, color_name, image

def get_cart_items(user_id):

    stmt = (
        select(
            Models.name.label("model"),
            Colors.name.label("color"),
            SimCards.name.label("sim"),
            MemoryStorage.name.label("memory"),
            Diagonals.name.label("diagonal"),
            ModelVariants.price,
            (ModelVariants.price * CartItems.quantity).label("sum"),
            CartItems.quantity
        )
        .select_from(CartItems)
        .outerjoin(ModelVariants, CartItems.model_variant_id == ModelVariants.id)
        .outerjoin(SimCards, ModelVariants.sim_id == SimCards.id)
        .outerjoin(Models, ModelVariants.model_id == Models.id)
        .outerjoin(Colors, ModelVariants.color_id == Colors.id)
        .outerjoin(MemoryStorage, ModelVariants.memory_id == MemoryStorage.id)
        .outerjoin(Diagonals, ModelVariants.diagonal_id == Diagonals.id)
        .where(CartItems.user_id == user_id)
    )

    result = session.execute(stmt)
    cart_items = result.mappings().all()
    return cart_items

def add_new_customer(user_id: int, username: str):
    try:
        customer = session.query(Customers).filter_by(telegram_id=user_id).first()
        if not customer:
            customer = Customers(telegram_id=user_id, username=username)
            session.add(customer)
            session.commit()
        return customer
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Ошибка добавления нового пользователя {user_id}: {e}")

def add_cart_item(variant_id, user_id):
    try:
        cart_item = session.query(CartItems).filter_by(user_id=user_id, model_variant_id=variant_id).first()
        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = CartItems(user_id=user_id, model_variant_id=variant_id, quantity=1)
            session.add(cart_item)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Ошибка добавления варианта в корзину {variant_id}: {e}")

def count_cart_sum(user_id):
    stmt = (
        select(
            func.sum(CartItems.quantity * ModelVariants.price).label("total_sum")
        )
        .select_from(CartItems)
        .outerjoin(ModelVariants, CartItems.model_variant_id == ModelVariants.id)
        .where(CartItems.user_id == user_id)
    )

    result = session.execute(stmt).scalar()
    return result or 0

def clear_user_cart(user_id):
    try:
        stmt = delete(CartItems).where(CartItems.user_id == user_id)
        session.execute(stmt)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Ошибка очистки корзины пользователя {user_id}: {e}")

# TODO: Дописать функцию для создания заказов
def make_order(user_id, total_price, date):
    try:
        order = Orders(customer_id=user_id, created_at=date, status="в работе", total_price=total_price)
        session.add(order)

        stmt = (
            select(
                CartItems.quantity,
                CartItems.model_variant_id
            )
            .select_from(CartItems)
            .where(CartItems.user_id == user_id)
        )
        result = session.execute(stmt)
        cart_items = result.mappings().all()

        for cart_item in cart_items:
            order_item = OrderItems(
                order_id=order.id,
                quantity=cart_item.quantity,
                model_variant_id=cart_item.model_variant_id)
            session.add(order_item)

        clear_user_cart(user_id)
        session.commit()

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Ошибка добавления предмета в заказ айди заказа: {e}")
        return None

    return order.id

