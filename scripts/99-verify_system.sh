#!/bin/bash
# 验证系统各部分是否正常工作

echo "🔍 系统验证检查"
echo "================================"
echo ""

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

# 1. Docker服务
echo "1️⃣  Docker服务检查"
echo "--------------------------------"

services=("kafka" "zookeeper" "minio" "spark-master" "spark-worker")
for service in "${services[@]}"; do
    if docker ps | grep -q $service; then
        echo -e "${GREEN}✅ $service 运行中${NC}"
        ((PASS++))
    else
        echo -e "${RED}❌ $service 未运行${NC}"
        ((FAIL++))
    fi
done
echo ""

# 2. 端口检查
echo "2️⃣  端口可访问性检查"
echo "--------------------------------"

if curl -f http://localhost:8080 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Spark Master UI (8080) 可访问${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ Spark Master UI (8080) 不可访问${NC}"
    ((FAIL++))
fi

if curl -f http://localhost:9001 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ MinIO Console (9001) 可访问${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ MinIO Console (9001) 不可访问${NC}"
    ((FAIL++))
fi

if docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Kafka (9092) 可访问${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ Kafka (9092) 不可访问${NC}"
    ((FAIL++))
fi
echo ""

# 3. 数据采集器
echo "3️⃣  数据采集器检查"
echo "--------------------------------"

COLLECTOR_COUNT=$(ps aux | grep -c "[c]ollector.py")
if [ "$COLLECTOR_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ ${COLLECTOR_COUNT} 个采集器运行中${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 没有采集器运行${NC}"
    ((FAIL++))
fi

if [ -f "logs/twitter_collector.log" ]; then
    TWITTER_MSGS=$(tail -100 logs/twitter_collector.log | grep -c "Sent tweet" || echo 0)
    if [ "$TWITTER_MSGS" -gt 0 ]; then
        echo -e "${GREEN}   Twitter: 最近发送了 ${TWITTER_MSGS} 条推文${NC}"
    else
        echo -e "${YELLOW}   Twitter: 暂无推文发送记录${NC}"
    fi
fi

if [ -f "logs/reddit_collector.log" ]; then
    REDDIT_MSGS=$(tail -100 logs/reddit_collector.log | grep -c "Sent Reddit post" || echo 0)
    if [ "$REDDIT_MSGS" -gt 0 ]; then
        echo -e "${GREEN}   Reddit: 最近发送了 ${REDDIT_MSGS} 个帖子${NC}"
    else
        echo -e "${YELLOW}   Reddit: 暂无帖子发送记录${NC}"
    fi
fi
echo ""

# 4. Kafka数据
echo "4️⃣  Kafka数据检查"
echo "--------------------------------"

KAFKA_COUNT=$(docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
    --broker-list localhost:9092 \
    --topic ai-social-raw 2>/dev/null | awk -F':' '{sum+=$NF} END {print sum}')

if [ "$KAFKA_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Kafka有 ${KAFKA_COUNT} 条消息${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ Kafka没有消息${NC}"
    ((FAIL++))
fi

# 显示最新5条消息示例
echo ""
echo "📝 最新消息示例（前5条）:"
docker exec kafka kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic ai-social-raw \
    --from-beginning \
    --max-messages 5 \
    --timeout-ms 3000 2>/dev/null | head -5
echo ""

# 5. MinIO数据
echo "5️⃣  MinIO数据检查"
echo "--------------------------------"

# 检查是否有MinIO CLI工具在容器中
if docker exec minio mc ls myminio/lakehouse/bronze/social_media 2>/dev/null | grep -q "partition_date"; then
    echo -e "${GREEN}✅ MinIO中有数据${NC}"
    echo ""
    echo "📂 目录结构:"
    docker exec minio mc ls --recursive myminio/lakehouse/bronze/social_media/ 2>/dev/null | head -20
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  MinIO的lakehouse bucket暂时没有数据${NC}"
    echo "   这是正常的，如果："
    echo "   1. 刚启动系统"
    echo "   2. 还没运行 Spark Streaming 写入作业"
    echo ""
    echo "💡 运行以下命令开始写入数据:"
    echo "   ./scripts/start_spark_with_minio.sh"
fi
echo ""

# 6. Spark作业
echo "6️⃣  Spark作业检查"
echo "--------------------------------"

# 检查是否有活动的Spark应用
SPARK_APPS=$(curl -s http://localhost:8080/json/ 2>/dev/null | grep -o '"activeapps":\[[^]]*\]' | grep -c '"id"' || echo 0)

if [ "$SPARK_APPS" -gt 0 ]; then
    echo -e "${GREEN}✅ 有 ${SPARK_APPS} 个Spark应用运行中${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  没有活动的Spark应用${NC}"
    echo "   启动Spark处理: ./scripts/start_spark_with_minio.sh"
fi
echo ""

# 总结
echo "================================"
echo "📊 验证总结"
echo "================================"
echo -e "${GREEN}✅ 通过: ${PASS} 项${NC}"
if [ "$FAIL" -gt 0 ]; then
    echo -e "${RED}❌ 失败: ${FAIL} 项${NC}"
fi
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}🎉 系统运行正常！${NC}"
else
    echo -e "${YELLOW}⚠️  系统部分组件需要修复${NC}"
    echo ""
    echo "建议运行:"
    echo "  ./scripts/full_restart.sh"
fi
echo ""
