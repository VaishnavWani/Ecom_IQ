import os
from dotenv import load_dotenv

load_dotenv()

# Kafka broker address (defaults to localhost:9092 for local testing)
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")