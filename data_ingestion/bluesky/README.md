# Bluesky Collector

收集来自 Bluesky 社交网络的 AI 相关帖子。

## 功能特性

- 🔵 使用 AT Protocol API 收集 Bluesky 帖子
- 🤖 专注于 AI 相关内容
- 📊 提取点赞、转发、回复等互动数据
- 🔄 定时自动采集
- 📤 数据发送到 Kafka

## 环境变量配置

在 `config/.env` 文件中添加以下配置:

```bash
# Bluesky API 配置
BLUESKY_HANDLE=your-handle.bsky.social
BLUESKY_APP_PASSWORD=your-app-password

# 可选: 采集间隔(秒)，默认使用 COLLECTION_INTERVAL_SECONDS
BLUESKY_COLLECTION_INTERVAL=60
```

### 获取 App Password

1. 登录 Bluesky: https://bsky.app/
2. 进入 Settings → App Passwords
3. 点击 "Add App Password"
4. 输入名称(如 "Lakehouse Pipeline")
5. 复制生成的密码并保存到 `.env` 文件

**注意**: 不要使用主密码,必须创建 App Password!

## 安装依赖

```bash
pip install atproto
```

或使用项目的 requirements:

```bash
pip install -r requirements.txt
```

## 运行 Collector

### 方式 1: 直接运行

```bash
cd data_ingestion/bluesky
python collector.py
```

### 方式 2: 使用 Docker (推荐)

更新 `docker-compose.yml` 添加 Bluesky 服务:

```yaml
bluesky-collector:
  build:
    context: ./data_ingestion
    dockerfile: Dockerfile
  command: python bluesky/collector.py
  env_file:
    - config/.env
  depends_on:
    - kafka
  restart: unless-stopped
  volumes:
    - ./logs:/app/logs
```

## 数据格式

发送到 Kafka 的消息格式:

```json
{
  "source": "bluesky",
  "timestamp": "2025-11-12T10:30:00Z",
  "data": {
    "id": "post_id",
    "uri": "at://did:plc:xxx/app.bsky.feed.post/xxx",
    "text": "Post content about AI...",
    "created_at": "2025-11-12T10:30:00Z",
    "author_did": "did:plc:xxx",
    "author_handle": "username.bsky.social",
    "author_display_name": "Display Name",
    "language": "en",
    "metrics": {
      "likes": 42,
      "reposts": 12,
      "replies": 5,
      "quotes": 3
    },
    "hashtags": ["AI", "MachineLearning"],
    "mentions": ["username1", "username2"]
  }
}
```

## 搜索关键词

Collector 会搜索以下 AI 相关关键词:

- AI, artificial intelligence
- machine learning, deep learning
- GPT, LLM, ChatGPT, Claude
- neural network, transformer
- generative AI, AGI
- diffusion model

## 日志

日志文件保存在 `logs/bluesky_collector.log`,自动按天轮转。

## 故障排查

### 1. 认证失败

```
❌ Bluesky authentication failed
```

**解决方法**:
- 确认 `BLUESKY_HANDLE` 格式正确 (如 `username.bsky.social`)
- 确认使用的是 App Password,不是主密码
- 检查密码是否正确复制(无多余空格)

### 2. atproto 未安装

```
⚠️  atproto library not installed
```

**解决方法**:
```bash
pip install atproto
```

### 3. Kafka 连接失败

```
❌ Failed to connect to Kafka
```

**解决方法**:
- 确认 Kafka 服务已启动
- 检查 `KAFKA_BOOTSTRAP_SERVERS` 配置

## API 限流

Bluesky API 有速率限制:
- 使用合理的采集间隔(建议 ≥60秒)
- 搜索间隔有 0.5 秒延迟
- 如遇限流,collector 会自动等待

## 参考文档

- Bluesky API 文档: https://docs.bsky.app/docs
- AT Protocol 文档: https://atproto.com/
- atproto Python SDK: https://github.com/MarshalX/atproto
