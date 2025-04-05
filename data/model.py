import csv
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, select, Table
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, outerjoin
from config_reader import config

Base = declarative_base()

engine = create_engine(config.db_link.get_secret_value())
Session = sessionmaker(bind=engine)
session = Session()

#Таблица Категория
class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    products = relationship("Product", back_populates="category")
    manufacturers = relationship("Manufacturer", secondary="manufacturer_category", back_populates="categories")

#Таблица Производитель
class Manufacturer(Base):
    __tablename__ = 'manufacturers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    products = relationship("Product", back_populates="manufacturer")
    categories = relationship("Category", secondary="manufacturer_category", back_populates="manufacturers")

manufacturer_category = Table(
    "manufacturer_category",
    Base.metadata,
    Column('manufacturer_id', Integer, ForeignKey('manufacturers.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)

#Таблица Устройство
class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship("Category", back_populates="products")

    manufacturer_id = Column(Integer, ForeignKey('manufacturers.id'))
    manufacturer = relationship("Manufacturer", back_populates="products")

    variants = relationship("ProductVariant", back_populates="product")


#Таблица характеристика устройства
class ProductVariant(Base):
    __tablename__ = 'product_variants'
    id = Column(Integer, primary_key=True, autoincrement=True)
    color = Column(String)
    memory = Column(Integer)
    price = Column(Float, nullable=False)

    product_id = Column(Integer, ForeignKey('products.id'))
    product = relationship("Product", back_populates="variants")


Base.metadata.create_all(engine)

def show_products(category_id: int, manufacturer_id: int):
    return session.query(Product, ProductVariant)\
        .outerjoin(ProductVariant, Product.id == ProductVariant.product_id)\
        .filter(
        Product.category_id == category_id,
        Product.manufacturer_id == manufacturer_id
    ).all()


def import_from_csv(file_path):
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        #Обработка производителя, если такого производителя нет, то он создается
        for row in reader:
            try:
                category = session.query(Category).filter_by(name=row['category']).first()
                if not category:
                    category = Category(name=row['category'])
                    session.add(category)

                manufacturer = session.query(Manufacturer).filter_by(name=row['manufacturer']).first()
                if not manufacturer:
                    manufacturer = Manufacturer(name=row['manufacturer'])
                    session.add(manufacturer)

                if manufacturer not in category.manufacturers:
                    category.manufacturers.append(manufacturer)

                product = session.query(Product).filter_by(name=row['model'],
                                                           manufacturer=manufacturer,
                                                           category_id=category.id).first()
                if not product:
                    product = Product(name=row['model'], manufacturer=manufacturer, category=category)
                    session.add(product)

                variant = session.query(ProductVariant).filter_by(
                    product_id=product.id,
                    color=row['color'],
                    memory=int(row['memory']) if row['memory'] else None
                ).first()

                if not variant:
                    variant = ProductVariant(
                        color=row['color'],
                        memory=int(row['memory']) if row['memory'] else None,
                        price=float(row['price']),
                        product=product
                    )
                    session.add(variant)
                session.commit()
            except Exception as e:
                print(e)
                session.rollback()
                continue
    print('Импорт данных завершен')

select(Category)
import_from_csv('devices.csv')
