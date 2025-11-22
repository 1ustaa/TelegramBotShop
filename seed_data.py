"""
Скрипт для заполнения базы данных тестовыми данными для аксессуаров
Запуск: python seed_data.py
"""

import asyncio
from data.model import (
    AsyncSessionLocal,
    Categories,
    AccessoryBrands,
    DeviceBrands,
    DeviceModels,
    Series,
    Colors,
    Products,
    OrderStatuses
)
from sqlalchemy import select


async def get_or_create(session, model, **kwargs):
    """Получить или создать объект"""
    result = await session.execute(select(model).filter_by(**kwargs))
    instance = result.scalar()
    if instance:
        return instance
    instance = model(**kwargs)
    session.add(instance)
    await session.flush()
    return instance


async def seed_database():
    """Заполнить базу тестовыми данными"""
    async with AsyncSessionLocal() as session:
        try:
            print("Начало заполнения базы данных...")
            
            # 1. Создаем категории
            print("\n1. Создание категорий...")
            cat_cases = await get_or_create(session, Categories, name="Чехлы для телефонов")
            cat_chargers = await get_or_create(session, Categories, name="Зарядники")
            cat_cables = await get_or_create(session, Categories, name="Кабели")
            cat_headphones = await get_or_create(session, Categories, name="Наушники")
            print("✓ Категории созданы")
            
            # 2. Создаем бренды аксессуаров
            print("\n2. Создание брендов аксессуаров...")
            brand_pitaka = await get_or_create(session, AccessoryBrands, name="Pitaka")
            brand_samsung = await get_or_create(session, AccessoryBrands, name="Samsung")
            brand_apple = await get_or_create(session, AccessoryBrands, name="Apple")
            brand_anker = await get_or_create(session, AccessoryBrands, name="Anker")
            print("✓ Бренды аксессуаров созданы")
            
            # 3. Создаем бренды устройств
            print("\n3. Создание брендов устройств...")
            device_brand_iphone = await get_or_create(session, DeviceBrands, name="iPhone")
            device_brand_samsung = await get_or_create(session, DeviceBrands, name="Samsung")
            device_brand_xiaomi = await get_or_create(session, DeviceBrands, name="Xiaomi")
            print("✓ Бренды устройств созданы")
            
            # 4. Создаем модели устройств
            print("\n4. Создание моделей устройств...")
            # iPhone модели
            model_iphone_17pro = await get_or_create(
                session, DeviceModels,
                name="17 Pro",
                device_brand_id=device_brand_iphone.id
            )
            model_iphone_16pro = await get_or_create(
                session, DeviceModels,
                name="16 Pro",
                device_brand_id=device_brand_iphone.id
            )
            model_iphone_15pro = await get_or_create(
                session, DeviceModels,
                name="15 Pro",
                device_brand_id=device_brand_iphone.id
            )
            
            # Samsung модели
            model_s24ultra = await get_or_create(
                session, DeviceModels,
                name="S24 Ultra",
                device_brand_id=device_brand_samsung.id
            )
            model_s23ultra = await get_or_create(
                session, DeviceModels,
                name="S23 Ultra",
                device_brand_id=device_brand_samsung.id
            )
            print("✓ Модели устройств созданы")
            
            # 5. Создаем серии
            print("\n5. Создание серий...")
            series_armor = await get_or_create(session, Series, name="Armor")
            series_slim = await get_or_create(session, Series, name="Slim")
            series_magsafe = await get_or_create(session, Series, name="MagSafe")
            print("✓ Серии созданы")
            
            # 6. Создаем цвета
            print("\n6. Создание цветов...")
            color_black = await get_or_create(session, Colors, name="Черный")
            color_white = await get_or_create(session, Colors, name="Белый")
            color_blue = await get_or_create(session, Colors, name="Синий")
            color_red = await get_or_create(session, Colors, name="Красный")
            color_green = await get_or_create(session, Colors, name="Зеленый")
            print("✓ Цвета созданы")
            
            # 7. Создаем продукты на основе аксесуары.txt
            print("\n7. Создание продуктов...")
            
            # Чехлы Pitaka
            products = [
                {
                    "category": cat_cases,
                    "accessory_brand": brand_pitaka,
                    "device_model": model_iphone_17pro,
                    "series": series_armor,
                    "color": color_black,
                    "price": 4500,
                    "description": "Арамидный чехол Pitaka для iPhone 17 Pro"
                },
                {
                    "category": cat_cases,
                    "accessory_brand": brand_pitaka,
                    "device_model": model_iphone_16pro,
                    "series": series_armor,
                    "color": color_black,
                    "price": 4200,
                    "description": "Арамидный чехол Pitaka для iPhone 16 Pro"
                },
                {
                    "category": cat_cases,
                    "accessory_brand": brand_pitaka,
                    "device_model": model_s24ultra,
                    "series": series_armor,
                    "color": color_black,
                    "price": 4300,
                    "description": "Арамидный чехол Pitaka для Samsung S24 Ultra"
                },
                
                # Зарядники
                {
                    "category": cat_chargers,
                    "accessory_brand": brand_samsung,
                    "device_model": model_s24ultra,
                    "series": None,
                    "color": color_black,
                    "price": 2500,
                    "description": "Быстрое зарядное устройство Samsung 45W"
                },
                {
                    "category": cat_chargers,
                    "accessory_brand": brand_anker,
                    "device_model": None,
                    "series": None,
                    "color": color_white,
                    "price": 3000,
                    "description": "Универсальное зарядное устройство Anker 65W"
                },
                
                # Кабели
                {
                    "category": cat_cables,
                    "accessory_brand": brand_apple,
                    "device_model": None,
                    "series": None,
                    "color": color_white,
                    "price": 1500,
                    "description": "Кабель Lightning to USB-C 1м"
                },
                {
                    "category": cat_cables,
                    "accessory_brand": brand_anker,
                    "device_model": None,
                    "series": None,
                    "color": color_black,
                    "price": 800,
                    "description": "Кабель USB-C to USB-C 2м"
                },
            ]
            
            for prod_data in products:
                product = Products(
                    category_id=prod_data["category"].id,
                    accessory_brand_id=prod_data["accessory_brand"].id,
                    device_model_id=prod_data["device_model"].id if prod_data["device_model"] else None,
                    series_id=prod_data["series"].id if prod_data["series"] else None,
                    color_id=prod_data["color"].id if prod_data["color"] else None,
                    price=prod_data["price"],
                    description=prod_data["description"],
                    is_active=True
                )
                session.add(product)
            
            print(f"✓ Создано {len(products)} продуктов")
            
            # 8. Создаем статусы заказов
            print("\n8. Создание статусов заказов...")
            await get_or_create(session, OrderStatuses, name="В работе")
            await get_or_create(session, OrderStatuses, name="Выполнен")
            await get_or_create(session, OrderStatuses, name="Отменен")
            print("✓ Статусы заказов созданы")
            
            # Сохраняем все изменения
            await session.commit()
            print("\n" + "="*50)
            print("✅ База данных успешно заполнена тестовыми данными!")
            print("="*50)
            print("\nТеперь вы можете:")
            print("1. Запустить бота: python main.py")
            print("2. Запустить админ-панель: python admin/app.py")
            print("3. Добавить изображения через админ-панель")
            
        except Exception as e:
            print(f"\n❌ Ошибка при заполнении базы: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    print("Скрипт заполнения базы данных тестовыми данными")
    print("=" * 50)
    asyncio.run(seed_database())

