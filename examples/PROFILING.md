> 中文版: [PROFILING_CN.md](PROFILING_CN.md)

# Example: Query Performance Profiling

## Scenario: diagnosing a slow query

Suppose a dashboard query is responding slowly and you need to identify the bottleneck.

---

## 1. Profile a query directly

```bash
ch profile "SELECT uniq(user_id) FROM events WHERE date >= today() - 7"
```

**Output:**
```
🔍 Query Profile
┌──────────────────────┬──────────────┐
│ Metric               │ Value        │
├──────────────────────┼──────────────┤
│ Wall time            │ 0.342s       │
│ DB duration          │ 298 ms       │
│ Rows read            │ 12,847,291   │
│ Bytes read           │ 412.30 MB    │
│ Memory used          │ 87.50 MB     │
│ Parts selected       │ 24           │
│ Ranges selected      │ 156          │
└──────────────────────┴──────────────┘
```

---

## 2. Understanding each metric

| Metric | Meaning | Optimization direction |
|--------|---------|------------------------|
| **Wall time** | Total elapsed time from sending the request to receiving the result (includes network) | Overall reference |
| **DB duration** | Actual server-side execution time | Primary optimization target |
| **Rows read** | Number of rows scanned on the server | Fewer is better — add indexes/partitions |
| **Bytes read** | Amount of data scanned | Fewer is better — consider column compression |
| **Memory used** | Peak memory used by the query | If high, optimize GROUP BY / JOIN |
| **Parts selected** | Number of parts touched | Fewer is better — check partition key |
| **Ranges selected** | Number of ranges touched | Fewer is better — check sort key |

---

## 3. Common diagnostic cases

### Case A: Full table scan (many parts selected)

```bash
ch profile "SELECT count() FROM events WHERE user_id = '123'"
```

If the output shows:
```
Parts selected: 2400     ← nearly all parts scanned
Ranges selected: 48000
Rows read: 500,000,000   ← 500M rows read to find one user
```

**Problem:** `user_id` is not in the sort key — ClickHouse does a full table scan.

**Fix:** Add `user_id` to the `ORDER BY` key, or create a secondary index (Bloom filter or set index).

---

### Case B: Effective partition pruning (few parts selected)

```bash
ch profile "SELECT count() FROM events WHERE date = today()"
```

If the output shows:
```
Parts selected: 3        ← only today's 3 parts scanned
Ranges selected: 12
Rows read: 1,234,567     ← only today's data read
```

**Conclusion:** The `date` partition key is working correctly — partition pruning is in effect.

---

### Case C: Memory pressure risk

```bash
ch profile "SELECT user_id, count() FROM events GROUP BY user_id"
```

If the output shows:
```
Memory used: 4,200.00 MB  ← 4 GB memory, near the limit
Rows read: 1,000,000,000
```

**Problem:** The GROUP BY result set is too large, creating high memory pressure.

**Fixes:**
- Replace `GROUP BY` + `count(DISTINCT)` with `uniq()`
- Add a `WHERE` clause to reduce the data range
- Use `approx_count_distinct()` for approximate results

---

## 4. Combining slowlog and profile for production diagnosis

First find the slowest queries with `slowlog`:
```bash
ch slowlog --top 5 --threshold 5000 --hours 1
```

Then reproduce the problematic SQL in a dev/test environment and profile it:
```bash
ch profile "the slow SQL you found"
```

This completes the full slow-query diagnosis workflow without writing a single `system.query_log` SQL statement by hand.
