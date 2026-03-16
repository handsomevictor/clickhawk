> 中文版: [MONITORING_CN.md](MONITORING_CN.md)

# Example: Live Monitoring and Slow Query Investigation

## 1. Live query monitoring

```bash
ch monitor
```

**Output (auto-refreshes every 2 seconds):**
```
⚡ Live Queries  (Ctrl+C to exit)
┌──────────┬──────────┬───────────┬──────────────────┬────────────┬─────────────────────────────────────────┐
│ ID       │ User     │ Elapsed(s)│ Rows Read        │ Memory     │ Query                                   │
├──────────┼──────────┼───────────┼──────────────────┼────────────┼─────────────────────────────────────────┤
│ 3a7f1c2b │ analyst  │ 42.1      │ 500.00 million   │ 2.34 GiB   │ SELECT uniq(user_id) ... ← red (>30s)  │
│ b2e4a891 │ default  │ 8.3       │ 12.47 million    │ 456.00 MiB │ SELECT count() ...     ← yellow (>5s)  │
│ f9d3c015 │ etl_user │ 0.8       │ 1.23 million     │ 45.00 MiB  │ INSERT INTO ...                         │
└──────────┴──────────┴───────────┴──────────────────┴────────────┴─────────────────────────────────────────┘
```

**Color coding:**
- Red: query has been running for over 30 seconds (usually warrants intervention)
- Yellow: query has been running for over 5 seconds (worth watching)
- Default: normal

Press `Ctrl+C` to exit.

---

## 2. Custom refresh interval

```bash
# Refresh every 5 seconds (reduces server query load)
ch monitor --interval 5

# Refresh every 1 second (high-frequency, useful for debugging)
ch monitor --interval 1
```

---

## 3. Slow query history

```bash
# Top 20 queries slower than 1s in the last 24h (default)
ch slowlog

# Queries slower than 5s in the last 1 hour only
ch slowlog --threshold 5000 --hours 1

# Show more results
ch slowlog --top 50

# Focus on extremely long queries only
ch slowlog --threshold 30000 --top 10
```

---

## 4. Production incident workflow

### Step 1: Detect the problem
Dashboard alert fires or users report slow queries.

```bash
ch monitor
```

### Step 2: Identify the slow query
```bash
ch slowlog --hours 1 --threshold 2000 --top 10
```

### Step 3: Analyze the specific query
Take the problematic SQL from slowlog, reproduce it in dev/test, and profile it:

```bash
ch profile "the problematic SQL"
```

Use `Parts selected` and `Ranges selected` to detect full table scans, and `Memory used` to identify memory pressure.

### Step 4: Verify the fix
After optimizing (adding an index, adjusting `ORDER BY`, rewriting the SQL), profile again to compare metrics:

```bash
ch profile "SELECT uniq(user_id) FROM events WHERE user_id > 1000"
```

---

## 5. Kill a runaway query

If `ch monitor` shows a query that has been running too long, get its full `query_id` and kill it:

```bash
# Get the full query_id
ch query "SELECT query_id, query FROM system.processes WHERE elapsed > 60"

# Kill the query (run inside clickhouse-client — ch kill is planned for v0.2)
# KILL QUERY WHERE query_id = 'full-query-id-here'
```

> **Coming soon:** `ch kill <query_id>` will let you terminate runaway queries directly from the terminal in a future release.
