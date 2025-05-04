from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from data.model import (
    session,
    Categories,
    Manufacturers,
    Models,
    manufacturer_category,
    Colors,
    ModelVariants
)
from data.crud import count_models_variants, query_models_variants
from keyboards.inline import main_menu_button, back_button
from sqlalchemy import desc

MAX_PAGE_SIZE = 2

def categories_kb(page=0 ,page_size: int=MAX_PAGE_SIZE):
    categories_count = session.query(Categories).count()
    page, total_pages= count_pages(categories_count, page_size, page)
    categories = session.query(Categories).offset(page * page_size).limit(page_size).all()

    builder = InlineKeyboardBuilder()
    [builder.button(text=category.name, callback_data=f"category_{category.id}") for category in categories]
    builder.adjust(2)

    pg_buttons = make_pagination_buttons("pg_category", [], total_pages, page)
    builder.row(*pg_buttons)

    builder.row(back_button())
    builder.row(main_menu_button())

    return builder.as_markup()

def manufacturer_kb(category_id, page = 0, page_size: int=MAX_PAGE_SIZE):
    manufacturer_count = session.query(Manufacturers).join(manufacturer_category).filter(
        manufacturer_category.c.category_id == category_id).count()
    page, total_pages = count_pages(manufacturer_count, page_size, page)
    manufacturers = session.query(Manufacturers).join(manufacturer_category).filter(
        manufacturer_category.c.category_id == category_id).offset(page * page_size).limit(page_size).all()

    builder = InlineKeyboardBuilder()
    for manufacturer in manufacturers:
        builder.button(text=manufacturer.name, callback_data=f"manufacturer_{manufacturer.id}")
    builder.adjust(2)

    pg_buttons = make_pagination_buttons("pg_manufacturer", [category_id], total_pages, page)
    builder.row(*pg_buttons)

    builder.row(back_button())
    builder.row(main_menu_button())
    return builder.as_markup()

def models_kb(category_id: int, manufacturer_id: int, page: int = 0, page_size: int=MAX_PAGE_SIZE):
    models_count = session.query(Models).filter_by(category_id=category_id, manufacturer_id=manufacturer_id).count()
    page, total_pages = count_pages(models_count, page_size, page)
    models = session.query(Models).filter_by(category_id=category_id, manufacturer_id=manufacturer_id) \
        .order_by(desc(Models.name)).offset(page * page_size).limit(page_size).all()

    builder = InlineKeyboardBuilder()
    for model in models:
        builder.button(text=model.name, callback_data=f"model_{model.id}")
    builder.adjust(2)

    pg_buttons = make_pagination_buttons("pg_model", [category_id, manufacturer_id], total_pages, page)
    builder.row(*pg_buttons)

    builder.row(back_button())
    builder.row(main_menu_button())
    return builder.as_markup()

def colors_kb(model_id, page: int = 0, page_size: int=MAX_PAGE_SIZE):
    subquery = (
        session.query(Colors.id)
        .join(ModelVariants, ModelVariants.color_id == Colors.id)
        .filter(ModelVariants.model_id == model_id)
        .distinct()
        .subquery()
    )
    colors_count = session.query(subquery.c.id).count()

    page, total_pages = count_pages(colors_count, page_size, page)

    colors = (
        session.query(Colors)
        .join(ModelVariants, ModelVariants.color_id == Colors.id)
        .filter(ModelVariants.model_id == model_id)
        .distinct()
        .order_by(Colors.name)
        .offset(page * page_size)
        .limit(page_size)
        .all()
    )

    builder = InlineKeyboardBuilder()
    for color in colors:
        builder.button(text=color.name, callback_data=f"color_{color.id}")
    builder.adjust(2)

    pg_buttons = make_pagination_buttons("pg_color",[model_id], total_pages, page)
    builder.row(*pg_buttons)

    builder.row(back_button())
    builder.row(main_menu_button())
    return builder.as_markup()

def variants_kb(model_id, color_id, page: int = 0, page_size: int=MAX_PAGE_SIZE):
    variants_count = count_models_variants(model_id, color_id)
    page, total_pages = count_pages(variants_count, page_size, page)
    variants = query_models_variants(model_id, color_id, page * page_size, page_size)

    builder = InlineKeyboardBuilder()
    for variant in variants:
        text = "".join([
            f"{variant.memory} " if variant.memory else "",
            f"{variant.sim} " if variant.sim else "",
            f"{variant.diagonal} " if variant.diagonal else "",
            f"{variant.price} руб " if variant.price else ""
        ]).strip()
        builder.button(text=text, callback_data=f"variant_{variant.id}")
    builder.adjust(1)

    pg_buttons = make_pagination_buttons("pg_variant", [model_id, color_id], total_pages, page)
    builder.row(*pg_buttons)

    builder.row(back_button())
    builder.row(main_menu_button())
    return builder.as_markup()

def make_pagination_buttons(prefix: str, items: list, total_pages: int, page: int) -> list:
    """
    :param prefix: str — префикс для callback_data (например, 'pg_model')
    :param items: list — список данных, включаемых в callback_data (например: [category_id, manufacturer_id, ...])
    :param total_pages: int — общее количество страниц
    :param page: int — текущая страница
    :return: list — список из InlineKeyboardButton'ов (⬅️ и ➡️ при необходимости)
    """

    if items:
        callback_data_string = "_" + "_".join(str(item) for item in items)
    else:
        callback_data_string = ""

    pagination_buttons = []
    if total_pages > 1:
        prev_page = (page - 1) if page > 0 else total_pages - 1
        next_page = (page + 1) % total_pages

        pagination_buttons.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data = f"{prefix}_prev{callback_data_string}_{prev_page}"
            )
        )
        pagination_buttons.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data = f"{prefix}_next{callback_data_string}_{next_page}"
            )
        )
    return pagination_buttons

def count_pages(count, page_size, page):
    total_pages = (count + page_size - 1) // page_size
    page = page % total_pages if total_pages > 0 else 0
    return page, total_pages