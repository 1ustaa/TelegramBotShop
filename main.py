import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram import F
from sqlalchemy.testing.suite.test_reflection import users
from telegram.constants import ParseMode
from aiogram.client.default import DefaultBotProperties
from model import session, Product


#Логирование
logging.basicConfig(level=logging.INFO)

load_dotenv()
bot = Bot(os.getenv("TELEGRAM_TOKEN"), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# @dp.message(Command("start"))
# async def cmd_start(message: types.Message):
#     models = session.query(Product).filter_by(model="iPhone 15 Pro").all()
#     iphones = ""
#     for model in models:
#         iphones = iphones + model.model + "\n"
#     await message.answer(iphones)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
        [types.KeyboardButton(text="Playstation")],
        [types.KeyboardButton(text="XBOX")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb)
    await message.answer("Какая консоль?", reply_markup=keyboard)

@dp.message(Command("test1"))
async def cmd_test1(message: types.Message):
    await message.answer("test1")

@dp.message(Command("test2"))
async def cmd_test2(message: types.Message):
    await message.answer("test2")

@dp.message(Command("dice"))
async def cmd_dice(message: types.Message):
    await message.answer_dice(emoji="🎲")

@dp.message(F.text, Command("text"))
async def any_message(message: types.Message):

    await message.answer(
        "Hello <u>world</u>"
    )
    await message.answer(
        "Hello <u>world</u>",
        parse_mode=None
    )

@dp.message(F.text, Command("hello"))
async def say_hello(message: types.Message):
    await message.reply(f"Hello {message.from_user.username}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())