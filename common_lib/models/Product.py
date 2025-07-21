from typing import List, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship
from .basemodels import ProductBase
from .Comment import CommentOut

if TYPE_CHECKING:
    from .Comment import Comment


class Product(ProductBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Связь "один ко многим": один продукт -> много комментариев
    comments: List["Comment"] = Relationship(back_populates="product")


class ProductCreate(ProductBase):
    pass


class ProductOut(ProductBase):
    id: UUID


class ProductOutWithComments(ProductOut):
    comments: List[CommentOut] = []
