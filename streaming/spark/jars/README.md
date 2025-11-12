# Spark JAR Dependencies

这个目录包含Spark所需的jar依赖文件。

**重要**: 这些jar文件**不应该**提交到Git（文件过大）。

## 如何获取jar文件

运行准备脚本自动下载所有依赖：

```bash
./scripts/00-prepare_jars.sh
```

## 所需jar文件列表

### Kafka连接器
- `spark-sql-kafka-0-10_2.12-3.5.0.jar` (~422KB)
- `kafka-clients-3.4.1.jar` (~4.8MB)
- `spark-token-provider-kafka-0-10_2.12-3.5.0.jar` (~55KB)
- `commons-pool2-2.11.1.jar` (~142KB)

### MinIO/S3A支持
- `hadoop-aws-3.3.4.jar` (~940KB)
- `aws-java-sdk-bundle-1.12.262.jar` (~268MB) ⚠️ 大文件

## 下载源

所有jar文件从Maven Central Repository下载：
- https://repo1.maven.org/maven2/

## Git配置

这些文件已在 `.gitignore` 中被忽略：
```
*.jar
streaming/spark/jars/*.jar
```

---

**自动化**: 运行 `./scripts/00-prepare_jars.sh` 会自动下载所有缺失的jar文件。
