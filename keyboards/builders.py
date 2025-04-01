from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from data.model import session, Category

def categories_kb():
    builder = InlineKeyboardBuilder()
    categories = session.query(Category).filter_by(parent_id=None).all()
    [builder.button(text=category.name, callback_data=f"categories_{category.id}") for category in categories]
    builder.adjust(2)
    return builder.as_markup()

def sub_categories_kb(category_id):
    builder = InlineKeyboardBuilder()
    categories = session.query(Category).filter_by(parent_id=category_id).all()
    [builder.button(text=category.name, callback_data=f"sub_categories_{category.id}") for category in categories]
    builder.adjust(2)
    return builder.as_markup()