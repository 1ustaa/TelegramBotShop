from email.policy import default

from aiogram import types, Router
from aiogram.filters.command import CommandStart, Command
from keyboards import inline, builders
from aiogram.client.default import DefaultBotProperties

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "<b>Добро пожаловать</b>\nВыберите категорию, чтобы посмотреть доступные модели:",
        reply_markup=builders.categories_kb())
