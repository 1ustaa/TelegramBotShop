from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)



def back_button(callback_data = "go_back"):
    return InlineKeyboardButton(text="Назад", callback_data=callback_data)

def main_menu_button(callback_data = "main_menu"):
    return InlineKeyboardButton(text="🏠 Главное меню", callback_data=callback_data)

menu_kb = InlineKeyboardMarkup(
     inline_keyboard=[
            [InlineKeyboardButton(text="💻 Категории", callback_data="categories")],
            [InlineKeyboardButton(text="🗑 Корзина (в работе)", callback_data="cart")],
            [InlineKeyboardButton(text="❓ Инфо", callback_data="information")],
            [InlineKeyboardButton(text="📟 Контакты", url="tg://resolve?domain=ustaa1")]
     ]
 )