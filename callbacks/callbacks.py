from aiogram import F, types, Router
from aiogram.exceptions import TelegramBadRequest

import keyboards
from states.states import ChoseDevice, push_state, pop_state, state_handlers
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

# TODO: Доработать кнопку назад
router = Router()


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

@router.callback_query(F.data == "categories")
async def process_category_selection(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите категорию", reply_markup=keyboards.builders.categories_kb()
    )
    await push_state(state, ChoseDevice.showing_categories)
    await callback.answer()

#Выбор производителя
@router.callback_query(F.data.startswith("categories_"), ChoseDevice.showing_categories)
async def process_category_selection(callback: types.CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[1])
    await state.update_data(chosen_category=category_id)
    await callback.message.edit_text(
        "Выберите производителя", reply_markup=keyboards.builders.manufacturer_kb(category_id)
    )
    await push_state(state, ChoseDevice.showing_manufacturers)
    await callback.answer()

@router.callback_query(F.data.startswith("manufacturer_"), ChoseDevice.showing_manufacturers)
async def process_device_selection(callback: types.CallbackQuery, state: FSMContext):
    manufacturer_id = int(callback.data.split("_")[1])
    data = await state.get_data()
    category_id = data["chosen_category"]
    await state.update_data(chosen_manufacturer=manufacturer_id)
    await callback.message.edit_text(
        "Выберите устройство", reply_markup=keyboards.builders.devices_kb(category_id, manufacturer_id)
    )
    await push_state(state, ChoseDevice.showing_devices)
    await callback.answer()

# @router.callback_query(F.data.startswith("devices_"), ChoseDevice.choosing_device)
# async def process_devices_pagination(callback: types.CallbackQuery, state: FSMContext):
#     data_parts = callback.data.split("_")
#     action = data_parts[1]
#     category_id = int(data_parts[2])
#     manufacturer_id = int(data_parts[3])
#     page = int(data_parts[4])
#
#     await callback.message.edit_text(
#         "Выберите устройство",
#         reply_markup=keyboards.builders.devices_kb(category_id, manufacturer_id, page)
#     )
#     await callback.answer()

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
