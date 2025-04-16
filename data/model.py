from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, select, Table, DateTime, BigInteger, UniqueConstraint
from sqlalchemy.types import DECIMAL
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, foreign
from config_reader import config
from datetime import datetime
import csv
from decimal import Decimal

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
    image = Column(String(500), nullable=True)

    variants = relationship("DeviceVariants", back_populates="device")

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

def show_products(model_id: int, page: int, page_size: int):
    return session.query(Devices, DeviceVariants)\
        .outerjoin(DeviceVariants, Devices.id == DeviceVariants.device_id)\
        .filter(
        Devices.model_id == model_id
    ).offset(page * page_size).limit(page_size).all()

# def count_products(category_id: int, manufacturer_id: int):
#      return session.query(Product, ProductVariant).outerjoin(ProductVariant, Product.id == ProductVariant.product_id)\
#          .filter(
#          Product.category_id == category_id,
#          Product.manufacturer_id == manufacturer_id
#      ).count()

def import_from_csv(file_path):
    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        #Обработка производителя, если такого производителя нет, то он создается
        for row in reader:
            try:
                category = session.query(Categories).filter_by(name=row["category"]).first()
                if not category:
                    category = Categories(name=row["category"])
                    session.add(category)

                manufacturer = session.query(Manufacturers).filter_by(name=row["manufacturer"]).first()
                if not manufacturer:
                    manufacturer = Manufacturers(name=row["manufacturer"])
                    session.add(manufacturer)

                if manufacturer not in category.manufacturers:
                    category.manufacturers.append(manufacturer)

                model = session.query(Models).filter_by(name=row["model"]).first()
                if not model:
                    model = Models(name=row["model"])
                    session.add(model)
                    session.flush()

                model.manufacturer = manufacturer
                model.category = category

                color = session.query(Colors).filter_by(name=row["color"]).first()
                if not color:
                    color = Colors(name=row["color"])
                    session.add(color)
                    session.flush()

                device = session.query(Devices).filter_by(model_id=model.id, color_id=color.id).first()
                if not device:
                    device = Devices(model=model, color=color, description=row["description"], image=row["image"])
                    session.add(device)
                    session.flush()

                variant = session.query(DeviceVariants).filter_by(
                    device_id=device.id,
                    memory=row["memory"],
                    sim=row["sim"],
                ).first()

                if not variant:
                    variant = DeviceVariants(
                        device=device,
                        memory=row["memory"],
                        sim=row["sim"],
                        price=Decimal(row["price"]) if row["price"] else Decimal("0.00")
                    )
                    session.add(variant)
                session.commit()
            except Exception as e:
                print(e)
                session.rollback()
                continue

    print("Импорт данных завершен")

import_from_csv("devices.csv")
