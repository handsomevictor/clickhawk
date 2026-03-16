> English version: [SCHEMA_EXPLORATION.md](SCHEMA_EXPLORATION.md)

# 示例：Schema 探索

## 1. 列出所有用户表

```bash
ch schema tables
```

**输出：**
```
                Tables
┌───────────────┬─────────────────┬────────────┬──────────┬──────────┐
│ Database      │ Table           │ Engine     │ Size     │ Rows     │
├───────────────┼─────────────────┼────────────┼──────────┼──────────┤
│ analytics     │ events          │ MergeTree  │ 128.4 GB │ 1.23 billion │
│ analytics     │ users           │ MergeTree  │ 2.1 GB   │ 5.67 million │
│ analytics     │ sessions        │ MergeTree  │ 45.2 GB  │ 312.4 million │
│ raw           │ kafka_events    │ Kafka      │ 0.00 B   │ 0        │
└───────────────┴─────────────────┴────────────┴──────────┴──────────┘
4 tables
```

---

## 2. 只看某个数据库的表

```bash
ch schema tables --database analytics
```

---

## 3. 查看具体表的结构

```bash
ch schema show events
```

**输出：**
```
              Schema: events
┌─────────────────┬──────────────────────┬─────────┬─────────────────────────┐
│ Column          │ Type                 │ Default │ Comment                 │
├─────────────────┼──────────────────────┼─────────┼─────────────────────────┤
│ event_id        │ UUID                 │         │ 全局唯一事件 ID          │
│ user_id         │ UInt64               │         │ 用户 ID                 │
│ event_type      │ LowCardinality(String)│         │ 事件类型                │
│ created_at      │ DateTime64(3)        │         │ 事件时间（毫秒精度）    │
│ date            │ Date                 │ toDate(created_at) │ 分区键   │
│ properties      │ Map(String, String)  │         │ 扩展属性                │
└─────────────────┴──────────────────────┴─────────┴─────────────────────────┘
```

---

## 4. 指定数据库查看表结构

```bash
ch schema show events --database analytics
```

当多个数据库有同名表时，用 `--database` 参数消除歧义。

---

## 5. 实用的 Schema 检查工作流

### 检查某个表是否有指定的列

```bash
ch schema show my_table | grep -i "user_id"
```

### 查找所有使用特定引擎的表

```bash
ch query "SELECT database, name FROM system.tables WHERE engine = 'Kafka'"
```

### 查看表的 DDL（建表语句）

```bash
ch query "SELECT create_table_query FROM system.tables WHERE name = 'events' AND database = 'analytics'" --format json
```

### 检查哪些表没有分区

```bash
ch query "SELECT database, name FROM system.tables WHERE engine LIKE '%MergeTree%' AND partition_key = '' AND database NOT IN ('system')"
```

### 查看表的索引信息

```bash
ch query "SELECT name, type, expr FROM system.data_skipping_indices WHERE table = 'events'"
```

---

## 6. 快速对比两个表的列数

```bash
# 查看 events 表的列数
ch query "SELECT count() FROM system.columns WHERE table = 'events'"

# 对比 dev 和 prod 同名表的列（结合 schema diff，v0.2 功能）
```

> **提示：** `ch schema diff` 功能正在 v0.2 开发中，将支持对比两个 ClickHouse 环境的 schema 差异，无需手动执行 SQL。
