#!/bin/bash
# Start Spark Streaming Job

echo "🚀 Starting Spark Streaming Job..."
echo ""

# Check if Spark Master is running
if ! curl -f http://localhost:8080 > /dev/null 2>&1; then
    echo "❌ Spark Master is not running!"
    echo "   Please start it first: ./scripts/start_full_infrastructure.sh"
    exit 1
fi

echo "✅ Spark Master is running"
echo ""

# Copy the Python script into Spark container
echo "📦 Copying streaming script to Spark Master..."
docker cp streaming/spark/simple_processor.py spark-master:/opt/spark-apps/simple_processor.py

echo "✅ Script copied"
echo ""

# Submit Spark job
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
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.executor.memory=1g \
  --conf spark.driver.memory=1g \
  /opt/spark-apps/simple_processor.py

echo ""
echo "🛑 Spark job stopped"
