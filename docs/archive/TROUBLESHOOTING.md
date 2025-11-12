# 故障排查手册

记录所有踩过的坑和解决方案。

---

## 🐛 已解决的问题

### 1. Spark镜像版本问题

**问题：** `bitnami/spark:3.4.1` 镜像找不到

**错误信息：**
```
Error: failed to resolve reference "docker.io/bitnami/spark:3.4.1": not found
```

**尝试的解决方案：**
- ❌ 升级到 3.5.0 → 仍然失败
- ❌ 使用Docker镜像加速 → 未解决根本问题

**最终解决方案：**
✅ 切换到Apache官方镜像 `apache/spark:3.5.0-python3`

**修改位置：** `docker-compose-full.yml`

---

### 2. Spark Worker权限错误

**问题：** Worker无法创建工作目录

**错误信息：**
```
java.io.IOException: Failed to create directory /opt/spark/work/app-xxx/0
```

**根本原因：** 容器内普通用户没有 `/opt/spark/work` 写权限

**解决方案：**
1. Worker以root用户运行：`user: root`
2. 使用 `/tmp` 目录：`SPARK_WORKER_DIR=/tmp/spark-work`
3. Volume映射到 `/tmp`

**修改位置：** `docker-compose-full.yml` spark-worker配置

---

### 3. Spark无法下载Maven依赖

**问题：** Spark尝试在线下载Kafka连接器失败

**错误信息：**
```
FileNotFoundException: /home/spark/.ivy2/cache/resolved-org.apache.spark-...
```

**根本原因：**
- 容器内Ivy缓存目录无写权限
- Maven仓库连接失败/慢

**解决方案：**
预先下载jar文件并通过 `--jars` 参数提供

**实施：**
1. 创建 `prepare_spark_jars.sh` 下载依赖
2. 创建 `start_spark_streaming_fixed.sh` 使用本地jar
3. 废弃原 `start_spark_streaming.sh`

---

### 4. Reddit API redirect_uri问题

**问题：** 创建Reddit应用时必须填写redirect_uri

**误区：** "script"类型应用不需要redirect URI

**实际情况：** Reddit表单验证强制要求填写

**解决方案：** 填写 `http://localhost:8080`（不会实际使用）

**文档更新：** `QUICKSTART.md` 添加详细说明

---

### 5. Docker Compose version警告

**问题：**
```
WARN: the attribute `version` is obsolete
```

**解决方案：** 删除 `version: '3.8'` 行

**影响：** 不影响功能，但清理警告

---

## 🔍 调试技巧

### 查看容器日志

```bash
# 实时查看
docker-compose -f docker-compose-full.yml logs -f <service-name>

# 查看最近100行
docker-compose -f docker-compose-full.yml logs --tail=100 <service-name>

# 示例
docker-compose -f docker-compose-full.yml logs --tail=50 spark-worker
```

### 进入容器调试

```bash
# 进入容器
docker exec -it <container-name> bash

# 示例：检查Spark Worker
docker exec -it spark-worker bash
ls -la /tmp/spark-work
ps aux | grep spark
```

### 测试网络连通性

```bash
# 容器间通信
docker exec spark-worker ping spark-master
docker exec spark-master nc -zv kafka 29092

# 主机到容器
curl http://localhost:8080
```

### 清理并重启

```bash
# 完全清理
docker-compose -f docker-compose-full.yml down -v
docker system prune -f

# 重新启动
docker-compose -f docker-compose-full.yml up -d
```

---

## ⚠️ 常见陷阱

### 1. 使用错误的Kafka地址

**错误：** 在Spark中使用 `localhost:9092`

**正确：**
- 容器内部：`kafka:29092`
- 主机访问：`localhost:9092`

### 2. 忘记激活虚拟环境

**错误：** 直接运行Python脚本

**正确：**
```bash
source venv/bin/activate
```

### 3. API密钥未配置

**检查：**
```bash
cat config/.env | grep TWITTER_BEARER_TOKEN
```

### 4. 端口冲突

**常见端口：**
- 8080 (Spark Master)
- 8501 (Streamlit)
- 9092 (Kafka)

**检查占用：**
```bash
lsof -i :8080
```

---

## 📝 问题报告模板

遇到新问题时，记录以下信息：

```
### 问题描述


### 复现步骤
1.
2.
3.

### 错误信息
```
粘贴错误日志
```

### 环境信息
- OS:
- Docker版本:
- Python版本:

### 尝试的解决方案
1.
2.

### 最终解决方案


### 相关文件
-
```

---

**更新日志**

- 2025-11-11: 初始版本，记录Phase 2B问题
