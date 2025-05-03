from data.model import *
import csv
from sqlalchemy import select
from config_reader import base_dir
import os

def query_models_variants(model_id: int, color_id:int, offset: int, limit: int):
    """

    :param model_id: int айди модели устройства
    :param color_id: int айди цвета устройства
    :param offset: int с какой записи выбирать
    :param limit: int ограничение по количеству записей
    :return: все варианты устройств с отбором по модели по цвету
    """
    stmt = (
        select(
            SimCards.name.label("sim"),
            MemoryStorage.name.label("memory"),
            ModelVariants.price.label("price"),
            ModelVariants.id.label("id")
        )
        .select_from(ModelVariants)
        .outerjoin(SimCards, ModelVariants.sim_id == SimCards.id)
        .outerjoin(MemoryStorage, ModelVariants.memory_id == MemoryStorage.id)
        .filter(ModelVariants.model_id == model_id, ModelVariants.color_id == color_id)
        .order_by(
            MemoryStorage.quantity,
            SimCards.name)
    )

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
            .filter_by(id=model.id, color_id=color.id)
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
            DeviceVariants.sim,
            DeviceVariants.memory,
            DeviceVariants.price,
            CartItems.quantity,
            (DeviceVariants.price * CartItems.quantity).label("sum")
        )
        .select_from(CartItems)
        .join(DeviceVariants, CartItems.variant_id == DeviceVariants.id)
        .join(Devices, DeviceVariants.device_id == Devices.id)
        .join(Models, Devices.model_id == Models.id)
        .join(Colors, Devices.color_id == Colors.id)
        .where(CartItems.user_id == user_id)
    )
    result = session.execute(stmt)
    cart_items = result.mappings().all()
    return cart_items

def add_new_customer(user_id: int, username: str):
    customer = session.query(Customers).filter_by(telegram_id=user_id).first()
    if not customer:
        customer = Customers(telegram_id=user_id, username=username)
        session.add(customer)
        session.commit()

def add_cart_item(variant_id, user_id):
    cart_item = session.query(CartItems).filter_by(user_id=user_id, variant_id=variant_id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItems(user_id=user_id, variant_id=variant_id, quantity=1)
        session.add(cart_item)
    session.commit()
