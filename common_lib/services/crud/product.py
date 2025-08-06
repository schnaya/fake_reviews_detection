import logging
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select

from common_lib.models import Product, ProductCreate


def get_product(session: Session, product_id: UUID) -> Optional[Product]:
    return session.get(Product, product_id)


def get_products(session: Session, skip: int = 0, limit: int = 10) -> List[Product]:
    statement = select(Product).offset(skip).limit(limit)
    return session.exec(statement).all()


def create_product(session: Session, product_in: ProductCreate) -> Product:
    db_product = Product.model_validate(product_in)

    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product


def update_product(
        session: Session, product_id: UUID, product_in: Product
) -> Optional[Product]:
    db_product = session.get(Product, product_id)
    if not db_product:
        return None

    product_data = product_in.model_dump(exclude_unset=True)

    for key, value in product_data.items():
        setattr(db_product, key, value)

    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product


def delete_product(session: Session, product_id: UUID) -> Optional[Product]:
    product = session.get(Product, product_id)
    if not product:
        return None

    session.delete(product)
    session.commit()
    return product


def ensure_products(session: Session):
    existing_product = session.exec(select(Product)).first()
    if existing_product:
        logging.info("Test products already exist. Skipping creation.")
        return

    logging.info("Creating test products...")
    products_to_create = [
        ProductCreate(name="Laptop 'Pro'", description="A powerful laptop for professionals", price=Decimal("1500.99")),
        ProductCreate(name="Smartphone 'Max'", description="A phone with a large screen and camera",
                      price=Decimal("999.50")),
        ProductCreate(name="Wireless Headphones", description="Crystal clear sound without wires",
                      price=Decimal("199.00")),
    ]

    for product_data in products_to_create:
        create_product(session=session, product_in=product_data)

    logging.info("Test products created successfully.")
