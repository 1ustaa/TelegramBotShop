import asyncio
import logging
import os

from aiogram.filters import CommandObject
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram import F
from sqlalchemy.testing.suite.test_reflection import users
from telegram.constants import ParseMode
from aiogram.client.default import DefaultBotProperties
from model import session, Product
import random


#Логирование
logging.basicConfig(level=logging.INFO)

load_dotenv()
bot = Bot(os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

@dp.message(F.text == "/start")
async def start(message: types.Message):
    await message.answer(f"Hello, {message.from_user.first_name}")

@dp.message(Command(commands=["rn", "random-number"]))
async def random_number(message: types.Message, command: CommandObject):
    try:
        if command.args is None:
            await message.answer(f"need 1 argument")
        else:
            a, b = [int(n) for n in command.args.split("-")]
            rn_number = random.randint(a, b)
            await message.answer(f"{rn_number}")
    except ValueError:
        await message.answer("value error, integer need")

@dp.message()
async def echo(message: types.Message):
    await message.answer("I dont understand you")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())