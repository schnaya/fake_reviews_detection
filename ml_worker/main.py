import json
import uuid

import pika
import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from common_lib.database.config import get_settings

from common_lib.models import User
from common_lib.data import PreprocessingPipelineBuilder
from tasks import PredictionTask, MLModel

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.environ.get('RABBITMQ_USER', 'user')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS', 'password')
RABBITMQ_VHOST = os.environ.get('RABBITMQ_VHOST', '/')
QUEUE_NAME = os.environ.get('QUEUE_NAME', 'ml_task_queue')

engine = create_engine(url=get_settings().DATABASE_URL_psycopg,
                       echo=False, pool_size=5, max_overflow=10)
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
queue_name = 'ml_task_queue'
channel.queue_declare(queue=queue_name, durable=True)
preprocessing_pipeline = PreprocessingPipelineBuilder.build()
ml_model = MLModel(model_path="model.pkl", pipeline=preprocessing_pipeline)

def callback(ch, method, properties, body):
    pass
'''
def callback(ch, method, properties, body):
    logger.info(f"Получено сообщение, delivery_tag: {method.delivery_tag}")
    db: Session = SessionLocal()
    task_id_str = None
    task_id = None

    try:
        message_data = json.loads(body.decode('utf-8'))
        task_id_str = message_data.get("task_id")
        user_id_str = message_data.get("user_id")


        task_id = uuid.UUID(task_id_str)
        user_id = uuid.UUID(user_id_str)
        logger.info(f"Parsed message: {body}")

        record = get_prediction_by_task_id(db, task_id)
        if not record:
             logger.error(f"Задача {task_id}: PredictionRecord не найден в БД. Сообщение будет удалено.")
             ch.basic_ack(delivery_tag=method.delivery_tag)
             return

        if record.status != PredictionStatus.QUEUED:
             logger.warning(f"Задача {task_id}: Обнаружен статус '{record.status}', ожидался 'QUEUED'. Сообщение будет удалено.")
             ch.basic_ack(delivery_tag=method.delivery_tag)
             return
        logger.info(f"Задача {task_id}: Установка статуса PROCESSING.")
        update_prediction_result(session=db, task_id=task_id, new_status=PredictionStatus.PROCESSING)
        logger.info(f"Задача {task_id}: Загрузка данных User {user_id} и House {house_id}.")
        user = db.query(User).filter(User.id == user_id).first()
        house = db.query(House).filter(House.id == house_id).first()

        if not user or not house:
            raise ValueError(f"User {user_id} или House {house_id} не найдены в БД.")

        logger.info(f"Задача {task_id}: Создание экземпляра PredictionTask.")
        prediction_task = PredictionTask(user=user, house=house, model=ml_model)

        logger.info(f"Задача {task_id}: Запуск prediction_task.execute()...")
        execution_result = prediction_task.execute()
        logger.info(f"Задача {task_id}: prediction_task.execute() завершен.")
        if isinstance(execution_result, dict):
            logger.info(f"Задача {task_id}: Установка статуса COMPLETED.")
            update_prediction_result(
                session=db,
                task_id=task_id,
                new_status=PredictionStatus.COMPLETED,
                schedule_data=execution_result
            )
            logger.info(f"Задача {task_id}: Успешно обработана. Отправка ACK.")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        elif isinstance(execution_result, str):
            error_message = execution_result
            logger.error(f"Задача {task_id}: Ошибка выполнения execute(): {error_message}")
            update_prediction_result(
                session=db,
                task_id=task_id,
                new_status=PredictionStatus.FAILED,
                error_message=error_message
            )
            logger.warning(f"Задача {task_id}: Статус FAILED установлен из-за ошибки в execute(). Отправка ACK.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            raise TypeError(f"Метод PredictionTask.execute() вернул неожиданный тип данных: {type(execution_result)}")


    except Exception as e:
        logger.error(f"!!! Критическая ошибка при обработке задачи {task_id_str}: {e}", exc_info=True)
        try:
            if task_id:
                logger.info(f"Задача {task_id}: Попытка установить статус FAILED в БД из-за внешней ошибки.")
                update_prediction_result(
                    session=db,
                    task_id=task_id,
                    new_status=PredictionStatus.FAILED,
                    error_message=f"Внешняя ошибка: {type(e).__name__}: {str(e)}"
                )
                logger.info(f"Задача {task_id}: Статус FAILED установлен.")
            else:
                 logger.error(f"Не удалось установить статус FAILED, т.к. task_id не был извлечен из сообщения.")

            logger.warning(f"Задача {task_id_str}: Отправка ACK после критической ошибки, чтобы удалить сообщение из очереди.")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as db_update_err:
             logger.critical(f"!!! КРИТИЧЕСКАЯ ОШИБКА при попытке обновить статус задачи {task_id_str} на FAILED: {db_update_err}", exc_info=True)
             ch.basic_ack(delivery_tag=method.delivery_tag)
'''
channel.basic_consume(
    queue=queue_name,
    on_message_callback=callback,
    auto_ack=False
)

logger.info('Waiting for messages. To exit, press Ctrl+C')
channel.start_consuming()