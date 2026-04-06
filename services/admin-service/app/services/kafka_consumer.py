import asyncio
import json
from datetime import datetime, timezone

from aiokafka import AIOKafkaConsumer, TopicPartition

from shared.core.config import BOOKING_EVENTS_TOPIC, KAFKA_BOOTSTRAP_SERVERS
from shared.db.mongo import mongo_db

consumer_task: asyncio.Task | None = None


async def consume_booking_events_forever() -> None:
    while True:
        consumer = None
        try:
            consumer = AIOKafkaConsumer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                metadata_max_age_ms=3000,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            )

            await consumer.start()
            print("Kafka consumer started")

            partitions = None
            while not partitions:
                partitions = consumer.partitions_for_topic(BOOKING_EVENTS_TOPIC)
                if not partitions:
                    print(f"Waiting for topic metadata: {BOOKING_EVENTS_TOPIC}")
                    await asyncio.sleep(2)

            topic_partitions = [
                TopicPartition(BOOKING_EVENTS_TOPIC, partition)
                for partition in sorted(partitions)
            ]
            consumer.assign(topic_partitions)
            print(f"Kafka consumer assigned partitions: {topic_partitions}")

            while True:
                records = await consumer.getmany(timeout_ms=1000)

                for tp, messages in records.items():
                    for msg in messages:
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
            if consumer is not None:
                try:
                    await consumer.stop()
                except Exception:
                    pass
            raise

        except Exception as exc:
            print(f"Kafka consumer loop failed, retrying in 2s: {exc}")
            await asyncio.sleep(2)

        finally:
            if consumer is not None:
                try:
                    await consumer.stop()
                except Exception:
                    pass


async def start_kafka_consumer() -> None:
    global consumer_task
    if consumer_task is None:
        consumer_task = asyncio.create_task(consume_booking_events_forever())


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