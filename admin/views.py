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
    Variations,
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

from data.crud import get_or_create_sync, SyncSessionLocal

# =============================
# VIEWS ДЛЯ ОСНОВНЫХ СУЩНОСТЕЙ
# =============================

class CategoriesView(ModelView):
    datamodel = SQLAInterface(Categories)

    columns = ["sort_order", "name"]
    list_columns = add_columns = edit_columns = show_columns = columns

    exclude_list = ["products"]
    add_exclude_columns = search_exclude_columns = edit_exclude_columns = show_exclude_columns = exclude_list

    label_columns = {"sort_order": "Порядок", "name": "Категория"}

class AccessoryBrandsView(ModelView):
    datamodel = SQLAInterface(AccessoryBrands)

    columns = ["sort_order", "name"]
    list_columns = add_columns = edit_columns = show_columns = columns

    exclude_list = ["products"]
    add_exclude_columns = search_exclude_columns = edit_exclude_columns = show_exclude_columns = exclude_list

    label_columns = {"sort_order": "Порядок", "name": "Бренд аксессуара"}

class DeviceBrandsView(ModelView):
    datamodel = SQLAInterface(DeviceBrands)

    columns = ["sort_order", "name"]
    list_columns = add_columns = edit_columns = show_columns = columns

    exclude_list = ["device_models"]
    add_exclude_columns = search_exclude_columns = edit_exclude_columns = show_exclude_columns = exclude_list

    label_columns = {"sort_order": "Порядок", "name": "Бренд устройства"}

class DeviceModelsView(ModelView):
    datamodel = SQLAInterface(DeviceModels)

    columns = ["sort_order", "name", "device_brand"]
    list_columns = add_columns = edit_columns = show_columns = columns

    exclude_list = ["products"]
    add_exclude_columns = search_exclude_columns = edit_exclude_columns = show_exclude_columns = exclude_list

    label_columns = {
        "sort_order": "Порядок",
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

class VariationsView(ModelView):
    datamodel = SQLAInterface(Variations)

    columns = ["name"]
    list_columns = add_columns = edit_columns = show_columns = columns

    exclude_list = ["products"]
    add_exclude_columns = search_exclude_columns = edit_exclude_columns = show_exclude_columns = exclude_list

    label_columns = {"name": "Вариация"}

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
        "category.name",
        "accessory_brand.name",
        "device_model.name",
        "series.name",
        "variation.name",
        "color.name",
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
        "category.name": "Категория",
        "category": "Категория",
        "accessory_brand": "Бренд аксессуара",
        "accessory_brand.name": "Бренд аксессуара",
        "device_model": "Модель устройства",
        "device_model.model": "Модель устройства",
        "series": "Серия",
        "series.name": "Серия",
        "variation": "Вариация",
        "variation.name": "Вариация",
        "color": "Цвет",
        "color.name": "Цвет",
        "price": "Цена",
        "description": "Описание",
        "is_active": "Активно"
    }
    
    # Список колонок доступных для сортировки
    # Flask-AppBuilder автоматически использует __str__ для связанных моделей
    column_sortable_list = list_columns
    
    # Явное указание полей для сортировки связанных моделей
    order_columns = [
        "category.name",
        "accessory_brand.name",
        "device_model.name",
        "series.name",
        "variation.name",
        "color.name",
        "price",
        "is_active"
    ]

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

def import_from_excel(file_path):
    """
    Импорт данных из Excel файла
    Структура: Категория, Бренд, Бренд устройства, Модель устройства, Серия, Вариация, Цвет, Цена
    """
    try:
        # Читаем Excel файл
        df = pd.read_excel(file_path)
        
        # Очищаем пробелы в названиях колонок
        df.columns = df.columns.str.strip()
        
        session = SyncSessionLocal()
        added_count = 0
        updated_count = 0
        error_count = 0
        
        try:
            for index, row in df.iterrows():
                try:
                    # Извлекаем данные из строки
                    category_name = str(row.get('Категория', '')).strip() if pd.notna(row.get('Категория')) else None
                    brand_name = str(row.get('Бренд', '')).strip() if pd.notna(row.get('Бренд')) else None
                    device_brand_name = str(row.get('Бренд устройства', '')).strip() if pd.notna(row.get('Бренд устройства')) else None
                    device_model_name = str(row.get('Модель устройства', '')).strip() if pd.notna(row.get('Модель устройства')) else None
                    series_name = str(row.get('Серия', '')).strip() if pd.notna(row.get('Серия')) else None
                    variation = str(row.get('Вариация', '')).strip() if pd.notna(row.get('Вариация')) else None
                    color_name = str(row.get('Цвет', '')).strip() if pd.notna(row.get('Цвет')) else None
                    
                    # Извлекаем цену
                    price = None
                    if pd.notna(row.get('Цена')):
                        try:
                            price = int(row.get('Цена'))
                        except (ValueError, TypeError):
                            pass
                    
                    # Пропускаем строки без обязательных полей
                    if not category_name or not brand_name:
                        continue
                    
                    # Получаем или создаем категорию
                    category = get_or_create_sync(session, Categories, name=category_name)
                    
                    # Получаем или создаем бренд аксессуара
                    accessory_brand = get_or_create_sync(session, AccessoryBrands, name=brand_name)
                    
                    # Получаем или создаем бренд устройства (если указан)
                    device_brand = None
                    if device_brand_name:
                        device_brand = get_or_create_sync(session, DeviceBrands, name=device_brand_name)
                    
                    # Получаем или создаем модель устройства (если указана)
                    device_model = None
                    if device_model_name and device_brand:
                        device_model = get_or_create_sync(
                            session, 
                            DeviceModels, 
                            name=device_model_name,
                            device_brand_id=device_brand.id
                        )
                    
                    # Получаем или создаем серию (если указана)
                    series = None
                    if series_name:
                        series = get_or_create_sync(session, Series, name=series_name)
                    
                    # Получаем или создаем вариацию (если указана)
                    variation_obj = None
                    if variation:
                        variation_obj = get_or_create_sync(session, Variations, name=variation)
                    
                    # Получаем или создаем цвет (если указан)
                    color = None
                    if color_name:
                        color = get_or_create_sync(session, Colors, name=color_name)
                    
                    # Проверяем, существует ли уже такой продукт
                    existing_product = session.query(Products).filter_by(
                        category_id=category.id,
                        accessory_brand_id=accessory_brand.id,
                        device_model_id=device_model.id if device_model else None,
                        series_id=series.id if series else None,
                        variation_id=variation_obj.id if variation_obj else None,
                        color_id=color.id if color else None
                    ).first()
                    
                    if existing_product:
                        # Обновляем существующий продукт
                        if price is not None:
                            existing_product.price = price
                        existing_product.is_active = True
                        updated_count += 1
                    else:
                        # Создаем новый продукт
                        product = Products(
                            category_id=category.id,
                            accessory_brand_id=accessory_brand.id,
                            device_model_id=device_model.id if device_model else None,
                            series_id=series.id if series else None,
                            variation_id=variation_obj.id if variation_obj else None,
                            color_id=color.id if color else None,
                            price=price,
                            is_active=True
                        )
                        session.add(product)
                        added_count += 1
                    
                except Exception as e:
                    error_count += 1
                    print(f"Ошибка обработки строки {index + 2}: {e}")
                    continue
            
            # Сохраняем все изменения
            session.commit()
            return added_count, updated_count, error_count
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    except Exception as e:
        print(f"Ошибка импорта из Excel: {e}")
        raise e

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
                    return redirect(url_for("ExcelUploadView.upload"))
                if allowed_file(file):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(self.upload_folder, filename)
                    
                    try:
                        # Сохраняем файл
                        file.save(file_path)
                        
                        # Импортируем данные
                        added_count, updated_count, error_count = import_from_excel(file_path)
                        
                        # Выводим результат
                        if error_count == 0:
                            flash(f"Файл успешно обработан! Добавлено: {added_count}, обновлено: {updated_count}", "success")
                        else:
                            flash(f"Файл обработан с ошибками. Добавлено: {added_count}, обновлено: {updated_count}, ошибок: {error_count}", "warning")
                        
                        # Удаляем временный файл
                        os.remove(file_path)
                        
                    except Exception as e:
                        flash(f"Ошибка обработки файла: {str(e)}", "danger")
                        # Удаляем файл в случае ошибки
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    
                    return redirect(url_for("ExcelUploadView.upload"))
                else:
                    flash("Недопустимый формат файла. Разрешены: xlsx, xls", "danger")
                    return redirect(url_for("ExcelUploadView.upload"))

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
