# Bluesky Collector 快速开始

## 1️⃣ 安装依赖

```bash
pip install atproto
```

## 2️⃣ 获取 App Password

1. 访问 https://bsky.app/settings/app-passwords
2. 点击 "Add App Password"
3. 输入名称: `Lakehouse Pipeline`
4. **复制生成的密码** (只显示一次!)

## 3️⃣ 配置环境变量

编辑 `config/.env`:

```bash
# Bluesky API Configuration
BLUESKY_HANDLE=your-username.bsky.social
BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
BLUESKY_COLLECTION_INTERVAL=60
```

## 4️⃣ 运行 Collector

```bash
python data_ingestion/bluesky/collector.py
```

## 5️⃣ 验证数据

查看 Dashboard 的 Recent Posts,应该能看到来自 Bluesky 的帖子(蓝色标签)。

## ⚠️ 常见问题

### 认证失败?
- 确认使用的是 **App Password**,不是账号密码
- Handle 格式: `username.bsky.social` (包含域名)

### 没有数据?
- 检查 Kafka 是否运行: `docker ps | grep kafka`
- 查看日志: `tail -f logs/bluesky_collector.log`

### API 限流?
- 增加采集间隔到 120 秒
- 减少搜索关键词数量

---

✅ 完成后,可以禁用 Twitter collector (在 config/.env 中注释 Twitter 配置)
