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
from data.crud import import_from_excel
from data.model import (Categories,
                        Manufacturers,
                        Models,
                        Colors,
                        SimCards,
                        MemoryStorage,
                        ModelVariants,
                        ModelsImages,
                        Diagonals,
                        Admins)

class CategoriesView(ModelView):
    datamodel = SQLAInterface(Categories)

    columns = ["name"]
    list_columns = add_columns = edit_columns = show_columns = columns

    exclude_list = ["models", "manufacturers"]
    add_exclude_columns = search_exclude_columns =  edit_exclude_columns = show_exclude_columns = exclude_list

    label_columns = {"name": "Категория"}

class ManufacturersView(ModelView):
    datamodel = SQLAInterface(Manufacturers)

    columns = ["name", "categories"]
    list_columns = add_columns = edit_columns = show_columns = columns

    exclude_list = ["models"]
    add_exclude_columns = search_exclude_columns =  edit_exclude_columns = show_exclude_columns = exclude_list

    label_columns = {"name": "Производитель",
                     "categories": "Категории"}

class ModelsView(ModelView):
    datamodel = SQLAInterface(Models)

    columns = ["category", "manufacturer", "name"]
    list_columns = add_columns = edit_columns = show_columns = columns

    exclude_list = ["images", "model_variants"]
    add_exclude_columns = search_exclude_columns =  edit_exclude_columns = show_exclude_columns = exclude_list

    label_columns = {"name": "Модель",
                     "category": "Категория",
                     "manufacturer": "Производитель",
                     "color": "Цвет",
                     "model_variants": "Вариант",
                     "description": "Описание"}

class ColorsView(ModelView):
    datamodel = SQLAInterface(Colors)

    columns = ["name"]
    list_columns = add_columns = edit_columns = show_columns = columns

    label_columns = {"name": "Цвет"}

    exclude_list = ["images", "variants"]
    add_exclude_columns = search_exclude_columns =  edit_exclude_columns = show_exclude_columns = exclude_list

class SimCardsView(ModelView):
    datamodel = SQLAInterface(SimCards)

    list_columns = ["name"]
    label_columns = {"name": "Симкарты"}

class MemoryStorageView(ModelView):
    datamodel = SQLAInterface(MemoryStorage)

    list_columns = ["name", "quantity"]
    label_columns = {"name": "Память",
                     "quantity": "Количество Gb"}

class DiagonalsView(ModelView):
    datamodel = SQLAInterface(Diagonals)

    list_columns = ["name", "quantity"]
    label_columns = {"name": "Диагональ",
                     "quantity": "Количество дюймов"}

class ModelVariantsView(ModelView):
    datamodel = SQLAInterface(ModelVariants)

    list_columns = ["model", "color", "sim", "memory", "diagonal", "price", "description", "is_active"]
    label_columns = {"model": "Устройство",
                     "color": "Цвет",
                     "sim": "Сим-карта",
                     "memory": "Память",
                     "diagonal": "Диагональ",
                     "price": "Цена",
                     "description": "Описание",
                     "is_active": "Активно"
                     }

class AdminsView(ModelView):
    datamodel = SQLAInterface(Admins)

    columns = ["id", "username"]
    list_columns = add_columns = edit_columns = show_columns = columns

class ModelsImagesView(ModelView):
    datamodel = SQLAInterface(ModelsImages)

    add_form_extra_fields = {
        "upload": FileField("Фото", render_kw={"accept": "image/*"})
    }

    list_columns = ['model', 'color', 'is_main']
    add_columns = ['model', 'color', 'upload', 'is_main']
    label_columns = {"model": "Устройство",
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
                    import_from_excel(file_path)
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