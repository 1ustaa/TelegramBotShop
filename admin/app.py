from flask import Flask
from flask_appbuilder import AppBuilder, SQLA
from config_reader import db_link
from views import (CategoriesView,
                   ManufacturersView,
                   ModelsView,
                   ColorsView,
                   SimCardsView,
                   MemoryStorageView,
                   ModelVariantsView,
                   ModelsImagesView)


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = db_link
app.config['SECRET_KEY'] = 'your_secret_key'

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


if __name__ == "__main__":
    app.run(debug=True)

