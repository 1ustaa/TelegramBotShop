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
from config_reader import db_link
from datetime import datetime

Base = declarative_base()

engine = create_engine(db_link)
Session = sessionmaker(bind=engine)
session = Session()

#Таблица Категория
class Categories(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    models = relationship("Models", back_populates="category")
    manufacturers = relationship("Manufacturers", secondary="manufacturer_category", back_populates="categories")

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

#Таблица Производитель
class Manufacturers(Base):
    __tablename__ = "manufacturers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    models = relationship("Models", back_populates="manufacturer")
    categories = relationship("Categories", secondary="manufacturer_category", back_populates="manufacturers")

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

#Таблица для связи категорий и производителей
manufacturer_category = Table(
    "manufacturer_category",
    Base.metadata,
    Column("manufacturer_id", Integer, ForeignKey("manufacturers.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True)
)

class Models(Base):
    __tablename__ = "models"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    images = relationship("ModelsImages", back_populates="model", cascade="all, delete-orphan")
    model_variants = relationship("ModelVariants", back_populates="model")

    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Categories", back_populates="models")

    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"))
    manufacturer = relationship("Manufacturers", back_populates="models")

    def __str__(self):
        return f"{self.category} {self.manufacturer} {self.name}"

    def __repr__(self):
        return f"{self.category} {self.manufacturer} {self.name}"

class ModelsImages(Base):
    __tablename__ = "models_images"
    __table_args__ = (UniqueConstraint("model_id", "color_id", name="uix_images_variant"),)
    id = Column(Integer, primary_key=True)
    path = Column(String, nullable=False)
    is_main = Column(Boolean, default=False)

    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"))
    model = relationship("Models", back_populates="images")

    color_id = Column(Integer, ForeignKey("colors.id", ondelete="CASCADE"))
    color = relationship("Colors", back_populates="images")

class Colors(Base):
    __tablename__ = "colors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    variants = relationship("ModelVariants", back_populates="color")
    images = relationship("ModelsImages", back_populates="color")

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

#Таблица характеристика устройства
#TODO: подумать какие еще характеристики могут пригодиться так как будут не только телефоны, но и наушники часы и так далее, например диагональ экрана для часов
class ModelVariants(Base):
    __tablename__ = "model_variants"
    __table_args__ = (UniqueConstraint("model_id", "sim_id", "memory_id", "color_id", "diagonal_id", name="uix_device_variant"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    price = Column(Integer, nullable=False)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)

    sim_id = Column(Integer, ForeignKey("sim_cards.id"), nullable=True)
    sim = relationship("SimCards")

    memory_id = Column(Integer, ForeignKey("memory_storage.id"), nullable=True)
    memory = relationship("MemoryStorage")

    model_id = Column(Integer, ForeignKey("models.id"))
    model = relationship("Models", back_populates="model_variants")

    diagonal_id = Column(Integer, ForeignKey("diagonals.id"))
    diagonal = relationship("Diagonals")

    color_id = Column(Integer, ForeignKey("colors.id"))
    color = relationship("Colors", back_populates="variants")

    def __str__(self):
        return f"Sim: {self.sim}, Память: {self.memory}, Цена: {self.price} руб"

class SimCards(Base):
    __tablename__ = "sim_cards"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class MemoryStorage(Base):
    __tablename__ = "memory_storage"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    quantity = Column(Integer)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class Diagonals(Base):
    __tablename__ = "diagonals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    quantity = Column(Integer)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

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
    user_id = Column(BigInteger, ForeignKey("customers.telegram_id"), nullable=False)

    quantity = Column(Integer, default=1)
    customer = relationship("Customers", back_populates="cart_items")

    model_variant = relationship("ModelVariants")
    model_variant_id = Column(Integer, ForeignKey("model_variants.id"), nullable=False)

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
    quantity = Column(Integer, default=1)

    order = relationship("Orders", back_populates="items")
    model_variant = relationship("ModelVariants")
    model_variant_id = Column(Integer, ForeignKey("model_variants.id"), nullable=False)

Base.metadata.create_all(engine)

