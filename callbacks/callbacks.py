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

@router.callback_query(F.data.startswith("categories_"), StateFilter(None))
async def process_category_selection(callback: types.CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[1])
    await callback.message.edit_text(
        "Выберите производителя", reply_markup=keyboards.builders.sub_categories_kb(category_id)
    )
    await callback.answer()
    await state.set_state(ChoseDevice.choosing_category)

@router.callback_query(F.data.startswith("sub_categories_"), ChoseDevice.choosing_category)
async def process_category_selection(callback: types.CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[1])
    await state.update_data(chosen_category=category_id)
    await callback.message.edit_text(
        "Выберите производителя", reply_markup=keyboards.builders.sub_categories_kb(category_id)
    )
    await callback.answer()
    await state.set_state(ChoseDevice.choosing_manufacturer)


