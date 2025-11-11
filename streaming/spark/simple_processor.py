"""
Simple Spark Streaming Processor - Test Version
Read from Kafka and print to console (no Delta Lake yet)
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, MapType

# Simple schema for Kafka messages
KAFKA_MESSAGE_SCHEMA = StructType([
    StructField("source", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("data", MapType(StringType(), StringType()), True)
])


def create_spark_session():
    """Create Spark session with Kafka support"""
    return (
        SparkSession.builder
        .appName("AI_Trend_Monitor_Simple")
        .master("spark://spark-master:7077")
        .config("spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0")
        .getOrCreate()
    )


def main():
    """Main streaming pipeline"""
    print("🚀 Starting simple Spark Streaming processor...")

    # Create Spark session
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    print("✅ Spark session created")

    # Read from Kafka
    print("📊 Connecting to Kafka...")

    kafka_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", "kafka:29092")
        .option("subscribe", "ai-social-raw")
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
    )

    print("✅ Connected to Kafka topic: ai-social-raw")

    # Parse JSON from Kafka value
    parsed_df = (
        kafka_df
        .selectExpr("CAST(value AS STRING) as json_value")
        .select(from_json(col("json_value"), KAFKA_MESSAGE_SCHEMA).alias("data"))
        .select(
            col("data.source").alias("source"),
            col("data.timestamp").alias("event_timestamp"),
            col("data.data").alias("raw_data"),
            current_timestamp().alias("processed_at")
        )
    )

    # Count by source
    counts_df = (
        parsed_df
        .groupBy("source")
        .count()
    )

    # Write to console (for testing)
    print("📺 Starting console output stream...")

    query1 = (
        parsed_df
        .writeStream
        .outputMode("append")
        .format("console")
        .option("truncate", False)
        .option("numRows", 10)
        .start()
    )

    query2 = (
        counts_df
        .writeStream
        .outputMode("complete")
        .format("console")
        .option("truncate", False)
        .start()
    )

    print("✅ Streaming started! Processing messages from Kafka...")
    print("📊 Watch the console for incoming data...")
    print("⏹️  Press Ctrl+C to stop")

    # Wait for termination
    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    main()
