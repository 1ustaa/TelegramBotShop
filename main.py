import asyncio
import logging
import os

from contextlib import suppress

from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
from aiogram.filters import CommandObject
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command, CommandStart
from aiogram.exceptions import TelegramBadRequest

import keybords

#Логирование
logging.basicConfig(level=logging.INFO)

load_dotenv()
bot = Bot(os.getenv("TELEGRAM_TOKEN"), default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

smiles = [
    ["🥑", "Avocado"],
    ["🌊", "Splash"],
    ["🌪️", "Tornado"],
    ["🏎️", "Car"]
]

@dp.callback_query(keybords.Pagination.filter(F.action.in_(["prev", "next"])))
async def pagination_handler(call: types.CallbackQuery, callback_data: keybords.Pagination):
    page_num = int(callback_data.page)
    page = page_num - 1 if page_num > 0 else 0

    if callback_data.action == "next":
        page = page_num + 1 if page_num < (len(smiles) - 1) else page_num

    with suppress(TelegramBadRequest):
        await call.message.edit_text(
            f"{smiles[page][0]} <b>{smiles[page][1]}</b>",
            reply_markup=keybords.paginator(page)
        )
    await call.answer()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Hello AIOgram 3.x", reply_markup=keybords.main_kb)

@dp.message()
async def echo(message: types.Message):
    msg = message.text.lower()

    if msg == "ссылки":
        await message.answer("Вот ваши ссылки", reply_markup=keybords.links_kb)
    elif msg == "спец. кнопки":
        await message.answer("Спец кнопки:", reply_markup=keybords.spec_kb)
    elif msg == "калькулятор":
        await  message.answer("Калькулятор", reply_markup=keybords.calc_kb())
    elif msg == "назад":
        await message.answer("Главное меню", reply_markup=keybords.main_kb)
    elif msg == "смайлики":
        await message.answer(f"{smiles[0][0]} <b>{smiles[0][1]}</b>", reply_markup=keybords.paginator())
    else:
        await message.answer("I dont understand you")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())