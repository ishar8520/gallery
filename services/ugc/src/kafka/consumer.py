import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer

from src.core.config import settings
from src.services.ugc import UGCService

logger = logging.getLogger(__name__)

UGC_TOPIC = 'ugc-events'


async def consume_ugc_events() -> None:
    consumer = AIOKafkaConsumer(
        UGC_TOPIC,
        bootstrap_servers=settings.kafka.bootstrap_servers,
        group_id=settings.kafka.group_id,
        auto_offset_reset='earliest',
        value_deserializer=lambda v: json.loads(v.decode()),
    )
    await consumer.start()
    logger.info('UGC Kafka consumer started, topic=%s', UGC_TOPIC)
    try:
        async for msg in consumer:
            try:
                _handle(msg.value, UGCService())
            except Exception:
                logger.exception('Failed to handle ugc event: %s', msg.value)
    finally:
        await consumer.stop()
        logger.info('UGC Kafka consumer stopped')


def _handle(event: dict, svc: UGCService) -> None:
    event_type = event.get('event_type')
    payload = event.get('payload', {})
    timestamp = event.get('timestamp', '')

    if event_type == 'photo_uploaded':
        svc.record_photo_event(
            event_type='photo_uploaded',
            user_id=payload.get('user_id', ''),
            photo_id=payload.get('photo_id', ''),
            title=payload.get('title', ''),
            timestamp=timestamp,
        )
    elif event_type == 'photo_deleted':
        svc.record_photo_event(
            event_type='photo_deleted',
            user_id=payload.get('user_id', ''),
            photo_id=payload.get('photo_id', ''),
            title='',
            timestamp=timestamp,
        )
    elif event_type == 'user_logged_in':
        svc.record_auth_event(
            user_id=payload.get('user_id', ''),
            provider=payload.get('provider', 'unknown'),
            timestamp=timestamp,
        )
    else:
        logger.debug('Unknown ugc event type: %s', event_type)


async def run_consumer_forever() -> None:
    while True:
        try:
            await consume_ugc_events()
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception('UGC consumer crashed, restarting in 5s')
            await asyncio.sleep(5)
