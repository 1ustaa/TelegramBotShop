from flask import Flask
from flask_appbuilder import AppBuilder, SQLA
from config_reader import db_link, secret_key
from admin.views import (CategoriesView,
                   ManufacturersView,
                   ModelsView,
                   ColorsView,
                   SimCardsView,
                   MemoryStorageView,
                   ModelVariantsView,
                   ModelsImagesView,
                   DiagonalsView,
                   ExcelUploadView,
                   AdminsView)


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = db_link
app.config['SECRET_KEY'] = secret_key

db = SQLA(app)
appbuilder = AppBuilder(app, db.session)

appbuilder.add_view(CategoriesView, "Категории")
appbuilder.add_view(ManufacturersView, "Производители")
appbuilder.add_view(ModelsView, "Модели")
appbuilder.add_view(ModelVariantsView, "Варианты")
appbuilder.add_view(ModelsImagesView, "Изображения")
appbuilder.add_view(ColorsView, "Цвета")
appbuilder.add_view(SimCardsView, "Сим-карты")
appbuilder.add_view(MemoryStorageView, "Память")
appbuilder.add_view(DiagonalsView, "Диагонали")
appbuilder.add_view(ExcelUploadView, "Загрузить товары")
appbuilder.add_view(AdminsView, "ТГ Админы")


if __name__ == "__main__":
    app.run(debug=False)

