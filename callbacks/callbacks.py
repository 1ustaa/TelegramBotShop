import os.path

from aiogram import F, types, Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile, InputMediaPhoto


import keyboards
from states.states import ChoseDevice, push_state, pop_state, state_handlers
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from data.crud import (get_color_model_image,
                       add_new_customer,
                       add_cart_item,
                       get_cart_items,
                       count_cart_sum,
                       query_models_variants,
                       clear_user_cart,
                       make_order,
                       get_admins,
                       get_order_details,
                       count_models_variants)

router = Router()

# callback для категорий
@router.callback_query(F.data == "categories")
async def process_category_selection(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите категорию", reply_markup=keyboards.builders.categories_kb()
    )
    await push_state(state, ChoseDevice.showing_categories)
    await callback.answer()

# callback для пагинации категорий
@router.callback_query(F.data.startswith("pg_category"))
async def process_category_pagination(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        page = int(data_split[3])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await callback.message.edit_text(
        "Выберите категорию", reply_markup=keyboards.builders.categories_kb(page)
    )
    await callback.answer()

# callback для производителей
@router.callback_query(
    F.data.startswith("category_"),
    ChoseDevice.showing_categories
)
async def process_manufacturer_selection(callback: types.CallbackQuery, state: FSMContext):
    try:
        category_id = int(callback.data.split("_")[1])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return
    await state.update_data(chosen_category=category_id)
    await callback.message.edit_text(
        "Выберите производителя", reply_markup=keyboards.builders.manufacturer_kb(category_id)
    )
    await push_state(state, ChoseDevice.showing_manufacturers)
    await callback.answer()

# callback для пагинации производителей
@router.callback_query(
    F.data.startswith("pg_manufacturer"),
    ChoseDevice.showing_manufacturers
)
async def process_manufacturer_pagination(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        category_id = int(data_split[3])
        page = int(data_split[4])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await callback.message.edit_text(
        "Выберите производителя", reply_markup=keyboards.builders.manufacturer_kb(category_id, page)
    )
    await callback.answer()

# callback для моделей
@router.callback_query(F.data.startswith("manufacturer_"), ChoseDevice.showing_manufacturers)
async def process_model_selection(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        manufacturer_id = int(data_split[1])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await state.update_data(chosen_manufacturer=manufacturer_id)
    data = await state.get_data()
    category_id = data.get("chosen_category")
    await callback.message.edit_text(
        "Выберите модель устройства", reply_markup=keyboards.builders.models_kb(category_id, manufacturer_id)
    )
    await push_state(state, ChoseDevice.showing_models)
    await callback.answer()

# callback для пагинации моделей
@router.callback_query(
    F.data.startswith("pg_model"),
    ChoseDevice.showing_models
)
async def process_model_pagination(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        category_id = int(data_split[3])
        manufacturer_id = int(data_split[4])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return


    page = int(data_split[5])

    await callback.message.edit_text(
        "Выберите модель устройства", reply_markup=keyboards.builders.models_kb(category_id, manufacturer_id, page)
    )
    await callback.answer()

# callback для цветов
@router.callback_query(F.data.startswith("model_"), ChoseDevice.showing_models)
async def process_color_selection(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        model_id = int(data_split[1])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await state.update_data(chosen_model=model_id)
    await callback.message.edit_text(
        "Выберите цвет устройства", reply_markup=keyboards.builders.colors_kb(model_id)
    )
    await push_state(state, ChoseDevice.showing_colors)
    await callback.answer()

# callback для пагинации цветов
@router.callback_query(
    F.data.startswith("pg_color"),
    ChoseDevice.showing_colors
)
async def process_color_pagination(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        model_id = int(data_split[3])
        page = int(data_split[4])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    await callback.message.edit_text(
        "Выберите цвет устройства", reply_markup=keyboards.builders.colors_kb(model_id, page)
    )
    await callback.answer()

# callback для вариантов
@router.callback_query(F.data.startswith("color_"), ChoseDevice.showing_colors)
async def process_variant_selection(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        color_id = int(data_split[1])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    data = await state.get_data()
    model_id = data.get("chosen_model")

    model_name, color_name, image_path = get_color_model_image(model_id, color_id)

    await state.update_data(chosen_color=color_id)

    variants_count = count_models_variants(model_id, color_id)
    if variants_count > 0:
        text = f"<b>{model_name} {color_name}</b>\nНажмите на кнопку с ценой, \nчто бы добавить товар в корзину"
    else:
        text = f"<b>{model_name} {color_name}</b>\nК сожалению данного товара пока что нет в наличии"

    if image_path and os.path.exists(image_path):
        photo = FSInputFile(image_path)
        await callback.message.edit_media(
                media=InputMediaPhoto(media=photo, caption=text),
                reply_markup=keyboards.builders.variants_kb(model_id, color_id)
        )
    else:
        await callback.message.edit_text(
                text,
                reply_markup=keyboards.builders.variants_kb(model_id ,color_id)
        )

    await push_state(state, ChoseDevice.showing_variants)
    await callback.answer()

# callback для пагинации вариантов
@router.callback_query(
    F.data.startswith("pg_variant"),
    ChoseDevice.showing_variants
)
async def process_variant_pagination(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")

    try:
        model_id = int(data_split[3])
        color_id = int(data_split[4])
        page = int(data_split[5])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return

    model_name, color_name, image_path = get_color_model_image(model_id, color_id)

    if image_path and os.path.exists(image_path):
        photo = FSInputFile(image_path)
        await callback.message.edit_media(
            media=InputMediaPhoto(media=photo, caption=f"<b>{model_name} {color_name}</b>"
                                                       "\nНажмите на кнопку с ценой, \nчто бы добавить товар в корзину"),
            reply_markup=keyboards.builders.variants_kb(model_id, color_id, page)
        )
    else:
        await callback.message.edit_text(
            f"<b>{model_name} {color_name}</b>\nНажмите на кнопку с ценой, \nчто бы добавить товар в корзину",
            reply_markup=keyboards.builders.variants_kb(model_id, color_id, page)
        )
    await callback.answer()

@router.callback_query(
    F.data.startswith("variant_"),
    ChoseDevice.showing_variants
)
async def add_item_in_cart(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    try:
        variant_id = int(data_split[1])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные.")
        return
    user_id = callback.from_user.id
    username = callback.from_user.username or "Без имени"
    customer = add_new_customer(user_id, username)
    add_cart_item(variant_id, customer.telegram_id)

    data = await state.get_data()
    model_id = data.get("chosen_model")
    color_id = data.get("chosen_color")

    model_name, color_name, image_path = get_color_model_image(model_id, color_id)
    variants = query_models_variants(model_id, color_id, variant_id)

    text_variant = ""
    for variant in variants:
        text_variant = "".join([
            f"{variant.memory} " if variant.memory else "",
            f"{variant.sim} " if variant.sim else "",
            f"{variant.diagonal} " if variant.diagonal else ""
        ]).strip()
    text = (f"Товар <b>{model_name} {color_name} {text_variant}</b>\n Добавлен в корзину \n "
            f"Что бы посмотреть корзину перейдите в главное меню")
    try:
        if image_path and os.path.exists(image_path):
            photo = FSInputFile(image_path)
            await callback.message.edit_media(
                media=InputMediaPhoto(media=photo, caption=text),
                reply_markup=keyboards.builders.variants_kb(model_id, color_id)
            )
        else:
            await callback.message.edit_text(
                text=text,
                reply_markup=keyboards.builders.variants_kb(model_id, color_id)
            )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise
    await callback.answer()

#TODO доработать функцию исправить ошибку удаления сообщения через 48 часов
async def safe_edit_message(callback: types.CallbackQuery, text: str=None, reply_markup=None, media=None):
    try:
        if media:
            try:
                await callback.message.edit_media(
                    media=InputMediaPhoto(
                        media=media,
                        caption=text
                    ),
                    reply_markup=reply_markup
                )
            except Exception as e:
                await callback.message.answer_photo(
                        media=media,
                        caption=text,
                        reply_markup=reply_markup)
        else:
            await callback.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        elif "there is no text in the message to edit" in str(e):
            try:
                await callback.message.delete()
            except TelegramBadRequest as del_err:
                if "message can't be deleted" in str(del_err):
                    await callback.message.answer(
                        text=text,
                        reply_markup=reply_markup
                    )
        else:
            raise

#callback для корзины
@router.callback_query(F.data == "cart")
async def show_cart(callback: types.CallbackQuery):
    cart_items = get_cart_items(callback.from_user.id)
    cart_sum = count_cart_sum(callback.from_user.id)

    if cart_items:
        text = (
            "Ваша 🛒:\n\n" + "\n\n"
            .join(["".join([
            f"<b>{item.model} </b>" if item.model else "",
            f"<b>{item.color} </b>" if item.color else "",
            f"<b>{item.sim} </b>" if item.sim else "",
            f"<b>{item.memory} </b>" if item.memory else "",
            # f"{item.price} " if item.price else "",
            "- ",
            f"{item.quantity } шт. " if item.quantity else "",
            f"сумма: {item.sum} руб " if item.sum else "цену уточнять",
            ]).strip() for item in cart_items]) + f"\n\n<b>Общая сумма: {cart_sum} руб</b>"
        )
    else:
        text = "Ваша 🛒:\n\n" + "В вашей корзине пока что нет товаров"

    await callback.message.edit_text(text, reply_markup=keyboards.inline.kart_kb)

#callback для удаления товаров из корзины
@router.callback_query(F.data == "drop_kart")
async def clear_user_cart_items(callback: types.CallbackQuery):
    clear_user_cart(callback.from_user.id)
    text = "Ваша корзина очищена"
    await callback.message.edit_text(text, reply_markup=keyboards.inline.kart_kb)

#callback для создания заказа
@router.callback_query(F.data == "make_order")
async def send_order(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    username = callback.from_user.username
    date = callback.message.date
    order = make_order(user_id, date)
    if order:
        admins, text = make_message(order.id, username)
        for admin in admins:
            await bot.send_message(admin.id, text)
        text = "Ваша заказ отправлен менеджеру в ближайшее время с вами свяжутся"
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

def make_message(order_id, username):
    admins = get_admins()
    order_items = get_order_details(order_id)
    text = (
            f"Заказ № {order_id} от пользователя @{username}:\n\n" + "\n\n"
            .join(["".join([
        f"<b>{item.manufacturer} </b>" if item.manufacturer else "",
        f"<b>{item.model} </b>" if item.model else "",
        f"<b>{item.color} </b>" if item.color else "",
        f"<b>{item.sim} </b>" if item.sim else "",
        f"<b>{item.memory} </b>" if item.memory else "",
        # f"{item.price} " if item.price else "",
        "- ",
        f"{item.quantity} шт. " if item.quantity else "",
        f"сумма: {item.sum} руб " if item.sum else "" + "\n"
    ]).strip() for item in order_items])
    )
    return admins, text



# callback для кнопки главное меню
@router.callback_query(F.data == "main_menu", StateFilter("*"))
async def return_main_menu(callback: types.CallbackQuery, state: FSMContext):
    text = "🏠 Главное меню."
    await safe_edit_message(callback, text, keyboards.inline.menu_kb)
    await state.clear()
    await callback.answer()

# callback для кнопки назад
@router.callback_query(F.data == "go_back", StateFilter("*"))
async def go_back(callback: types.CallbackQuery, state: FSMContext):
    prev_state = await pop_state(state)

    if prev_state is None:
        await safe_edit_message(
            callback, "🏠 Главное меню.", keyboards.inline.menu_kb
        )
        return

    data = await state.get_data()
    handler = state_handlers.get(prev_state)

    if handler:
        try:
            markup = handler["markup"](data)
            text = handler["text"]
            try:
                await safe_edit_message(callback, text, markup)
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    pass
                else:
                    raise
        except Exception as e:
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
                 "\nМы — онлайн-магазин техники, в ассортименте: смартфоны, планшеты, часы и аудиоустройства от разных производителей. Мы стараемся предложить вам актуальные и качественные устройства по хорошим ценам."
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

