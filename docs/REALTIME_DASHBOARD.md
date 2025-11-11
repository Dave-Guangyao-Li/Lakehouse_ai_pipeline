# 实时Dashboard指南

## 🎉 恭喜进入Phase 2！

你现在可以在Dashboard中查看**真实的数据**了！

---

## 🚀 快速启动实时Dashboard

### 1️⃣ 停止当前的示例Dashboard

在当前Dashboard终端按 **Ctrl+C** 停止

### 2️⃣ 启动实时Dashboard

```bash
./scripts/start_dashboard_realtime.sh
```

或者手动启动：

```bash
source venv/bin/activate
streamlit run dashboard/app_realtime.py
```

### 3️⃣ 访问Dashboard

浏览器打开：http://localhost:8501

你会看到：
- 🔴 **LIVE DATA** 标记
- 真实的Twitter和Reddit数据
- 实时统计数据
- 真实的作者、话题、互动数据

---

## 📊 Dashboard功能

### 实时数据展示

- **总帖子数**：从Kafka读取的真实消息数量
- **Twitter/Reddit分布**：真实的数据源占比
- **热门话题**：基于真实文本内容分析的关键词
- **最活跃作者**：真实的Twitter用户和Reddit用户
- **最近帖子**：最新的真实推文和Reddit帖子

### 自动刷新

- Dashboard每30秒自动刷新一次
- 可以在侧边栏调整刷新间隔
- 也可以手动点击"🔄 Refresh Now"

---

## 🔍 数据流说明

### 当前数据流（Phase 2 - 方案A）

```
Twitter/Reddit API
       ↓
   采集器 (Python)
       ↓
    Kafka  ←── Dashboard直接读取
       ↓
   [Spark未启动]
       ↓
   [Delta Lake空]
```

**优点：**
- ✅ 立即看到真实数据
- ✅ 验证采集器工作正常
- ✅ 理解数据格式和内容

**限制：**
- ⚠️ 没有数据处理和清洗
- ⚠️ 没有持久化存储（Kafka有保留期）
- ⚠️ 话题分析比较简单

---

## 📈 看到的数据说明

### Twitter数据

每条推文包含：
- **文本内容**：推文的实际内容
- **作者**：Twitter用户名
- **互动数据**：点赞、转发、回复、引用数
- **Hashtags**：推文中的标签
- **创建时间**：推文发布时间

### Reddit数据

每个帖子包含：
- **标题+正文**：Reddit帖子内容
- **作者**：Reddit用户名
- **Subreddit**：来自哪个子版块
- **分数**：upvote分数
- **评论数**：帖子的评论数量
- **创建时间**：帖子发布时间

---

## 🎯 下一步优化方向

### Phase 2B：完整Lakehouse架构

1. **解决Spark启动问题**
   - 尝试不同的Spark镜像
   - 或者使用本地Spark安装

2. **实现Spark Streaming处理**
   - 数据清洗和标准化
   - 热点检测算法
   - 情感分析

3. **写入Delta Lake**
   - Bronze层：原始数据
   - Silver层：清洗后数据
   - Gold层：聚合分析结果

4. **Dashboard读取Delta Lake**
   - 更复杂的分析
   - 历史趋势对比
   - 更准确的热点检测

### Phase 2C：添加AI能力

1. **文本Embedding**
   - 使用Sentence Transformers生成向量
   - 存储到Milvus向量数据库

2. **语义搜索**
   - 按意思搜索相似内容
   - 发现相关讨论

3. **RAG问答系统**
   - 问题："最近关于GPT-5的讨论有哪些？"
   - 系统：检索相关数据 + LLM生成回答

4. **趋势预测**
   - 基于历史数据预测热点话题
   - 检测突然爆发的话题

---

## 🛠️ 故障排查

### Dashboard显示"No data available"

**检查清单：**

1. **Kafka是否有数据？**
   ```bash
   docker exec -it kafka kafka-console-consumer \
     --bootstrap-server localhost:9092 \
     --topic ai-social-raw \
     --from-beginning \
     --max-messages 5
   ```

2. **采集器是否运行？**
   ```bash
   tail -f logs/twitter_collector.log
   tail -f logs/reddit_collector.log
   ```

3. **Kafka服务是否正常？**
   ```bash
   docker ps | grep kafka
   ```

### Dashboard加载很慢

- Kafka消息太多（>1000条）
- 调整 `kafka_reader.py` 中的 `max_messages` 参数
- 或者只读取最近的消息

### 连接错误

- 确保Kafka运行在 `localhost:9092`
- 检查防火墙设置
- 确保没有其他服务占用端口

---

## 📚 代码说明

### 新增文件

1. **dashboard/kafka_reader.py**
   - Kafka数据读取模块
   - 解析Twitter/Reddit消息
   - 转换为DataFrame

2. **dashboard/app_realtime.py**
   - 实时Dashboard应用
   - 连接Kafka读取数据
   - 实时统计和可视化

3. **scripts/start_dashboard_realtime.sh**
   - 实时Dashboard启动脚本

### 保留文件

- **dashboard/app.py** - 原始示例数据版本（仍可使用）
- **scripts/start_dashboard.sh** - 启动示例版本

---

## 🎓 学习要点

### 你已经掌握的技术

✅ **端到端数据pipeline**
- API数据采集
- Kafka消息队列
- 实时数据可视化

✅ **分布式系统基础**
- 容器化部署（Docker）
- 消息队列使用
- 数据持久化

✅ **数据工程实践**
- 数据采集策略
- 数据格式设计
- 实时数据处理

### 下一步学习方向

🔜 **流处理框架**（Spark Streaming）
🔜 **Lakehouse架构**（Delta Lake）
🔜 **向量数据库**（Milvus）
🔜 **RAG系统**（LangChain）

---

## 💡 小贴士

### 对比示例数据和真实数据

可以同时运行两个版本：

```bash
# 终端1：示例数据版本（端口8501）
streamlit run dashboard/app.py

# 终端2：实时数据版本（端口8502）
streamlit run dashboard/app_realtime.py --server.port 8502
```

访问：
- 示例版本：http://localhost:8501
- 实时版本：http://localhost:8502

### 调整采集关键词

编辑 `config/.env`：

```bash
AI_KEYWORDS=GPT,Claude,LLM,Gemini,AI,ChatGPT,自定义关键词
```

重启采集器即可生效。

---

**享受你的实时AI趋势监控系统吧！** 🎉🚀

有任何问题随时查看日志或询问！
