# Phase 2B: 完整Lakehouse架构实施指南

## 🎯 目标

实现完整的数据处理pipeline：
```
Twitter/Reddit → 采集器 → Kafka → Spark Streaming → MinIO → Dashboard
```

---

## 🚀 实施步骤

### Step 1: 停止当前的minimal基础设施

```bash
cd ~/Documents/Lakehouse_ai_pipeline

# 停止minimal版本
docker-compose -f docker-compose-minimal.yml down
```

### Step 2: 启动完整基础设施（包含Spark）

```bash
# 启动完整版（Kafka + MinIO + Spark）
./scripts/start_full_infrastructure.sh
```

**等待约30秒让所有服务启动完成。**

你应该看到：
```
✅ Kafka is ready
✅ MinIO is ready
✅ Spark Master is ready
✅ Spark Worker is ready
```

### Step 3: 验证Spark集群

**访问Spark Master UI:**

浏览器打开：http://localhost:8080

你应该看到：
- **Workers**: 1 (Alive)
- **Cores**: 2
- **Memory**: 2.0 GB

这说明Spark Master和Worker已成功连接！

### Step 4: 确保采集器正在运行

```bash
# 检查采集器状态
ps aux | grep collector

# 如果没运行，启动它们
./scripts/start_collectors.sh

# 查看日志
tail -f logs/twitter_collector.log
```

### Step 5: 运行Spark Streaming作业

```bash
# 启动Spark处理作业
./scripts/start_spark_streaming.sh
```

**你应该看到：**

```
🚀 Starting Spark Streaming Job...
✅ Spark Master is running
📦 Copying streaming script to Spark Master...
🔥 Submitting Spark job...
```

然后Spark会开始输出处理的数据：

```
+--------+-------------------+-------------------+
|source  |event_timestamp    |processed_at       |
+--------+-------------------+-------------------+
|twitter |2025-11-11T16:47:44|2025-11-11 17:00:00|
|reddit  |2025-11-11T16:49:06|2025-11-11 17:00:00|
+--------+-------------------+-------------------+

+--------+-----+
|source  |count|
+--------+-----+
|twitter |96   |
|reddit  |2    |
+--------+-----+
```

这说明Spark正在**实时处理Kafka中的数据**！

### Step 6: 验证完整数据流

现在你的完整pipeline正在运行：

```
Twitter API → Python采集器 ✅
      ↓
   Kafka ✅
      ↓
Spark Streaming ✅ ← 正在实时处理
      ↓
   Console输出 ✅
```

---

## 🔍 监控和验证

### 查看Spark作业状态

**Spark Master UI:**
- http://localhost:8080
- 查看 "Running Applications"

**Spark Application UI:**
- http://localhost:4040
- 查看流处理统计、Stage、Executor信息

### 查看Kafka消息

```bash
# 查看topic中的消息数量
docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic ai-social-raw
```

### 查看容器状态

```bash
# 查看所有容器
docker-compose -f docker-compose-full.yml ps

# 查看Spark Master日志
docker-compose -f docker-compose-full.yml logs -f spark-master

# 查看Spark Worker日志
docker-compose -f docker-compose-full.yml logs -f spark-worker
```

---

## 📊 当前 vs 目标架构

### 当前实现（Phase 2B - Step 1）

```
Twitter/Reddit API
       ↓
   采集器 ✅
       ↓
    Kafka ✅
       ↓
 Spark Streaming ✅ (输出到Console)
```

### 下一步（Phase 2B - Step 2）

添加Delta Lake存储：

```
Twitter/Reddit API
       ↓
   采集器 ✅
       ↓
    Kafka ✅
       ↓
 Spark Streaming ✅
       ↓
  Delta Lake (MinIO) ← 待实现
  (Bronze/Silver/Gold)
       ↓
   Dashboard
```

---

## 🎯 下一步任务

### 任务1: 实现Delta Lake写入

修改 `streaming/spark/processor.py` 添加Delta Lake支持：

1. 安装Delta Lake包
2. 配置MinIO连接
3. 实现Bronze层写入（原始数据）
4. 实现Silver层写入（清洗后）
5. 实现Gold层写入（聚合数据）

### 任务2: Dashboard连接Delta Lake

修改Dashboard从Delta Lake读取数据而不是直接从Kafka。

### 任务3: 实现热点检测算法

在Spark中实现真正的趋势检测：
- 滑动窗口聚合
- 关键词频率统计
- 话题突发检测

---

## 🛠️ 故障排查

### Spark启动失败

**检查Docker资源：**
- Docker Desktop → Settings → Resources
- 推荐：至少4GB内存

**查看错误日志：**
```bash
docker-compose -f docker-compose-full.yml logs spark-master
docker-compose -f docker-compose-full.yml logs spark-worker
```

### Spark Worker未连接到Master

**检查网络：**
```bash
docker exec spark-worker ping spark-master
```

**重启Worker：**
```bash
docker-compose -f docker-compose-full.yml restart spark-worker
```

### Spark无法读取Kafka

**检查Kafka地址：**
- 在Spark中使用：`kafka:29092`（容器内部）
- 在主机使用：`localhost:9092`

**验证Kafka连接：**
```bash
docker exec spark-master nc -zv kafka 29092
```

### 镜像下载慢

**使用Docker镜像加速：**

编辑 `~/.docker/daemon.json`：
```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn"
  ]
}
```

重启Docker Desktop。

---

## 📈 性能优化

### Spark配置调优

编辑 `scripts/start_spark_streaming.sh`：

```bash
--conf spark.executor.memory=2g \
--conf spark.driver.memory=2g \
--conf spark.executor.cores=2 \
--conf spark.sql.shuffle.partitions=4
```

### Kafka调优

编辑 `docker-compose-full.yml` Kafka环境变量：

```yaml
KAFKA_NUM_PARTITIONS: 4  # 增加分区数
KAFKA_LOG_RETENTION_HOURS: 24  # 减少保留时间
```

---

## 🎉 成就解锁

完成这个阶段后，你将拥有：

✅ **完整的Lakehouse基础设施**
- Kafka消息队列
- MinIO对象存储
- Spark分布式处理

✅ **实时数据处理pipeline**
- 数据采集 → 队列 → 处理

✅ **可扩展的架构**
- 可以添加更多Worker
- 可以处理更大数据量

---

## 📚 学习资源

### Spark Streaming
- [官方文档](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Spark + Kafka集成](https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html)

### Delta Lake
- [Delta Lake官方文档](https://docs.delta.io/)
- [Delta Lake with Spark](https://docs.delta.io/latest/quick-start.html)

### MinIO
- [MinIO Python客户端](https://min.io/docs/minio/linux/developers/python/minio-py.html)
- [S3A配置](https://hadoop.apache.org/docs/stable/hadoop-aws/tools/hadoop-aws/index.html)

---

**准备好了吗？开始实施！** 🚀

```bash
# 1. 停止minimal基础设施
docker-compose -f docker-compose-minimal.yml down

# 2. 启动完整基础设施
./scripts/start_full_infrastructure.sh

# 3. 验证Spark UI
# 浏览器打开: http://localhost:8080

# 4. 启动Spark Streaming
./scripts/start_spark_streaming.sh
```

有任何问题随时告诉我！💪
