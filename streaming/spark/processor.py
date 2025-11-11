"""
Spark Streaming Processor
Processes social media data from Kafka and writes to Delta Lake
"""
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, to_timestamp, current_timestamp,
    explode, lower, regexp_replace, split, size,
    window, count, sum as _sum, avg, collect_list
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    TimestampType, BooleanType, ArrayType, MapType
)
from delta import configure_spark_with_delta_pip


# Define schema for incoming Kafka messages
KAFKA_MESSAGE_SCHEMA = StructType([
    StructField("source", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("data", MapType(StringType(), StringType()), True)
])

# Schema for Twitter data
TWITTER_SCHEMA = StructType([
    StructField("id", StringType(), False),
    StructField("text", StringType(), True),
    StructField("created_at", StringType(), True),
    StructField("author_id", StringType(), True),
    StructField("author_username", StringType(), True),
    StructField("author_name", StringType(), True),
    StructField("author_verified", BooleanType(), True),
    StructField("language", StringType(), True),
    StructField("metrics", StructType([
        StructField("likes", IntegerType(), True),
        StructField("retweets", IntegerType(), True),
        StructField("replies", IntegerType(), True),
        StructField("quotes", IntegerType(), True)
    ]), True),
    StructField("hashtags", ArrayType(StringType()), True),
    StructField("mentions", ArrayType(StringType()), True)
])

# Schema for Reddit data
REDDIT_SCHEMA = StructType([
    StructField("id", StringType(), False),
    StructField("title", StringType(), True),
    StructField("text", StringType(), True),
    StructField("created_utc", StringType(), True),
    StructField("author", StringType(), True),
    StructField("subreddit", StringType(), True),
    StructField("url", StringType(), True),
    StructField("permalink", StringType(), True),
    StructField("metrics", StructType([
        StructField("score", IntegerType(), True),
        StructField("upvote_ratio", IntegerType(), True),
        StructField("num_comments", IntegerType(), True)
    ]), True),
    StructField("is_self", BooleanType(), True),
    StructField("flair", StringType(), True)
])


class SocialMediaStreamProcessor:
    """Process streaming social media data with Spark"""

    def __init__(self, kafka_servers="localhost:9092", kafka_topic="ai-social-raw"):
        """Initialize Spark session with Delta Lake support"""
        self.kafka_servers = kafka_servers
        self.kafka_topic = kafka_topic

        # Create Spark session with Delta Lake
        builder = (
            SparkSession.builder
            .appName("AI_Trend_Monitor_Streaming")
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .config("spark.hadoop.fs.s3a.endpoint", os.getenv("MINIO_ENDPOINT", "http://localhost:9000"))
            .config("spark.hadoop.fs.s3a.access.key", os.getenv("MINIO_ACCESS_KEY", "minioadmin"))
            .config("spark.hadoop.fs.s3a.secret.key", os.getenv("MINIO_SECRET_KEY", "minioadmin"))
            .config("spark.hadoop.fs.s3a.path.style.access", "true")
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
            .config("spark.sql.streaming.checkpointLocation", "/tmp/spark-checkpoint")
        )

        self.spark = configure_spark_with_delta_pip(builder).getOrCreate()
        self.spark.sparkContext.setLogLevel("WARN")

        print("✅ Spark session created with Delta Lake support")

    def read_kafka_stream(self):
        """Read streaming data from Kafka"""
        return (
            self.spark.readStream
            .format("kafka")
            .option("kafka.bootstrap.servers", self.kafka_servers)
            .option("subscribe", self.kafka_topic)
            .option("startingOffsets", "latest")
            .option("failOnDataLoss", "false")
            .load()
        )

    def process_bronze_layer(self, df):
        """
        Bronze layer: Raw data with minimal processing
        Just parse JSON and add ingestion timestamp
        """
        return (
            df.selectExpr("CAST(value AS STRING) as json_value")
            .select(from_json(col("json_value"), KAFKA_MESSAGE_SCHEMA).alias("data"))
            .select(
                col("data.source").alias("source"),
                col("data.timestamp").alias("event_timestamp"),
                col("data.data").alias("raw_data"),
                current_timestamp().alias("ingested_at")
            )
        )

    def process_silver_layer_twitter(self, df):
        """
        Silver layer: Clean and standardize Twitter data
        """
        # Parse Twitter data from JSON
        twitter_df = (
            df.filter(col("source") == "twitter")
            .select(
                from_json(col("raw_data"), TWITTER_SCHEMA).alias("tweet"),
                col("ingested_at")
            )
            .select("tweet.*", "ingested_at")
        )

        # Clean and transform
        cleaned_df = (
            twitter_df
            .withColumn("text_clean", regexp_replace(lower(col("text")), r"http\S+|www\S+|@\S+|#", ""))
            .withColumn("engagement_score",
                       col("metrics.likes") * 2 + col("metrics.retweets") * 5 +
                       col("metrics.replies") * 3 + col("metrics.quotes") * 4)
            .withColumn("created_at_ts", to_timestamp(col("created_at")))
            .withColumn("num_hashtags", size(col("hashtags")))
            .withColumn("num_mentions", size(col("mentions")))
            .filter(col("language").isin(["en", "zh"]))  # English or Chinese
            .dropDuplicates(["id"])
        )

        return cleaned_df

    def process_silver_layer_reddit(self, df):
        """
        Silver layer: Clean and standardize Reddit data
        """
        # Parse Reddit data
        reddit_df = (
            df.filter(col("source") == "reddit")
            .select(
                from_json(col("raw_data"), REDDIT_SCHEMA).alias("post"),
                col("ingested_at")
            )
            .select("post.*", "ingested_at")
        )

        # Clean and transform
        cleaned_df = (
            reddit_df
            .withColumn("text_clean", regexp_replace(lower(col("text")), r"http\S+|www\S+", ""))
            .withColumn("full_text", concat_ws(" ", col("title"), col("text")))
            .withColumn("engagement_score",
                       col("metrics.score") + col("metrics.num_comments") * 2)
            .withColumn("created_at_ts", to_timestamp(col("created_utc")))
            .dropDuplicates(["id"])
        )

        return cleaned_df

    def detect_trending_topics(self, df):
        """
        Gold layer: Detect trending topics using windowed aggregations
        """
        # Extract keywords (simplified - in production use NLP)
        AI_KEYWORDS = ["gpt", "claude", "llm", "openai", "anthropic", "gemini",
                      "chatgpt", "ai", "machine learning", "deep learning"]

        # This is a simplified version - real implementation would use more sophisticated NLP
        trending = (
            df.withWatermark("created_at_ts", "10 minutes")
            .groupBy(
                window(col("created_at_ts"), "1 hour", "30 minutes"),
                col("source")
            )
            .agg(
                count("*").alias("post_count"),
                _sum("engagement_score").alias("total_engagement"),
                avg("engagement_score").alias("avg_engagement"),
                collect_list("id").alias("post_ids")
            )
            .withColumn("trend_score",
                       col("post_count") * col("avg_engagement") / 100)
            .orderBy(col("trend_score").desc())
        )

        return trending

    def write_to_delta(self, df, path, checkpoint_path, output_mode="append"):
        """
        Write streaming data to Delta Lake

        Args:
            df: Streaming DataFrame
            path: Delta table path (e.g., "s3a://lakehouse/bronze/raw")
            checkpoint_path: Checkpoint location
            output_mode: "append" or "complete"
        """
        return (
            df.writeStream
            .format("delta")
            .outputMode(output_mode)
            .option("checkpointLocation", checkpoint_path)
            .option("path", path)
            .start()
        )

    def run_pipeline(self):
        """Run the complete streaming pipeline"""
        print("🚀 Starting streaming pipeline...")

        # Read from Kafka
        kafka_stream = self.read_kafka_stream()

        # Bronze layer: Raw data
        bronze_df = self.process_bronze_layer(kafka_stream)
        bronze_query = self.write_to_delta(
            bronze_df,
            "s3a://bronze/social_media",
            "/tmp/checkpoint/bronze"
        )
        print("✅ Bronze layer started")

        # Silver layer: Cleaned data (we'd need separate streams for Twitter/Reddit)
        # For simplicity, writing to console here
        silver_query = (
            bronze_df.writeStream
            .outputMode("append")
            .format("console")
            .option("truncate", False)
            .start()
        )
        print("✅ Silver layer started (console output)")

        # Wait for termination
        print("📊 Pipeline running. Press Ctrl+C to stop.")
        self.spark.streams.awaitAnyTermination()


def main():
    """Main entry point"""
    # Configuration from environment
    kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_topic = os.getenv("KAFKA_TOPIC_RAW", "ai-social-raw")

    # Create processor
    processor = SocialMediaStreamProcessor(kafka_servers, kafka_topic)

    try:
        processor.run_pipeline()
    except KeyboardInterrupt:
        print("\n⏹️  Pipeline stopped by user")
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        raise


if __name__ == "__main__":
    main()
