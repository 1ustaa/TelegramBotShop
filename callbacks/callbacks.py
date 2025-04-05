from aiogram import F, types, Router
from aiogram.exceptions import TelegramBadRequest
from contextlib import suppress
import keyboards
from data.subloader import get_json
from states.states import ChoseDevice
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter


router = Router()

@router.callback_query(keyboards.fabrics.Pagination.filter(F.action.in_(["prev", "next"])))
async def pagination_handler(call: types.CallbackQuery, callback_data: keyboards.fabrics.Pagination):
    smiles = await get_json("smiles.json")
    page_num = int(callback_data.page)
    page = page_num - 1 if page_num > 0 else 0

    if callback_data.action == "next":
        page = page_num + 1 if page_num < (len(smiles) - 1) else page_num

    with suppress(TelegramBadRequest):
        await call.message.edit_text(
            f"{smiles[page][0]} <b>{smiles[page][1]}</b>",
            reply_markup=keyboards.fabrics.paginator(page)
        )
    await call.answer()

#Выбор производителя
@router.callback_query(F.data.startswith("categories_"), ChoseDevice.choosing_category)
async def process_category_selection(callback: types.CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[1])
    await state.update_data(chosen_category=category_id)
    await callback.message.edit_text(
        "Выберите производителя", reply_markup=keyboards.builders.manufacturer_kb(category_id)
    )
    await state.set_state(ChoseDevice.choosing_manufacturer)
    await callback.answer()

@router.callback_query(F.data.startswith("manufacturer_"), ChoseDevice.choosing_manufacturer)
async def process_device_selection(callback: types.CallbackQuery, state: FSMContext):
    manufacturer_id = int(callback.data.split("_")[1])
    category_id = await state.get_data()
    category_id = category_id['chosen_category']
    await state.update_data(chosen_manufacturer=manufacturer_id)
    await callback.message.edit_text(
        "Выберите устройство", reply_markup=keyboards.builders.devices_kb(category_id, manufacturer_id)
    )
    await state.set_state(ChoseDevice.choosing_device)
    await callback.answer()




