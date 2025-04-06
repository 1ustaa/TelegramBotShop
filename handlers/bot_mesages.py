from aiogram import types, Router

router = Router()

@router.message()
async def echo(message: types.Message):
    msg = message.text.lower()

    await message.answer("Произошла ошибка")