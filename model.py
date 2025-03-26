import csv
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import os
from dotenv import load_dotenv

Base = declarative_base()

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
session = Session()

#Таблица Производитель
class Manufacturer(Base):
    __tablename__ = 'manufacturers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    products = relationship("Product", back_populates="manufacturer")

#Таблица Категория
class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    parent_id = Column(Integer, ForeignKey('categories.id'))
    products = relationship("Product", back_populates="category")

#Таблица Устройство
class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, autoincrement=True)
    model = Column(String, nullable=False)

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

def import_from_csv(file_path):
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        #Обработка производителя, если такого производителя нет, то он создается
        for row in reader:
            manufacturer = session.query(Manufacturer).filter_by(name=row['manufacturer']).first()

            if not manufacturer:
                manufacturer = Manufacturer(name=row['manufacturer'])
                session.add(manufacturer)
                session.commit()

            parent_category = None
            if row['parent_category']:
                parent_category = session.query(Category).filter_by(name=row['parent_category']).first()
                if not parent_category:
                    parent_category = Category(name=row['parent_category'])
                    session.add(parent_category)
                    session.commit()

            category = session.query(Category).filter_by(name=row['category']).first()
            if not category:
                category = Category(name=row['category'], parent_id=parent_category.id if parent_category else None)
                session.add(category)
                session.commit()

            product = session.query(Product).filter_by(model=row['model'],
                                                       manufacturer_id=manufacturer.id,
                                                       category_id=category.id).first()
            if not product:
                product = Product(model=row['model'], manufacturer=manufacturer, category=category)
                session.add(product)
                session.commit()

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
    print('Импорт данных завершен')

#import_from_csv('devices.csv')
