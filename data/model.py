from operator import index

from sqlalchemy import (
    create_engine,
    Column,
    Integer, String,
    ForeignKey,
    Table,
    DateTime,
    BigInteger,
    UniqueConstraint,
    Boolean
)

from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from config_reader import db_link_async
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

Base = declarative_base()

engine = create_async_engine(db_link_async, future=True, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Таблица Категория аксессуаров
class Categories(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    sort_order = Column(Integer, nullable=True, default=0)
    products = relationship("Products", back_populates="category")

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

# Таблица Бренд аксессуара
class AccessoryBrands(Base):
    __tablename__ = "accessory_brands"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    sort_order = Column(Integer, nullable=True, default=0)
    products = relationship("Products", back_populates="accessory_brand")

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

# Таблица Бренд устройства (для совместимости аксессуара)
class DeviceBrands(Base):
    __tablename__ = "device_brands"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    sort_order = Column(Integer, nullable=True, default=0)
    device_models = relationship("DeviceModels", back_populates="device_brand")

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

# Таблица Модель устройства (для совместимости аксессуара)
class DeviceModels(Base):
    __tablename__ = "device_models"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    sort_order = Column(Integer, nullable=True, default=0)
    
    device_brand_id = Column(Integer, ForeignKey("device_brands.id"), nullable=True)
    device_brand = relationship("DeviceBrands", back_populates="device_models")
    
    products = relationship("Products", back_populates="device_model")

    def __str__(self):
        if self.device_brand:
            return f"{self.device_brand.name} {self.name}"
        return self.name

    def __repr__(self):
        return self.__str__()

# Таблица Серия аксессуара
class Series(Base):
    __tablename__ = "series"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    products = relationship("Products", back_populates="series")

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

# Таблица Вариация
class Variations(Base):
    __tablename__ = "variations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    products = relationship("Products", back_populates="variation")

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

# Таблица Цвет
class Colors(Base):
    __tablename__ = "colors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    products = relationship("Products", back_populates="color")
    images = relationship("ProductImages", back_populates="color")

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

# Главная таблица Продукт (Аксессуар)
class Products(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint(
            'category_id', 
            'accessory_brand_id', 
            'device_model_id', 
            'series_id', 
            'variation_id',
            'color_id', 
            name='uq_product_combination'
        ),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Цена и описание
    price = Column(Integer, nullable=True)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Связи с другими таблицами
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    category = relationship("Categories", back_populates="products")
    
    accessory_brand_id = Column(Integer, ForeignKey("accessory_brands.id"), nullable=False)
    accessory_brand = relationship("AccessoryBrands", back_populates="products")
    
    # Опциональные поля для совместимости с устройствами
    device_model_id = Column(Integer, ForeignKey("device_models.id"), nullable=True)
    device_model = relationship("DeviceModels", back_populates="products")
    
    series_id = Column(Integer, ForeignKey("series.id"), nullable=True)
    series = relationship("Series", back_populates="products")
    
    variation_id = Column(Integer, ForeignKey("variations.id"), nullable=True)
    variation = relationship("Variations", back_populates="products")
    
    color_id = Column(Integer, ForeignKey("colors.id"), nullable=True)
    color = relationship("Colors", back_populates="products")
    
    # Изображения
    images = relationship("ProductImages", back_populates="product", cascade="all, delete-orphan")

    def __str__(self):
        parts = []
        if self.category:
            parts.append(str(self.category))
        if self.accessory_brand:
            parts.append(str(self.accessory_brand))
        if self.device_model:
            parts.append(str(self.device_model))
        if self.series:
            parts.append(str(self.series))
        if self.variation:
            parts.append(str(self.variation))
        if self.color:
            parts.append(str(self.color))
        return " ".join(parts)

    def __repr__(self):
        return self.__str__()

# Таблица изображений продуктов
class ProductImages(Base):
    __tablename__ = "product_images"
    id = Column(Integer, primary_key=True)
    path = Column(String, nullable=False)
    is_main = Column(Boolean, default=False)

    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    product = relationship("Products", back_populates="images")

    color_id = Column(Integer, ForeignKey("colors.id", ondelete="CASCADE"), nullable=True)
    color = relationship("Colors", back_populates="images")

class Customers(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    telegram_id = Column(BigInteger, unique=True)

    cart_items = relationship("CartItems", back_populates="customer")
    orders = relationship("Orders", back_populates="customer")

    def __str__(self):
        return f"{self.username} ({self.telegram_id})"

    def __repr__(self):
        return self.__str__()

class CartItems(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("customers.telegram_id"), nullable=False)

    quantity = Column(Integer, default=1)
    customer = relationship("Customers", back_populates="cart_items")

    product = relationship("Products")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    def __str__(self):
        return f"{self.product} x {self.quantity}"

    def __repr__(self):
        return self.__str__()

class Orders(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.telegram_id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    status_id = Column(Integer, ForeignKey("order_statuses.id"), nullable=True)
    status = relationship("OrderStatuses")
    total_price = Column(Integer, nullable=False)

    customer = relationship("Customers", back_populates="orders")
    items  = relationship("OrderItems", back_populates="order", cascade="all, delete-orphan")

    def __str__(self):
        return f"Order #{self.id} - {self.total_price} руб"

    def __repr__(self):
        return self.__str__()

class OrderItems(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    quantity = Column(Integer, default=1)

    order = relationship("Orders", back_populates="items")
    product = relationship("Products")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    def __str__(self):
        return f"{self.product} x {self.quantity}"

    def __repr__(self):
        return self.__str__()

class Admins(Base):
    __tablename__ = "admins"
    id = Column(BigInteger, unique=True,  primary_key=True)
    username = Column(String(100), nullable=True)
    chat_id = Column(BigInteger, unique=True)

    def __str__(self):
        return self.username or f"Admin {self.id}"

    def __repr__(self):
        return self.__str__()

class OrderStatuses(Base):
    __tablename__ = "order_statuses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
