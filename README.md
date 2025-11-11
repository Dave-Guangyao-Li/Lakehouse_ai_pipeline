# AI Trend Real-time Monitoring System

实时监控社交媒体上的AI领域讨论，检测热点话题，分析趋势变化。

## 项目简介

这是一个基于现代Lakehouse架构的全栈AI数据工程项目，从社交媒体（Twitter/Reddit）实时采集AI相关讨论，通过流处理分析热点趋势，并提供可视化Dashboard。

**核心特性**:
- 实时数据采集（Twitter + Reddit API）
- 流式处理（Kafka + Spark Streaming）
- Lakehouse架构存储（MinIO + Delta Lake）
- 热点话题自动检测
- 实时Dashboard展示

## 技术栈

### MVP阶段
- **数据采集**: Python, Tweepy, PRAW
- **消息队列**: Apache Kafka
- **流处理**: Spark Structured Streaming
- **存储**: MinIO (S3兼容) + Delta Lake
- **分析**: DuckDB
- **可视化**: Streamlit
- **容器化**: Docker Compose

### 未来扩展
- 向量数据库: Milvus
- RAG框架: LangChain + OpenAI/Claude API
- 任务调度: Apache Airflow
- 批处理: Apache Spark (PySpark)

## 项目结构

```
lakehouse_ai_pipeline/
├── docs/
│   └── PROJECT_PLAN.md          # 详细项目规划文档
├── data_ingestion/              # 数据采集层
│   ├── twitter/                 # Twitter爬虫
│   ├── reddit/                  # Reddit爬虫
│   └── kafka_producer.py        # Kafka生产者
├── streaming/                   # 流处理层
│   ├── kafka/                   # Kafka配置
│   └── spark/                   # Spark Streaming作业
├── storage/                     # 存储层
│   ├── minio/                   # MinIO配置
│   └── delta_lake/              # Delta Lake表定义
├── analytics/                   # 分析脚本
│   └── queries.py               # DuckDB查询
├── dashboard/                   # 可视化层
│   └── app.py                   # Streamlit应用
├── config/                      # 配置文件
├── docker-compose.yml           # 容器编排
└── README.md
```

## 快速开始

### 前置要求

- Docker Desktop (>= 4.0)
- Python 3.9+
- Twitter Developer账号（用于API访问）
- Reddit API密钥

### 安装步骤

#### 1. 克隆项目（或使用当前目录）

```bash
cd lakehouse_ai_pipeline
```

#### 2. 配置环境变量

```bash
cp config/env.example config/.env
# 编辑 config/.env 填入你的API密钥
```

需要配置的密钥:
- `TWITTER_API_KEY`
- `TWITTER_API_SECRET`
- `TWITTER_BEARER_TOKEN`
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`

#### 3. 启动基础设施

```bash
docker-compose up -d
```

这将启动:
- Kafka (端口: 9092)
- Zookeeper (端口: 2181)
- MinIO (端口: 9000, Console: 9001)
- Spark Master (端口: 7077, UI: 8080)
- Spark Worker

#### 4. 安装Python依赖

```bash
pip install -r requirements.txt
```

#### 5. 启动数据采集

```bash
# 启动Twitter采集器
python data_ingestion/twitter/collector.py &

# 启动Reddit采集器
python data_ingestion/reddit/collector.py &
```

#### 6. 启动Spark Streaming作业

```bash
spark-submit \
  --packages io.delta:delta-core_2.12:2.4.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0 \
  streaming/spark/processor.py
```

#### 7. 启动Dashboard

```bash
streamlit run dashboard/app.py
```

访问 `http://localhost:8501` 查看实时Dashboard

## 使用指南

### 查看Kafka消息

```bash
docker exec -it kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic ai-social-raw \
  --from-beginning
```

### 查看MinIO数据

访问 `http://localhost:9001`，使用默认凭证登录：
- 用户名: `minioadmin`
- 密码: `minioadmin`

### 查询Delta Lake数据

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# 读取Silver层数据
df = spark.read.format("delta").load("s3a://lakehouse/silver/social_posts")
df.show()
```

## 开发指南

### 添加新的数据源

1. 在 `data_ingestion/` 创建新目录（如 `hackernews/`）
2. 实现爬虫脚本 `collector.py`
3. 在Kafka Producer中添加新topic
4. 更新Spark Streaming作业以处理新数据源

### 修改热点检测算法

编辑 `streaming/spark/processor.py` 中的 `detect_trending_topics()` 函数。

当前实现:
```python
trend_score = (mention_count * engagement) / time_decay
```

### 自定义Dashboard

编辑 `dashboard/app.py`，使用Streamlit组件：
- `st.line_chart()` - 趋势图表
- `st.bar_chart()` - 柱状图
- `st.dataframe()` - 数据表格
- `st.metric()` - 指标卡片

## 数据架构

### Delta Lake分层

```
Bronze Layer (原始数据)
  ├── 保留完整JSON格式
  ├── 分区: date
  └── 保留期: 30天

Silver Layer (清洗数据)
  ├── 标准化Schema
  ├── 去重
  ├── 分区: date, source
  └── 保留期: 90天

Gold Layer (聚合数据)
  ├── 按小时/话题聚合
  ├── 趋势计算
  └── 保留期: 1年
```

## 监控与运维

### 查看Spark作业状态

访问 `http://localhost:8080` 查看Spark Master UI

### 查看Kafka消费者lag

```bash
docker exec -it kafka kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe \
  --group spark-streaming-group
```

### 查看容器日志

```bash
docker-compose logs -f spark-streaming
```

## 故障排除

### Kafka连接失败

检查Kafka是否正常运行:
```bash
docker ps | grep kafka
docker-compose logs kafka
```

### Spark任务OOM

调整 `docker-compose.yml` 中的Spark内存配置:
```yaml
environment:
  - SPARK_WORKER_MEMORY=4g
  - SPARK_EXECUTOR_MEMORY=2g
```

### MinIO访问权限问题

重新设置bucket权限:
```bash
docker exec -it minio mc policy set public myminio/lakehouse
```

## 路线图

- [x] MVP规划文档
- [ ] 基础设施搭建（Docker Compose）
- [ ] 数据采集模块（Twitter + Reddit）
- [ ] Spark Streaming流处理
- [ ] Delta Lake存储配置
- [ ] Streamlit Dashboard
- [ ] 向量搜索（Milvus）
- [ ] RAG问答系统
- [ ] Airflow调度
- [ ] 生产环境部署

详细规划见 [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md)

## 贡献

这是一个个人学习项目，欢迎提出建议和改进意见！

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎通过以下方式联系:
- GitHub Issues
- Email: [你的邮箱]

---

**项目状态**: 🚧 开发中 (MVP阶段)

最后更新: 2025-11-11
