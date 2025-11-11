# AI Trend Real-time Monitoring System

实时监控社交媒体上的AI领域讨论，检测热点话题，分析趋势变化。

**项目状态**: ✅ Phase 2B 完成 | **版本**: v1.0

## 🎯 项目简介

基于现代Lakehouse架构的全栈AI数据工程项目，实现完整的实时数据处理pipeline：

```
Twitter/Reddit → Kafka → Spark Streaming → MinIO + Delta Lake → Dashboard
```

**核心特性**:
- ✅ 实时数据采集（Twitter + Reddit API）
- ✅ 流式处理（Kafka + Spark Streaming）
- ✅ Lakehouse架构（MinIO + Delta Lake）
- ✅ 实时Dashboard（Streamlit）
- 🔜 向量搜索 + RAG（计划中）

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

## 🚀 快速开始（5分钟）

```bash
# 1. 配置API密钥
cp config/env.example config/.env
# 编辑填入Twitter和Reddit密钥

# 2. 启动完整基础设施
./scripts/start_full_infrastructure.sh

# 3. 安装Python环境
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 4. 启动数据采集
./scripts/start_collectors.sh

# 5. 准备Spark依赖（首次）
./scripts/prepare_spark_jars.sh

# 6. 启动Spark处理
./scripts/start_spark_streaming_fixed.sh
```

**访问点：**
- Spark UI: http://localhost:8080
- MinIO Console: http://localhost:9001
- Dashboard: `./scripts/start_dashboard_realtime.sh`

📖 **详细指南**: [docs/COMPLETE_GUIDE.md](docs/COMPLETE_GUIDE.md)

## 📚 文档导航

| 文档 | 说明 |
|------|------|
| **[COMPLETE_GUIDE.md](docs/COMPLETE_GUIDE.md)** | 📖 完整使用指南（主文档） |
| **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** | 🔧 故障排查和已知问题 |
| **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** | 🏗️ 技术架构详解 |
| **[QUICKSTART.md](docs/QUICKSTART.md)** | ⚡ API密钥配置指南 |

## 📊 数据查看

**Kafka消息：**
```bash
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic ai-social-raw --max-messages 10
```

**MinIO存储：**
- 访问: http://localhost:9001
- 凭证: minioadmin / minioadmin

**Spark作业：**
- Master UI: http://localhost:8080
- Application UI: http://localhost:4040

## 🎯 已完成功能

✅ **Phase 1**: MVP架构搭建
✅ **Phase 2A**: Dashboard实时数据展示
✅ **Phase 2B**: 完整Spark Streaming处理

## 🔮 下一步计划

**Phase 3**: Delta Lake持久化（1-2周）
- 实现Bronze/Silver/Gold数据分层
- Dashboard从Delta Lake读取数据

**Phase 4**: 向量搜索 + RAG（2-3周）
- Milvus向量数据库
- 语义搜索和智能问答
- LangChain + OpenAI/Claude API

**Phase 5**: 生产化部署（1个月+）
- 云端部署（AWS/Azure）
- 高可用配置
- 监控告警系统

## 🤝 贡献与反馈

这是一个个人学习项目，旨在实践现代数据工程技术栈。

**问题反馈**: GitHub Issues
**文档改进**: Pull Requests欢迎

## 📄 许可证

MIT License

---

**维护者**: Guangyao Li
**最后更新**: 2025-11-11
**版本**: v1.0 (Phase 2B完成)
