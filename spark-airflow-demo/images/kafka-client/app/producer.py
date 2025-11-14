from kafka import KafkaProducer
from loguru import logger
import json, time, sys

logger.info("Starting Kafka producer...")

producer = KafkaProducer(
    bootstrap_servers="kafka:29092",
    retries=5,
    acks="all",
    value_serializer=lambda x: json.dumps(x).encode("utf-8")
)

while True:
    msg = {"timestamp": time.time()}
    producer.send("demo-topic", msg)
    logger.info(f"Sent: {msg}")
    producer.flush()
    time.sleep(1)