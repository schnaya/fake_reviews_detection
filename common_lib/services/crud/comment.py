# services/crud_comment.py
import json
import logging
import os
from datetime import datetime
from uuid import UUID
from typing import Optional

import pika
from pika.exceptions import ProbableAuthenticationError
from sqlmodel import Session

from common_lib.models.Comment import Comment, CommentCreate, CommentUpdateModeration
from common_lib.models.User import User

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
    comment_service = CommentService()
    comment_service.publish_moderation_task(comment_id=str(db_comment.id), text=comment_in.text, user_id=str(author.id))
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


class CommentService:
    def __init__(self):
        self.rabbitmq_config = {
            'host': os.getenv('RABBITMQ_HOST', 'localhost'),
            'port': int(os.getenv('RABBITMQ_PORT', 5672)),
            'user': os.getenv('RABBITMQ_USER', 'guest'),
            'password': os.getenv('RABBITMQ_PASS', 'guest'),
            'vhost': os.getenv('RABBITMQ_VHOST', '/'),
            'queue': os.getenv('QUEUE_NAME', 'ml_task_queue')
        }

    def publish_moderation_task(self, comment_id: str, text: str, user_id: str):
        """
        Публикация задачи модерации с правильной аутентификацией
        """
        connection = None

        try:
            credentials = pika.PlainCredentials(
                self.rabbitmq_config['user'],
                self.rabbitmq_config['password']
            )
            connection_params = pika.ConnectionParameters(
                host=self.rabbitmq_config['host'],
                port=self.rabbitmq_config['port'],
                virtual_host=self.rabbitmq_config['vhost'],
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )

            connection = pika.BlockingConnection(connection_params)
            channel = connection.channel()

            channel.queue_declare(
                queue=self.rabbitmq_config['queue'],
                durable=True
            )

            message = {
                'task_id': comment_id,
                'task_type': 'text_classification',
                'text': text,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat()
            }

            channel.basic_publish(
                exchange='',
                routing_key=self.rabbitmq_config['queue'],
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Устойчивость к перезагрузке
                    content_type='application/json'
                )
            )

            logger.info(f"Задача модерации отправлена для комментария {comment_id}")

        except pika.exceptions.ProbableAuthenticationError as e:
            logger.error(f"Ошибка аутентификации RabbitMQ: {e}")
            logger.error(f"Проверьте переменные окружения:")
            logger.error(f"  RABBITMQ_HOST: {self.rabbitmq_config['host']}")
            logger.error(f"  RABBITMQ_USER: {self.rabbitmq_config['user']}")
            logger.error(f"  RABBITMQ_PASSWORD: {'*' * len(self.rabbitmq_config['password'])}")
            raise
        except Exception as e:
            logger.error(f"Ошибка отправки в RabbitMQ: {e}")
            raise
        finally:
            if connection and not connection.is_closed:
                connection.close()