#!/bin/bash
# 启动Spark Streaming（写入MinIO版本）

echo "🚀 Starting Spark Streaming Job (写入MinIO)..."
echo ""

# 检查Spark Master
if ! curl -f http://localhost:8080 > /dev/null 2>&1; then
    echo "❌ Spark Master未运行！"
    echo "   请先运行: ./scripts/full_restart.sh"
    exit 1
fi

echo "✅ Spark Master运行中"
echo ""

# 检查jar文件
if [ ! -f "streaming/spark/jars/spark-sql-kafka-0-10_2.12-3.5.0.jar" ]; then
    echo "❌ Kafka connector jars未找到！"
    echo "   运行: ./scripts/prepare_spark_jars.sh"
    exit 1
fi

echo "✅ Jar文件就绪"
echo ""

# 下载Hadoop AWS jar（用于S3A支持）
if [ ! -f "streaming/spark/jars/hadoop-aws-3.3.4.jar" ]; then
    echo "📦 下载Hadoop AWS jar（MinIO支持）..."
    cd streaming/spark/jars
    curl -L -O https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar
    curl -L -O https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar
    cd ../../..
    echo "✅ 下载完成"
    echo ""
fi

# 复制文件到容器
echo "📦 复制文件到Spark Master..."
docker cp streaming/spark/processor_with_minio.py spark-master:/opt/spark-apps/
docker cp streaming/spark/jars/. spark-master:/opt/spark-apps/jars/

echo "✅ 文件已复制"
echo ""

# 提交Spark作业
echo "🔥 提交Spark作业（写入MinIO）..."
echo ""
echo "   你应该看到："
echo "   - 连接到Kafka"
echo "   - 开始写入MinIO"
echo "   - 每30秒一个批次"
echo ""
echo "   按 Ctrl+C 停止作业"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

docker exec -it spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --jars /opt/spark-apps/jars/spark-sql-kafka-0-10_2.12-3.5.0.jar,/opt/spark-apps/jars/kafka-clients-3.4.1.jar,/opt/spark-apps/jars/spark-token-provider-kafka-0-10_2.12-3.5.0.jar,/opt/spark-apps/jars/commons-pool2-2.11.1.jar,/opt/spark-apps/jars/hadoop-aws-3.3.4.jar,/opt/spark-apps/jars/aws-java-sdk-bundle-1.12.262.jar \
  --conf spark.executor.memory=1g \
  --conf spark.driver.memory=1g \
  /opt/spark-apps/processor_with_minio.py

echo ""
echo "🛑 Spark作业已停止"
echo ""
echo "📊 验证数据是否写入MinIO:"
echo "   1. 访问 http://localhost:9001"
echo "   2. 登录 (minioadmin/minioadmin)"
echo "   3. 进入 'lakehouse' bucket"
echo "   4. 应该看到 bronze/social_media/ 目录"
echo ""
