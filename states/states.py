from aiogram.fsm.state import StatesGroup, State

class ChoseDevice(StatesGroup):
    choosing_category = State()
    choosing_manufacturer = State()
    choosing_device = State()