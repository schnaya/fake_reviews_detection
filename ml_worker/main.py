import json
import logging
import os
import uuid
from typing import Dict, Any

import pika
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from common_lib.database.config import get_settings
from tasks import MLModel

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# RabbitMQ настройки
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.environ.get('RABBITMQ_USER', 'user')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS', 'password')
RABBITMQ_VHOST = os.environ.get('RABBITMQ_VHOST', '/')
QUEUE_NAME = os.environ.get('QUEUE_NAME', 'ml_task_queue')

engine = create_engine(
    url=get_settings().DATABASE_URL_psycopg,
    echo=False,
    pool_size=5,
    max_overflow=10
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)

connection_params = pika.ConnectionParameters(
    host=RABBITMQ_HOST,
    port=RABBITMQ_PORT,
    virtual_host=RABBITMQ_VHOST,
    credentials=pika.PlainCredentials(
        username=RABBITMQ_USER,
        password=RABBITMQ_PASS
    ),
    heartbeat=30,
    blocked_connection_timeout=2
)

connection = pika.BlockingConnection(connection_params)
channel = connection.channel()
queue_name = QUEUE_NAME
channel.queue_declare(queue=queue_name, durable=True)

ml_model = MLModel()


def process_text_classification_task(task_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Обрабатывает задачу классификации текста
    """
    text_to_analyze = task_data.get('text', '')
    user_id = task_data.get('user_id')

    if not text_to_analyze:
        raise ValueError("Текст для анализа не предоставлен")

    prediction_result = ml_model.predict_label(text_to_analyze)

    result = {
        'text': text_to_analyze[:200] + '...' if len(text_to_analyze) > 200 else text_to_analyze,
        'prediction': prediction_result,
        'user_id': str(user_id) if user_id else None,
        'processed_at': str(uuid.uuid4())
    }

    return result


def callback(ch, method, properties, body):
    """
    Callback функция для обработки сообщений из RabbitMQ
    """
    logger.info(f"Получено сообщение, delivery_tag: {method.delivery_tag}")
    db: Session = SessionLocal()
    task_id_str = None
    task_id = None

    try:

        message_data = json.loads(body.decode('utf-8'))
        task_id_str = message_data.get("task_id")
        task_type = message_data.get("task_type", "text_classification")

        logger.info(f"Обработка задачи {task_id_str} типа {task_type}")

        if task_id_str:
            task_id = uuid.UUID(task_id_str)

        if task_type == "text_classification":
            result = process_text_classification_task(message_data, db)
            logger.info(f"Задача {task_id_str} успешно обработана")
            logger.info(f"Результат: {result['prediction']}")

        else:
            raise ValueError(f"Неизвестный тип задачи: {task_type}")

        # Здесь можно сохранить результат в БД
        # update_task_result(db, task_id, result)

        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"Задача {task_id_str} завершена успешно")

    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except ValueError as e:
        logger.error(f"Ошибка валидации данных задачи {task_id_str}: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except Exception as e:
        logger.error(f"Критическая ошибка при обработке задачи {task_id_str}: {e}", exc_info=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    finally:
        db.close()


channel.basic_qos(prefetch_count=1)
channel.basic_consume(
    queue=queue_name,
    on_message_callback=callback,
    auto_ack=False
)

logger.info('Ожидание сообщений. Для выхода нажмите Ctrl+C')

try:
    channel.start_consuming()
except KeyboardInterrupt:
    logger.info('Получен сигнал прерывания. Остановка...')
    channel.stop_consuming()
    connection.close()