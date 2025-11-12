#!/bin/bash
# Start Spark Streaming Job - Fixed version with local jars

echo "🚀 Starting Spark Streaming Job (Fixed)..."
echo ""

# Check if Spark Master is running
if ! curl -f http://localhost:8080 > /dev/null 2>&1; then
    echo "❌ Spark Master is not running!"
    echo "   Please start it first: ./scripts/start_full_infrastructure.sh"
    exit 1
fi

echo "✅ Spark Master is running"
echo ""

# Check if jars exist
if [ ! -f "streaming/spark/jars/spark-sql-kafka-0-10_2.12-3.5.0.jar" ]; then
    echo "❌ Kafka connector jars not found!"
    echo "   Please run: ./scripts/prepare_spark_jars.sh"
    exit 1
fi

echo "✅ Kafka connector jars found"
echo ""

# Copy the Python script into Spark container
echo "📦 Copying streaming script to Spark Master..."
docker cp streaming/spark/simple_processor.py spark-master:/opt/spark-apps/simple_processor.py

# Copy jars to Spark container
echo "📦 Copying jar files to Spark Master..."
docker exec spark-master mkdir -p /opt/spark-apps/jars
docker cp streaming/spark/jars/. spark-master:/opt/spark-apps/jars/

echo "✅ Files copied"
echo ""

# Submit Spark job with local jars
echo "🔥 Submitting Spark job..."
echo ""
echo "   You should see:"
echo "   - Kafka messages being processed"
echo "   - Source counts (Twitter vs Reddit)"
echo "   - Real-time updates"
echo ""
echo "   Press Ctrl+C to stop the job"
echo ""

docker exec -it spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --jars /opt/spark-apps/jars/spark-sql-kafka-0-10_2.12-3.5.0.jar,/opt/spark-apps/jars/kafka-clients-3.4.1.jar,/opt/spark-apps/jars/spark-token-provider-kafka-0-10_2.12-3.5.0.jar,/opt/spark-apps/jars/commons-pool2-2.11.1.jar \
  --conf spark.executor.memory=1g \
  --conf spark.driver.memory=1g \
  /opt/spark-apps/simple_processor.py

echo ""
echo "🛑 Spark job stopped"
