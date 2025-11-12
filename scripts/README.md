# 脚本使用指南

所有脚本已按照运行顺序编号，方便你按序执行。

---

## 🚀 核心脚本（按运行顺序）

### 00 - 首次准备

```bash
./00-prepare_jars.sh
```

**作用**: 下载Spark所需的jar文件（Kafka连接器、Hadoop AWS等）
**何时使用**: 首次运行系统时，或jar文件丢失时
**运行时间**: ~1-2分钟（下载依赖）

---

### 01 - 完整重启（主要脚本）⭐

```bash
./01-full_restart.sh
```

**作用**: 一键完整重启整个系统
- 检查前置条件（Docker、.env、venv、jars）
- 停止所有现有服务
- 启动基础设施（Kafka、MinIO、Spark）
- 启动数据采集器
- 验证每个服务健康状态

**何时使用**:
- 日常启动系统
- 系统出现问题需要重启
- 从零开始启动

**运行时间**: ~2分钟
**输出**: 彩色状态输出 + 下一步操作提示

---

### 02 - 启动Spark写MinIO

```bash
./02-start_spark_minio.sh
```

**作用**: 启动Spark Streaming，实时处理Kafka数据并写入MinIO
- 自动下载S3A相关jar（首次）
- 复制文件到Spark容器
- 提交Spark作业（每30秒批量写入）

**何时使用**: 在01完成后，新建终端运行
**前置条件**: 必须先运行 `01-full_restart.sh`
**运行时间**: 持续运行（按Ctrl+C停止）
**输出**: Spark日志 + 批次处理信息

**验证数据**:
- 访问 http://localhost:9001
- 查看 `lakehouse/bronze/social_media/` 目录

---

### 03 - 启动Dashboard

```bash
./03-start_dashboard.sh
```

**作用**: 启动Streamlit实时Dashboard
**何时使用**: 在01完成后，新建终端运行
**前置条件**: 必须先运行 `01-full_restart.sh`
**运行时间**: 持续运行（按Ctrl+C停止）
**访问**: http://localhost:8501

---

### 99 - 系统验证

```bash
./99-verify_system.sh
```

**作用**: 完整的系统健康检查
- ✅ Docker服务状态（5个容器）
- ✅ 端口可访问性（8080, 9001, 9092）
- ✅ 数据采集器运行状态
- ✅ Kafka消息数量
- ✅ MinIO数据存在性
- ✅ Spark作业状态

**何时使用**:
- 验证系统是否正常运行
- 故障排查第一步
- 查看系统统计信息

**运行时间**: ~10秒

---

## 🛠️ 工具脚本

### start_collectors.sh

```bash
./start_collectors.sh
```

**作用**: 单独启动数据采集器（Twitter + Reddit）
**何时使用**:
- 采集器崩溃需要重启
- 只想启动采集器（不启动整个系统）

**注意**: 通常由 `01-full_restart.sh` 自动调用，无需单独运行

---

### stop_collectors.sh

```bash
./stop_collectors.sh
```

**作用**: 停止所有数据采集器
**何时使用**:
- 需要停止数据采集（但保留其他服务）
- 系统关闭前

---

### start_full_infrastructure.sh

```bash
./start_full_infrastructure.sh
```

**作用**: 启动基础设施（Kafka、MinIO、Spark）
**何时使用**:
- 只启动基础设施（不启动采集器）
- 调试基础设施问题

**注意**: 通常由 `01-full_restart.sh` 自动调用，无需单独运行

---

## 📋 完整启动流程（推荐）

### 首次启动

```bash
# 终端1: 准备jar（首次）
./00-prepare_jars.sh

# 终端1: 完整重启
./01-full_restart.sh

# 终端2: 启动Spark写MinIO
./02-start_spark_minio.sh

# 终端3: 启动Dashboard
./03-start_dashboard.sh

# 终端4（可选）: 验证系统
./99-verify_system.sh
```

### 日常启动（jar已准备）

```bash
# 终端1: 完整重启
./01-full_restart.sh

# 终端2: 启动Spark写MinIO
./02-start_spark_minio.sh

# 终端3: 启动Dashboard
./03-start_dashboard.sh
```

---

## 🛑 停止系统

```bash
# 1. 停止Spark（在运行02的终端按 Ctrl+C）
# 2. 停止Dashboard（在运行03的终端按 Ctrl+C）

# 3. 停止采集器
./stop_collectors.sh

# 4. 停止基础设施
docker-compose -f docker-compose-full.yml down

# 5. (可选) 删除所有数据
docker-compose -f docker-compose-full.yml down -v
```

---

## 🔍 脚本速查

| 脚本 | 用途 | 运行频率 | 前置条件 |
|------|------|----------|----------|
| `00-prepare_jars.sh` | 下载jar依赖 | 首次/丢失时 | 网络连接 |
| `01-full_restart.sh` | 完整重启系统 | 每次启动 | Docker运行 |
| `02-start_spark_minio.sh` | Spark处理 | 需要写MinIO时 | 01已运行 |
| `03-start_dashboard.sh` | 可视化 | 需要查看数据时 | 01已运行 |
| `99-verify_system.sh` | 健康检查 | 随时 | 01已运行 |
| `stop_collectors.sh` | 停止采集器 | 关闭系统时 | - |

---

## 📁 目录结构

```
scripts/
├── README.md                      # 本文档
├── 00-prepare_jars.sh             # 准备jar
├── 01-full_restart.sh             # 完整重启（主要）⭐
├── 02-start_spark_minio.sh        # Spark写MinIO
├── 03-start_dashboard.sh          # Dashboard
├── 99-verify_system.sh            # 系统验证
├── start_collectors.sh            # 工具：启动采集器
├── stop_collectors.sh             # 工具：停止采集器
├── start_full_infrastructure.sh   # 工具：启动基础设施
└── deprecated/                    # 废弃脚本
    └── start_spark_streaming_fixed.sh
```

---

## ⚠️ 常见问题

### Q: 应该先运行哪个脚本？

A:
```bash
# 首次启动：00 → 01 → 02 → 03
# 日常启动：01 → 02 → 03
```

### Q: 可以只运行01吗？

A: 可以！`01-full_restart.sh` 会启动基础设施和采集器。
   `02` 和 `03` 是可选的（用于写MinIO和可视化）。

### Q: 脚本报错怎么办？

A:
1. 先运行 `./99-verify_system.sh` 查看哪个组件有问题
2. 查看日志：`docker-compose -f docker-compose-full.yml logs`
3. 参考主文档 `docs/MASTER_GUIDE.md` 的故障排查部分

### Q: 如何停止某个脚本？

A: 在运行脚本的终端按 `Ctrl+C`

---

## 🎯 最佳实践

1. **每次启动都运行01**: 确保系统干净启动
2. **用99验证**: 启动后运行 `99-verify_system.sh` 确认一切正常
3. **查看日志**: 出问题时优先查看 `logs/` 目录下的日志文件
4. **保持终端独立**: 02和03应该在独立终端运行，方便查看日志

---

**版本**: 2.0
**更新日期**: 2025-11-11
**维护者**: Guangyao Li
