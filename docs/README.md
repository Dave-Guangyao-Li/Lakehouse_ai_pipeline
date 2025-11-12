# AI趋势监控系统 - 文档中心

欢迎！这个项目实现了一个基于Lakehouse架构的AI趋势实时监控系统。

---

## 📖 主文档

**请阅读 → [MASTER_GUIDE.md](MASTER_GUIDE.md)** ⭐

这是唯一你需要的完整文档，包含：
- 快速开始（5分钟启动）
- API配置详解
- 系统架构说明
- 完整使用场景
- 故障排查大全
- 命令速查表
- 扩展路线图

---

## 🚀 快速开始（3条命令）

```bash
# 1. 完整重启系统（自动验证）
./scripts/01-full_restart.sh

# 2. 启动Spark写入MinIO（新建终端）
./scripts/02-start_spark_minio.sh

# 3. 启动Dashboard（新建终端）
./scripts/03-start_dashboard.sh
```

**访问点**:
- Spark Master: http://localhost:8080
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- Dashboard: http://localhost:8501

---

## 🔍 系统验证

```bash
./scripts/99-verify_system.sh
```

---

## 📚 归档文档

旧版本文档已归档到 `archive/` 目录，供参考。

---

**版本**: v2.0
**更新日期**: 2025-11-11
**维护者**: Guangyao Li
