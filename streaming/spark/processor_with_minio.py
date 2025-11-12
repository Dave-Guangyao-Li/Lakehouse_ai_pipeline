"""
Spark Streaming Processor - 写入MinIO版本
读取Kafka数据并写入MinIO (Bronze层)
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, to_timestamp, current_timestamp,
    to_date, lit
)
from pyspark.sql.types import StructType, StructField, StringType, MapType


# Kafka消息Schema
KAFKA_MESSAGE_SCHEMA = StructType([
    StructField("source", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("data", MapType(StringType(), StringType()), True)
])


def create_spark_session():
    """创建带MinIO配置的Spark Session"""
    return (
        SparkSession.builder
        .appName("AI_Trend_Monitor_MinIO")
        .master("spark://spark-master:7077")
        .config("spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                "org.apache.hadoop:hadoop-aws:3.3.4")
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
        .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
        .config("spark.hadoop.fs.s3a.secret.key", "minioadmin")
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .getOrCreate()
    )


def main():
    """主处理流程"""
    print("🚀 Starting Spark Streaming processor (MinIO版本)...")

    # 创建Spark Session
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    print("✅ Spark session created with MinIO configuration")

    # 从Kafka读取
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

    # 解析JSON
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
        .withColumn("partition_date", to_date(col("processed_at")))
    )

    # 写入MinIO Bronze层（Parquet格式）
    print("💾 Starting to write data to MinIO...")
    print("   Path: s3a://lakehouse/bronze/social_media/")

    query = (
        parsed_df
        .writeStream
        .format("parquet")
        .outputMode("append")
        .option("checkpointLocation", "s3a://lakehouse/checkpoints/bronze")
        .option("path", "s3a://lakehouse/bronze/social_media")
        .partitionBy("partition_date", "source")  # 按日期和来源分区
        .trigger(processingTime='30 seconds')  # 每30秒批次
        .start()
    )

    print("✅ Streaming started! Writing to MinIO...")
    print("📊 Data location: s3a://lakehouse/bronze/social_media/")
    print("📂 Partitioned by: partition_date, source")
    print("")
    print("🔍 验证数据:")
    print("   1. 访问 http://localhost:9001")
    print("   2. 登录 (minioadmin/minioadmin)")
    print("   3. 进入 'lakehouse' bucket")
    print("   4. 查看 bronze/social_media/ 目录")
    print("")
    print("⏹️  Press Ctrl+C to stop")
    print("")

    # 等待终止
    query.awaitTermination()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Streaming stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
