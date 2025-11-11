# AI 趋势实时监控系统 - 项目规划文档

## 📌 项目概览

### 项目名称
**AI Trend Real-time Monitoring System（AI趋势实时监控系统）**

### 项目目标
构建一个可扩展的数据工程和AI应用，实时监控社交媒体上的AI领域讨论，检测热点话题，分析趋势变化，并提供智能洞察。通过这个项目学习和实践现代数据湖仓（Lakehouse）架构和实时数据处理技术栈。

### 核心价值
- **个人价值**: 持续追踪AI领域最新动态，发现值得深入学习的话题
- **技术价值**: 掌握完整的数据工程技术栈（流处理、数据湖、AI应用）
- **可扩展性**: MVP设计可逐步演进为生产级系统

---

## 🏗️ 技术架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          数据采集层                                    │
│  Twitter API  │  Reddit API  │  (未来: HackerNews, Podcasts)         │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        消息队列层 (Kafka)                             │
│  Topic: ai-tweets  │  ai-reddit  │  ai-news                         │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    流处理层 (Spark Streaming)                         │
│  - 实时数据清洗  │  - 关键词提取  │  - 情感分析  │  - 热点检测      │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   存储层 (MinIO + Delta Lake)                        │
│  Bronze Layer (原始数据) → Silver Layer (清洗后) → Gold Layer (聚合) │
└────────────────┬────────────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
┌──────────────┐  ┌──────────────────┐
│  分析层       │  │  可视化层          │
│  - DuckDB    │  │  - Streamlit      │
│  - 趋势分析   │  │  - 实时Dashboard   │
│  (未来: RAG)  │  │  (未来: Tableau)   │
└──────────────┘  └──────────────────┘
```

### 技术栈选择

#### Phase 1: MVP 阶段（当前重点）

| 层级 | 技术 | 选择理由 |
|------|------|----------|
| **数据采集** | Python + Tweepy/PRAW | 成熟的API库，快速开发 |
| **消息队列** | Apache Kafka | 行业标准流式消息队列，支持高吞吐 |
| **流处理** | Spark Streaming | 与Spark生态集成好，易于扩展到批处理 |
| **对象存储** | MinIO | 本地S3兼容存储，开发友好 |
| **数据湖** | Delta Lake | ACID支持，时间旅行，Schema演化 |
| **轻量分析** | DuckDB | 内嵌分析数据库，无需单独服务 |
| **可视化** | Streamlit | Python原生，快速原型开发 |
| **容器化** | Docker Compose | 本地开发环境一键启动 |

#### Phase 2: 扩展阶段（未来规划）

| 新增功能 | 技术选择 |
|----------|----------|
| **向量搜索** | Milvus + Sentence Transformers |
| **RAG问答** | LangChain + OpenAI API |
| **任务调度** | Apache Airflow |
| **批处理** | Apache Spark (PySpark) |
| **高级可视化** | Apache Superset 或 Metabase |

---

## 🎯 MVP 功能规划

### 核心功能（第一版）

#### 1. 数据采集模块
- **Twitter监控**
  - 使用Twitter API v2 采集包含AI关键词的推文
  - 关键词列表: `["GPT", "Claude", "LLM", "机器学习", "深度学习", "AI", "OpenAI", "Anthropic"]`
  - 采集频率: 每5分钟轮询一次
  - 数据字段: `{tweet_id, text, author, created_at, likes, retweets, hashtags}`

- **Reddit监控**
  - 监控子版块: r/MachineLearning, r/artificial, r/LocalLLaMA
  - 采集新帖子和热门评论
  - 采集频率: 每10分钟
  - 数据字段: `{post_id, title, text, author, subreddit, score, num_comments, created_at}`

#### 2. 实时流处理
- **数据清洗**
  - 去重（基于ID）
  - 文本标准化（去除特殊字符、URL）
  - 语言检测（过滤非英文/中文）

- **特征提取**
  - 关键词频率统计
  - Hashtag提取
  - 提及的AI公司/模型识别

- **热点检测**
  - 滑动窗口（1小时）内话题频率突增检测
  - 计算话题热度分数 = (提及次数 × 互动量) / 时间衰减

#### 3. 数据湖存储（Delta Lake三层架构）
```
storage/
├── bronze/              # 原始数据（JSON格式，保留所有字段）
│   ├── twitter/
│   └── reddit/
├── silver/              # 清洗后的数据（Parquet格式，标准化Schema）
│   ├── social_posts/
│   └── trending_topics/
└── gold/                # 聚合分析结果（按时间/话题聚合）
    ├── hourly_trends/
    └── topic_timeseries/
```

#### 4. 简单Dashboard
- **实时监控面板**（Streamlit应用）
  - 当前热点话题Top 10
  - 话题趋势折线图（最近24小时）
  - 关键词词云
  - 数据源统计（Twitter vs Reddit占比）
  - 实时消息流（最新20条）

---

## 📊 数据流设计

### 实时数据流
```
1. 数据采集 (每5-10分钟)
   ↓
2. 发送到Kafka Topic
   - ai-social-raw (原始数据)
   ↓
3. Spark Streaming消费
   - 读取Kafka
   - 清洗 + 特征提取
   - 热点检测
   ↓
4. 写入Delta Lake
   - Bronze: 原始数据存档
   - Silver: 清洗后数据
   - Gold: 聚合统计结果
   ↓
5. Dashboard查询展示
   - DuckDB查询Delta Lake
   - Streamlit实时刷新
```

### 数据Schema设计

#### Bronze Layer (原始数据)
```python
{
    "source": "twitter" | "reddit",
    "raw_data": {...},          # 原始JSON
    "ingested_at": "timestamp",
    "partition_date": "YYYY-MM-DD"
}
```

#### Silver Layer (标准化数据)
```python
{
    "post_id": "string",
    "source": "string",
    "text": "string",
    "author": "string",
    "created_at": "timestamp",
    "engagement_score": "int",   # likes/retweets/score
    "keywords": ["string"],
    "hashtags": ["string"],
    "processed_at": "timestamp"
}
```

#### Gold Layer (趋势聚合)
```python
{
    "topic": "string",
    "hour": "timestamp",
    "mention_count": "int",
    "total_engagement": "int",
    "top_posts": ["post_id"],
    "trend_score": "float"
}
```

---

## 🚀 实施步骤

### Phase 1.1: 基础设施搭建（Week 1）

- [ ] 创建项目结构和Git仓库
- [ ] 编写 `docker-compose.yml`
  - Kafka + Zookeeper
  - MinIO (S3替代)
  - Spark Standalone集群
- [ ] 配置网络和数据卷持久化
- [ ] 测试容器启动和连通性

### Phase 1.2: 数据采集层（Week 2）

- [ ] 申请Twitter Developer账号和API密钥
- [ ] 申请Reddit API密钥
- [ ] 实现Twitter爬虫 (`data_ingestion/twitter/collector.py`)
- [ ] 实现Reddit爬虫 (`data_ingestion/reddit/collector.py`)
- [ ] 实现Kafka Producer (`data_ingestion/kafka_producer.py`)
- [ ] 测试数据采集并发送到Kafka

### Phase 1.3: 流处理层（Week 3）

- [ ] 编写Spark Streaming作业 (`streaming/spark/processor.py`)
  - Kafka消费者配置
  - 数据清洗逻辑
  - 关键词提取
  - 热点检测算法
- [ ] 配置Delta Lake写入
- [ ] 测试端到端数据流

### Phase 1.4: 存储和分析层（Week 4）

- [ ] 配置MinIO和Delta Lake表结构
- [ ] 实现Bronze/Silver/Gold数据分层逻辑
- [ ] 编写DuckDB查询脚本 (`analytics/queries.py`)
- [ ] 创建数据质量检查脚本

### Phase 1.5: 可视化层（Week 5）

- [ ] 开发Streamlit Dashboard (`dashboard/app.py`)
  - 实时热点话题展示
  - 趋势图表
  - 词云可视化
  - 数据统计卡片
- [ ] 连接DuckDB数据源
- [ ] 优化刷新性能

### Phase 1.6: 测试和优化（Week 6）

- [ ] 端到端测试
- [ ] 性能优化（Kafka分区、Spark并行度）
- [ ] 错误处理和日志
- [ ] 编写部署文档

---

## 🔮 扩展路线图

### Phase 2: 增强分析能力（Month 2-3）

#### 2.1 向量化搜索
- 集成Milvus向量数据库
- 使用Sentence Transformers生成文本embedding
- 实现语义相似内容搜索

#### 2.2 RAG问答系统
- 基于LangChain构建RAG框架
- 连接OpenAI/Claude API
- 支持自然语言查询: "最近关于GPT-5的讨论有哪些？"

#### 2.3 高级分析
- 情感分析（正面/负面/中性）
- 话题建模（LDA）
- 影响力用户识别

### Phase 3: 多模态和自动化（Month 4-6）

#### 3.1 播客集成
- 添加AI播客数据源（RSS订阅）
- 音频转录（Whisper API）
- 播客内容向量化和检索

#### 3.2 调度自动化
- 集成Apache Airflow
- DAG任务编排
- 自动化数据质量检查
- 定时报告生成

#### 3.3 批处理分析
- 使用Spark批处理历史数据
- 生成周报/月报
- 趋势预测模型

### Phase 4: 生产化（Month 6+）

- 迁移到云端（AWS S3 + EMR / Azure）
- 高可用性配置（Kafka集群、Spark HA）
- 监控和告警（Prometheus + Grafana）
- CI/CD流水线
- 成本优化

---

## 💡 技术挑战与解决方案

### 挑战1: API限流
**问题**: Twitter/Reddit API有请求频率限制
**解决方案**:
- 实现指数退避重试机制
- 使用多个API密钥轮询
- 缓存最近查询结果

### 挑战2: 数据去重
**问题**: 同一内容可能被多次采集
**解决方案**:
- 使用Delta Lake的MERGE INTO实现upsert
- 基于唯一ID（tweet_id/post_id）去重

### 挑战3: 实时性能
**问题**: Spark Streaming延迟可能较高
**解决方案**:
- 优化micro-batch间隔（从10s调整到5s）
- 使用Structured Streaming的连续处理模式
- 考虑未来迁移到Flink（延迟更低）

### 挑战4: 存储成本
**问题**: 长期存储大量社交媒体数据成本高
**解决方案**:
- 实现数据生命周期策略（Bronze保留30天，Silver保留90天）
- 使用Parquet压缩格式
- 定期归档冷数据到低成本存储

---

## 📈 成功指标

### MVP阶段（Phase 1完成时）
- [ ] 成功采集并存储 10,000+ 条社交媒体帖子
- [ ] 实时处理延迟 < 1分钟
- [ ] 准确识别至少5个热点话题
- [ ] Dashboard稳定运行，刷新延迟 < 3秒
- [ ] 数据质量：去重率 > 95%

### 长期目标
- [ ] 日均处理 50,000+ 条消息
- [ ] 支持10+数据源
- [ ] RAG问答准确率 > 85%
- [ ] 系统可用性 > 99%

---

## 📚 学习资源

### 必读文档
- [Delta Lake官方文档](https://docs.delta.io/)
- [Spark Structured Streaming编程指南](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Kafka Connect文档](https://kafka.apache.org/documentation/)

### 推荐课程
- DataTalksClub - Data Engineering Zoomcamp
- Databricks Academy - Lakehouse Fundamentals

### 相关项目参考
- [Awesome Data Engineering](https://github.com/igorbarinov/awesome-data-engineering)
- [Real-time Stream Processing Examples](https://github.com/topics/stream-processing)

---

## 🤝 贡献指南

这是一个个人学习项目，但设计时考虑了可扩展性。未来可能开源并接受社区贡献。

---

**最后更新**: 2025-11-11
**版本**: v1.0 - MVP规划
**作者**: Guangyao Li
