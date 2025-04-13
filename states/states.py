from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from keyboards import builders

class ChoseDevice(StatesGroup):
    showing_categories = State()
    showing_manufacturers = State()
    showing_devices = State()
    showing_variants = State()

state_handlers = {
    ChoseDevice.showing_categories:{
        "markup": lambda data: builders.categories_kb(),
        "text": "Выберите категорию"
    },
    ChoseDevice.showing_manufacturers:{
        "markup": lambda data: builders.manufacturer_kb(data["chosen_category"]),
        "text": "Выберите производителя"
    },
    # ChoseDevice.choosing_device: {
    #     "markup": lambda data: builders.devices_kb(data["chosen_manufacturer"]),
    #     "text": "Выберите производителя"
    # }
}

async def push_state(state: FSMContext, new_state, clear_history=False, max_size=10):
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