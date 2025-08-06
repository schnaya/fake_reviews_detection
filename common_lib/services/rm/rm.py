import asyncio
from typing import Dict, Any, Optional

import aio_pika
import pika
import logging
import json
from common_lib.database.config import get_settings
from fastapi import HTTPException

logger = logging.getLogger(__name__)
settings = get_settings()

connection: Optional[aio_pika.RobustConnection] = None
channel: Optional[aio_pika.Channel] = None
QUEUE_NAME: str = settings.QUEUE_NAME


connection_params = pika.ConnectionParameters(
    host='rabbitmq',
    port=5672,
    virtual_host='/',
    credentials=pika.PlainCredentials(
        username='rmuser',
        password='rmpassword'
    ),
    heartbeat=30,
    blocked_connection_timeout=2
)


async def connect_rabbitmq():
    global connection, channel
    loop = asyncio.get_event_loop()
    vhost = settings.RABBITMQ_VHOST if settings.RABBITMQ_VHOST.startswith('/') else f'/{settings.RABBITMQ_VHOST}'
    rabbitmq_url = (
        f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASS}@"
        f"{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}{vhost}"
    )
    logger.info(f"Connecting to RabbitMQ at {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}{vhost}...")

    try:
        connection = await aio_pika.connect_robust(rabbitmq_url, loop=loop)
        channel = await connection.channel()
        await channel.declare_queue(QUEUE_NAME, durable=True)

        logger.info(f"RabbitMQ connection and channel established. Queue '{QUEUE_NAME}' declared.")

    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ or declare queue: {e}", exc_info=True)
        raise


async def close_rabbitmq():
    global connection
    if connection:
        logger.info("Closing RabbitMQ connection.")
        await connection.close()


async def get_rabbitmq_channel() -> aio_pika.Channel:

    global channel
    if channel is None or channel.is_closed:
        logger.error("Attempted to get RabbitMQ channel, but it's None or closed.")
    logger.debug(f"Providing RabbitMQ channel: {channel}")
    return channel


async def publish_message(channel: aio_pika.Channel, routing_key: str, message_body: Dict[str, Any]):
    try:
        message = aio_pika.Message(
            body=json.dumps(message_body).encode('utf-8'),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        await channel.default_exchange.publish(
            message,
            routing_key=routing_key
        )
        logger.info(f"Message published to queue '{routing_key}': {message_body.get('task_id')}")
    except Exception as e:
        task_id = message_body.get("task_id", "N/A")
        logger.error(f"Failed to publish message for task {task_id}: {e}", exc_info=True)
        raise