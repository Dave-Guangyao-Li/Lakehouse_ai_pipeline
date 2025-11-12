# AI趋势监控系统 - 完整指南

**版本**: v2.0 (MinIO版本) | **更新日期**: 2025-11-11 | **状态**: Phase 2B 完成

---

## 目录

- [快速开始（5分钟）](#快速开始5分钟)
- [API配置详解](#api配置详解)
- [系统架构](#系统架构)
- [完整使用场景](#完整使用场景)
- [故障排查大全](#故障排查大全)
- [命令速查表](#命令速查表)
- [扩展路线图](#扩展路线图)

---

## 快速开始（5分钟）

### 前置要求

- Docker Desktop (运行中) - [下载](https://www.docker.com/products/docker-desktop)
- Python 3.9+
- Twitter API密钥
- Reddit API密钥

### 一键启动命令

```bash
# Step 1: 完整重启系统（自动验证所有组件）
./scripts/01-full_restart.sh

# Step 2: 启动Spark写入MinIO（新建终端）
./scripts/02-start_spark_minio.sh

# Step 3: 启动Dashboard（新建终端）
./scripts/03-start_dashboard.sh

# Step 4: 验证系统状态（可选）
./scripts/99-verify_system.sh
```

### 访问点

| 服务 | URL | 用户名/密码 |
|------|-----|------------|
| Spark Master | http://localhost:8080 | - |
| Spark Worker | http://localhost:8081 | - |
| MinIO Console | http://localhost:9001 | minioadmin/minioadmin |
| Dashboard | http://localhost:8501 | - |
| Spark App UI | http://localhost:4040 | (Spark运行后) |

---

## API配置详解

### Twitter API 申请

1. 访问 [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. 创建新App
3. 获取 **Bearer Token** (Essential access即可)

### Reddit API 申请

1. 访问 [Reddit Apps](https://www.reddit.com/prefs/apps)
2. 点击 "Create App" 或 "Create Another App"
3. 填写信息:
   - **name**: 任意名称（如 "AI Trend Monitor"）
   - **App type**: 选择 **"script"**（重要！）
   - **description**: 简短描述（如 "Personal AI trend monitoring"）
   - **redirect uri**: 填写 `http://localhost:8080`（script类型必须填写但不会使用）
4. 记录:
   - **Client ID**: app名称下方的字符串（如 `abcd1234efgh`）
   - **Client Secret**: 标注为 "secret" 的那行

### 配置环境变量

```bash
# 1. 复制模板
cp config/env.example config/.env

# 2. 编辑config/.env，填入密钥
nano config/.env  # 或使用任何编辑器
```

必填内容：
```bash
TWITTER_BEARER_TOKEN=你的Twitter_Bearer_Token
REDDIT_CLIENT_ID=你的Reddit_Client_ID
REDDIT_CLIENT_SECRET=你的Reddit_Client_Secret
REDDIT_USER_AGENT=AI_Trend_Monitor/1.0  # 自定义，格式: AppName/Version
```

---

## 系统架构

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
Streamlit Dashboard (实时可视化)
```

### 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 采集 | Tweepy + PRAW | API数据采集 |
| 队列 | Apache Kafka | 消息缓冲 |
| 处理 | Spark Streaming | 实时ETL |
| 存储 | MinIO + Delta Lake | Lakehouse |
| 可视化 | Streamlit | 实时Dashboard |
| 容器化 | Docker Compose | 本地环境 |

### 目录结构

```
lakehouse_ai_pipeline/
├── config/                     # 配置文件
│   ├── .env                    # API密钥（需创建）
│   └── env.example             # 模板
│
├── data_ingestion/              # 数据采集
│   ├── twitter/collector.py    # Twitter爬虫
│   ├── reddit/collector.py     # Reddit爬虫
│   ├── kafka_producer.py       # Kafka生产者
│   └── config.py               # 配置管理
│
├── streaming/spark/             # Spark作业
│   ├── processor_with_minio.py # MinIO写入版本（推荐）
│   ├── simple_processor.py     # 控制台输出版本
│   └── jars/                   # Kafka+S3A连接器
│
├── dashboard/                   # 可视化
│   ├── app_realtime.py         # 实时Dashboard（推荐）
│   └── kafka_reader.py         # Kafka数据读取
│
├── scripts/                     # 启动脚本
│   ├── 01-full_restart.sh         # 完整重启 + 验证
│   ├── 02-start_spark_minio.sh  # 启动Spark写MinIO
│   ├── 03-start_dashboard.sh  # 启动Dashboard
│   ├── 99-verify_system.sh        # 系统健康检查
│   ├── start_collectors.sh     # 启动采集器
│   ├── stop_collectors.sh      # 停止采集器
│   └── 00-prepare_jars.sh   # 下载Spark依赖
│
├── docker-compose-full.yml      # 完整基础设施（使用中）
├── requirements.txt             # Python依赖
└── docs/                        # 文档
```

### 数据Schema设计

#### Bronze Layer (原始数据)
```python
{
    "source": "twitter" | "reddit",
    "event_timestamp": "ISO8601",
    "raw_data": {...},          # 原始JSON
    "processed_at": "timestamp",
    "partition_date": "YYYY-MM-DD"
}
```

#### Silver Layer (标准化数据 - 计划中)
```python
{
    "post_id": "string",
    "source": "string",
    "text": "string",
    "author": "string",
    "created_at": "timestamp",
    "engagement_score": "int",
    "keywords": ["string"],
    "hashtags": ["string"]
}
```

#### Gold Layer (趋势聚合 - 计划中)
```python
{
    "topic": "string",
    "hour": "timestamp",
    "mention_count": "int",
    "total_engagement": "int",
    "trend_score": "float"
}
```

---

## 完整使用场景

### 场景1：首次启动系统

```bash
# 1. 配置API密钥
cp config/env.example config/.env
nano config/.env  # 填入Twitter和Reddit API密钥

# 2. 一键完整重启（包含所有验证）
./scripts/01-full_restart.sh
# 这个脚本会：
# - 检查Docker、.env、venv、jar依赖
# - 停止所有现有服务
# - 启动Kafka、MinIO、Spark、采集器
# - 验证每个服务健康状态
# - 等待数据采集开始

# 3. 启动Spark写入MinIO（新建终端）
./scripts/02-start_spark_minio.sh
# 这会每30秒批量写入数据到MinIO

# 4. 启动Dashboard（新建终端）
./scripts/03-start_dashboard.sh
# 访问 http://localhost:8501
```

**预期输出**:
- Kafka有500+消息
- MinIO的 `lakehouse/bronze/social_media/` 有数据
- Spark UI显示活跃应用
- Dashboard显示实时数据

---

### 场景2：日常启动（已配置过）

```bash
# 方式1: 使用一键脚本
./scripts/01-full_restart.sh

# 方式2: 手动启动（更灵活）
docker-compose -f docker-compose-full.yml up -d
source venv/bin/activate
./scripts/start_collectors.sh
./scripts/02-start_spark_minio.sh  # 新建终端
./scripts/03-start_dashboard.sh  # 新建终端
```

---

### 场景3：验证系统状态

```bash
# 运行系统健康检查
./scripts/99-verify_system.sh
```

**检查项**:
- ✅ Docker服务（5个容器）
- ✅ 端口可访问性（8080, 9001, 9092）
- ✅ 数据采集器运行状态
- ✅ Kafka消息数量
- ✅ MinIO数据（重点！）
- ✅ Spark作业状态

---

### 场景4：查看数据和日志

**查看Kafka消息**:
```bash
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic ai-social-raw \
  --from-beginning \
  --max-messages 10
```

**查看采集器日志**:
```bash
# 实时查看
tail -f logs/twitter_collector.log
tail -f logs/reddit_collector.log

# 查看最近100行
tail -100 logs/twitter_collector.log
```

**查看MinIO数据**:
1. 访问 http://localhost:9001
2. 登录 (minioadmin/minioadmin)
3. 进入 `lakehouse` bucket
4. 查看 `bronze/social_media/partition_date=YYYY-MM-DD/` 目录
5. 应该看到Parquet文件

**命令行查看MinIO**:
```bash
docker exec minio mc ls --recursive myminio/lakehouse/bronze/social_media/
```

**查看Spark作业详情**:
- Master UI: http://localhost:8080
- Application UI: http://localhost:4040 (作业运行时)
- Worker UI: http://localhost:8081

---

### 场景5：停止所有服务

```bash
# 1. 停止Spark Streaming（按 Ctrl+C）
# 2. 停止Dashboard（按 Ctrl+C）
# 3. 停止采集器
./scripts/stop_collectors.sh

# 4. 停止基础设施
docker-compose -f docker-compose-full.yml down

# 5. （可选）删除所有数据卷
docker-compose -f docker-compose-full.yml down -v
```

---

## 故障排查大全

### 问题1: Docker无法启动

**症状**:
```
ERROR: Cannot connect to the Docker daemon
```

**解决**:
1. 打开Docker Desktop
2. 等待Docker完全启动
3. 验证: `docker ps`

---

### 问题2: Spark Worker启动失败

**症状**:
```
java.io.IOException: Failed to create directory /opt/spark/work/...
Executor 0-9 all failed
```

**原因**: 容器用户没有写权限

**解决**: 已在 `docker-compose-full.yml` 中修复
- Worker以root用户运行
- 使用 `/tmp/spark-work` 作为工作目录

如仍有问题:
```bash
docker-compose -f docker-compose-full.yml restart spark-worker
docker-compose -f docker-compose-full.yml logs spark-worker
```

---

### 问题3: Spark无法下载Kafka连接器

**症状**:
```
FileNotFoundException: /home/spark/.ivy2/cache/resolved-...
Failed to download org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0
```

**原因**: Maven依赖下载失败（网络或权限问题）

**解决**: 使用预下载jar的脚本
```bash
# 1. 预下载jar文件
./scripts/00-prepare_jars.sh

# 2. 使用修复后的脚本启动Spark
./scripts/02-start_spark_minio.sh
```

不要使用旧的 `start_spark_streaming.sh`（已弃用）

---

### 问题4: Twitter API 401错误

**症状**:
```
tweepy.errors.Unauthorized: 401 Unauthorized
```

**可能原因**:
- Bearer Token错误或过期
- 使用了错误的Token类型（应该用Bearer Token，不是API Key）

**解决**:
1. 检查 `config/.env` 中的 `TWITTER_BEARER_TOKEN`
2. 确认Twitter Developer账号状态
3. 测试连接:

```bash
source venv/bin/activate
python -c "
import os
from dotenv import load_dotenv
load_dotenv('config/.env')
token = os.getenv('TWITTER_BEARER_TOKEN')
print(f'Token存在: {bool(token)}')
print(f'Token长度: {len(token) if token else 0}')
print(f'Token前缀: {token[:20] if token else \"无\"}...')
"
```

---

### 问题5: Reddit连接失败

**症状**:
```
prawcore.exceptions.NotFound: received 404 HTTP response
prawcore.exceptions.TooManyRequests: received 429 HTTP response
```

**可能原因**:
- Subreddit名称错误或不存在
- API限流（请求过于频繁）
- redirect_uri未正确配置

**解决**:

**5.1 检查Subreddit名称**:
编辑 `data_ingestion/reddit/collector.py`，注释掉问题subreddit:
```python
TARGET_SUBREDDITS = [
    'MachineLearning',
    'LocalLLaMA',
    # 'ArtificialIntelligence',  # 暂时禁用
]
```

**5.2 增加采集间隔**:
编辑 `config/.env`:
```bash
REDDIT_COLLECTION_INTERVAL=600  # 改为10分钟
```

**5.3 验证API配置**:
```bash
python -c "
import praw
from dotenv import load_dotenv
import os
load_dotenv('config/.env')

reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)
print('只读模式:', reddit.read_only)
print('可以访问:', reddit.user.me() is None)
"
```

---

### 问题6: Dashboard无数据

**症状**: Dashboard显示 "No data available"

**检查清单**:

```bash
# 1. Kafka是否有数据？
docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic ai-social-raw

# 2. 采集器是否运行？
ps aux | grep collector

# 3. 查看采集器日志
tail -20 logs/twitter_collector.log
tail -20 logs/reddit_collector.log

# 4. 手动消费Kafka测试
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic ai-social-raw \
  --from-beginning \
  --max-messages 5
```

**常见解决方案**:
- 采集器未运行 → `./scripts/start_collectors.sh`
- API密钥错误 → 检查 `config/.env`
- Kafka未启动 → `docker-compose -f docker-compose-full.yml up -d`

---

### 问题7: 端口占用

**症状**:
```
Port 8080 is already in use
Error starting userland proxy: listen tcp4 0.0.0.0:9092: bind: address already in use
```

**解决**:

```bash
# 查找占用进程
lsof -i :8080
lsof -i :9092

# 停止冲突服务
docker-compose -f docker-compose-full.yml down

# 或杀掉进程（谨慎！）
kill -9 <PID>
```

---

### 问题8: MinIO没有数据

**症状**: 访问MinIO Console看不到 `bronze/social_media/` 数据

**原因**: 可能还在用旧的控制台输出版Spark处理器

**解决**:

```bash
# 1. 停止旧的Spark作业（如果有）
# 在运行Spark的终端按 Ctrl+C

# 2. 使用MinIO写入版本
./scripts/02-start_spark_minio.sh

# 3. 等待30秒（第一个批次）

# 4. 验证MinIO数据
docker exec minio mc ls --recursive myminio/lakehouse/bronze/social_media/

# 5. 或访问 http://localhost:9001 查看
```

---

### 问题9: Spark作业内存不足

**症状**:
```
Container killed by YARN for exceeding memory limits
java.lang.OutOfMemoryError: Java heap space
```

**解决**:

编辑 `scripts/02-start_spark_minio.sh`，增加内存配置:
```bash
--conf spark.executor.memory=2g \
--conf spark.driver.memory=2g \
```

确保Docker Desktop分配足够内存（设置 → Resources → Memory → 至少4GB）

---

### 问题10: Docker Compose警告

**症状**:
```
WARN[0000] /path/to/docker-compose.yml: `version` is obsolete
```

**解决**: 这只是警告，不影响运行

如想消除:
```bash
# 编辑docker-compose-full.yml，删除第一行的version字段
sed -i.bak '1d' docker-compose-full.yml
```

---

## 命令速查表

### 启动相关
```bash
./scripts/01-full_restart.sh                 # 完整重启 + 验证所有组件
./scripts/02-start_spark_minio.sh       # 启动Spark写MinIO
./scripts/03-start_dashboard.sh     # 启动Dashboard
./scripts/start_collectors.sh             # 启动采集器
```

### 停止相关
```bash
./scripts/stop_collectors.sh              # 停止采集器
docker-compose -f docker-compose-full.yml down  # 停止基础设施
docker-compose -f docker-compose-full.yml down -v  # 停止并删除数据
```

### 查看相关
```bash
# 系统状态
./scripts/99-verify_system.sh                # 完整健康检查
docker ps                                 # 查看容器状态
docker-compose -f docker-compose-full.yml logs -f  # 查看所有日志

# 采集器日志
tail -f logs/twitter_collector.log        # Twitter实时日志
tail -f logs/reddit_collector.log         # Reddit实时日志

# Kafka
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic ai-social-raw \
  --from-beginning \
  --max-messages 10                       # 查看消息

# MinIO
docker exec minio mc ls --recursive myminio/lakehouse/bronze/social_media/
```

### 测试相关
```bash
curl http://localhost:8080                # 测试Spark Master
curl http://localhost:9000/minio/health/live  # 测试MinIO
curl http://localhost:9001                # 测试MinIO Console
```

### 重置系统
```bash
# 完全重置（删除所有数据）
./scripts/stop_collectors.sh
docker-compose -f docker-compose-full.yml down -v
rm -rf logs/*.log
# 然后重新启动
./scripts/01-full_restart.sh
```

---

## 扩展路线图

### ✅ 已完成

- [x] Phase 1: MVP架构搭建
- [x] Phase 2A: Dashboard实时展示
- [x] Phase 2B: Spark Streaming集成
- [x] Phase 2C: MinIO持久化（Bronze层）

### 🔄 Phase 3: Delta Lake完整实现（下一步）

**目标**: 实现完整的Bronze/Silver/Gold三层架构

**任务**:
1. 修改 `streaming/spark/processor_with_minio.py`
2. 添加Delta Lake格式写入（替代Parquet）
3. 实现Silver层数据清洗:
   - 去重（基于post_id）
   - 文本标准化
   - 关键词提取
4. 实现Gold层聚合:
   - 按小时聚合趋势
   - 热点话题排名
   - 用户活跃度统计
5. Dashboard连接Delta Lake读取

**预计时间**: 1-2周

---

### 📅 Phase 4: 向量搜索和RAG（2-3周后）

**目标**: 语义搜索和智能问答

**技术栈**:
- Milvus（向量数据库）
- Sentence Transformers（文本embedding）
- LangChain + OpenAI/Claude API

**功能**:
- 语义相似搜索："找出所有关于GPT-5的讨论"
- 自然语言问答："最近大家对Claude的评价如何？"
- 趋势预测："哪个AI话题最近热度上升最快？"

**实施步骤**:
1. 添加Milvus到 `docker-compose-full.yml`
2. 实现文本向量化 Pipeline
3. 构建RAG问答接口
4. Dashboard添加搜索功能

---

### 🚀 Phase 5: 生产化部署（1个月后）

**目标**: 部署到云端，实现高可用

**改进点**:
- **云端迁移**: AWS S3 + EMR 或 Azure HDInsight
- **Kafka集群**: 3节点高可用配置
- **Spark HA**: 多Master + Zookeeper协调
- **监控告警**: Prometheus + Grafana + AlertManager
- **CI/CD**: GitHub Actions自动部署
- **成本优化**: S3生命周期策略，Spot实例

---

## 性能指标

### 当前系统容量

| 指标 | 当前值 | 理论上限 |
|------|--------|----------|
| 采集频率 | 5分钟/次 | API限制 |
| Kafka吞吐 | ~100msg/s | 10K msg/s |
| Spark处理延迟 | <30秒 | <1秒 |
| 存储 | MinIO无限 | 磁盘空间 |
| 数据保留 | Kafka 7天 | 可配置 |

### 资源使用

- **Docker内存**: 建议4GB+（当前配置）
- **磁盘空间**: 10GB+（数据增长）
- **CPU**: 2核心+
- **网络**: 需稳定连接（API调用）

---

## 获取帮助

### 日志位置

- 采集器日志: `logs/*.log`
- Spark日志: `docker-compose -f docker-compose-full.yml logs spark-master`
- Kafka日志: `docker-compose -f docker-compose-full.yml logs kafka`
- MinIO日志: `docker-compose -f docker-compose-full.yml logs minio`

### 调试技巧

1. **从上游到下游排查**:
   ```
   API → 采集器 → Kafka → Spark → MinIO → Dashboard
   ```

2. **使用99-verify_system.sh**:
   ```bash
   ./scripts/99-verify_system.sh
   ```

3. **查看Docker日志**:
   ```bash
   docker-compose -f docker-compose-full.yml logs -f --tail=100
   ```

4. **进入容器调试**:
   ```bash
   docker exec -it spark-master bash
   docker exec -it kafka bash
   docker exec -it minio bash
   ```

---

## 学习资源

### 必读文档

- [Delta Lake官方文档](https://docs.delta.io/)
- [Spark Structured Streaming编程指南](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Kafka文档](https://kafka.apache.org/documentation/)
- [MinIO文档](https://min.io/docs/)

### 推荐课程

- DataTalksClub - Data Engineering Zoomcamp
- Databricks Academy - Lakehouse Fundamentals
- Apache Spark官方教程

### 相关项目参考

- [Awesome Data Engineering](https://github.com/igorbarinov/awesome-data-engineering)
- [Real-time Stream Processing Examples](https://github.com/topics/stream-processing)

---

## 项目成果

通过这个项目，你已经掌握:

✅ **数据工程技能**
- 完整的ETL pipeline搭建
- 实时数据处理（Streaming）
- Lakehouse架构实践

✅ **技术栈实践**
- Docker容器化部署
- Apache Kafka消息队列
- Spark分布式计算
- Python数据采集和处理
- MinIO对象存储

✅ **项目管理能力**
- 分阶段实施（MVP → Phase 2 → Phase 3）
- 问题排查和解决
- 文档编写和维护

---

**恭喜你完成了Phase 2B！** 🎉

系统现在可以:
- ✅ 实时采集Twitter和Reddit数据
- ✅ 通过Kafka传输
- ✅ Spark实时处理
- ✅ 写入MinIO持久化存储
- ✅ Dashboard可视化展示

**下一个里程碑**: 实现Delta Lake完整三层架构 🚀

---

**文档版本**: 2.0
**最后更新**: 2025-11-11
**维护者**: Guangyao Li
**项目开始**: 2025-11-11
