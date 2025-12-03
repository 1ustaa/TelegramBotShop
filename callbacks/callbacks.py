import os.path
import inspect

from aiogram import F, types, Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile, InputMediaPhoto

import keyboards
from states.states import ChoseProduct, push_state, pop_state, state_handlers, get_next_state
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from data.crud import (
    get_product_by_id,
    get_product_image,
    get_product_full_info,
    add_new_customer,
    add_cart_item,
    get_cart_items,
    count_cart_sum,
    clear_user_cart,
    make_order,
    get_admins,
    get_order_details
)

router = Router()

# =============================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================

async def safe_edit_message(callback: types.CallbackQuery, text: str = None, reply_markup=None, media=None):
    """Безопасное редактирование сообщения"""
    # Если reply_markup - это корутина, await'им её
    if reply_markup and hasattr(reply_markup, '__await__'):
        reply_markup = await reply_markup
    
    try:
        if media:
            await callback.message.edit_media(
                media=InputMediaPhoto(
                    media=media,
                    caption=text
                ),
                reply_markup=reply_markup
            )
        else:
            await callback.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return
        elif "there is no text in the message to edit" in str(e):
            # Сообщение содержит медиа, пытаемся удалить и отправить новое текстовое
            try:
                await callback.message.delete()
            except Exception:
                # Не удалось удалить (возможно, старое сообщение) - просто отправим новое
                pass
            try:
                await callback.message.answer(text, reply_markup=reply_markup)
            except Exception as e2:
                print(f"Ошибка отправки сообщения: {e2}")
        else:
            # Другая ошибка - также пытаемся удалить и отправить новое
            try:
                await callback.message.delete()
            except Exception:
                # Не удалось удалить (возможно, старое сообщение) - просто отправим новое
                pass
            try:
                await callback.message.answer(text, reply_markup=reply_markup)
            except Exception as e2:
                print(f"Ошибка отправки сообщения: {e2}")

async def transition_to_next_state(callback: types.CallbackQuery, state: FSMContext):
    """Переход к следующему состоянию с учетом динамического пропуска"""
    current_state = await state.get_state()
    data = await state.get_data()
    
    next_state = await get_next_state(current_state, data)
    
    if next_state:
        # Специальная обработка для состояния showing_products
        # Если товар один - сразу показываем карточку, пропуская состояние showing_products
        if next_state == ChoseProduct.showing_products:
            from data.model import AsyncSessionLocal, Products
            from sqlalchemy import select, func
            
            async with AsyncSessionLocal() as session:
                stmt = (
                    select(Products)
                    .where(
                        Products.category_id == data["chosen_category"],
                        Products.accessory_brand_id == data["chosen_accessory_brand"],
                        Products.is_active == True
                    )
                )
                
                if data.get("chosen_device_model"):
                    stmt = stmt.where(Products.device_model_id == data["chosen_device_model"])
                if data.get("chosen_series"):
                    stmt = stmt.where(Products.series_id == data["chosen_series"])
                if data.get("chosen_variation"):
                    stmt = stmt.where(Products.variation_id == data["chosen_variation"])
                if data.get("chosen_color"):
                    stmt = stmt.where(Products.color_id == data["chosen_color"])
                
                result = await session.execute(stmt)
                products = result.scalars().all()
                
                # Если товар ровно один - сразу показываем карточку, пропускаем showing_products
                if len(products) == 1:
                    product = products[0]
                    await state.update_data(chosen_product=product.id)
                    
                    product_info = await get_product_full_info(product.id)
                    if product_info:
                        # Формируем текст карточки
                        text_parts = ["<b>Информация о товаре:</b>\n"]
                        if product_info["category"]:
                            text_parts.append(f"Категория: {product_info['category']}")
                        if product_info["accessory_brand"]:
                            text_parts.append(f"Бренд: {product_info['accessory_brand']}")
                        if product_info["device_model"]:
                            text_parts.append(f"Совместимость: {product_info['device_model']}")
                        if product_info["series"]:
                            text_parts.append(f"Серия: {product_info['series']}")
                        if product_info["variation"]:
                            text_parts.append(f"Вариация: {product_info['variation']}")
                        if product_info["color"]:
                            text_parts.append(f"Цвет: {product_info['color']}")
                        if product_info["price"]:
                            text_parts.append(f"\n<b>Цена: {product_info['price']} руб</b>")
                        else:
                            text_parts.append("\n<b>Цену уточнять</b>")
                        
                        text = "\n".join(text_parts)
                        
                        # Получаем изображение
                        image_path = await get_product_image(product.id, product_info.get("color_id"))
                        
                        if image_path and os.path.exists(image_path):
                            await state.update_data(image_path=image_path)
                            photo = FSInputFile(image_path)
                            await callback.message.edit_media(
                                media=InputMediaPhoto(media=photo, caption=text),
                                reply_markup=keyboards.builders.product_kb()
                            )
                        else:
                            await callback.message.edit_text(
                                text,
                                reply_markup=keyboards.builders.product_kb()
                            )
                        
                        # Переходим сразу к showing_product, минуя showing_products
                        await push_state(state, ChoseProduct.showing_product)
                        return
        
        # Обычный переход к следующему состоянию
        await push_state(state, next_state)
        
        handler = state_handlers.get(next_state)
        
        if handler:
            # Получаем markup - может быть async функцией, обычной функцией или объектом
            markup_source = handler["markup"]
            
            # Проверяем, является ли это асинхронной функцией
            if inspect.iscoroutinefunction(markup_source):
                markup = await markup_source(data)
            # Проверяем, является ли это обычной функцией
            elif callable(markup_source):
                markup = markup_source(data)
                # Если результат - корутина, нужно ее await-нуть
                if inspect.iscoroutine(markup):
                    markup = await markup
            # Иначе это уже готовый объект клавиатуры
            else:
                markup = markup_source
            
            text = handler["text"]
            
            try:
                # Теперь markup - это уже готовая клавиатура, а не корутина
                await callback.message.edit_text(text, reply_markup=markup)
            except TelegramBadRequest as e:
                # Если сообщение содержит медиа, пытаемся удалить его и отправляем новое текстовое
                if "there is no text in the message to edit" in str(e):
                    try:
                        await callback.message.delete()
                    except Exception:
                        # Не удалось удалить (возможно, старое сообщение) - просто отправим новое
                        pass
                    try:
                        await callback.message.answer(text, reply_markup=markup)
                    except Exception as e2:
                        print(f"Ошибка при отправке сообщения: {e2}")
                elif "message is not modified" not in str(e):
                    print(f"Ошибка перехода к следующему состоянию: {e}")
            except Exception as e:
                print(f"Ошибка перехода к следующему состоянию: {e}")
    else:
        await callback.answer("Завершено")

# =============================
# CALLBACK HANDLERS
# =============================

# Категории
@router.callback_query(F.data == "categories")
async def process_category_selection(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите категорию аксессуара", reply_markup=await keyboards.builders.categories_kb()
    )
    await push_state(state, ChoseProduct.showing_categories)
    await callback.answer()

# Пагинация категорий
@router.callback_query(F.data.startswith("pg_category"))
async def process_category_pagination(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        page = int(data_split[3])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await callback.message.edit_text(
        "Выберите категорию аксессуара", reply_markup=await keyboards.builders.categories_kb(page)
    )
    await callback.answer()

# Выбор бренда категории
@router.callback_query(
    F.data.startswith("category_"),
    ChoseProduct.showing_categories
)
async def process_accessory_brand_selection(callback: types.CallbackQuery, state: FSMContext):
    try:
        category_id = int(callback.data.split("_")[1])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return
    
    await state.update_data(chosen_category=category_id)
    await transition_to_next_state(callback, state)
    await callback.answer()

# Пагинация брендов аксессуаров
@router.callback_query(
    F.data.startswith("pg_accessory_brand"),
    ChoseProduct.showing_accessory_brands
)
async def process_accessory_brand_pagination(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        category_id = int(data_split[4])
        page = int(data_split[5])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await callback.message.edit_text(
        "Выберите бренд аксессуара", reply_markup=await keyboards.builders.accessory_brands_kb(category_id, page)
    )
    await callback.answer()

# Выбор бренда аксессуара
@router.callback_query(
    F.data.startswith("accessory_brand_"),
    ChoseProduct.showing_accessory_brands
)
async def process_device_brand_selection(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        accessory_brand_id = int(data_split[2])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await state.update_data(chosen_accessory_brand=accessory_brand_id)
    await transition_to_next_state(callback, state)
    await callback.answer()

# Пагинация брендов устройств
@router.callback_query(
    F.data.startswith("pg_device_brand"),
    ChoseProduct.showing_device_brands
)
async def process_device_brand_pagination(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        category_id = int(data_split[4])
        accessory_brand_id = int(data_split[5])
        page = int(data_split[6])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await callback.message.edit_text(
        "Выберите бренд устройства",
        reply_markup=await keyboards.builders.device_brands_kb(category_id, accessory_brand_id, page)
    )
    await callback.answer()

# Выбор бренда устройства
@router.callback_query(
    F.data.startswith("device_brand_"),
    ChoseProduct.showing_device_brands
)
async def process_device_model_selection(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        device_brand_id = int(data_split[2])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await state.update_data(chosen_device_brand=device_brand_id)
    await transition_to_next_state(callback, state)
    await callback.answer()

# Пагинация моделей устройств
@router.callback_query(
    F.data.startswith("pg_device_model"),
    ChoseProduct.showing_device_models
)
async def process_device_model_pagination(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        category_id = int(data_split[4])
        accessory_brand_id = int(data_split[5])
        device_brand_id = int(data_split[6]) if len(data_split) > 7 else None
        page = int(data_split[7] if len(data_split) > 7 else data_split[6])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await callback.message.edit_text(
        "Выберите модель устройства",
        reply_markup=await keyboards.builders.device_models_kb(
            category_id, accessory_brand_id, device_brand_id, page
        )
    )
    await callback.answer()

# Выбор модели устройства
@router.callback_query(
    F.data.startswith("device_model_"),
    ChoseProduct.showing_device_models
)
async def process_series_selection(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        device_model_id = int(data_split[2])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await state.update_data(chosen_device_model=device_model_id)
    await transition_to_next_state(callback, state)
    await callback.answer()

# Пагинация серий
@router.callback_query(
    F.data.startswith("pg_series"),
    ChoseProduct.showing_series
)
async def process_series_pagination(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        category_id = int(data_split[3])
        accessory_brand_id = int(data_split[4])
        device_model_id = int(data_split[5]) if len(data_split) > 6 else None
        page = int(data_split[6] if len(data_split) > 6 else data_split[5])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await callback.message.edit_text(
        "Выберите серию",
        reply_markup=await keyboards.builders.series_kb(category_id, accessory_brand_id, device_model_id, page)
    )
    await callback.answer()

# Выбор серии
@router.callback_query(
    F.data.startswith("series_"),
    ChoseProduct.showing_series
)
async def process_variation_selection(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        series_id = int(data_split[1])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await state.update_data(chosen_series=series_id)
    await transition_to_next_state(callback, state)
    await callback.answer()

# Пагинация вариаций
@router.callback_query(
    F.data.startswith("pg_variation"),
    ChoseProduct.showing_variations
)
async def process_variation_pagination(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        category_id = int(data_split[3])
        accessory_brand_id = int(data_split[4])
        device_model_id = int(data_split[5]) if len(data_split) > 7 else None
        series_id = int(data_split[6]) if len(data_split) > 7 else None
        page = int(data_split[-1])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await callback.message.edit_text(
        "Выберите вариацию",
        reply_markup=await keyboards.builders.variations_kb(
            category_id, accessory_brand_id, device_model_id, series_id, page
        )
    )
    await callback.answer()

# Выбор вариации
@router.callback_query(
    F.data.startswith("variation_"),
    ChoseProduct.showing_variations
)
async def process_color_selection(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        variation_id = int(data_split[1])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await state.update_data(chosen_variation=variation_id)
    await transition_to_next_state(callback, state)
    await callback.answer()

# Пагинация цветов
@router.callback_query(
    F.data.startswith("pg_color"),
    ChoseProduct.showing_colors
)
async def process_color_pagination(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    data = await state.get_data()
    
    try:
        page = int(data_split[-1])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await callback.message.edit_text(
        "Выберите цвет",
        reply_markup=await keyboards.builders.colors_kb(
            data["chosen_category"],
            data["chosen_accessory_brand"],
            data.get("chosen_device_model"),
            data.get("chosen_series"),
            data.get("chosen_variation"),
            page
        )
    )
    await callback.answer()

# Выбор цвета
@router.callback_query(
    F.data.startswith("color_"),
    ChoseProduct.showing_colors
)
async def process_product_selection(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        color_id = int(data_split[1])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await state.update_data(chosen_color=color_id)
    await transition_to_next_state(callback, state)
    await callback.answer()

# Пагинация продуктов (используется только когда товаров больше одного)
@router.callback_query(
    F.data.startswith("pg_product"),
    ChoseProduct.showing_products
)
async def process_product_pagination(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    data = await state.get_data()
    
    try:
        page = int(data_split[-1])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await callback.message.edit_text(
        "Выберите товар",
        reply_markup=await keyboards.builders.products_kb(
            data["chosen_category"],
            data["chosen_accessory_brand"],
            data.get("chosen_device_model"),
            data.get("chosen_series"),
            data.get("chosen_variation"),
            data.get("chosen_color"),
            page
        )
    )
    await callback.answer()

# Выбор продукта - показываем карточку
@router.callback_query(
    F.data.startswith("product_"),
    ChoseProduct.showing_products
)
async def show_product_card(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        product_id = int(data_split[1])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    product_info = await get_product_full_info(product_id)
    if not product_info:
        await callback.answer("Товар не найден")
        return

    await state.update_data(chosen_product=product_id)

    # Формируем текст карточки
    text_parts = ["<b>Информация о товаре:</b>\n"]
    if product_info["category"]:
        text_parts.append(f"Категория: {product_info['category']}")
    if product_info["accessory_brand"]:
        text_parts.append(f"Бренд: {product_info['accessory_brand']}")
    if product_info["device_model"]:
        text_parts.append(f"Совместимость: {product_info['device_model']}")
    if product_info["series"]:
        text_parts.append(f"Серия: {product_info['series']}")
    if product_info["variation"]:
        text_parts.append(f"Вариация: {product_info['variation']}")
    if product_info["color"]:
        text_parts.append(f"Цвет: {product_info['color']}")
    if product_info["price"]:
        text_parts.append(f"\n<b>Цена: {product_info['price']} руб</b>")
    else:
        text_parts.append("\n<b>Цену уточнять</b>")
    
    text = "\n".join(text_parts)

    # Получаем изображение
    image_path = await get_product_image(product_id, product_info.get("color_id"))
    
    if image_path and os.path.exists(image_path):
        await state.update_data(image_path=image_path)
        photo = FSInputFile(image_path)
        await callback.message.edit_media(
            media=InputMediaPhoto(media=photo, caption=text),
            reply_markup=keyboards.builders.product_kb()
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=keyboards.builders.product_kb()
        )

    await push_state(state, ChoseProduct.showing_product)
    await callback.answer()

# Переход к выбору количества
@router.callback_query(
    F.data == "select_quantity",
    ChoseProduct.showing_product
)
async def start_quantity_selection(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(selected_quantity="")
    
    text = "Выберите количество товара:"
    data = await state.get_data()
    image_path = data.get("image_path")
    
    if image_path and os.path.exists(image_path):
        # Если было фото, пытаемся удалить медиа-сообщение и отправить новое текстовое
        try:
            await callback.message.delete()
        except Exception as e:
            # Если не удалось удалить (например, сообщение старше 48 часов)
            print(f"Не удалось удалить сообщение: {e}")
        
        # В любом случае отправляем новое сообщение
        try:
            await callback.message.answer(
                text,
                reply_markup=keyboards.builders.quantity_kb()
            )
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
    else:
        # Если нет фото, просто редактируем текст
        await callback.message.edit_text(
            text,
            reply_markup=keyboards.builders.quantity_kb()
        )
    
    await push_state(state, ChoseProduct.selecting_quantity)
    await callback.answer()

# Обработка выбора количества
@router.callback_query(
    F.data.startswith("qty_"),
    ChoseProduct.selecting_quantity
)
async def process_quantity_selection(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    data = await state.get_data()
    current_qty = data.get("selected_quantity", "")
    
    if action == "confirm":
        # Подтверждение и добавление в корзину
        if not current_qty or int(current_qty) <= 0:
            await callback.answer("Выберите количество товара")
            return
        
        quantity = int(current_qty)
        product_id = data.get("chosen_product")
        
        user_id = callback.from_user.id
        username = callback.from_user.username or "Без имени"
        customer = await add_new_customer(user_id, username)
        await add_cart_item(product_id, customer.telegram_id, quantity)
        
        product_info = await get_product_full_info(product_id)
        text = f"Товар добавлен в корзину!\nКоличество: {quantity} шт."
        
        # Пытаемся удалить предыдущее сообщение
        try:
            await callback.message.delete()
        except Exception:
            # Не удалось удалить (возможно, сообщение старше 48 часов) - ничего страшного
            pass
        
        # В любом случае отправляем новое сообщение
        try:
            await callback.message.answer(
                text,
                reply_markup=keyboards.inline.order_variant_kb
            )
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
        
        await callback.answer()
        
    elif action == "backspace":
        # Стереть последнюю цифру
        new_qty = current_qty[:-1]
        await state.update_data(selected_quantity=new_qty)
        
        display_qty = new_qty if new_qty else "0"
        text = f"Количество: {display_qty}"
        
        # Просто редактируем текст без фото
        try:
            await callback.message.edit_text(
                text,
                reply_markup=keyboards.builders.quantity_kb()
            )
        except TelegramBadRequest as e:
            # Если не удалось отредактировать, пытаемся удалить и отправить новое
            try:
                await callback.message.delete()
            except Exception:
                # Не удалось удалить (возможно, старое сообщение) - просто отправим новое
                pass
            
            try:
                await callback.message.answer(text, reply_markup=keyboards.builders.quantity_kb())
            except Exception as e2:
                print(f"Ошибка при отправке сообщения: {e2}")
        await callback.answer()
        
    else:
        # Добавление цифры
        if len(current_qty) < 3:  # Ограничение 3 цифры (максимум 999)
            new_qty = current_qty + action
            await state.update_data(selected_quantity=new_qty)
            
            text = f"Количество: {new_qty}"
            
            # Просто редактируем текст без фото
            try:
                await callback.message.edit_text(
                    text,
                    reply_markup=keyboards.builders.quantity_kb()
                )
            except TelegramBadRequest as e:
                # Если не удалось отредактировать, пытаемся удалить и отправить новое
                try:
                    await callback.message.delete()
                except Exception:
                    # Не удалось удалить (возможно, старое сообщение) - просто отправим новое
                    pass
                
                try:
                    await callback.message.answer(text, reply_markup=keyboards.builders.quantity_kb())
                except Exception as e2:
                    print(f"Ошибка при отправке сообщения: {e2}")
        await callback.answer()

# =============================
# КОРЗИНА И ЗАКАЗЫ
# =============================

@router.callback_query(F.data == "cart", StateFilter("*"))
async def show_cart(callback: types.CallbackQuery, state: FSMContext):
    cart_items = await get_cart_items(callback.from_user.id)
    cart_sum = await count_cart_sum(callback.from_user.id)

    if cart_items:
        text = "Ваша 🛒:\n\n" + "\n\n".join([
            "".join([
                f"<b>{item.category} </b>" if item.category else "",
                f"<b>{item.brand} </b>" if item.brand else "",
                f"<b>{item.device_model} </b>" if item.device_model else "",
                f"<b>{item.series} </b>" if item.series else "",
                f"<b>{item.color} </b>" if item.color else "",
                f"<b>{item.variation} </b>" if item.variation else "",
                "- ",
                f"{item.quantity} шт. " if item.quantity else "",
                f"сумма: {item.sum} руб " if item.sum else "цену уточнять",
            ]).strip() for item in cart_items
        ]) + f"\n\n<b>Общая сумма: {cart_sum} руб</b>"
    else:
        text = "Ваша 🛒:\n\nВ вашей корзине пока что нет товаров"

    await safe_edit_message(callback, text, keyboards.inline.kart_kb)
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "drop_kart")
async def clear_user_cart_items(callback: types.CallbackQuery):
    await clear_user_cart(callback.from_user.id)
    text = "Ваша корзина очищена"
    await callback.message.edit_text(text, reply_markup=keyboards.inline.kart_kb)
    await callback.answer()

@router.callback_query(F.data == "make_order")
async def send_order(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    username = callback.from_user.username
    date = callback.message.date
    order = await make_order(user_id, date)
    
    if order:
        admins, text = await make_message(order.id, username)
        for admin in admins:
            await bot.send_message(admin.id, text)
        text = "Ваш заказ отправлен менеджеру. В ближайшее время с вами свяжутся"
    else:
        text = "Ваша корзина пуста, для создания заказа необходимо добавить товар в корзину"
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboards.inline.kart_kb)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise
    await callback.answer()

async def make_message(order_id, username):
    admins = await get_admins()
    order_items = await get_order_details(order_id)
    text = (
        f"Заказ № {order_id} от пользователя @{username}:\n\n" + "\n\n".join([
            "".join([
                f"<b>{item.category} </b>" if item.category else "",
                f"<b>{item.brand} </b>" if item.brand else "",
                f"<b>{item.device_model} </b>" if item.device_model else "",
                f"<b>{item.series} </b>" if item.series else "",
                f"<b>{item.color} </b>" if item.color else "",
                f"<b>{item.variation} </b>" if item.variation else "",
                "- ",
                f"{item.quantity} шт. " if item.quantity else "",
                f"сумма: {item.sum} руб " if item.sum else "" + "\n"
            ]).strip() for item in order_items
        ])
    )
    return admins, text

# =============================
# НАВИГАЦИЯ
# =============================

@router.callback_query(F.data == "main_menu", StateFilter("*"))
async def return_main_menu(callback: types.CallbackQuery, state: FSMContext):
    text = "🏠 Главное меню."
    await safe_edit_message(callback, text, keyboards.inline.menu_kb)
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "go_back", StateFilter("*"))
async def go_back(callback: types.CallbackQuery, state: FSMContext):
    prev_state = await pop_state(state)

    if prev_state is None:
        await safe_edit_message(
            callback, "🏠 Главное меню.", keyboards.inline.menu_kb
        )
        # Очищаем image_path при возврате в главное меню
        await state.update_data(image_path=None)
        return

    data = await state.get_data()
    
    # Очищаем image_path, если возвращаемся не в showing_product
    if prev_state != ChoseProduct.showing_product:
        await state.update_data(image_path=None)
    
    # Специальная обработка для состояния showing_product
    if prev_state == ChoseProduct.showing_product:
        product_id = data.get("chosen_product")
        if product_id:
            product_info = await get_product_full_info(product_id)
            if product_info:
                # Формируем текст карточки
                text_parts = ["<b>Информация о товаре:</b>\n"]
                if product_info["category"]:
                    text_parts.append(f"Категория: {product_info['category']}")
                if product_info["accessory_brand"]:
                    text_parts.append(f"Бренд: {product_info['accessory_brand']}")
                if product_info["device_model"]:
                    text_parts.append(f"Совместимость: {product_info['device_model']}")
                if product_info["series"]:
                    text_parts.append(f"Серия: {product_info['series']}")
                if product_info["variation"]:
                    text_parts.append(f"Вариация: {product_info['variation']}")
                if product_info["color"]:
                    text_parts.append(f"Цвет: {product_info['color']}")
                if product_info["price"]:
                    text_parts.append(f"\n<b>Цена: {product_info['price']} руб</b>")
                else:
                    text_parts.append("\n<b>Цену уточнять</b>")
                
                text = "\n".join(text_parts)
                
                # Получаем изображение
                image_path = data.get("image_path")
                if image_path and os.path.exists(image_path):
                    photo = FSInputFile(image_path)
                    try:
                        await callback.message.edit_media(
                            media=InputMediaPhoto(media=photo, caption=text),
                            reply_markup=keyboards.builders.product_kb()
                        )
                    except TelegramBadRequest as e:
                        if "message is not modified" not in str(e):
                            raise
                else:
                    try:
                        await callback.message.edit_text(
                            text,
                            reply_markup=keyboards.builders.product_kb()
                        )
                    except TelegramBadRequest as e:
                        if "message is not modified" not in str(e):
                            raise
                
                await callback.answer()
                return

    handler = state_handlers.get(prev_state)

    if handler:
        try:
            # Получаем markup - может быть async функцией, обычной функцией или объектом
            markup_source = handler["markup"]
            
            # Проверяем, является ли это асинхронной функцией
            if inspect.iscoroutinefunction(markup_source):
                markup = await markup_source(data)
            # Проверяем, является ли это обычной функцией
            elif callable(markup_source):
                markup = markup_source(data)
                # Если результат - корутина, нужно ее await-нуть
                if inspect.iscoroutine(markup):
                    markup = await markup
            # Иначе это уже готовый объект клавиатуры
            else:
                markup = markup_source
            
            text = handler["text"]
            media = None
            if "media" in handler.keys():
                media_path = handler["media"](data)
                if media_path and os.path.exists(media_path):
                    media = FSInputFile(media_path)
            
            try:
                await safe_edit_message(callback, text, markup, media)
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    pass
                else:
                    raise
        except Exception as e:
            print(f"Ошибка возврата назад: {e}")
            await safe_edit_message(
                callback,
                "Ошибка при возврате назад. Попробуйте снова.",
                reply_markup=keyboards.inline.menu_kb
            )
    else:
        await safe_edit_message(
            callback,
            "Неизвестное состояние. Возвращаемся в главное меню.",
            reply_markup=keyboards.inline.menu_kb
        )

    await callback.answer()

# callback для отображения информации о магазине
@router.callback_query(F.data == "information")
async def process_category_selection(callback: types.CallbackQuery):
    try:
        await callback.message.edit_text(
            text="💳 <b>О магазине</b>"
                 "\nМы — онлайн-магазин аксессуаров для техники. В ассортименте: чехлы, зарядники, кабели и другие аксессуары от разных производителей. Мы стараемся предложить вам актуальные и качественные товары по хорошим ценам."
                 "\n\nℹ️ <b>Обратите внимание:</b>"
                 "\nИнформация, представленная в данном Telegram-боте, не является публичной офертой."
                 "\nУточнить наличие и цену можно у нашего менеджера после оформления заказа.",
            reply_markup=keyboards.inline.menu_kb
        )

    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise
    await callback.answer()
