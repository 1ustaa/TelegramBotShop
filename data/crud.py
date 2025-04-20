from data.model import *

def show_products(model_id: int, page: int, page_size: int):
    return session.query(Devices, DeviceVariants)\
        .outerjoin(DeviceVariants, Devices.id == DeviceVariants.device_id)\
        .filter(
        Devices.model_id == model_id
    ).offset(page * page_size).limit(page_size).all()

def import_from_csv(file_path):
    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        #Обработка производителя, если такого производителя нет, то он создается
        for row in reader:
            try:
                category = session.query(Categories).filter_by(name=row["category"]).first()
                if not category:
                    category = Categories(name=row["category"])
                    session.add(category)

                manufacturer = session.query(Manufacturers).filter_by(name=row["manufacturer"]).first()
                if not manufacturer:
                    manufacturer = Manufacturers(name=row["manufacturer"])
                    session.add(manufacturer)

                if manufacturer not in category.manufacturers:
                    category.manufacturers.append(manufacturer)

                model = session.query(Models).filter_by(name=row["model"]).first()
                if not model:
                    model = Models(name=row["model"])
                    session.add(model)
                    session.flush()

                model.manufacturer = manufacturer
                model.category = category

                color = session.query(Colors).filter_by(name=row["color"]).first()
                if not color:
                    color = Colors(name=row["color"])
                    session.add(color)
                    session.flush()

                device = session.query(Devices).filter_by(model_id=model.id, color_id=color.id).first()
                if not device:
                    device = Devices(model=model, color=color, description=row["description"])
                    session.add(device)
                    session.flush()

                image = session.query(DeviceImages).filter_by(path=row["image"], device_id=device.id).first()
                if not image:
                    image = DeviceImages(path=row["image"], is_main=True, device=device)
                    session.add(image)

                variant = session.query(DeviceVariants).filter_by(
                    device_id=device.id,
                    memory=row["memory"],
                    sim=row["sim"],
                ).first()

                if not variant:
                    variant = DeviceVariants(
                        device=device,
                        memory=row["memory"],
                        sim=row["sim"],
                        price=Decimal(row["price"]) if row["price"] else Decimal("0.00")
                    )
                    session.add(variant)
                session.commit()
            except Exception as e:
                print(e)
                session.rollback()
                continue

    print("Импорт данных завершен")

import_from_csv("devices.csv")

def query_device_variants(model_id: int, color_id:int, offset: int, limit: int):
    """

    :param model_id: int айди модели устройства
    :param color_id: int айди цвета устройства
    :param offset: int с какой записи выбирать
    :param limit: int ограничение по количеству записей
    :return: все варианты устройств с отбором по модели по цвету
    """
    stmt  = (
        select(DeviceVariants)
        .join(DeviceVariants.device)
        .join(Devices.model)
        .join(Devices.color)
        .where(Devices.model_id == model_id, Devices.color_id == color_id)
        .order_by(
            Models.name,
            Colors.name,
            DeviceVariants.memory,
            DeviceVariants.sim
        )
        .offset(offset)
        .limit(limit)
        # options позволяет заранее подгрузить связанные объекты
        # (в нашем случае model и color для device), чтобы
        # избежать лишних запросов в базу при обращении к этим полям
        .options(
            selectinload(DeviceVariants.device).selectinload(Devices.model),
            selectinload(DeviceVariants.device).selectinload(Devices.color)
        )
    )
    result = session.execute(stmt)
    device_variants = result.scalars().all()
    return device_variants

def count_device_variants(model_id :int, color_id:int) -> int:
    stmt = (
        select(func.count())
        .select_from(DeviceVariants)
        .join(DeviceVariants.device)
        .where(Devices.model_id == model_id, Devices.color_id == color_id)
    )
    result = session.execute(stmt)
    count = result.scalar_one()
    return count

def get_color_model_image(model_id, color_id):
    model = session.get(Models, model_id)
    color = session.get(Colors, color_id)

    model_name = model.name if model else ""
    color_name = color.name if color else ""

    image = ""

    if model and color:
        device = (
            session.query(Devices)
            .filter_by(model_id=model.id, color_id=color.id)
            .first()
        )
        if device:
            main_image = next((img for img in device.images if img.is_main), None)
            if main_image:
                image = os.path.join("stock", "devices_images", main_image.path)

    return model_name, color_name, image