from aiogram import types, Router
from aiogram.filters.command import CommandStart
from keyboards import builders, inline
from states.states import ChoseDevice
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter


router = Router()

#Выбор категории
@router.message(CommandStart(), StateFilter(None))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer(
        "<b>Добро пожаловать в наш Telegram-магазин техники! 🖥</b>"
        "\nЗдесь вы можете удобно ознакомиться с ассортиментом смартфонов, планшетов, умных часов, акустических систем и других гаджетов."
        "\nЧтобы начать — выберите один из пунктов ниже. Если возникнут вопросы — мы всегда на связи!",
        reply_markup=inline.menu_kb)
    await state.set_state(ChoseDevice.choosing_category)
