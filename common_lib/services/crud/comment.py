# services/crud_comment.py
import json
import logging
from uuid import UUID
from typing import Optional

import pika
from sqlmodel import Session

from common_lib.models.Comment import Comment, CommentCreate, CommentUpdateModeration
from common_lib.models.User import User
RABBITMQ_HOST = 'rabbitmq'
QUEUE_NAME = 'ml_task_queue'

logger = logging.getLogger(__name__)


def get_comment(session: Session, comment_id: UUID) -> Optional[Comment]:
    """Получить комментарий по его ID."""
    return session.get(Comment, comment_id)


def create_comment(
        session: Session,
        comment_in: CommentCreate,
        author: User
) -> Comment:
    db_comment = Comment.model_validate(comment_in, update={"user_id": author.id})

    session.add(db_comment)
    session.commit()
    session.refresh(db_comment)
    publish_moderation_task(comment_id=db_comment.id)
    return db_comment


def delete_comment(session: Session, comment_id: UUID) -> Optional[Comment]:
    comment = session.get(Comment, comment_id)
    if not comment:
        return None

    session.delete(comment)
    session.commit()
    return comment


def moderate_comment(
        session: Session, comment_id: UUID, moderation_in: CommentUpdateModeration
) -> Optional[Comment]:
    """Обновляет статус модерации комментария."""
    comment = session.get(Comment, comment_id)
    if not comment:
        return None

    comment.moderation_status = moderation_in.moderation_status

    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment


def publish_moderation_task(comment_id: UUID):
    """
    Публикует задачу на модерацию комментария в очередь RabbitMQ.
    """
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        message = {
            "task_type": "comment_moderation",
            "comment_id": str(comment_id)
        }

        message_body = json.dumps(message)

        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=message_body,
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        logger.info(f"Задача для модерации комментария {comment_id} успешно отправлена в очередь.")
        connection.close()
    except Exception as e:
        logger.error(f"Не удалось отправить задачу в RabbitMQ для комментария {comment_id}: {e}", exc_info=True)


