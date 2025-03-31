from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from data.model import session, Category

def calc():
    builder = ReplyKeyboardBuilder()
    items = [
        "1", "2", "3", "/",
        "4", "5", "6", "*",
        "7", "8", "9", "+",
        "0", ".", "=", "-",
    ]
    [builder.button(text=item) for item in items]
    builder.button(text="назад")
    builder.adjust(4, 4, 4, 4, 1)
    return builder.as_markup(resize_keyboard=True)

def categories_kb():
    builder = InlineKeyboardBuilder()
    categories = session.query(Category).filter_by(parent_id=None).all()
    [builder.button(text=category.name, callback_data=f"categories_{category.id}") for category in categories]
    builder.adjust(2)
    return builder.as_markup()