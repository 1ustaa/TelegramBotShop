from aiogram import types, Router
from aiogram.filters.command import CommandStart
from keyboards import builders, inline
from states.states import ChoseProduct
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter


router = Router()

# Команда /start
@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer(
        "<b>Добро пожаловать в наш Telegram-магазин аксессуаров! 🎧</b>"
        "\nЗдесь вы можете удобно ознакомиться с ассортиментом чехлов, зарядников, кабелей и других аксессуаров для ваших устройств."
        "\nЧтобы начать — выберите один из пунктов ниже. Если возникнут вопросы — мы всегда на связи!",
        reply_markup=inline.menu_kb)
    await state.clear()
