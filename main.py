import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

#Логирование
logging.basicConfig(level=logging.INFO)

load_dotenv()
bot = Bot(os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hello!")

@dp.message(Command("test1"))
async def cmd_test1(message: types.Message):
    await message.answer("test1")

@dp.message(Command("test2"))
async def cmd_test2(message: types.Message):
    await message.answer("test2")

@dp.message(Command("dice"))
async def cmd_dice(message: types.Message):
    await message.answer_dice(emoji="🎲")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())