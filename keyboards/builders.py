import asyncio
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from sqlalchemy import select, func, desc
from data.model import (
    AsyncSessionLocal,
    Categories,
    AccessoryBrands,
    DeviceBrands,
    DeviceModels,
    Series,
    Colors,
    Products
)
from keyboards.inline import main_menu_button, back_button

MAX_PAGE_SIZE = 6

# =============================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================

def count_pages(count, page_size, page):
    """Подсчет страниц для пагинации"""
    total_pages = (count + page_size - 1) // page_size
    page = page % total_pages if total_pages > 0 else 0
    return page, total_pages

def make_pagination_buttons(prefix: str, items: list, total_pages: int, page: int) -> list:
    """
    Создание кнопок пагинации
    :param prefix: префикс для callback_data (например, 'pg_category')
    :param items: список данных для callback_data
    :param total_pages: общее количество страниц
    :param page: текущая страница
    :return: список кнопок
    """
    if items:
        callback_data_string = "_" + "_".join(str(item) for item in items)
    else:
        callback_data_string = ""

    pagination_buttons = []
    if total_pages > 1:
        prev_page = (page - 1) if page > 0 else total_pages - 1
        next_page = (page + 1) % total_pages

        pagination_buttons.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"{prefix}_prev{callback_data_string}_{prev_page}"
            )
        )
        pagination_buttons.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"{prefix}_next{callback_data_string}_{next_page}"
            )
        )
    return pagination_buttons

# =============================
# КЛАВИАТУРЫ ДЛЯ ВЫБОРА
# =============================

async def categories_kb(page=0, page_size: int = MAX_PAGE_SIZE):
    """Клавиатура выбора категории"""
    async with AsyncSessionLocal() as session:
        result_count = await session.execute(select(func.count()).select_from(Categories))
        categories_count = result_count.scalar_one()
        page, total_pages = count_pages(categories_count, page_size, page)
        
        result = await session.execute(
            select(Categories)
            .offset(page * page_size)
            .limit(page_size)
            .order_by(Categories.name)
        )
        categories = result.scalars().all()

    builder = InlineKeyboardBuilder()
    [builder.button(text=category.name, callback_data=f"category_{category.id}") for category in categories]
    builder.adjust(2)

    pg_buttons = make_pagination_buttons("pg_category", [], total_pages, page)
    builder.row(*pg_buttons)

    builder.row(back_button())
    builder.row(main_menu_button())
    return builder.as_markup()

async def accessory_brands_kb(category_id: int = None, page=0, page_size: int = MAX_PAGE_SIZE):
    """Клавиатура выбора бренда аксессуара"""
    if not category_id:
        # Если нет категории, возвращаем пустую клавиатуру с кнопкой назад
        builder = InlineKeyboardBuilder()
        builder.row(back_button())
        builder.row(main_menu_button())
        return builder.as_markup()
    
    async with AsyncSessionLocal() as session:
        # Получаем уникальные бренды аксессуаров для выбранной категории
        stmt = (
            select(AccessoryBrands)
            .join(Products, Products.accessory_brand_id == AccessoryBrands.id)
            .where(
                Products.category_id == category_id,
                Products.is_active == True
            )
            .distinct()
            .order_by(AccessoryBrands.name)
        )
        
        brands_count = await session.execute(
            select(func.count(func.distinct(AccessoryBrands.id)))
            .select_from(AccessoryBrands)
            .join(Products, Products.accessory_brand_id == AccessoryBrands.id)
            .where(
                Products.category_id == category_id,
                Products.is_active == True
            )
        )
        brands_count = brands_count.scalar_one()
        page, total_pages = count_pages(brands_count, page_size, page)
        
        result = await session.execute(stmt.offset(page * page_size).limit(page_size))
        brands = result.scalars().all()

    builder = InlineKeyboardBuilder()
    for brand in brands:
        builder.button(text=brand.name, callback_data=f"accessory_brand_{brand.id}")
    builder.adjust(2)

    pg_buttons = make_pagination_buttons("pg_accessory_brand", [category_id], total_pages, page)
    builder.row(*pg_buttons)

    builder.row(back_button())
    builder.row(main_menu_button())
    return builder.as_markup()

async def device_brands_kb(category_id: int, accessory_brand_id: int, page=0, page_size: int = MAX_PAGE_SIZE):
    """Клавиатура выбора бренда устройства"""
    async with AsyncSessionLocal() as session:
        stmt = (
            select(DeviceBrands)
            .join(DeviceModels, DeviceModels.device_brand_id == DeviceBrands.id)
            .join(Products, Products.device_model_id == DeviceModels.id)
            .where(
                Products.category_id == category_id,
                Products.accessory_brand_id == accessory_brand_id,
                Products.is_active == True
            )
            .distinct()
            .order_by(DeviceBrands.name)
        )
        
        brands_count = await session.execute(
            select(func.count(func.distinct(DeviceBrands.id)))
            .select_from(DeviceBrands)
            .join(DeviceModels, DeviceModels.device_brand_id == DeviceBrands.id)
            .join(Products, Products.device_model_id == DeviceModels.id)
            .where(
                Products.category_id == category_id,
                Products.accessory_brand_id == accessory_brand_id,
                Products.is_active == True
            )
        )
        brands_count = brands_count.scalar_one()
        page, total_pages = count_pages(brands_count, page_size, page)
        
        result = await session.execute(stmt.offset(page * page_size).limit(page_size))
        device_brands = result.scalars().all()

    builder = InlineKeyboardBuilder()
    for brand in device_brands:
        builder.button(text=brand.name, callback_data=f"device_brand_{brand.id}")
    builder.adjust(2)

    pg_buttons = make_pagination_buttons("pg_device_brand", [category_id, accessory_brand_id], total_pages, page)
    builder.row(*pg_buttons)

    builder.row(back_button())
    builder.row(main_menu_button())
    return builder.as_markup()

async def device_models_kb(
    category_id: int,
    accessory_brand_id: int,
    device_brand_id: int = None,
    page=0,
    page_size: int = MAX_PAGE_SIZE
):
    """Клавиатура выбора модели устройства"""
    async with AsyncSessionLocal() as session:
        stmt = (
            select(DeviceModels)
            .join(Products, Products.device_model_id == DeviceModels.id)
            .where(
                Products.category_id == category_id,
                Products.accessory_brand_id == accessory_brand_id,
                Products.is_active == True
            )
        )
        
        if device_brand_id:
            stmt = stmt.where(DeviceModels.device_brand_id == device_brand_id)
        
        stmt = stmt.distinct().order_by(DeviceModels.name)
        
        models_count = await session.execute(
            select(func.count(func.distinct(DeviceModels.id)))
            .select_from(DeviceModels)
            .join(Products, Products.device_model_id == DeviceModels.id)
            .where(
                Products.category_id == category_id,
                Products.accessory_brand_id == accessory_brand_id,
                Products.is_active == True
            )
        )
        models_count = models_count.scalar_one()
        page, total_pages = count_pages(models_count, page_size, page)
        
        result = await session.execute(stmt.offset(page * page_size).limit(page_size))
        models = result.scalars().all()

    builder = InlineKeyboardBuilder()
    for model in models:
        # Загружаем связь с брендом
        builder.button(text=model.name, callback_data=f"device_model_{model.id}")
    builder.adjust(2)

    params = [category_id, accessory_brand_id]
    if device_brand_id:
        params.append(device_brand_id)
    pg_buttons = make_pagination_buttons("pg_device_model", params, total_pages, page)
    builder.row(*pg_buttons)

    builder.row(back_button())
    builder.row(main_menu_button())
    return builder.as_markup()

async def series_kb(
    category_id: int,
    accessory_brand_id: int,
    device_model_id: int = None,
    page=0,
    page_size: int = MAX_PAGE_SIZE
):
    """Клавиатура выбора серии"""
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Series)
            .join(Products, Products.series_id == Series.id)
            .where(
                Products.category_id == category_id,
                Products.accessory_brand_id == accessory_brand_id,
                Products.is_active == True
            )
        )
        
        if device_model_id:
            stmt = stmt.where(Products.device_model_id == device_model_id)
        
        stmt = stmt.distinct().order_by(Series.name)
        
        series_count = await session.execute(
            select(func.count(func.distinct(Series.id)))
            .select_from(Series)
            .join(Products, Products.series_id == Series.id)
            .where(
                Products.category_id == category_id,
                Products.accessory_brand_id == accessory_brand_id,
                Products.is_active == True
            )
        )
        series_count = series_count.scalar_one()
        page, total_pages = count_pages(series_count, page_size, page)
        
        result = await session.execute(stmt.offset(page * page_size).limit(page_size))
        series_list = result.scalars().all()

    builder = InlineKeyboardBuilder()
    for s in series_list:
        builder.button(text=s.name, callback_data=f"series_{s.id}")
    builder.adjust(2)

    params = [category_id, accessory_brand_id]
    if device_model_id:
        params.append(device_model_id)
    pg_buttons = make_pagination_buttons("pg_series", params, total_pages, page)
    builder.row(*pg_buttons)

    builder.row(back_button())
    builder.row(main_menu_button())
    return builder.as_markup()

async def colors_kb(
    category_id: int,
    accessory_brand_id: int,
    device_model_id: int = None,
    series_id: int = None,
    page=0,
    page_size: int = MAX_PAGE_SIZE
):
    """Клавиатура выбора цвета"""
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Colors)
            .join(Products, Products.color_id == Colors.id)
            .where(
                Products.category_id == category_id,
                Products.accessory_brand_id == accessory_brand_id,
                Products.is_active == True
            )
        )
        
        if device_model_id:
            stmt = stmt.where(Products.device_model_id == device_model_id)
        if series_id:
            stmt = stmt.where(Products.series_id == series_id)
        
        stmt = stmt.distinct().order_by(Colors.name)
        
        colors_count = await session.execute(
            select(func.count(func.distinct(Colors.id)))
            .select_from(Colors)
            .join(Products, Products.color_id == Colors.id)
            .where(
                Products.category_id == category_id,
                Products.accessory_brand_id == accessory_brand_id,
                Products.is_active == True
            )
        )
        colors_count = colors_count.scalar_one()
        page, total_pages = count_pages(colors_count, page_size, page)
        
        result = await session.execute(stmt.offset(page * page_size).limit(page_size))
        colors = result.scalars().all()

    builder = InlineKeyboardBuilder()
    for color in colors:
        builder.button(text=color.name, callback_data=f"color_{color.id}")
    builder.adjust(2)

    params = [category_id, accessory_brand_id]
    if device_model_id:
        params.append(device_model_id)
    if series_id:
        params.append(series_id)
    pg_buttons = make_pagination_buttons("pg_color", params, total_pages, page)
    builder.row(*pg_buttons)

    builder.row(back_button())
    builder.row(main_menu_button())
    return builder.as_markup()

async def products_kb(
    category_id: int,
    accessory_brand_id: int,
    device_model_id: int = None,
    series_id: int = None,
    color_id: int = None,
    page=0,
    page_size: int = MAX_PAGE_SIZE
):
    """Клавиатура выбора конкретного продукта"""
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Products)
            .where(
                Products.category_id == category_id,
                Products.accessory_brand_id == accessory_brand_id,
                Products.is_active == True
            )
        )
        
        if device_model_id:
            stmt = stmt.where(Products.device_model_id == device_model_id)
        if series_id:
            stmt = stmt.where(Products.series_id == series_id)
        if color_id:
            stmt = stmt.where(Products.color_id == color_id)
        
        products_count = await session.execute(
            select(func.count(Products.id))
            .where(
                Products.category_id == category_id,
                Products.accessory_brand_id == accessory_brand_id,
                Products.is_active == True
            )
        )
        products_count = products_count.scalar_one()
        page, total_pages = count_pages(products_count, page_size, page)
        
        result = await session.execute(
            stmt.offset(page * page_size).limit(page_size).order_by(Products.id)
        )
        products = result.scalars().all()

    builder = InlineKeyboardBuilder()
    for product in products:
        # Создаем текст кнопки с ценой
        text = f"{product.price} руб" if product.price else "Цену уточнять"
        if product.variation:
            text = f"{product.variation} - {text}"
        builder.button(text=text, callback_data=f"product_{product.id}")
    builder.adjust(1)

    params = [category_id, accessory_brand_id]
    if device_model_id:
        params.append(device_model_id)
    if series_id:
        params.append(series_id)
    if color_id:
        params.append(color_id)
    pg_buttons = make_pagination_buttons("pg_product", params, total_pages, page)
    builder.row(*pg_buttons)

    builder.row(back_button())
    builder.row(main_menu_button())
    return builder.as_markup()

def product_kb():
    """Клавиатура для карточки продукта (переход к выбору количества)"""
    from keyboards.inline import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Выбрать количество", callback_data="select_quantity")],
            [back_button()],
            [main_menu_button()]
        ]
    )

def quantity_kb():
    """Клавиатура выбора количества (кейпад 1-9)"""
    from keyboards.inline import InlineKeyboardMarkup, InlineKeyboardButton
    
    buttons = []
    # Создаем кейпад 1-9
    for row in range(3):
        row_buttons = []
        for col in range(3):
            num = row * 3 + col + 1
            row_buttons.append(
                InlineKeyboardButton(text=str(num), callback_data=f"qty_{num}")
            )
        buttons.append(row_buttons)
    
    # Добавляем кнопки управления
    buttons.append([
        InlineKeyboardButton(text="⬅️ Стереть", callback_data="qty_backspace"),
        InlineKeyboardButton(text="0", callback_data="qty_0"),
        InlineKeyboardButton(text="✅ Добавить", callback_data="qty_confirm")
    ])
    buttons.append([back_button(), main_menu_button()])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
