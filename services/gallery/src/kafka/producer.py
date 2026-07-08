import json

from aiokafka import AIOKafkaProducer
from fastapi import Request

from src.core.config import settings


async def create_producer() -> AIOKafkaProducer:
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka.bootstrap_servers,
        value_serializer=lambda v: json.dumps(v, default=str).encode(),
    )
    await producer.start()
    return producer


def get_kafka_producer(request: Request) -> AIOKafkaProducer:
    return request.app.state.kafka_producer
