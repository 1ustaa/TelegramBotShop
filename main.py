import asyncio
import logging
import os
from aiogram.client.default import DefaultBotProperties
from aiogram import Bot, Dispatcher
from handlers import bot_mesages, user_commands
from callbacks import pagination

from config_reader import config

async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=config.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    dp.include_routers(
        user_commands.router,
        pagination.router,
        bot_mesages.router
    )

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())