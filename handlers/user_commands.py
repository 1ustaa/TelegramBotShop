from aiogram import types, Router
from aiogram.filters.command import CommandStart, Command
from keyboards import reply, builders

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Hello AIOgram 3.x", reply_markup=reply.main)

@router.message(Command("bot-test"))
async def show_cata(message: types.Message):
    await  message.answer("Выберите категорию товара", reply_markup=builders.categories_kb())