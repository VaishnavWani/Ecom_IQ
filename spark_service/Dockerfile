FROM spark:3.5.1-python3

USER root
WORKDIR /app

COPY kafka_consumer.py .

CMD ["/opt/spark/bin/spark-submit", \
     "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.postgresql:postgresql:42.6.0", \
     "kafka_consumer.py"]