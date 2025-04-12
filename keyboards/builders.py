from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from data.model import session, Categories, Manufacturers, manufacturer_category
from keyboards.inline import main_menu_button, back_button

# TODO: Сделать пагинацию на клавиатурах

def categories_kb():
    builder = InlineKeyboardBuilder()
    categories = session.query(Categories).all()
    [builder.button(text=category.name, callback_data=f"categories_{category.id}") for category in categories]
    builder.adjust(2)
    builder.row(main_menu_button())
    return builder.as_markup()

def manufacturer_kb(category_id):
    builder = InlineKeyboardBuilder()
    manufacturers = session.query(Manufacturers).join(manufacturer_category).filter(
        manufacturer_category.c.category_id == category_id).all()
    for manufacturer in manufacturers:
        builder.button(text=manufacturer.name, callback_data=f"manufacturer_{manufacturer.id}")
    builder.adjust(2)
    builder.row(back_button())
    builder.row(main_menu_button())
    return builder.as_markup()

def devices_kb(category_id: int, manufacturer_id: int, page: int = 0, page_size: int = 5):
    builder = InlineKeyboardBuilder()
    devices = show_products(category_id, manufacturer_id, page, page_size)
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
            text += f" {" ".join(spec)}"
        builder.button(text=text, callback_data=f"variant_{variant.id}" if variant else f"device_{device.id}")

    total_devices = count_products(category_id, manufacturer_id)
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"devices_prev_{category_id}_{manufacturer_id}_{page - 1}"
            )
        )
    if (page + 1) * page_size < total_devices:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"devices_next_{category_id}_{manufacturer_id}_{page + 1}"
            )
        )

    builder.adjust(1)
    if pagination_buttons:
        builder.row(*pagination_buttons)
    builder.row(back_button())
    builder.row(main_menu_button())
    return builder.as_markup()
