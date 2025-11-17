import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

from data.model import *
from sqlalchemy import select, func, delete
from config_reader import base_dir
import os

async def query_models_variants(model_id: int, color_id: int, variant_id: int = None, offset: int = None, limit: int = None):
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
            Diagonals.name,
            SimCards.name)
    )
    if variant_id is not None:
        stmt = stmt.filter(ModelVariants.id == variant_id)
    if offset is not None:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)

    async with AsyncSessionLocal() as session:
        result = await session.execute(stmt)
        return result.mappings().all()

async def count_models_variants(model_id: int, color_id: int) -> int:
    stmt = (
        select(func.count(ModelVariants.id))
        .where(
            ModelVariants.model_id == model_id,
            ModelVariants.color_id == color_id,
            ModelVariants.is_active == True
        )
    )
    async with AsyncSessionLocal() as session:
        result = await session.execute(stmt)
        count = result.scalar()
    return count

async def get_color_model_image(model_id, color_id):
    async with AsyncSessionLocal() as session:
        model = await session.get(Models, model_id)
        color = await session.get(Colors, color_id)
        model_name = model.name if model else ""
        color_name = color.name if color else ""
        image = ""
        if model and color:
            result = await session.execute(
                select(ModelsImages).filter_by(model_id=model.id, color_id=color.id)
            )
            img_obj = result.scalar()
            if img_obj:
                image = os.path.join(base_dir, "stock", "devices_images", img_obj.path)
    return model_name, color_name, image

async def get_variant_name(model_id, color_id, variant_id):
    model_name, color_name, image_path = await get_color_model_image(model_id, color_id)
    variant = await query_models_variants(model_id, color_id, variant_id)

    text_variant = ""
    for feature in variant:
        text_variant = "".join([
            f"{feature.memory} " if feature.memory else "",
            f"{feature.sim} " if feature.sim else "",
            f"{feature.diagonal} " if feature.diagonal else ""
        ]).strip()
    variant_name = f"{model_name} {color_name} {text_variant}"
    return variant_name

async def get_cart_items(user_id):
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
        .order_by(
            Models.name,
            Colors.name,
            SimCards.name,
            MemoryStorage.name,
            Diagonals.name,
            ModelVariants.price)
    )
    async with AsyncSessionLocal() as session:
        result = await session.execute(stmt)
        cart_items = result.mappings().all()
    return cart_items

async def add_new_customer(user_id: int, username: str):
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

async def add_cart_item(variant_id, user_id):
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(CartItems).filter_by(user_id=user_id, model_variant_id=variant_id)
            )
            cart_item = result.scalar()
            if cart_item:
                cart_item.quantity += 1
            else:
                cart_item = CartItems(user_id=user_id, model_variant_id=variant_id, quantity=1)
                session.add(cart_item)
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            print(f"Ошибка добавления варианта в корзину {variant_id}: {e}")

async def count_cart_sum(user_id):
    stmt = (
        select(
            func.sum(CartItems.quantity * ModelVariants.price).label("total_sum")
        )
        .select_from(CartItems)
        .outerjoin(ModelVariants, CartItems.model_variant_id == ModelVariants.id)
        .where(CartItems.user_id == user_id)
    )
    async with AsyncSessionLocal() as session:
        result = await session.execute(stmt)
        total = result.scalar()
    return total or 0

async def clear_user_cart(user_id):
    async with AsyncSessionLocal() as session:
        try:
            stmt = delete(CartItems).where(CartItems.user_id == user_id)
            await session.execute(stmt)
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            print(f"Ошибка очистки корзины пользователя {user_id}: {e}")

async def make_order(user_id, date):
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
                    CartItems.model_variant_id
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
                    model_variant_id=cart_item["model_variant_id"])
                session.add(order_item)
            await clear_user_cart(user_id)
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            print(f"Ошибка добавления предмета в заказ айди заказа: {e}")
            return None
        return order

async def get_admins():
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
    stmt = (
        select(
            Manufacturers.name.label("manufacturer"),
            Models.name.label("model"),
            Colors.name.label("color"),
            SimCards.name.label("sim"),
            MemoryStorage.name.label("memory"),
            Diagonals.name.label("diagonal"),
            ModelVariants.price,
            (ModelVariants.price * OrderItems.quantity).label("sum"),
            OrderItems.quantity
        )
        .select_from(OrderItems)
        .outerjoin(ModelVariants, OrderItems.model_variant_id == ModelVariants.id)
        .outerjoin(SimCards, ModelVariants.sim_id == SimCards.id)
        .outerjoin(Models, ModelVariants.model_id == Models.id)
        .outerjoin(Manufacturers, Manufacturers.id == Models.manufacturer_id)
        .outerjoin(Colors, ModelVariants.color_id == Colors.id)
        .outerjoin(MemoryStorage, ModelVariants.memory_id == MemoryStorage.id)
        .outerjoin(Diagonals, ModelVariants.diagonal_id == Diagonals.id)
        .where(OrderItems.order_id == order_id)
        .order_by(
            Manufacturers.name,
            Models.name,
            Colors.name,
            SimCards.name,
            MemoryStorage.name,
            Diagonals.name,
            ModelVariants.price,
            SimCards.name)
    )
    async with AsyncSessionLocal() as session:
        result = await session.execute(stmt)
        order_items = result.mappings().all()
    return order_items

async def get_or_create(local_session, model, **kwargs):
    result = await local_session.execute(select(model).filter_by(**kwargs))
    instance = result.scalar()
    if instance:
        return instance
    instance = model(**kwargs)
    local_session.add(instance)
    await local_session.commit()
    return instance

# def import_from_excel(file_path):
#     local_session = Session(bind=engine)

#     xls = pd.read_excel(file_path, sheet_name=None)

#     for sheet_name, df in xls.items():
#         df.fillna("", inplace=True)

#         for _, row in df.iterrows():
#             try:
#                 category = get_or_create(local_session, Categories, name=row["Категория"])
#                 manufacturer = get_or_create(local_session, Manufacturers, name=row["Производитель"])

#                 if category not in manufacturer.categories:
#                     manufacturer.categories.append(category)

#                 model = local_session.query(Models).filter_by(name=row["Устройство"]).first()
#                 if not model:
#                     model = Models(name=row["Устройство"], category=category, manufacturer=manufacturer)
#                     local_session.add(model)
#                     local_session.flush()

#                 color = get_or_create(local_session, Colors, name=row["Цвет"])
#                 sim = get_or_create(local_session, SimCards, name=row["SIM"]) if row["SIM"] else None
#                 memory_str = int(row['Память']) if type(row['Память']) == int else row['Память']
#                 memory = local_session.query(MemoryStorage).filter(MemoryStorage.name.like(f"%{memory_str}%")).first()
#                 if not memory:
#                     memory = None
#                 diagonal = get_or_create(local_session, Diagonals, name=str(row["Диагональ"])) if row["Диагональ"] else None

#                 price = int(row["Цена"]) if row["Цена"] else 0
#                 description = row["Описание"] or ""
#                 is_active = str(row["Активно"]).strip().lower() in ("true", "1", "да")

#                 exists = local_session.query(ModelVariants).filter_by(
#                     model_id=model.id,
#                     sim_id=sim.id if sim else None,
#                     memory_id=memory.id if memory else None,
#                     diagonal_id=diagonal.id if diagonal else None,
#                     color_id=color.id
#                 ).first()

#                 if not exists:
#                     variant = ModelVariants(
#                         model=model,
#                         sim=sim,
#                         memory=memory,
#                         diagonal=diagonal,
#                         color=color,
#                         price=price,
#                         description=description,
#                         is_active=is_active
#                     )
#                     local_session.add(variant)
#                 else:
#                     exists.is_active = is_active
#                     exists.price = price

#                 local_session.commit()
#             except Exception as e:
#                 local_session.rollback()
#                 print(e)
#                 continue
#     local_session.close()
