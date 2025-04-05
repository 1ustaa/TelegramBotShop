from aiogram import types, Router
from aiogram.filters.command import CommandStart
from keyboards import builders
from states.states import ChoseDevice
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter


router = Router()

#Выбор категории
@router.message(CommandStart(), StateFilter(None))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer(
        "<b>Добро пожаловать</b>\nВыберите категорию, чтобы посмотреть доступные модели:",
        reply_markup=builders.categories_kb())
    await state.set_state(ChoseDevice.choosing_category)

