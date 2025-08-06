from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from common_lib.models.Comment import CommentCreate, CommentOut, Comment, CommentUpdateModeration
from common_lib.services.crud import comment
from common_lib.database.database import get_session


from common_lib.services.auth.auth_service import get_current_active_user, require_role
from common_lib.models.User import User, RoleEnum
from common_lib.services.crud.comment import moderate_comment

comment_router = APIRouter(
)


@comment_router.post(
    "/",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Оставить комментарий к продукту"
)
def create_new_comment(
        comment_in: CommentCreate,
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
):
    return comment.create_comment(
        session=session,
        comment_in=comment_in,
        author=current_user
    )


@comment_router.delete(
    "/{comment_id}",
    response_model=CommentOut,
    summary="Удалить комментарий"
)
def delete_existing_comment(
        comment_id: UUID,
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
):
    comment_to_delete = comment.get_comment(session=session, comment_id=comment_id)

    if not comment_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Комментарий с ID {comment_id} не найден."
        )

    is_author = comment_to_delete.user_id == current_user.id
    is_admin = current_user.role == RoleEnum.ADMIN

    if not is_author and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления этого комментария."
        )

    deleted_comment = comment.delete_comment(session=session, comment_id=comment_id)
    return deleted_comment


@comment_router.put(
    "/{comment_id}/moderate",
    response_model=CommentOut,
    summary="Изменить статус модерации комментария (фейк/не фейк)",
    dependencies=[Depends(require_role(RoleEnum.ADMIN))]
)
def update_comment_moderation_status(
    comment_id: UUID,
    moderation_in: CommentUpdateModeration,
    session: Session = Depends(get_session)
):
    moderated_comment = moderate_comment(
        session=session,
        comment_id=comment_id,
        moderation_in=moderation_in
    )
    if not moderated_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Комментарий с ID {comment_id} не найден."
        )
    return moderated_comment
