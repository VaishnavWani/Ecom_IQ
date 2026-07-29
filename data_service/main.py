import time
import logging
from producer import KafkaStreamProducer
from generator import EcomIqDataGenerator

logger = logging.getLogger("ECOM-IQ-RUNNER")

if __name__ == "__main__":
    producer = KafkaStreamProducer()
    generator = EcomIqDataGenerator(producer)

    logger.info("1. Seeding 7 Dimension topics...")
    generator.seed_dimensions()

    logger.info("2. Streaming 7 Fact topics (Press Ctrl+C to stop)...")
    try:
        while True:
            for _ in range(5):
                generator.generate_order_flow()
            for _ in range(2):
                generator.generate_inventory_event()
            
            producer.flush()
            logger.info("Pushed micro-batch of events to Kafka topics...")
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping generator...")
    finally:
        producer.close()