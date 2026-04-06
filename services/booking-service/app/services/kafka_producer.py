import asyncio
import json

from aiokafka import AIOKafkaProducer

from shared.core.config import KAFKA_BOOTSTRAP_SERVERS, BOOKING_EVENTS_TOPIC

producer: AIOKafkaProducer | None = None


async def start_kafka_producer(retries: int = 30, delay: int = 2) -> None:
    global producer

    if producer is not None:
        return

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await producer.start()
            print(f"Kafka producer connected on attempt {attempt}")
            return
        except Exception as exc:
            last_error = exc
            print(f"Kafka producer connection failed on attempt {attempt}/{retries}: {exc}")

            if producer is not None:
                try:
                    await producer.stop()
                except Exception:
                    pass
                producer = None

            await asyncio.sleep(delay)

    raise last_error


async def stop_kafka_producer() -> None:
    global producer

    if producer is not None:
        try:
            await producer.stop()
        finally:
            producer = None


async def publish_booking_event(event: dict) -> None:
    global producer

    if producer is None:
        try:
            await start_kafka_producer(retries=5, delay=2)
        except Exception as exc:
            print(f"Kafka producer could not connect before publish: {exc}")
            return

    try:
        await producer.send_and_wait(BOOKING_EVENTS_TOPIC, event)
    except Exception as exc:
        print(f"Kafka publish failed: {exc}")