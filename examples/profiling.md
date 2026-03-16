# 示例：查询性能分析

## 场景：诊断一条慢查询

假设你的仪表板某个查询响应慢，想知道瓶颈在哪里。

---

## 1. 直接 Profile 一条查询

```bash
ch profile "SELECT uniq(user_id) FROM events WHERE date >= today() - 7"
```

**输出：**
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

## 2. 理解各指标的含义

| 指标 | 含义 | 优化方向 |
|------|------|----------|
| **Wall time** | 从发出请求到收到结果的总时间（含网络） | 整体参考值 |
| **DB duration** | ClickHouse 服务端实际执行耗时 | 主要优化目标 |
| **Rows read** | 服务端扫描的行数 | 越少越好，加索引/分区 |
| **Bytes read** | 扫描的数据量 | 越少越好，考虑列压缩 |
| **Memory used** | 查询使用的峰值内存 | 过高则优化 GROUP BY/JOIN |
| **Parts selected** | 命中的 part 数量 | 越少越好，检查分区键 |
| **Ranges selected** | 命中的 range 数量 | 越少越好，检查排序键 |

---

## 3. 典型诊断案例

### 案例 A：全表扫描（Parts 数量很多）

```bash
ch profile "SELECT count() FROM events WHERE user_id = '123'"
```

如果输出：
```
Parts selected: 2400     ← 几乎所有 part 都被扫描
Ranges selected: 48000
Rows read: 500,000,000   ← 读了 5 亿行找一个 user
```

**问题**：`user_id` 不在排序键中，ClickHouse 做了全表扫描。

**解决方案**：将 `user_id` 加入 ORDER BY 键，或者新建二级索引（Bloom filter 或 set 索引）。

---

### 案例 B：分区剪枝有效（Parts 数量很少）

```bash
ch profile "SELECT count() FROM events WHERE date = today()"
```

如果输出：
```
Parts selected: 3        ← 只扫描了今天的 3 个 part
Ranges selected: 12
Rows read: 1,234,567     ← 只读了今天的数据
```

**结论**：分区键 `date` 工作正常，分区剪枝生效。

---

### 案例 C：内存溢出风险

```bash
ch profile "SELECT user_id, count() FROM events GROUP BY user_id"
```

如果输出：
```
Memory used: 4,200.00 MB  ← 4GB 内存，接近限制
Rows read: 1,000,000,000
```

**问题**：GROUP BY 结果集太大，内存压力高。

**解决方案**：
- 使用 `uniq()` 替代 `GROUP BY` + `count(DISTINCT)`
- 加 WHERE 条件缩小数据范围
- 或者使用 `approx_count_distinct()` 近似计算

---

## 4. 结合 slowlog 定位生产慢查询

先用 `slowlog` 找到最慢的查询：
```bash
ch slowlog --top 5 --threshold 5000 --hours 1
```

找到问题 SQL 后，在开发环境 profile：
```bash
ch profile "找到的慢 SQL"
```

这样就完成了完整的慢查询诊断流程，无需手写任何 `system.query_log` SQL。
