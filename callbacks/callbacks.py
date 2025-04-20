import os.path

from aiogram import F, types, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile, InputMediaPhoto

import keyboards
from states.states import ChoseDevice, push_state, pop_state, state_handlers
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from data.model import get_color_model_image

router = Router()

# TODO: Исправить работы изображений

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

    if image_path and os.path.exists(image_path):
        photo = FSInputFile(image_path)
        await callback.message.edit_media(
                media=InputMediaPhoto(media=photo, caption=f"<b>{model_name} {color_name}</b>"
                                                           "\nНажмите на вариант устройства, что бы добавить его в корзину"),
                reply_markup=keyboards.builders.variants_kb(model_id, color_id)
        )
    else:
        await callback.message.edit_text(
                f"<b>{model_name} {color_name}</b>\nНажмите на вариант устройства, что бы добавить его в корзину",
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
                                                       "\nНажмите на вариант устройства, что бы добавить его в корзину"),
            reply_markup=keyboards.builders.variants_kb(model_id, color_id, page)
        )
    else:
        await callback.message.edit_text(
            f"<b>{model_name} {color_name}</b>\nНажмите на вариант устройства, что бы добавить его в корзину",
            reply_markup=keyboards.builders.variants_kb(model_id, color_id, page)
        )
    await callback.answer()

async def safe_edit_message(callback: types.CallbackQuery, text: str=None, reply_markup=None, media=None):
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
            pass
        elif "there is no text in the message to edit" in str(e):
            await callback.message.delete()
            await callback.message.answer(
                text=text,
                reply_markup=reply_markup
            )
        else:
            raise


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