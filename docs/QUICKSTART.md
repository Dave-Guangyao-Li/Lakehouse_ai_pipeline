# 快速入门指南 (Quick Start Guide)

本指南将帮助你在15分钟内启动AI趋势监控系统。

## 前置要求检查

在开始之前，请确保已安装：

- [ ] Docker Desktop (>= 4.0) - [下载链接](https://www.docker.com/products/docker-desktop)
- [ ] Python 3.9+ - 检查: `python3 --version`
- [ ] Git (可选)

## 第一步：获取API密钥

### Twitter API (必需)

1. 访问 [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. 创建一个新的App
3. 生成API密钥：
   - API Key
   - API Secret
   - Bearer Token

### Reddit API (必需)

1. 访问 [Reddit Apps](https://www.reddit.com/prefs/apps)
2. 点击 "Create App" 或 "Create Another App"
3. 填写应用信息：
   - **name**: 任意名称（如 "AI Trend Monitor"）
   - **App type**: 选择 "**script**"（个人使用）
   - **description**: 简短描述（如 "Personal AI trend monitoring tool"）
   - **about url**: 留空即可
   - **redirect uri**: 填写 `http://localhost:8080`（script类型不会实际使用，但必须填写）
4. 点击 "Create app"
5. 记录以下信息：
   - **Client ID**: 在app名称下方的一串字符（如 `abcd1234efgh`）
   - **Client Secret**: 标注为 "secret" 的那一行

## 第二步：配置环境变量

```bash
# 1. 复制环境变量模板
cp config/env.example config/.env

# 2. 编辑 config/.env 文件，填入你的API密钥
nano config/.env  # 或使用任何文本编辑器
```

必须配置的变量：
```bash
TWITTER_BEARER_TOKEN=你的Twitter Bearer Token
REDDIT_CLIENT_ID=你的Reddit Client ID
REDDIT_CLIENT_SECRET=你的Reddit Client Secret
```

## 第三步：启动基础设施

```bash
# 给脚本添加执行权限
chmod +x scripts/*.sh

# 启动所有基础服务（Kafka, MinIO, Spark）
./scripts/start_infrastructure.sh
```

等待所有服务启动完成（约30秒）。

**验证服务状态：**
- Kafka: `docker ps | grep kafka`
- MinIO Console: 打开浏览器访问 http://localhost:9001
  - 用户名: `minioadmin`
  - 密码: `minioadmin`
- Spark Master UI: http://localhost:8080

## 第四步：安装Python依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或 Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

## 第五步：启动数据采集器

```bash
# 启动Twitter和Reddit采集器
./scripts/start_collectors.sh
```

**查看采集日志：**
```bash
# 实时查看Twitter采集日志
tail -f logs/twitter_collector.log

# 实时查看Reddit采集日志
tail -f logs/reddit_collector.log
```

## 第六步：启动Dashboard

打开新的终端窗口：

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动Streamlit Dashboard
./scripts/start_dashboard.sh
```

浏览器会自动打开 http://localhost:8501

## 第七步（可选）：启动Spark Streaming

如果你想实时处理数据并写入Delta Lake：

```bash
# 提交Spark Streaming作业
spark-submit \
  --packages io.delta:delta-core_2.12:2.4.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0 \
  --master spark://localhost:7077 \
  streaming/spark/processor.py
```

## 验证系统运行

### 1. 检查Kafka消息

```bash
# 查看Kafka topic列表
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

# 查看原始数据流
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic ai-social-raw \
  --from-beginning \
  --max-messages 10
```

### 2. 检查MinIO存储

1. 访问 http://localhost:9001
2. 登录后查看 `lakehouse` bucket
3. 应该能看到 `bronze/`, `silver/`, `gold/` 目录

### 3. 查看Dashboard

访问 http://localhost:8501，你应该看到：
- 实时热点话题
- 数据源统计
- 趋势图表

## 停止系统

```bash
# 停止数据采集器
./scripts/stop_collectors.sh

# 停止基础设施
docker-compose down

# 停止Dashboard (在Dashboard终端按 Ctrl+C)
```

## 常见问题

### Q: Kafka连接失败
**A:** 确保Docker容器正在运行：
```bash
docker ps | grep kafka
docker-compose logs kafka
```

### Q: API限流错误
**A:** Twitter/Reddit API有请求限制。调整采集频率：
```bash
# 编辑 config/.env
COLLECTION_INTERVAL_SECONDS=600  # 改为10分钟
```

### Q: 没有看到数据
**A:** 检查：
1. API密钥是否正确配置
2. 采集器日志是否有错误
3. Kafka中是否有消息

```bash
tail -f logs/twitter_collector.log
tail -f logs/reddit_collector.log
```

### Q: Spark任务失败
**A:** 检查内存配置，确保Docker有足够资源（推荐8GB+）

## 下一步

恭喜！系统已经运行起来了。接下来可以：

1. **查看详细规划**: 阅读 [PROJECT_PLAN.md](PROJECT_PLAN.md)
2. **自定义关键词**: 编辑 `config/.env` 中的 `AI_KEYWORDS`
3. **添加新数据源**: 参考 `data_ingestion/` 中的示例代码
4. **实现RAG功能**: 查看Phase 2扩展计划
5. **优化性能**: 调整Spark并行度和内存配置

## 获取帮助

- 查看 [README.md](../README.md) 获取完整文档
- 查看 [PROJECT_PLAN.md](PROJECT_PLAN.md) 了解架构设计
- 检查日志文件排查问题

---

**预计完成时间**: 15-20分钟
**难度级别**: 初级-中级
**最后更新**: 2025-11-11
