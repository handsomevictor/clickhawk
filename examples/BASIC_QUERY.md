> 中文版: [BASIC_QUERY_CN.md](BASIC_QUERY_CN.md)

# Example: Basic Queries

## 1. Check connection and cluster health

```bash
ch health
```

**Output:**
```
✓  ClickHouse  24.3.1.1
    Uptime   : 7 days, 3 hours
    Databases: 5
    Tables   : 42
```

---

## 2. Run a simple query (table format, default)

```bash
ch query "SELECT database, count() AS tables FROM system.tables GROUP BY database ORDER BY tables DESC"
```

**Output:**
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

## 3. JSON output (pipe-friendly)

```bash
ch query "SELECT name, engine, total_rows FROM system.tables LIMIT 5" --format json
```

**Output:**
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

Combine with `jq`:
```bash
ch query "SELECT name, total_bytes FROM system.tables" --format json | jq '.[] | select(.total_bytes > 1000000000)'
```

---

## 4. CSV output (data export)

```bash
ch query "SELECT date, count() FROM events GROUP BY date ORDER BY date" --format csv > daily_counts.csv
```

---

## 5. Limit returned rows

```bash
# Quickly preview a large table
ch query "SELECT * FROM events" --limit 10
```

This executes `SELECT * FROM (SELECT * FROM events) LIMIT 10` — useful for checking data shape quickly.

---

## 6. Query system information

```bash
# View changed settings
ch query "SELECT name, value FROM system.settings WHERE changed = 1"

# Check replica sync status
ch query "SELECT database, table, is_leader, is_readonly FROM system.replicas"

# View disk usage per table
ch query "SELECT database, name, formatReadableSize(total_bytes) AS size FROM system.tables WHERE database NOT IN ('system') ORDER BY total_bytes DESC LIMIT 20"
```

---

## 7. Quick data exploration

```bash
# Check the range of a timestamp column
ch query "SELECT min(created_at), max(created_at), count() FROM events"

# Daily row counts (check data completeness)
ch query "SELECT toDate(created_at) AS day, count() AS cnt FROM events GROUP BY day ORDER BY day DESC LIMIT 30"

# Check NULL distribution
ch query "SELECT countIf(user_id IS NULL) AS null_count, count() AS total FROM events"
```
