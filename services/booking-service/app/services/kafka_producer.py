import json
from aiokafka import AIOKafkaProducer

from shared.core.config import KAFKA_BOOTSTRAP_SERVERS, BOOKING_EVENTS_TOPIC

producer: AIOKafkaProducer | None = None


async def start_kafka_producer() -> None:
    global producer
    if producer is not None:
        return

    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await producer.start()


async def stop_kafka_producer() -> None:
    global producer
    if producer is not None:
        await producer.stop()
        producer = None


async def publish_booking_event(event: dict) -> None:
    if producer is None:
        return

    await producer.send_and_wait(BOOKING_EVENTS_TOPIC, event)