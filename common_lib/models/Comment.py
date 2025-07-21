from enum import Enum
from typing import List, TYPE_CHECKING
from uuid import UUID, uuid4
from pydantic import ConfigDict
from sqlmodel import Field, Relationship, SQLModel
from .basemodels import CommentBase

if TYPE_CHECKING:
    from .User import User
    from .Product import Product


class ModerationStatus(str, Enum):
    NOT_CHECKED = "not_checked"
    APPROVED = "approved"
    REJECTED = "rejected"


class Comment(CommentBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    moderation_status: ModerationStatus = Field(
        default=ModerationStatus.NOT_CHECKED,
        index=True
    )

    user_id: UUID = Field(foreign_key="user.id", index=True)
    product_id: UUID = Field(foreign_key="product.id", index=True)

    user: "User" = Relationship(back_populates="comments")
    product: "Product" = Relationship(back_populates="comments")


class CommentCreate(CommentBase):
    product_id: UUID


class CommentOut(CommentBase):
    id: UUID
    user_id: UUID
    product_id: UUID
    moderation_status: ModerationStatus

    model_config = ConfigDict(from_attributes=True)


class CommentUpdateModeration(SQLModel):
    moderation_status: ModerationStatus
