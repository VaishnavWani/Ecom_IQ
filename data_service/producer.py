import json
import logging
from kafka import KafkaProducer
from config import KAFKA_BOOTSTRAP_SERVERS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("KAFKA-PRODUCER")

class KafkaStreamProducer:
    def __init__(self):
        # Connect to Kafka and setup JSON serializer
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            retries=5
        )
        logger.info(f"Connected to Kafka brokers at: {KAFKA_BOOTSTRAP_SERVERS}")

    def send(self, topic_name: str, payload: dict):
        """Sends a single dictionary message to a specific Kafka topic."""
        self.producer.send(topic_name, value=payload)

    def flush(self):
        """Ensures all buffered messages are sent."""
        self.producer.flush()

    def close(self):
        self.producer.close()
        logger.info("Kafka producer connection closed.")