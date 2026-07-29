import os
import logging

# Hadoop path override — only needed for local Windows dev, ignored in Docker
if os.getenv("HADOOP_HOME"):
    os.environ["PATH"] += os.pathsep + os.path.join(os.environ["HADOOP_HOME"], "bin")
os.environ["JAVA_TOOL_OPTIONS"] = "-Duser.timezone=UTC"

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("EcomIq-Consumer")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092")
JDBC_URL = os.getenv("JDBC_URL", "jdbc:postgresql://127.0.0.1:5432/postgres")
JDBC_USER = os.getenv("JDBC_USER", "postgres")
JDBC_PASSWORD = os.getenv("JDBC_PASSWORD")
JDBC_DRIVER = "org.postgresql.Driver"


def create_spark_session():
    spark = SparkSession.builder \
        .appName("EcomIqStableConsumer") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.postgresql:postgresql:42.6.0") \
        .config("spark.sql.shuffle.partitions", "2") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")
    return spark


def consume_topic_to_postgres(spark, topic_name, table_name, schema):
    """Reads a Kafka topic and writes each micro-batch to PostgreSQL via foreachBatch."""
    logger.info(f"Starting stream: [{topic_name}] -> PostgreSQL table [{table_name}]")

    raw_stream = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", topic_name) \
        .option("startingOffsets", "earliest") \
        .load()

    parsed_stream = raw_stream \
        .selectExpr("CAST(value AS STRING)") \
        .select(from_json(col("value"), schema).alias("data")) \
        .select("data.*")

    def write_batch_to_postgres(batch_df, batch_id):
        if batch_df.isEmpty():
            return
        batch_df.write \
            .format("jdbc") \
            .mode("append") \
            .option("url", JDBC_URL) \
            .option("dbtable", table_name) \
            .option("user", JDBC_USER) \
            .option("password", JDBC_PASSWORD) \
            .option("driver", JDBC_DRIVER) \
            .save()

    # foreachBatch: Spark has no native streaming JDBC sink, so each
    # micro-batch is written using the regular batch JDBC writer.
    query = parsed_stream.writeStream \
        .foreachBatch(write_batch_to_postgres) \
        .option("checkpointLocation", f"/tmp/checkpoints/{table_name}") \
        .trigger(processingTime="5 seconds") \
        .start()

    return query


if __name__ == "__main__":
    spark_session = create_spark_session()

    # ---------------------------------------------------------------
    # Schemas: 7 dimension tables + 7 fact tables = 14 total
    # ---------------------------------------------------------------
    schemas = {
        # --- Dimensions ---
        "dim_regions": StructType([
            StructField("region_id", StringType(), True),
            StructField("region_name", StringType(), True),
            StructField("country", StringType(), True),
        ]),
        "dim_categories": StructType([
            StructField("category_id", StringType(), True),
            StructField("category_name", StringType(), True),
        ]),
        "dim_skus": StructType([
            StructField("sku_id", StringType(), True),
            StructField("category_id", StringType(), True),
            StructField("baseline_price", DoubleType(), True),
        ]),
        "dim_customer_addresses": StructType([
            StructField("address_id", StringType(), True),
            StructField("city", StringType(), True),
            StructField("region_id", StringType(), True),
        ]),
        "dim_customers": StructType([
            StructField("customer_id", StringType(), True),
            StructField("address_id", StringType(), True),
            StructField("registration_date", StringType(), True),
        ]),
        "dim_warehouses": StructType([
            StructField("warehouse_id", StringType(), True),
            StructField("region_id", StringType(), True),
        ]),
        "dim_payment_methods": StructType([
            StructField("method_id", StringType(), True),
            StructField("method_name", StringType(), True),
        ]),
        # --- Facts ---
        "fact_order_headers": StructType([
            StructField("order_id", StringType(), True),
            StructField("customer_id", StringType(), True),
            StructField("total_order_value", DoubleType(), True),
            StructField("event_timestamp", StringType(), True),
        ]),
        "fact_order_lines": StructType([
            StructField("line_id", StringType(), True),
            StructField("order_id", StringType(), True),
            StructField("sku_id", StringType(), True),
            StructField("warehouse_id", StringType(), True),
            StructField("quantity", IntegerType(), True),
            StructField("line_value", DoubleType(), True),
        ]),
        "fact_payments": StructType([
            StructField("payment_id", StringType(), True),
            StructField("order_id", StringType(), True),
            StructField("method_id", StringType(), True),
            StructField("amount", DoubleType(), True),
            StructField("payment_status", StringType(), True),
            StructField("failure_reason", StringType(), True),
            StructField("event_timestamp", StringType(), True),
        ]),
        "fact_shipments": StructType([
            StructField("shipment_id", StringType(), True),
            StructField("order_id", StringType(), True),
            StructField("courier_name", StringType(), True),
            StructField("event_type", StringType(), True),
            StructField("event_timestamp", StringType(), True),
        ]),
        "fact_returns": StructType([
            StructField("return_id", StringType(), True),
            StructField("line_id", StringType(), True),
            StructField("return_reason", StringType(), True),
            StructField("return_status", StringType(), True),
            StructField("event_timestamp", StringType(), True),
        ]),
        "fact_inventory_transactions": StructType([
            StructField("transaction_id", StringType(), True),
            StructField("sku_id", StringType(), True),
            StructField("warehouse_id", StringType(), True),
            StructField("event_type", StringType(), True),
            StructField("quantity_change", IntegerType(), True),
            StructField("event_timestamp", StringType(), True),
        ]),
        "fact_user_clickstream": StructType([
            StructField("event_id", StringType(), True),
            StructField("customer_id", StringType(), True),
            StructField("sku_id", StringType(), True),
            StructField("device_type", StringType(), True),
            StructField("event_type", StringType(), True),
            StructField("event_timestamp", StringType(), True),
        ]),
    }

    # table_name -> topic_name (matches producer's self.producer.send(...) calls)
    table_to_topic = {table: f"topic_{table}" for table in schemas}

    queries = []
    for table_name, schema in schemas.items():
        topic_name = table_to_topic[table_name]
        q = consume_topic_to_postgres(spark_session, topic_name, table_name, schema)
        queries.append(q)

    logger.info(f"All {len(queries)} streams started. Awaiting termination...")
    spark_session.streams.awaitAnyTermination()