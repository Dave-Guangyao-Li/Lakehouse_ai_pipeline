# AI趋势监控系统 - 完整指南

**版本**: v1.0 | **更新日期**: 2025-11-11 | **状态**: Phase 2B 完成

---

## 📖 目录

1. [快速开始](#快速开始)
2. [系统架构](#系统架构)
3. [完整使用流程](#完整使用流程)
4. [故障排查](#故障排查)
5. [下一步扩展](#下一步扩展)

---

## 🚀 快速开始

### 前置要求

- Docker Desktop (运行中)
- Python 3.9+
- Twitter API密钥
- Reddit API密钥

### 5分钟启动

```bash
# 1. 配置API密钥
cp config/env.example config/.env
# 编辑 config/.env 填入密钥

# 2. 启动基础设施
./scripts/start_full_infrastructure.sh

# 3. 安装Python依赖
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 4. 启动数据采集
./scripts/start_collectors.sh

# 5. 下载Spark依赖（首次运行）
./scripts/prepare_spark_jars.sh

# 6. 启动Spark处理
./scripts/start_spark_streaming_fixed.sh
```

**访问点：**
- Spark UI: http://localhost:8080
- MinIO: http://localhost:9001 (minioadmin/minioadmin)
- Dashboard: 运行 `./scripts/start_dashboard_realtime.sh`

---

## 🏗️ 系统架构

### 数据流

```
Twitter/Reddit API
       ↓
Python采集器 (每5分钟)
       ↓
Apache Kafka (ai-social-raw topic)
       ↓
Spark Streaming (实时处理)
       ↓
MinIO + Delta Lake (Bronze/Silver/Gold)
       ↓
Streamlit Dashboard
```

### 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 采集 | Tweepy + PRAW | API数据采集 |
| 队列 | Kafka | 消息缓冲 |
| 处理 | Spark Streaming | 实时ETL |
| 存储 | MinIO + Delta Lake | Lakehouse |
| 可视化 | Streamlit | 实时Dashboard |

### 目录结构

```
lakehouse_ai_pipeline/
├── config/              # 配置文件
│   └── .env            # API密钥（需创建）
├── data_ingestion/      # 数据采集
│   ├── twitter/
│   ├── reddit/
│   └── kafka_producer.py
├── streaming/spark/     # Spark作业
│   ├── simple_processor.py
│   └── jars/           # Kafka连接器
├── dashboard/           # 可视化
│   ├── app_realtime.py
│   └── kafka_reader.py
├── scripts/             # 启动脚本
└── docs/                # 文档
```

---

## 📋 完整使用流程

### 场景1：首次启动系统

**步骤：**

```bash
# 1. 配置环境
cd ~/Documents/Lakehouse_ai_pipeline
cp config/env.example config/.env
nano config/.env  # 填入Twitter和Reddit API密钥

# 2. 启动基础设施
./scripts/start_full_infrastructure.sh
# 等待30秒，所有服务启动

# 3. 验证服务
docker ps  # 应该看到5个容器运行
curl http://localhost:8080  # Spark Master UI可访问

# 4. 安装Python环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. 启动数据采集
./scripts/start_collectors.sh
# 查看日志确认正常：tail -f logs/twitter_collector.log

# 6. 准备Spark依赖（首次需要）
./scripts/prepare_spark_jars.sh
# 等待jar文件下载完成

# 7. 启动Spark Streaming
./scripts/start_spark_streaming_fixed.sh
```

**预期输出：**

Spark应显示类似以下的输出：
```
✅ Spark session created
📊 Connecting to Kafka...
✅ Connected to Kafka topic: ai-social-raw
-------------------------------------------
Batch: 0
-------------------------------------------
+-------+-----+
|source |count|
+-------+-----+
|twitter|193  |
|reddit |373  |
+-------+-----+
```

---

### 场景2：日常启动（已配置过）

```bash
# 1. 启动基础设施
./scripts/start_full_infrastructure.sh

# 2. 启动采集器
source venv/bin/activate
./scripts/start_collectors.sh

# 3. 启动Spark处理
./scripts/start_spark_streaming_fixed.sh
```

---

### 场景3：查看实时Dashboard

```bash
# 新终端窗口
cd ~/Documents/Lakehouse_ai_pipeline
source venv/bin/activate
./scripts/start_dashboard_realtime.sh

# 浏览器自动打开 http://localhost:8501
```

**Dashboard功能：**
- 实时数据统计（Twitter/Reddit帖子数）
- 热门话题分析（基于关键词）
- 最活跃作者
- 最近帖子列表
- 自动刷新（可配置）

---

### 场景4：停止所有服务

```bash
# 1. 停止Spark Streaming（在运行的终端按 Ctrl+C）

# 2. 停止采集器
./scripts/stop_collectors.sh

# 3. 停止Dashboard（按 Ctrl+C）

# 4. 停止基础设施
docker-compose -f docker-compose-full.yml down
```

---

### 场景5：查看数据和日志

**查看Kafka消息：**
```bash
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic ai-social-raw \
  --from-beginning \
  --max-messages 10
```

**查看采集器日志：**
```bash
# 实时查看
tail -f logs/twitter_collector.log
tail -f logs/reddit_collector.log

# 查看最近100行
tail -100 logs/twitter_collector.log
```

**查看MinIO数据：**
1. 访问 http://localhost:9001
2. 登录 (minioadmin/minioadmin)
3. 查看buckets: lakehouse, bronze, silver, gold

**查看Spark作业详情：**
- Master UI: http://localhost:8080
- Application UI: http://localhost:4040
- Worker UI: http://localhost:8081

---

## 🔧 故障排查

### 问题1: Docker无法启动

**症状：**
```
ERROR: Cannot connect to the Docker daemon
```

**解决：**
1. 打开Docker Desktop
2. 等待Docker完全启动
3. 验证：`docker ps`

---

### 问题2: Spark Worker启动失败

**症状：**
```
java.io.IOException: Failed to create directory /opt/spark/work/...
```

**解决：**

已在 `docker-compose-full.yml` 中修复：
- Worker以root用户运行
- 使用 `/tmp/spark-work` 作为工作目录

如仍有问题：
```bash
# 重启服务
docker-compose -f docker-compose-full.yml restart spark-worker

# 查看日志
docker-compose -f docker-compose-full.yml logs spark-worker
```

---

### 问题3: Spark无法下载Kafka连接器

**症状：**
```
FileNotFoundException: /home/spark/.ivy2/cache/resolved-...
```

**解决：**

使用修复后的脚本（已预下载jar）：
```bash
./scripts/prepare_spark_jars.sh
./scripts/start_spark_streaming_fixed.sh
```

不要使用 `start_spark_streaming.sh`（已弃用）。

---

### 问题4: Twitter API 401错误

**症状：**
```
401 Unauthorized
```

**解决：**
1. 检查 `config/.env` 中的密钥是否正确
2. 确认使用的是 `TWITTER_BEARER_TOKEN`（不是API Key）
3. 验证Twitter Developer账号状态

**测试连接：**
```bash
source venv/bin/activate
python -c "
import os
from dotenv import load_dotenv
load_dotenv('config/.env')
print('Bearer Token:', os.getenv('TWITTER_BEARER_TOKEN')[:20] + '...')
"
```

---

### 问题5: Reddit连接失败

**症状：**
```
received 404 HTTP response
```

**可能原因：**
- Subreddit名称错误或不存在
- API限流

**解决：**

编辑 `data_ingestion/reddit/collector.py`，注释掉问题subreddit：
```python
TARGET_SUBREDDITS = [
    'MachineLearning',
    'LocalLLaMA',
    # 'ArtificialIntelligence',  # 暂时禁用
]
```

---

### 问题6: Dashboard无数据

**症状：**
Dashboard显示 "No data available"

**检查清单：**

```bash
# 1. Kafka是否有数据？
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic ai-social-raw \
  --from-beginning \
  --max-messages 5

# 2. 采集器是否运行？
ps aux | grep collector

# 3. 查看采集器日志
tail -20 logs/twitter_collector.log
```

---

### 问题7: 端口占用

**症状：**
```
Port 8080 is already in use
```

**解决：**
```bash
# 查找占用进程
lsof -i :8080

# 停止冲突服务
docker-compose -f docker-compose-full.yml down

# 或杀掉进程
kill -9 <PID>
```

---

## 🎯 下一步扩展

### Phase 3: 添加Delta Lake持久化

**目标：** 将处理后的数据写入Delta Lake

**实施：**
1. 修改 `streaming/spark/processor.py`
2. 添加Delta Lake写入逻辑
3. 实现Bronze/Silver/Gold三层
4. Dashboard从Delta Lake读取

**预计时间：** 1-2周

---

### Phase 4: 向量搜索和RAG

**目标：** 语义搜索和智能问答

**技术栈：**
- Milvus（向量数据库）
- Sentence Transformers（文本embedding）
- LangChain + OpenAI/Claude API

**功能：**
- 语义相似搜索
- 自然语言问答
- 趋势预测

**预计时间：** 2-3周

---

### Phase 5: 生产化部署

**目标：** 部署到云端，高可用

**改进：**
- 迁移到AWS/Azure
- Kafka集群（3节点）
- Spark HA配置
- 监控告警（Prometheus + Grafana）
- CI/CD流水线

---

## 📊 性能指标

### 当前系统容量

| 指标 | 当前值 | 理论上限 |
|------|--------|----------|
| 采集频率 | 5分钟/次 | API限制 |
| Kafka吞吐 | ~100msg/s | 10K msg/s |
| Spark处理延迟 | <1秒 | <100ms |
| 存储 | MinIO | 无限 |
| 数据保留 | Kafka 7天 | 可配置 |

### 资源使用

- **Docker内存**: 建议4GB+
- **磁盘空间**: 10GB+（数据增长）
- **CPU**: 2核心+

---

## 📚 快速命令参考

```bash
# === 启动相关 ===
./scripts/start_full_infrastructure.sh    # 启动基础设施
./scripts/start_collectors.sh             # 启动采集器
./scripts/start_spark_streaming_fixed.sh  # 启动Spark
./scripts/start_dashboard_realtime.sh     # 启动Dashboard

# === 停止相关 ===
./scripts/stop_collectors.sh              # 停止采集器
docker-compose -f docker-compose-full.yml down  # 停止基础设施

# === 查看相关 ===
docker ps                                 # 查看容器状态
docker-compose -f docker-compose-full.yml logs -f  # 查看所有日志
tail -f logs/twitter_collector.log        # 查看Twitter日志
tail -f logs/reddit_collector.log         # 查看Reddit日志

# === 测试相关 ===
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic ai-social-raw \
  --from-beginning \
  --max-messages 10                       # 查看Kafka消息

curl http://localhost:8080                # 测试Spark Master
curl http://localhost:9000/minio/health/live  # 测试MinIO
```

---

## 🆘 获取帮助

### 查看日志位置

- 采集器日志: `logs/*.log`
- Spark日志: `docker-compose -f docker-compose-full.yml logs spark-master`
- Kafka日志: `docker-compose -f docker-compose-full.yml logs kafka`

### 重置系统

```bash
# 完全重置（删除所有数据）
docker-compose -f docker-compose-full.yml down -v
rm -rf logs/*.log
# 然后重新启动
```

---

**文档版本**: 1.0
**最后更新**: 2025-11-11
**维护者**: Guangyao Li
