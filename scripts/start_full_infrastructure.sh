#!/bin/bash
# Start FULL infrastructure including Spark (using Apache official image)

echo "🚀 Starting FULL Lakehouse AI Pipeline Infrastructure..."
echo "   This includes: Kafka + MinIO + Spark"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if .env file exists
if [ ! -f "config/.env" ]; then
    echo "⚠️  config/.env not found. Creating from template..."
    cp config/env.example config/.env
    echo "⚠️  Please edit config/.env with your API keys"
    echo ""
fi

# Stop any existing containers from minimal config
echo "🛑 Stopping minimal infrastructure (if running)..."
docker-compose -f docker-compose-minimal.yml down 2>/dev/null
echo ""

# Start full Docker Compose services
echo "🐳 Starting FULL Docker services..."
echo "   - Zookeeper"
echo "   - Kafka"
echo "   - MinIO (S3-compatible storage)"
echo "   - Spark Master"
echo "   - Spark Worker"
echo ""

docker-compose -f docker-compose-full.yml up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be ready (30 seconds)..."
sleep 30

# Check service health
echo ""
echo "🔍 Checking service status..."
echo ""

# Check Kafka
if docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
    echo "✅ Kafka is ready"
else
    echo "⚠️  Kafka is not ready yet"
fi

# Check MinIO
if curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
    echo "✅ MinIO is ready"
else
    echo "⚠️  MinIO is not ready yet"
fi

# Check Spark Master
if curl -f http://localhost:8080 > /dev/null 2>&1; then
    echo "✅ Spark Master is ready"
else
    echo "⚠️  Spark Master is not ready yet"
fi

# Check Spark Worker
if curl -f http://localhost:8081 > /dev/null 2>&1; then
    echo "✅ Spark Worker is ready"
else
    echo "⚠️  Spark Worker is not ready yet"
fi

echo ""
echo "📊 Full infrastructure started! Access points:"
echo ""
echo "   🌐 Kafka:         localhost:9092"
echo "   🌐 MinIO Console: http://localhost:9001 (admin/minioadmin)"
echo "   🌐 MinIO API:     http://localhost:9000"
echo "   🌐 Spark Master:  http://localhost:8080"
echo "   🌐 Spark Worker:  http://localhost:8081"
echo ""
echo "📝 Next steps:"
echo "   1. Visit Spark Master UI: http://localhost:8080"
echo "   2. Verify worker is connected (should show 1 worker)"
echo "   3. Run Spark streaming job: ./scripts/start_spark_streaming.sh"
echo "   4. Check data in MinIO: http://localhost:9001"
echo ""
echo "🛑 To stop all services: docker-compose -f docker-compose-full.yml down"
echo "📊 To view logs: docker-compose -f docker-compose-full.yml logs -f"
echo ""
