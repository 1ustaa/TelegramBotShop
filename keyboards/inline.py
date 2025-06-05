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
            [InlineKeyboardButton(text="🗑 Корзина", callback_data="cart")],
            [InlineKeyboardButton(text="❓ Инфо", callback_data="information")],
            [InlineKeyboardButton(text="📟 Контакты", url="tg://resolve?domain=ustaa1")]
     ]
 )

kart_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Очистить корзину", callback_data="drop_kart")],
        [InlineKeyboardButton(text="Оформить заказ", callback_data="make_order")],
        [InlineKeyboardButton(text="Связаться с продавцом", url="tg://resolve?domain=ustaa1")],
        [main_menu_button()]
    ]
)

variant_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Добавить в корзину", callback_data="add_order_item")],
        [back_button()]
    ]
)

order_variant_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Перейти в корзину", callback_data="cart")],
        [back_button()]
    ]
)