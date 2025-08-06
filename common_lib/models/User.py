from pydantic import ConfigDict
from uuid import UUID, uuid4
from enum import Enum
from typing import List, Any, TYPE_CHECKING
from sqlmodel import Field, Relationship
from .basemodels import UserBase

if TYPE_CHECKING:
    from .Comment import Comment


class RoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(UserBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    hashed_password: str
    role: RoleEnum = Field(default=RoleEnum.USER)

    comments: List["Comment"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    password: str
    role: RoleEnum = RoleEnum.USER


class UserOut(UserBase):
    id: UUID
    role: RoleEnum

    model_config = ConfigDict(from_attributes=True)
