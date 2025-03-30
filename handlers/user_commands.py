from aiogram import types, Router
from aiogram.filters.command import CommandStart
from keyboards import reply

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Hello AIOgram 3.x", reply_markup=reply.main)