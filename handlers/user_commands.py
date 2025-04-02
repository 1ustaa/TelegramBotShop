from aiogram import types, Router
from aiogram.filters.command import CommandStart
from keyboards import builders
from states.states import ChoseDevice

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "<b>Добро пожаловать</b>\nВыберите категорию, чтобы посмотреть доступные модели:",
        reply_markup=builders.categories_kb())

