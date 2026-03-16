> 中文版: [SCHEMA_EXPLORATION_CN.md](SCHEMA_EXPLORATION_CN.md)

# Example: Schema Exploration

## 1. List all user tables

```bash
ch schema tables
```

**Output:**
```
                Tables
┌───────────────┬─────────────────┬────────────┬──────────┬───────────────┐
│ Database      │ Table           │ Engine     │ Size     │ Rows          │
├───────────────┼─────────────────┼────────────┼──────────┼───────────────┤
│ analytics     │ events          │ MergeTree  │ 128.4 GB │ 1.23 billion  │
│ analytics     │ users           │ MergeTree  │ 2.1 GB   │ 5.67 million  │
│ analytics     │ sessions        │ MergeTree  │ 45.2 GB  │ 312.4 million │
│ raw           │ kafka_events    │ Kafka      │ 0.00 B   │ 0             │
└───────────────┴─────────────────┴────────────┴──────────┴───────────────┘
4 tables
```

---

## 2. Filter by database

```bash
ch schema tables --database analytics
```

---

## 3. Inspect a table's structure

```bash
ch schema show events
```

**Output:**
```
              Schema: events
┌─────────────────┬──────────────────────┬────────────────────┬─────────────────────────┐
│ Column          │ Type                 │ Default            │ Comment                 │
├─────────────────┼──────────────────────┼────────────────────┼─────────────────────────┤
│ event_id        │ UUID                 │                    │ Globally unique event ID│
│ user_id         │ UInt64               │                    │ User ID                 │
│ event_type      │ LowCardinality(String)│                   │ Event type              │
│ created_at      │ DateTime64(3)        │                    │ Event timestamp (ms)    │
│ date            │ Date                 │ toDate(created_at) │ Partition key           │
│ properties      │ Map(String, String)  │                    │ Extended attributes     │
└─────────────────┴──────────────────────┴────────────────────┴─────────────────────────┘
```

---

## 4. Specify a database when showing a table

```bash
ch schema show events --database analytics
```

Use `--database` to disambiguate when multiple databases contain a table with the same name.

---

## 5. Practical schema inspection workflows

### Check whether a table has a specific column

```bash
ch schema show my_table | grep -i "user_id"
```

### Find all tables using a specific engine

```bash
ch query "SELECT database, name FROM system.tables WHERE engine = 'Kafka'"
```

### View a table's DDL (CREATE TABLE statement)

```bash
ch query "SELECT create_table_query FROM system.tables WHERE name = 'events' AND database = 'analytics'" --format json
```

### Find tables with no partition key

```bash
ch query "SELECT database, name FROM system.tables WHERE engine LIKE '%MergeTree%' AND partition_key = '' AND database NOT IN ('system')"
```

### View a table's skip indexes

```bash
ch query "SELECT name, type, expr FROM system.data_skipping_indices WHERE table = 'events'"
```

---

## 6. Quickly compare column counts between two tables

```bash
# Count columns in the events table
ch query "SELECT count() FROM system.columns WHERE table = 'events'"
```

> **Coming soon:** `ch schema diff` is in development for v0.2 and will compare schema differences between two ClickHouse environments without any manual SQL.
