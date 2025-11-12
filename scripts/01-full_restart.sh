#!/bin/bash
# 完整重启脚本 - 从头到尾验证每一步

set -e  # 遇到错误立即退出

echo "🔄 AI趋势监控系统 - 完整重启"
echo "================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 0: 检查前置条件
echo "📋 Step 0: 检查前置条件"
echo "--------------------------------"

if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker未运行！请先启动Docker Desktop${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker正在运行${NC}"

if [ ! -f "config/.env" ]; then
    echo -e "${RED}❌ config/.env不存在！${NC}"
    echo "请运行: cp config/env.example config/.env"
    echo "然后编辑填入API密钥"
    exit 1
fi
echo -e "${GREEN}✅ config/.env存在${NC}"

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  虚拟环境不存在，创建中...${NC}"
    python3 -m venv venv
fi
echo -e "${GREEN}✅ Python虚拟环境就绪${NC}"

if [ ! -f "streaming/spark/jars/spark-sql-kafka-0-10_2.12-3.5.0.jar" ]; then
    echo -e "${YELLOW}⚠️  Spark jar不存在，下载中...${NC}"
    ./scripts/prepare_spark_jars.sh
fi
echo -e "${GREEN}✅ Spark依赖就绪${NC}"

echo ""

# Step 1: 停止所有服务
echo "🛑 Step 1: 停止所有现有服务"
echo "--------------------------------"
docker-compose -f docker-compose-full.yml down 2>/dev/null || true
./scripts/stop_collectors.sh 2>/dev/null || true
echo -e "${GREEN}✅ 所有服务已停止${NC}"
echo ""

# Step 2: 启动基础设施
echo "🚀 Step 2: 启动基础设施"
echo "--------------------------------"
docker-compose -f docker-compose-full.yml up -d

echo "⏳ 等待服务启动（30秒）..."
sleep 30

# 验证每个服务
echo ""
echo "🔍 验证服务状态..."

# 检查Kafka
if docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Kafka就绪${NC}"
else
    echo -e "${RED}❌ Kafka未就绪${NC}"
    exit 1
fi

# 检查MinIO
if curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
    echo -e "${GREEN}✅ MinIO就绪${NC}"
else
    echo -e "${RED}❌ MinIO未就绪${NC}"
    exit 1
fi

# 检查Spark Master
if curl -f http://localhost:8080 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Spark Master就绪${NC}"
else
    echo -e "${RED}❌ Spark Master未就绪${NC}"
    exit 1
fi

# 检查Spark Worker
if curl -f http://localhost:8081 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Spark Worker就绪${NC}"
else
    echo -e "${RED}❌ Spark Worker未就绪${NC}"
    exit 1
fi

echo ""

# Step 3: 启动采集器
echo "📡 Step 3: 启动数据采集器"
echo "--------------------------------"
source venv/bin/activate

# 启动采集器
./scripts/start_collectors.sh

echo "⏳ 等待采集器收集数据（15秒）..."
sleep 15

# 验证采集器
if ps aux | grep -q "[c]ollector.py"; then
    echo -e "${GREEN}✅ 采集器正在运行${NC}"

    # 检查日志
    if [ -f "logs/twitter_collector.log" ]; then
        TWITTER_LINES=$(tail -20 logs/twitter_collector.log | grep -c "Sent tweet" || echo 0)
        echo -e "${GREEN}   Twitter: ${TWITTER_LINES} 条推文已发送${NC}"
    fi

    if [ -f "logs/reddit_collector.log" ]; then
        REDDIT_LINES=$(tail -20 logs/reddit_collector.log | grep -c "Sent Reddit post" || echo 0)
        echo -e "${GREEN}   Reddit: ${REDDIT_LINES} 个帖子已发送${NC}"
    fi
else
    echo -e "${RED}❌ 采集器未运行${NC}"
    exit 1
fi

echo ""

# Step 4: 验证Kafka数据
echo "📊 Step 4: 验证Kafka数据"
echo "--------------------------------"

# 检查Kafka消息数量
KAFKA_COUNT=$(docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
    --broker-list localhost:9092 \
    --topic ai-social-raw 2>/dev/null | awk -F':' '{sum+=$NF} END {print sum}')

if [ "$KAFKA_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Kafka有 ${KAFKA_COUNT} 条消息${NC}"
else
    echo -e "${YELLOW}⚠️  Kafka暂时没有消息，等待采集器...${NC}"
fi

echo ""

# Step 5: 显示系统状态
echo "📈 Step 5: 系统状态总览"
echo "================================"
echo ""
echo "🎯 运行中的服务:"
docker-compose -f docker-compose-full.yml ps
echo ""

echo "🌐 访问点:"
echo "   - Spark Master UI:  http://localhost:8080"
echo "   - Spark Worker UI:  http://localhost:8081"
echo "   - MinIO Console:    http://localhost:9001"
echo "   - Spark App UI:     http://localhost:4040 (Spark运行后)"
echo ""

echo "📊 数据统计:"
echo "   - Kafka消息数: ${KAFKA_COUNT}"
echo "   - 采集器状态: $(ps aux | grep -c "[c]ollector.py") 个进程运行中"
echo ""

echo "✅ 基础设施启动完成！"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 下一步操作:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  启动Spark Streaming (写入MinIO):"
echo "   ./scripts/start_spark_with_minio.sh"
echo ""
echo "2️⃣  查看实时处理日志:"
echo "   tail -f logs/twitter_collector.log"
echo ""
echo "3️⃣  启动Dashboard:"
echo "   ./scripts/start_dashboard_realtime.sh"
echo ""
echo "4️⃣  验证MinIO数据:"
echo "   访问 http://localhost:9001"
echo "   查看 'lakehouse' bucket"
echo ""
echo "🛑 停止所有服务:"
echo "   ./scripts/stop_collectors.sh"
echo "   docker-compose -f docker-compose-full.yml down"
echo ""
