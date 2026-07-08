import json
import logging

from aiokafka import AIOKafkaConsumer

from src.core.config import settings
from src.services.mail import MailService

logger = logging.getLogger(__name__)

MAIL_TOPIC = 'mail-events'


async def handle_event(event: dict, mail_service: MailService) -> None:
    event_type = event.get('event_type')
    if event_type == 'user_registered':
        payload = event['payload']
        await mail_service.send_welcome_email(
            to=payload['email'],
            username=payload['username'],
        )
    else:
        logger.warning('Unknown event type: %s', event_type)


async def start_consumer(mail_service: MailService) -> None:
    consumer = AIOKafkaConsumer(
        MAIL_TOPIC,
        bootstrap_servers=settings.kafka.bootstrap_servers,
        group_id=settings.kafka.group_id,
        value_deserializer=lambda m: json.loads(m.decode()),
        auto_offset_reset='earliest',
    )
    await consumer.start()
    logger.info('Kafka consumer started, listening to %s', MAIL_TOPIC)
    try:
        async for msg in consumer:
            try:
                await handle_event(msg.value, mail_service)
            except Exception:
                logger.exception('Failed to handle event: %s', msg.value)
    finally:
        await consumer.stop()
        logger.info('Kafka consumer stopped')
