from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session

from common_lib.database.database import get_session
from common_lib.models.Product import Product, ProductCreate, ProductOutWithComments
from common_lib.services.crud.product import get_products, get_product, delete_product, create_product

product_router = APIRouter()


@product_router.post(
    "/",
    response_model=Product,
    status_code=status.HTTP_201_CREATED
)
def create_new_product(
    product_in: ProductCreate,
    session: Session = Depends(get_session)
):
    return create_product(session=session, product_in=product_in)

@product_router.get("/", response_model=List[Product])
def get_all_products(
    skip: int = 0, limit: int = 10, session: Session = Depends(get_session)
):
    return get_products(session=session, skip=skip, limit=limit)


@product_router.get("/{product_id}", response_model=Product)
def get_product_by_id(product_id: UUID, session: Session = Depends(get_session)):
    product = get_product(session=session, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Продукт с ID {product_id} не найден"
        )
    return product


@product_router.delete("/{product_id}", response_model=Product)
def delete_existing_product(product_id: UUID, session: Session = Depends(get_session)):
    deleted_product = delete_product(session=session, product_id=product_id)
    if not deleted_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Продукт с ID {product_id} не найден для удаления"
        )
    return deleted_product


@product_router.get(
    "/{product_id}/with-comments",
    response_model=ProductOutWithComments,
    summary="Получить продукт с комментариями"
)
def get_product_with_comments(product_id: UUID, session: Session = Depends(get_session)):
    """
    Получает информацию о продукте и список всех его комментариев.
    """
    # SQLModel автоматически подгрузит связанные комментарии,
    # так как в модели Product есть `Relationship`.
    product = get_product(session=session, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Продукт с ID {product_id} не найден"
        )
    return product