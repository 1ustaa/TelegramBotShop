from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

links = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="YouTube", url="https://clck.ru/3JvDWj"),
            InlineKeyboardButton(text="Telegram", url="tg://resolve?domain=ustaa1")
        ]
    ]
)