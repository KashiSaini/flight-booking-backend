import asyncio
import json
from datetime import datetime, timezone

from aiokafka import AIOKafkaConsumer

from shared.core.config import BOOKING_EVENTS_TOPIC, KAFKA_BOOTSTRAP_SERVERS
from shared.db.mongo import mongo_db

consumer_task: asyncio.Task | None = None


async def consume_booking_events() -> None:
    consumer = AIOKafkaConsumer(
        BOOKING_EVENTS_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="admin-service-group",
        auto_offset_reset="latest",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    await consumer.start()
    try:
        async for msg in consumer:
            event = msg.value

            await mongo_db.booking_events.insert_one(
                {
                    "kafka_topic": msg.topic,
                    "kafka_partition": msg.partition,
                    "kafka_offset": msg.offset,
                    "received_at": datetime.now(timezone.utc),
                    "event": event,
                }
            )
    except asyncio.CancelledError:
        raise
    finally:
        await consumer.stop()


async def start_kafka_consumer() -> None:
    global consumer_task
    if consumer_task is None:
        consumer_task = asyncio.create_task(consume_booking_events())


async def stop_kafka_consumer() -> None:
    global consumer_task
    if consumer_task is None:
        return

    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass
    consumer_task = None