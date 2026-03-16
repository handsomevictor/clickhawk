# 示例：实时监控与慢查询排查

## 1. 实时查询监控

```bash
ch monitor
```

**输出（每 2 秒自动刷新）：**
```
⚡ Live Queries  (Ctrl+C to exit)
┌──────────┬──────────┬───────────┬─────────────┬──────────┬────────────────────────────────────────────────────────────┐
│ ID       │ User     │ Elapsed(s)│ Rows Read   │ Memory   │ Query                                                      │
├──────────┼──────────┼───────────┼─────────────┼──────────┼────────────────────────────────────────────────────────────┤
│ 3a7f1c2b │ analyst  │ 42.1      │ 500.00 million│ 2.34 GiB │ SELECT uniq(user_id) FROM events WHERE date >= ...      │ ← 红色（>30s）
│ b2e4a891 │ default  │ 8.3       │ 12.47 million │ 456.00 MiB│ SELECT count() FROM sessions GROUP BY country         │ ← 黄色（>5s）
│ f9d3c015 │ etl_user │ 0.8       │ 1.23 million  │ 45.00 MiB │ INSERT INTO events_summary SELECT ...                │
└──────────┴──────────┴───────────┴─────────────┴──────────┴────────────────────────────────────────────────────────────┘
```

**颜色含义：**
- 红色：查询已运行超过 30 秒（通常需要干预）
- 黄色：查询已运行超过 5 秒（值得关注）
- 默认：正常

按 `Ctrl+C` 退出监控。

---

## 2. 自定义刷新频率

```bash
# 每 5 秒刷新一次（减少对服务器的查询压力）
ch monitor --interval 5

# 每 1 秒刷新一次（高频监控，适合调试）
ch monitor --interval 1
```

---

## 3. 查看慢查询历史

```bash
# 查看最近 24h 慢于 1s 的前 20 条查询（默认）
ch slowlog

# 只看最近 1h 内慢于 5s 的查询
ch slowlog --threshold 5000 --hours 1

# 显示更多条数
ch slowlog --top 50

# 只关注超长查询
ch slowlog --threshold 30000 --top 10
```

**输出：**
```
🐢 Slow Queries  (last 24h  ·  ≥1000ms  ·  top 20)
┌──────────┬─────────────┬───────────────┬───────────┬─────────┬──────────┬──────────────────────────────────────────────────────────────────────────┐
│ Time     │ Duration(ms)│ Rows Read     │ Bytes Read│ Memory  │ User     │ Query                                                                    │
├──────────┼─────────────┼───────────────┼───────────┼─────────┼──────────┼──────────────────────────────────────────────────────────────────────────┤
│ 14:32:01 │ 45230       │ 1.23 billion  │ 392.10 GB │ 4.23 GB │ analyst  │ SELECT uniq(user_id) FROM events WHERE ...                               │
│ 13:15:44 │ 12483       │ 500.00 million│ 156.30 GB │ 1.87 GB │ etl_user │ INSERT INTO summary SELECT date, count() FROM events GROUP BY date       │
│ 11:02:17 │ 8321        │ 200.00 million│ 62.40 GB  │ 890.00 MB│ default │ SELECT * FROM events WHERE user_id IN (SELECT user_id FROM ...)         │
└──────────┴─────────────┴───────────────┴───────────┴─────────┴──────────┴──────────────────────────────────────────────────────────────────────────┘
3 queries found
```

---

## 4. 生产排查工作流

### 步骤 1：发现问题
仪表盘告警或用户反馈查询变慢。

```bash
# 检查此刻是否有异常长跑查询
ch monitor
```

### 步骤 2：定位慢查询
```bash
# 查看最近 1h 的慢查询
ch slowlog --hours 1 --threshold 2000 --top 10
```

### 步骤 3：分析具体查询
从 slowlog 中找到问题 SQL，在开发/测试环境重现并 profile：

```bash
ch profile "问题 SQL"
```

根据 `Parts selected` 和 `Ranges selected` 判断是否存在全表扫描，根据 `Memory used` 判断是否有内存压力。

### 步骤 4：验证优化效果
优化后（加索引、调整 ORDER BY、重写 SQL），再次 profile 对比指标：

```bash
# 优化前
ch profile "SELECT uniq(user_id) FROM events WHERE user_id > 1000"

# 优化后（假设加了 ORDER BY user_id）
ch profile "SELECT uniq(user_id) FROM events WHERE user_id > 1000"
```

---

## 5. 查杀失控查询

如果 `ch monitor` 发现某个查询跑了太久，通过以下方式获取其完整 query_id 后 kill：

```bash
# 查询完整的 query_id
ch query "SELECT query_id, query FROM system.processes WHERE elapsed > 60"

# Kill 指定查询（在 clickhouse-client 中执行，ClickHawk v0.2 将集成 kill 命令）
# KILL QUERY WHERE query_id = 'full-query-id-here'
```

> **提示：** `ch kill <query_id>` 功能正在规划中，将在未来版本中支持直接从终端终止失控查询。
