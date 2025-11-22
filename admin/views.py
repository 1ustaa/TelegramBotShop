from aiohttp import request
from flask_appbuilder import has_access, BaseView, expose
from flask_appbuilder.views import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface
from openpyxl.reader.excel import load_workbook
from werkzeug.utils import secure_filename
from wtforms import FileField
from flask import request, url_for, redirect, flash, render_template
from config_reader import base_dir
from markupsafe import Markup
import os
from io import BytesIO
import pandas as pd

from data.model import (
    Categories,
    AccessoryBrands,
    DeviceBrands,
    DeviceModels,
    Series,
    Colors,
    Products,
    ProductImages,
    Admins,
    Customers,
    Orders,
    OrderStatuses,
    OrderItems,
    CartItems
)

# =============================
# VIEWS ДЛЯ ОСНОВНЫХ СУЩНОСТЕЙ
# =============================

class CategoriesView(ModelView):
    datamodel = SQLAInterface(Categories)

    columns = ["name"]
    list_columns = add_columns = edit_columns = show_columns = columns

    exclude_list = ["products"]
    add_exclude_columns = search_exclude_columns = edit_exclude_columns = show_exclude_columns = exclude_list

    label_columns = {"name": "Категория"}

class AccessoryBrandsView(ModelView):
    datamodel = SQLAInterface(AccessoryBrands)

    columns = ["name"]
    list_columns = add_columns = edit_columns = show_columns = columns

    exclude_list = ["products"]
    add_exclude_columns = search_exclude_columns = edit_exclude_columns = show_exclude_columns = exclude_list

    label_columns = {"name": "Бренд аксессуара"}

class DeviceBrandsView(ModelView):
    datamodel = SQLAInterface(DeviceBrands)

    columns = ["name"]
    list_columns = add_columns = edit_columns = show_columns = columns

    exclude_list = ["device_models"]
    add_exclude_columns = search_exclude_columns = edit_exclude_columns = show_exclude_columns = exclude_list

    label_columns = {"name": "Бренд устройства"}

class DeviceModelsView(ModelView):
    datamodel = SQLAInterface(DeviceModels)

    columns = ["name", "device_brand"]
    list_columns = add_columns = edit_columns = show_columns = columns

    exclude_list = ["products"]
    add_exclude_columns = search_exclude_columns = edit_exclude_columns = show_exclude_columns = exclude_list

    label_columns = {
        "name": "Модель устройства",
        "device_brand": "Бренд устройства"
    }

class SeriesView(ModelView):
    datamodel = SQLAInterface(Series)

    columns = ["name"]
    list_columns = add_columns = edit_columns = show_columns = columns

    exclude_list = ["products"]
    add_exclude_columns = search_exclude_columns = edit_exclude_columns = show_exclude_columns = exclude_list

    label_columns = {"name": "Серия"}

class ColorsView(ModelView):
    datamodel = SQLAInterface(Colors)

    columns = ["name"]
    list_columns = add_columns = edit_columns = show_columns = columns

    label_columns = {"name": "Цвет"}

    exclude_list = ["products", "images"]
    add_exclude_columns = search_exclude_columns = edit_exclude_columns = show_exclude_columns = exclude_list

# =============================
# VIEWS ДЛЯ ПРОДУКТОВ
# =============================

class ProductsView(ModelView):
    datamodel = SQLAInterface(Products)

    list_columns = [
        "category",
        "accessory_brand",
        "device_model",
        "series",
        "variation",
        "color",
        "price",
        "is_active"
    ]
    
    add_columns = edit_columns = show_columns = [
        "category",
        "accessory_brand",
        "device_model",
        "series",
        "variation",
        "color",
        "price",
        "description",
        "is_active"
    ]

    label_columns = {
        "category": "Категория",
        "accessory_brand": "Бренд аксессуара",
        "device_model": "Модель устройства",
        "series": "Серия",
        "variation": "Вариация",
        "color": "Цвет",
        "price": "Цена",
        "description": "Описание",
        "is_active": "Активно"
    }

    exclude_list = ["images"]
    add_exclude_columns = search_exclude_columns = edit_exclude_columns = show_exclude_columns = exclude_list

class ProductImagesView(ModelView):
    datamodel = SQLAInterface(ProductImages)

    add_form_extra_fields = {
        "upload": FileField("Фото", render_kw={"accept": "image/*"})
    }

    list_columns = ['product', 'color', 'is_main']
    add_columns = ['product', 'color', 'upload', 'is_main']
    
    label_columns = {
        "product": "Продукт",
        "color": "Цвет",
        "is_main": "Главное"
    }

    exclude_list = ["path"]
    add_exclude_columns = search_exclude_columns = edit_exclude_columns = show_exclude_columns = exclude_list

    def _save_image(self, file_storage):
        filename = secure_filename(file_storage.filename)
        filepath = os.path.join(base_dir, "stock", "devices_images", filename)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        file_storage.save(filepath)
        return filename

    def pre_add(self, item):
        file = request.files.get("upload")
        if file and file.filename:
            saved_path = self._save_image(file)
            item.path = saved_path

    def pre_delete(self, item):
        if item.path:
            full_path = os.path.join(base_dir, "stock", "devices_images", item.path)
            if os.path.isfile(full_path):
                try:
                    os.remove(full_path)
                except Exception as e:
                    print(f"Ошибка удаления файла: {e}")

# =============================
# VIEWS ДЛЯ ПОЛЬЗОВАТЕЛЕЙ И ЗАКАЗОВ
# =============================

class CustomersView(ModelView):
    datamodel = SQLAInterface(Customers)

    list_columns = ["telegram_id", "username"]
    show_columns = ["telegram_id", "username", "orders", "cart_items"]

    label_columns = {
        "telegram_id": "Telegram ID",
        "username": "Имя пользователя",
        "orders": "Заказы",
        "cart_items": "Корзина"
    }

    exclude_list = []
    add_exclude_columns = search_exclude_columns = edit_exclude_columns = show_exclude_columns = exclude_list

class OrdersView(ModelView):
    datamodel = SQLAInterface(Orders)

    list_columns = ["id", "customer", "created_at", "status", "total_price"]
    show_columns = ["id", "customer", "created_at", "status", "total_price", "items"]
    
    edit_columns = ["status"]

    label_columns = {
        "id": "№ Заказа",
        "customer": "Клиент",
        "created_at": "Дата создания",
        "status": "Статус",
        "total_price": "Сумма",
        "items": "Товары"
    }

class OrderItemsView(ModelView):
    datamodel = SQLAInterface(OrderItems)

    list_columns = ["order", "product", "quantity"]
    
    label_columns = {
        "order": "Заказ",
        "product": "Товар",
        "quantity": "Количество"
    }

class OrderStatusesView(ModelView):
    datamodel = SQLAInterface(OrderStatuses)

    list_columns = ["name"]
    add_columns = edit_columns = show_columns = ["name"]

    label_columns = {"name": "Статус заказа"}

class CartItemsView(ModelView):
    datamodel = SQLAInterface(CartItems)

    list_columns = ["customer", "product", "quantity"]
    
    label_columns = {
        "customer": "Клиент",
        "product": "Товар",
        "quantity": "Количество"
    }

class AdminsView(ModelView):
    datamodel = SQLAInterface(Admins)

    columns = ["id", "username"]
    list_columns = add_columns = edit_columns = show_columns = columns

    label_columns = {
        "id": "Telegram ID",
        "username": "Имя пользователя"
    }

# =============================
# EXCEL UPLOAD VIEW
# =============================

class ExcelUploadView(BaseView):
    route_base = "/excel_upload"
    default_view = "upload"
    upload_folder = os.path.join(base_dir, "stock")

    @expose('/', methods=["GET", "POST"])
    @has_access
    def upload(self):
        if request.method == "POST":
            if "file" not in request.files:
                flash("Файл не выбран.", "danger")
                return redirect(request.url)
            file = request.files.get("file")
            if file:
                if file.filename == "":
                    flash("Файл не выбран.", "danger")
                    return redirect(request.url)
                if allowed_file(file):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(self.upload_folder, filename)
                    file.save(file_path)
                    flash("Файл успешно загружен", "success")
                    # Здесь можно добавить функцию импорта
                    # import_from_excel(file_path)
                    os.remove(file_path)
                    return redirect(request.url)
                else:
                    flash("Недопустимый формат файла. Разрешены: xlsx, xls", "danger")
                    return redirect(request.url)

        return self.render_template("excel_upload.html")

def allowed_file(file_storage):
    try:
        in_memory = BytesIO(file_storage.read())
        load_workbook(filename=in_memory)
        file_storage.seek(0)
        return True
    except Exception:
        file_storage.seek(0)
        return False
