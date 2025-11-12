#!/bin/bash
# Download required Spark jars

echo "📦 Downloading Spark Kafka connector jars..."
echo ""

# Create jars directory
mkdir -p streaming/spark/jars

cd streaming/spark/jars

# Download Kafka connector and dependencies for Spark 3.5.0
echo "⬇️  Downloading spark-sql-kafka..."
curl -L -O https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.0/spark-sql-kafka-0-10_2.12-3.5.0.jar

echo "⬇️  Downloading kafka-clients..."
curl -L -O https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.1/kafka-clients-3.4.1.jar

echo "⬇️  Downloading spark-token-provider-kafka..."
curl -L -O https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.0/spark-token-provider-kafka-0-10_2.12-3.5.0.jar

echo "⬇️  Downloading commons-pool2..."
curl -L -O https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar

cd ../../..

echo ""
echo "✅ All jars downloaded!"
echo "📁 Location: streaming/spark/jars/"
echo ""
echo "Next: Run ./scripts/start_spark_streaming_fixed.sh"
