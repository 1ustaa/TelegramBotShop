from aiogram import F, types, Router
import keyboards
from states.states import ChoseDevice
from aiogram.fsm.context import FSMContext

router = Router()

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

@router.callback_query(F.data.startswith("devices_"), ChoseDevice.choosing_device)
async def process_devices_pagination(callback: types.CallbackQuery, state: FSMContext):
    data_parts = callback.data.split("_")
    action = data_parts[1]
    category_id = int(data_parts[2])
    manufacturer_id = int(data_parts[3])
    page = int(data_parts[4])

    await callback.message.edit_text(
        "Выберите устройство",
        reply_markup=keyboards.builders.devices_kb(category_id, manufacturer_id, page)
    )
    await callback.answer()