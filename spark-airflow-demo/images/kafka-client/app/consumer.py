from kafka import KafkaConsumer
import json
from loguru import logger

consumer = KafkaConsumer(
    "demo-topic",
    bootstrap_servers="kafka:29092",
    auto_offset_reset="latest",
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)

logger.info("Consumer started")

for msg in consumer:
    logger.info(f"Received: {msg.value}")