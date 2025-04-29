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
from sqlalchemy.types import DECIMAL
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from config_reader import config
from datetime import datetime

Base = declarative_base()

engine = create_engine(config.db_link.get_secret_value())
Session = sessionmaker(bind=engine)
session = Session()

#Таблица Категория
class Categories(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    models = relationship("Models", back_populates="category")
    manufacturers = relationship("Manufacturers", secondary="manufacturer_category", back_populates="categories")

#Таблица Производитель
class Manufacturers(Base):
    __tablename__ = "manufacturers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    models = relationship("Models", back_populates="manufacturer")
    categories = relationship("Categories", secondary="manufacturer_category", back_populates="manufacturers")

class Models(Base):
    __tablename__ = "models"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)

    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Categories", back_populates="models")

    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"))
    manufacturer = relationship("Manufacturers", back_populates="models")

    devices = relationship("Devices", back_populates="model")

manufacturer_category = Table(
    "manufacturer_category",
    Base.metadata,
    Column("manufacturer_id", Integer, ForeignKey("manufacturers.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True)
)

#Таблица Устройство
class Devices(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, autoincrement=True)

    model_id = Column(Integer, ForeignKey("models.id"))
    model = relationship("Models", back_populates="devices")

    color_id = Column(Integer, ForeignKey("colors.id"))
    color = relationship("Colors", back_populates="devices")

    description = Column(String(500), nullable=True)

    images = relationship("DeviceImages", back_populates="device", cascade="all, delete-orphan")

    variants = relationship("DeviceVariants", back_populates="device")

class DeviceImages(Base):
    __tablename__ = "device_images"

    id = Column(Integer, primary_key=True)
    path = Column(String, nullable=False)
    is_main = Column(Boolean, default=False)

    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))
    device = relationship("Devices", back_populates="images")

class Colors(Base):
    __tablename__ = "colors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    devices = relationship("Devices", back_populates="color")

#Таблица характеристика устройства
class DeviceVariants(Base):
    __tablename__ = "device_variants"
    __table_args__ = (UniqueConstraint("device_id", "sim", "memory", name="uix_device_variant"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    sim = Column(String(20), nullable=True)
    memory = Column(String(100), nullable=True)
    price = Column(DECIMAL(12, 2), nullable=False)

    device_id = Column(Integer, ForeignKey("devices.id"))
    device = relationship("Devices", back_populates="variants")

class Customers(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    telegram_id = Column(BigInteger, unique=True)

    cart_items = relationship("CartItems", back_populates="customer")
    orders = relationship("Orders", back_populates="customer")

class CartItems(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("device_variants.id"), nullable=False)
    quantity = Column(Integer, default=1)

    customer = relationship("Customers", back_populates="cart_items")
    variant = relationship("DeviceVariants")

class Orders(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    status = Column(String(50))
    total_price = Column(DECIMAL(12, 2))

    customer = relationship("Customers", back_populates="orders")
    items  = relationship("OrderItems", back_populates="order", cascade="all, delete-orphan")

class OrderItems(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, autoincrement=True)

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("device_variants.id"), nullable=False)
    quantity = Column(Integer, default=1)

    order = relationship("Orders", back_populates="items")
    variant = relationship("DeviceVariants")

Base.metadata.create_all(engine)

