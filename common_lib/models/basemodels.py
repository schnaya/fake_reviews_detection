from typing import Optional

from pydantic import EmailStr
from sqlmodel import SQLModel, Field


class UserBase(SQLModel):
    name: str = Field(index=True)
    email: EmailStr = Field(unique=True, index=True)


class ProductBase(SQLModel):
    name: str = Field(index=True)
    description: Optional[str] = None
    price: float


class CommentBase(SQLModel):
    text: str
    rating: int = Field(ge=1, le=5)
