import logging
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select

from common_lib.models import Product, ProductCreate


def get_product(session: Session, product_id: UUID) -> Optional[Product]:
    """Получить продукт по его ID из базы данных."""
    return session.get(Product, product_id)


def get_products(session: Session, skip: int = 0, limit: int = 10) -> List[Product]:
    """Получить список продуктов с пагинацией из базы данных."""
    statement = select(Product).offset(skip).limit(limit)
    return session.exec(statement).all()


def create_product(session: Session, product_in: ProductCreate) -> Product:
    """Создать новый продукт в базе данных."""
    # model_validate преобразует ProductCreate в Product
    db_product = Product.model_validate(product_in)

    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product


def update_product(
        session: Session, product_id: UUID, product_in: Product
) -> Optional[Product]:
    """Обновить продукт в базе данных."""
    db_product = session.get(Product, product_id)
    if not db_product:
        return None

    # Получаем данные из product_in, исключая те, что не были переданы (None)
    product_data = product_in.model_dump(exclude_unset=True)

    # Обновляем поля модели
    for key, value in product_data.items():
        setattr(db_product, key, value)

    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product


def delete_product(session: Session, product_id: UUID) -> Optional[Product]:
    """Удалить продукт из базы данных."""
    product = session.get(Product, product_id)
    if not product:
        return None

    session.delete(product)
    session.commit()
    return product


def ensure_products(session: Session):
    """Проверяет, есть ли продукты в БД, и если нет, создает тестовые."""
    # Проверяем, есть ли хотя бы один продукт
    existing_product = session.exec(select(Product)).first()
    if existing_product:
        logging.info("Тестовые продукты уже существуют. Создание пропущено.")
        return

    logging.info("Создание тестовых продуктов...")
    products_to_create = [
        ProductCreate(name="Ноутбук 'Pro'", description="Мощный ноутбук для профессионалов", price=Decimal("1500.99")),
        ProductCreate(name="Смартфон 'Max'", description="Телефон с большим экраном и камерой",
                      price=Decimal("999.50")),
        ProductCreate(name="Беспроводные наушники", description="Кристально чистый звук без проводов",
                      price=Decimal("199.00")),
    ]

    for product_data in products_to_create:
        create_product(session=session, product_in=product_data)

    logging.info("Тестовые продукты успешно созданы.")
