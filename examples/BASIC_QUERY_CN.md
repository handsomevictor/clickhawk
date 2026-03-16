> English version: [BASIC_QUERY.md](BASIC_QUERY.md)

# 示例：基础查询

## 1. 验证连接和集群状态

```bash
ch health
```

**输出：**
```
✓  ClickHouse  24.3.1.1
    Uptime   : 7 days, 3 hours
    Databases: 5
    Tables   : 42
```

---

## 2. 执行简单查询（表格格式，默认）

```bash
ch query "SELECT database, count() AS tables FROM system.tables GROUP BY database ORDER BY tables DESC"
```

**输出：**
```
┌─────────────────────┬────────┐
│ database            │ tables │
├─────────────────────┼────────┤
│ analytics           │ 28     │
│ raw                 │ 14     │
│ default             │ 3      │
└─────────────────────┴────────┘
3 rows
```

---

## 3. JSON 格式输出（适合接管道处理）

```bash
ch query "SELECT name, engine, total_rows FROM system.tables LIMIT 5" --format json
```

**输出：**
```json
[
  {
    "name": "events",
    "engine": "MergeTree",
    "total_rows": 1234567890
  },
  ...
]
```

结合 `jq` 使用：
```bash
ch query "SELECT name, total_bytes FROM system.tables" --format json | jq '.[] | select(.total_bytes > 1000000000)'
```

---

## 4. CSV 格式输出（导出数据）

```bash
ch query "SELECT date, count() FROM events GROUP BY date ORDER BY date" --format csv > daily_counts.csv
```

---

## 5. 限制返回行数

```bash
# 快速预览大表的数据
ch query "SELECT * FROM events" --limit 10
```

这会执行 `SELECT * FROM (SELECT * FROM events) LIMIT 10`，适合快速检查数据格式。

---

## 6. 查看系统信息

```bash
# 查看当前配置
ch query "SELECT name, value FROM system.settings WHERE changed = 1"

# 查看正在运行的副本同步状态
ch query "SELECT database, table, is_leader, is_readonly FROM system.replicas"

# 查看各表的磁盘占用
ch query "SELECT database, name, formatReadableSize(total_bytes) AS size FROM system.tables WHERE database NOT IN ('system') ORDER BY total_bytes DESC LIMIT 20"
```

---

## 7. 快速数据探查

```bash
# 查看某个时间字段的数据范围
ch query "SELECT min(created_at), max(created_at), count() FROM events"

# 按天统计数据量（检查数据完整性）
ch query "SELECT toDate(created_at) AS day, count() AS cnt FROM events GROUP BY day ORDER BY day DESC LIMIT 30"

# 查看 NULL 值分布
ch query "SELECT countIf(user_id IS NULL) AS null_count, count() AS total FROM events"
```
