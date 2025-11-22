from flask import Flask
from flask_appbuilder import AppBuilder, SQLA
from config_reader import db_link, secret_key
from admin.views import (
    CategoriesView,
    AccessoryBrandsView,
    DeviceBrandsView,
    DeviceModelsView,
    SeriesView,
    ColorsView,
    ProductsView,
    ProductImagesView,
    CustomersView,
    OrdersView,
    OrderItemsView,
    OrderStatusesView,
    CartItemsView,
    AdminsView,
    ExcelUploadView
)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = db_link
app.config['SECRET_KEY'] = secret_key
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLA(app)
appbuilder = AppBuilder(app, db.session)

# Регистрация views для справочников
appbuilder.add_view(CategoriesView, "Категории", category="Справочники")
appbuilder.add_view(AccessoryBrandsView, "Бренды аксессуаров", category="Справочники")
appbuilder.add_view(DeviceBrandsView, "Бренды устройств", category="Справочники")
appbuilder.add_view(DeviceModelsView, "Модели устройств", category="Справочники")
appbuilder.add_view(SeriesView, "Серии", category="Справочники")
appbuilder.add_view(ColorsView, "Цвета", category="Справочники")

# Регистрация views для продуктов
appbuilder.add_view(ProductsView, "Продукты", category="Товары")
appbuilder.add_view(ProductImagesView, "Изображения", category="Товары")

# Регистрация views для пользователей и заказов
appbuilder.add_view(CustomersView, "Клиенты", category="Пользователи")
appbuilder.add_view(CartItemsView, "Корзины", category="Пользователи")

appbuilder.add_view(OrdersView, "Заказы", category="Заказы")
appbuilder.add_view(OrderItemsView, "Позиции заказов", category="Заказы")
appbuilder.add_view(OrderStatusesView, "Статусы заказов", category="Заказы")

# Регистрация views для админов и загрузки
appbuilder.add_view(AdminsView, "ТГ Админы")
appbuilder.add_view(ExcelUploadView, "Загрузить товары")

if __name__ == "__main__":
    app.run(debug=False)
