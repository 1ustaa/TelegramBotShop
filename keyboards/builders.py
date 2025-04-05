from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from data.model import session, Category, Product, Manufacturer, manufacturer_category, show_products

def categories_kb():
    builder = InlineKeyboardBuilder()
    categories = session.query(Category).all()
    [builder.button(text=category.name, callback_data=f"categories_{category.id}") for category in categories]
    builder.adjust(2)
    return builder.as_markup()

def manufacturer_kb(category_id):
    builder = InlineKeyboardBuilder()
    manufacturers = session.query(Manufacturer).join(manufacturer_category).filter(
        manufacturer_category.c.category_id == category_id).all()
    for manufacturer in manufacturers:
        builder.button(text=manufacturer.name, callback_data=f"manufacturer_{manufacturer.id}")
    builder.adjust(2)
    return builder.as_markup()

def devices_kb(category_id, manufacturer_id):
    builder = InlineKeyboardBuilder()
    devices = show_products(category_id, manufacturer_id)
    for device, variant in devices:
        text = device.name
        if variant:
            spec = []
            if variant.color:
                spec.append(variant.color)
            if variant.memory:
                spec.append(f"{variant.memory}GB")
            if variant.price:
                spec.append(f"{variant.price} руб.")
            text += f" ({' '.join(spec)})"

        builder.button(text=text, callback_data=f"variant_{variant.id}" if variant else f"device_{device.id}")
    builder.adjust(1)
    return builder.as_markup()
