#!/bin/bash
# Start all infrastructure services with Docker Compose

echo "🚀 Starting Lakehouse AI Pipeline Infrastructure..."
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
    echo "⚠️  Please edit config/.env with your API keys before running collectors"
    echo ""
fi

# Start Docker Compose services
echo "🐳 Starting Docker services..."
echo "   - Zookeeper"
echo "   - Kafka"
echo "   - MinIO (S3-compatible storage)"
echo "   - Spark (Master + Workers)"
echo ""

docker-compose up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "🔍 Checking service status..."
echo ""

# Check Kafka
if docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
    echo "✅ Kafka is ready"
else
    echo "⚠️  Kafka is not ready yet (may need more time)"
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

echo ""
echo "📊 Infrastructure started! Access points:"
echo ""
echo "   🌐 Kafka:         localhost:9092"
echo "   🌐 MinIO Console: http://localhost:9001 (admin/minioadmin)"
echo "   🌐 MinIO API:     http://localhost:9000"
echo "   🌐 Spark Master:  http://localhost:8080"
echo "   🌐 Spark Worker1: http://localhost:8081"
echo "   🌐 Spark Worker2: http://localhost:8082"
echo ""
echo "📝 Next steps:"
echo "   1. Edit config/.env with your API keys"
echo "   2. Install Python dependencies: pip install -r requirements.txt"
echo "   3. Start data collectors: ./scripts/start_collectors.sh"
echo "   4. Start Spark streaming: ./scripts/start_streaming.sh"
echo "   5. Launch dashboard: ./scripts/start_dashboard.sh"
echo ""
echo "🛑 To stop all services: docker-compose down"
echo ""
