from aiogram import F, types, Router
from aiogram.exceptions import TelegramBadRequest

import keyboards
from states.states import ChoseDevice, push_state, pop_state, state_handlers
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

# TODO: Сделать пагинацию для моделей
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
    page = int(data_split[3])

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
    category_id = int(callback.data.split("_")[1])
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

    category_id = int(data_split[3])
    page = int(data_split[4])

    await callback.message.edit_text(
        "Выберите производителя", reply_markup=keyboards.builders.manufacturer_kb(category_id, page)
    )
    await callback.answer()

# callback для моделей
@router.callback_query(F.data.startswith("manufacturer_"), ChoseDevice.showing_manufacturers)
async def process_model_selection(callback: types.CallbackQuery, state: FSMContext):
    data_split = callback.data.split("_")
    manufacturer_id = int(data_split[1])
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

    category_id = int(data_split[3])
    manufacturer_id = int(data_split[4])
    page = int(data_split[5])

    await callback.message.edit_text(
        "Выберите модель устройства", reply_markup=keyboards.builders.models_kb(category_id, manufacturer_id, page)
    )
    await callback.answer()

# callback для кнопки главное меню
@router.callback_query(F.data == "main_menu", StateFilter("*"))
async def return_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🏠 Главное меню.",
        reply_markup=keyboards.inline.menu_kb)
    await state.clear()
    await callback.answer()

# callback для кнопки назад
@router.callback_query(F.data == "go_back", StateFilter("*"))
async def go_back(callback: types.CallbackQuery, state: FSMContext):
    prev_state = await pop_state(state)

    if prev_state is None:
        await callback.message.edit_text(
            "🏠 Главное меню.",
            reply_markup=keyboards.inline.menu_kb
        )
        return

    data = await state.get_data()
    handler = state_handlers.get(prev_state)

    if handler:
        try:
            markup = handler["markup"](data)
            text = handler["text"]
            try:
                await callback.message.edit_text(text, reply_markup=markup)
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    pass
                else:
                    raise
        except Exception as e:
            await callback.message.edit_text(
                "Ошибка при возврате назад. Попробуйте снова.",
                reply_markup=keyboards.inline.menu_kb
            )
    else:
        await callback.message.edit_text(
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
