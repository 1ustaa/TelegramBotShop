from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from keyboards import builders
from sqlalchemy import select, func
from data.model import (
    AsyncSessionLocal,
    Categories,
    AccessoryBrands,
    DeviceModels,
    DeviceBrands,
    Series,
    Colors,
    Products
)

class ChoseProduct(StatesGroup):
    """Состояния для выбора аксессуара"""
    showing_categories = State()
    showing_accessory_brands = State()
    showing_device_brands = State()
    showing_device_models = State()
    showing_series = State()
    showing_colors = State()
    showing_products = State()
    showing_product = State()
    selecting_quantity = State()

# Определяем последовательность состояний для динамического пропуска
STATE_SEQUENCE = [
    ChoseProduct.showing_categories,
    ChoseProduct.showing_accessory_brands,
    ChoseProduct.showing_device_brands,
    ChoseProduct.showing_device_models,
    ChoseProduct.showing_series,
    ChoseProduct.showing_colors,
    ChoseProduct.showing_products,
]

# Определяем какие данные нужны для каждого состояния
STATE_DATA_REQUIREMENTS = {
    ChoseProduct.showing_categories: [],
    ChoseProduct.showing_accessory_brands: ["chosen_category"],
    ChoseProduct.showing_device_brands: ["chosen_category", "chosen_accessory_brand"],
    ChoseProduct.showing_device_models: ["chosen_category", "chosen_accessory_brand", "chosen_device_brand"],
    ChoseProduct.showing_series: ["chosen_category", "chosen_accessory_brand"],
    ChoseProduct.showing_colors: ["chosen_category", "chosen_accessory_brand"],
    ChoseProduct.showing_products: ["chosen_category", "chosen_accessory_brand"],
}

async def should_show_state(state, data: dict) -> bool:
    """
    Проверяет, нужно ли показывать данное состояние пользователю.
    Возвращает True, если есть варианты для выбора, иначе False.
    
    ВАЖНО: Категория и бренд аксессуара - обязательные этапы (всегда True)
    Остальные этапы - опциональные (проверяем наличие данных в БД)
    """
    async with AsyncSessionLocal() as session:
        if state == ChoseProduct.showing_categories:
            # Всегда показываем категории (обязательный этап)
            return True
        
        elif state == ChoseProduct.showing_accessory_brands:
            # Всегда показываем бренды аксессуаров (обязательный этап)
            # Это обязательное поле в модели Products
            category_id = data.get("chosen_category")
            if not category_id:
                return False
            return True
        
        elif state == ChoseProduct.showing_device_brands:
            # Проверяем наличие брендов устройств
            category_id = data.get("chosen_category")
            accessory_brand_id = data.get("chosen_accessory_brand")
            if not category_id or not accessory_brand_id:
                return False
            
            stmt = (
                select(func.count(func.distinct(DeviceModels.device_brand_id)))
                .join(Products, Products.device_model_id == DeviceModels.id)
                .where(
                    Products.category_id == category_id,
                    Products.accessory_brand_id == accessory_brand_id,
                    Products.is_active == True,
                    DeviceModels.device_brand_id.isnot(None)
                )
            )
            result = await session.execute(stmt)
            return result.scalar() > 0
        
        elif state == ChoseProduct.showing_device_models:
            # Проверяем наличие моделей устройств
            category_id = data.get("chosen_category")
            accessory_brand_id = data.get("chosen_accessory_brand")
            device_brand_id = data.get("chosen_device_brand")
            if not category_id or not accessory_brand_id:
                return False
            
            stmt = (
                select(func.count(func.distinct(Products.device_model_id)))
                .where(
                    Products.category_id == category_id,
                    Products.accessory_brand_id == accessory_brand_id,
                    Products.is_active == True,
                    Products.device_model_id.isnot(None)
                )
            )
            if device_brand_id:
                stmt = stmt.join(DeviceModels, Products.device_model_id == DeviceModels.id).where(
                    DeviceModels.device_brand_id == device_brand_id
                )
            result = await session.execute(stmt)
            return result.scalar() > 0
        
        elif state == ChoseProduct.showing_series:
            # Проверяем наличие серий
            category_id = data.get("chosen_category")
            accessory_brand_id = data.get("chosen_accessory_brand")
            device_model_id = data.get("chosen_device_model")
            if not category_id or not accessory_brand_id:
                return False
            
            stmt = (
                select(func.count(func.distinct(Products.series_id)))
                .where(
                    Products.category_id == category_id,
                    Products.accessory_brand_id == accessory_brand_id,
                    Products.is_active == True,
                    Products.series_id.isnot(None)
                )
            )
            if device_model_id:
                stmt = stmt.where(Products.device_model_id == device_model_id)
            result = await session.execute(stmt)
            return result.scalar() > 0
        
        elif state == ChoseProduct.showing_colors:
            # Проверяем наличие цветов
            category_id = data.get("chosen_category")
            accessory_brand_id = data.get("chosen_accessory_brand")
            device_model_id = data.get("chosen_device_model")
            series_id = data.get("chosen_series")
            if not category_id or not accessory_brand_id:
                return False
            
            stmt = (
                select(func.count(func.distinct(Products.color_id)))
                .where(
                    Products.category_id == category_id,
                    Products.accessory_brand_id == accessory_brand_id,
                    Products.is_active == True,
                    Products.color_id.isnot(None)
                )
            )
            if device_model_id:
                stmt = stmt.where(Products.device_model_id == device_model_id)
            if series_id:
                stmt = stmt.where(Products.series_id == series_id)
            result = await session.execute(stmt)
            return result.scalar() > 0
        
        elif state == ChoseProduct.showing_products:
            # Всегда показываем список продуктов, если дошли до этого этапа
            return True
        
        return False

async def get_next_state(current_state, data: dict):
    """
    Определяет следующее состояние с учетом динамического пропуска этапов.
    Возвращает следующее состояние или None, если все этапы пройдены.
    """
    try:
        # Ищем индекс текущего состояния
        current_index = -1
        for i, state in enumerate(STATE_SEQUENCE):
            if state == current_state:
                current_index = i
                break
        
        if current_index == -1:
            # Если состояние не найдено, начинаем с первого
            current_index = -1
    except Exception as e:
        print(f"Ошибка определения индекса состояния: {e}")
        current_index = -1
    
    # Перебираем следующие состояния
    for i in range(current_index + 1, len(STATE_SEQUENCE)):
        next_state = STATE_SEQUENCE[i]
        should_show = await should_show_state(next_state, data)
        
        if should_show:
            return next_state
    
    # Если дошли до конца, переходим к списку продуктов
    return ChoseProduct.showing_products

state_handlers = {
    ChoseProduct.showing_categories: {
        "markup": lambda data: builders.categories_kb(),
        "text": "Выберите категорию аксессуара"
    },
    ChoseProduct.showing_accessory_brands: {
        "markup": lambda data: builders.accessory_brands_kb(data["chosen_category"]),
        "text": "Выберите бренд аксессуара"
    },
    ChoseProduct.showing_device_brands: {
        "markup": lambda data: builders.device_brands_kb(
            data.get("chosen_category"),
            data.get("chosen_accessory_brand")
        ),
        "text": "Выберите бренд устройства"
    },
    ChoseProduct.showing_device_models: {
        "markup": lambda data: builders.device_models_kb(
            data.get("chosen_category"),
            data.get("chosen_accessory_brand"),
            data.get("chosen_device_brand")
        ),
        "text": "Выберите модель устройства"
    },
    ChoseProduct.showing_series: {
        "markup": lambda data: builders.series_kb(
            data.get("chosen_category"),
            data.get("chosen_accessory_brand"),
            data.get("chosen_device_model")
        ),
        "text": "Выберите серию"
    },
    ChoseProduct.showing_colors: {
        "markup": lambda data: builders.colors_kb(
            data.get("chosen_category"),
            data.get("chosen_accessory_brand"),
            data.get("chosen_device_model"),
            data.get("chosen_series")
        ),
        "text": "Выберите цвет"
    },
    ChoseProduct.showing_products: {
        "markup": lambda data: builders.products_kb(
            data.get("chosen_category"),
            data.get("chosen_accessory_brand"),
            data.get("chosen_device_model"),
            data.get("chosen_series"),
            data.get("chosen_color")
        ),
        "text": "Выберите товар"
    },
    ChoseProduct.showing_product: {
        "markup": lambda data: builders.product_kb(),
        "text": "Выберите количество"
    },
    ChoseProduct.selecting_quantity: {
        "markup": lambda data: builders.quantity_kb(),
        "text": "Выберите количество товара"
    }
}

async def push_state(state: FSMContext, new_state, clear_history=False, max_size=10):
    """Добавить новое состояние в историю"""
    if clear_history:
        await state.update_data(state_history=[])
        await state.clear()
    else:
        data = await state.get_data()
        history = data.get("state_history", [])
        current_state = await state.get_state()
        if current_state:
            history.append(current_state)
        if len(history) > max_size:
            history.pop(0)
        await state.update_data(state_history=history)
    await state.set_state(new_state)

async def pop_state(state: FSMContext):
    """Вернуться к предыдущему состоянию"""
    data = await state.get_data()
    history = data.get("state_history", [])
    if history:
        prev_state = history.pop()
        await state.update_data(state_history=history)
        await state.set_state(prev_state)
        return prev_state
    else:
        print("История пуста, сбрасываем состояние.")
        await state.clear()
        return None
