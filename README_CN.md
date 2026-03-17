# ClickHawk

> English version: [README.md](README.md)

> ClickHouse 数据工程师的命令行瑞士军刀 — 查询、诊断、监控、探索，一个命令搞定。

[![PyPI version](https://img.shields.io/pypi/v/clickhawk)](https://pypi.org/project/clickhawk/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)]()
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

---

## 为什么需要 ClickHawk？

ClickHouse 生态里有很多工具，但没有一个能解决数据工程师日常工作中的真实痛点：

- 调试慢查询？要手写 `SELECT * FROM system.query_log WHERE ...` 看一堆裸文本
- 查看当前运行查询？要登录 `clickhouse-client` 再执行 `SELECT * FROM system.processes`
- 分析 EXPLAIN 输出？纯文本 tree，没有颜色和层次感，几乎无法阅读
- 查表结构？切换到 DBeaver/DataGrip，又慢又重
- 不同环境 schema 对比？没有工具，只能手动

**ClickHawk 把这些高频操作统一成一个 `ch` 命令**，终端里一行搞定，适合脚本化和 pipeline 集成。

---

## 与现有工具的对比

| 工具 | 类型 | 格式化输出 | 性能分析 | 慢查询 | 实时监控 | Schema 探索 | 脚本友好 |
|------|------|:---:|:---:|:---:|:---:|:---:|:---:|
| **ClickHawk** | CLI 工具 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `clickhouse-client` | 官方 CLI | ❌ | ❌ | ❌ | ❌ | 有限 | ✅ |
| `clickhouse-connect` | Python SDK | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| DBeaver / DataGrip | GUI | ✅ | 有限 | ❌ | ❌ | ✅ | ❌ |
| `infi.clickhouse_orm` | ORM 库 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

**核心优势：**

- **一条命令，完整工作流** — 从查询执行到性能调试到 schema 管理，无需切换工具
- **终端原生体验** — 基于 Rich 的彩色表格、实时刷新，比 `clickhouse-client` 的裸文本体验好一个量级
- **零配置启动** — 一个 `.env` 文件，或直接设置环境变量，`pip install` 即用
- **脚本友好** — 支持 `--format json/csv` 输出，可以直接接管道
- **跨平台** — 纯 Python 实现，macOS、Linux、Windows 均可运行，无任何系统级依赖
- **轻量无依赖** — 不需要 Java、Electron 或任何系统依赖，`pip install` 即用
- **开源可扩展** — MIT 协议，欢迎贡献新命令

---

## 安装

```bash
pip install clickhawk
```

**或者从源码安装（开发模式）：**

```bash
git clone https://github.com/handsomevictor/clickhawk.git
cd clickhawk
pip install -e ".[dev]"
```

**环境要求：** Python 3.13+

> **没有 ClickHouse？** 查看 [本地安装教程 →](TUTORIAL_CN.md)，包含 macOS / Linux / Windows 完整步骤及常见坑的解决方案。

---

## 快速开始

**第一步：配置连接**

```bash
cp .env.example .env
# 编辑 .env，填入你的 ClickHouse 连接信息
```

或者直接设置环境变量：

```bash
export CH_HOST=your-clickhouse-host
export CH_USER=default
export CH_PASSWORD=your-password
export CH_DATABASE=default
```

**第二步：验证连接**

```bash
ch health
```

```
✓  ClickHouse  24.3.1.1
    Uptime   : 7 days, 3 hours
    Databases: 5
    Tables   : 42
```

**第三步：开始使用**

```bash
ch query "SELECT version()"
ch profile "SELECT uniq(user_id) FROM events WHERE date >= today() - 7"
ch slowlog --top 20
ch monitor
```

---

## 命令参考

### `ch health` — 集群健康检查

```bash
ch health
```

```
✓  ClickHouse  24.3.1.1
    Uptime   : 7 days, 3 hours
    Databases: 5
    Tables   : 42
```

---

### `ch query` — 执行 SQL 查询

```bash
ch query "SELECT database, count() FROM system.tables GROUP BY database"
```

```
┌──────────────────┬──────────┐
│ database         │ count()  │
├──────────────────┼──────────┤
│ default          │       12 │
│ system           │       73 │
│ demo             │        5 │
└──────────────────┴──────────┘
3 rows  (0.021s)
```

```bash
# JSON / CSV 输出，方便接管道
ch query "SELECT database, count() FROM system.tables GROUP BY database" --format json

# 限制行数
ch query "SELECT * FROM events" --limit 5
```

| 选项 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--format` | `-f` | `table` | 输出格式：`table` / `json` / `csv` |
| `--limit` | `-l` | 无 | 限制返回行数 |

---

### `ch profile` — 查询性能分析

```bash
ch profile "SELECT uniq(user_id) FROM events"
```

```
╔══════════════════════╦══════════════╗
║ Metric               ║ Value        ║
╠══════════════════════╬══════════════╣
║ Wall time            ║ 0.342s       ║
║ DB duration          ║ 298 ms       ║
║ Rows read            ║ 12,847,291   ║
║ Bytes read           ║ 412.30 MB    ║
║ Memory used          ║ 87.50 MB     ║
║ Parts selected       ║ 24           ║
║ Ranges selected      ║ 156          ║
╚══════════════════════╩══════════════╝
```

从 `system.query_log` 提取真实的执行统计，包括读取的行数、字节数、内存使用、选中的 parts 和 ranges —— 这些是优化 ClickHouse 查询的核心指标。

---

### `ch slowlog` — 慢查询历史

```bash
ch slowlog
ch slowlog --top 50 --threshold 500 --hours 48
```

```
┌──────────────────────┬────────────┬───────────┬──────────────────────────────────────┐
│ started              │ duration   │ user      │ query                                │
├──────────────────────┼────────────┼───────────┼──────────────────────────────────────┤
│ 2026-03-17 09:12:44  │ 4,821 ms   │ analyst   │ SELECT uniq(session_id) FROM events… │
│ 2026-03-17 08:55:01  │ 3,102 ms   │ default   │ SELECT * FROM orders WHERE date >=…  │
└──────────────────────┴────────────┴───────────┴──────────────────────────────────────┘
```

| 选项 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--top` | `-n` | `20` | 显示条数 |
| `--threshold` | `-t` | `1000` | 最小耗时（毫秒） |
| `--hours` | | `24` | 回溯时间范围（小时） |

---

### `ch schema show` — 查看表结构

```bash
ch schema show events
ch schema show events --database analytics
```

```
┌─────────────┬─────────────────────────┬─────────┬─────────┐
│ Column      │ Type                    │ Default │ Comment │
├─────────────┼─────────────────────────┼─────────┼─────────┤
│ event_id    │ UUID                    │         │         │
│ user_id     │ UInt64                  │         │         │
│ event_type  │ LowCardinality(String)  │         │         │
│ date        │ Date                    │         │         │
│ created_at  │ DateTime                │ now()   │         │
└─────────────┴─────────────────────────┴─────────┴─────────┘
```

---

### `ch schema tables` — 列出所有表

```bash
ch schema tables
ch schema tables --database analytics
```

```
┌──────────────┬──────────────┬──────────────────┬──────────┬────────────┐
│ database     │ table        │ engine           │ size     │ rows       │
├──────────────┼──────────────┼──────────────────┼──────────┼────────────┤
│ demo         │ events       │ MergeTree        │ 412.3 MB │ 12,847,291 │
│ demo         │ orders       │ MergeTree        │  87.1 MB │  1,203,445 │
│ demo         │ users        │ ReplacingMergeT… │   2.1 MB │     45,231 │
└──────────────┴──────────────┴──────────────────┴──────────┴────────────┘
```

---

### `ch monitor` — 实时查询监控

```bash
ch monitor           # 默认每 2s 刷新一次
ch monitor --interval 5
```

```
Running queries  (2026-03-17 09:15:30)
┌──────────────────┬──────────┬───────────┬──────────────────────────────────────┐
│ query_id         │ elapsed  │ user      │ query                                │
├──────────────────┼──────────┼───────────┼──────────────────────────────────────┤
│ 3a7f1c2b…        │  38.2 s  │ analyst   │ SELECT uniq(session_id) FROM events… │  ← 红色
│ d91e4f07…        │   6.7 s  │ default   │ SELECT count() FROM orders WHERE …   │  ← 黄色
└──────────────────┴──────────┴───────────┴──────────────────────────────────────┘
```

超过 5s 显示黄色警告，超过 30s 显示红色告警。按 `Ctrl+C` 退出。

---

### `ch explain` — 彩色 EXPLAIN 树

```bash
ch explain "SELECT uniq(user_id) FROM events WHERE date >= today() - 7"
ch explain "SELECT count() FROM events" --kind pipeline
ch explain "select count() from events" --kind syntax
```

```
Expression
└── Aggregating
    └── Filter
        └── ReadFromMergeTree (demo.events)
              Indexes:
                PrimaryKey
                  Condition: true
                  Parts: 24/24
                  Granules: 3721/3721
```

以彩色树形渲染 EXPLAIN 输出 —— `ReadFromMergeTree` 青色、`Filter` 黄色、`Aggregating` 品红色 —— 让查询计划一目了然。

---

### `ch schema diff` — 跨环境 Schema 对比

```bash
ch schema diff events --host2 staging.internal --database analytics
```

```
Schema diff: demo.events  (prod vs staging)
┌─────────────┬──────────────────────────┬──────────────────────────┐
│ Column      │ prod                     │ staging                  │
├─────────────┼──────────────────────────┼──────────────────────────┤
│ session_id  │ String                   │ —           (removed)    │  ← 红色
│ v2_flag     │ —           (missing)    │ UInt8                    │  ← 绿色
│ event_type  │ String                   │ LowCardinality(String)   │  ← 黄色
└─────────────┴──────────────────────────┴──────────────────────────┘
```

---

### `ch migrate` — Schema 迁移管理

```bash
ch migrate status --dir migrations/
ch migrate run --dir migrations/ --dry-run
ch migrate run --dir migrations/
```

```
Migration status  (dir: migrations/)
┌───────────────────────────────┬──────────┬──────────────────────┐
│ File                          │ Status   │ Applied at           │
├───────────────────────────────┼──────────┼──────────────────────┤
│ 001_create_events.sql         │ applied  │ 2026-03-15 10:22:01  │
│ 002_add_session_id.sql        │ applied  │ 2026-03-16 08:45:33  │
│ 003_add_v2_flag.sql           │ pending  │ —                    │
└───────────────────────────────┴──────────┴──────────────────────┘

✓ Applied 003_add_v2_flag.sql
1 migration applied.
```

按字母顺序执行目录下的 `.sql` 文件，通过 `_clickhawk_migrations` 表追踪已执行的迁移，保证幂等性。

---

### `ch check nulls` — 列级空值率扫描

```bash
ch check nulls events --database analytics
ch check nulls large_table --sample 500000
```

```
Null analysis: demo.events  (sample: 1,000,000 rows)
┌─────────────┬────────────┬──────────┐
│ Column      │ Null count │ Null %   │
├─────────────┼────────────┼──────────┤
│ event_id    │          0 │   0.00 % │
│ user_id     │          0 │   0.00 % │
│ session_id  │    142,301 │  14.23 % │  ← 黄色
│ referrer    │    603,812 │  60.38 % │  ← 红色
└─────────────┴────────────┴──────────┘
```

---

### `ch check cardinality` — 列级基数扫描

```bash
ch check cardinality events --database analytics
```

```
Cardinality: demo.events  (sample: 1,000,000 rows)
┌─────────────┬─────────────┬───────────┬──────────────────────────────┐
│ Column      │ Cardinality │ Ratio %   │ Verdict                      │
├─────────────┼─────────────┼───────────┼──────────────────────────────┤
│ user_id     │     891,204 │   89.12 % │ high — consider skip index   │
│ session_id  │     712,448 │   71.24 % │ high                         │
│ event_type  │          12 │    0.00 % │ low — consider LowCardinality│
│ date        │         365 │    0.04 % │ low — consider LowCardinality│
└─────────────┴─────────────┴───────────┴──────────────────────────────┘
```

---

### `ch export` — 导出到 CSV / JSON / Parquet / S3

```bash
ch export "SELECT * FROM events WHERE date = today()" --output today.csv
ch export "SELECT * FROM events" --output snapshot.parquet  # 需要: pip install pyarrow
ch export events --output events.json --limit 10000

# 直接上传到 S3（需要: pip install boto3）
ch export "SELECT * FROM events" --s3 s3://my-bucket/exports/events.csv
```

```
✓ 12,847,291 rows → today.csv
✓ 12,847,291 rows → s3://my-bucket/exports/events.csv
```

| 选项 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--output` | `-o` | — | 本地输出文件 |
| `--s3` | | — | S3 目标 URI（`s3://bucket/key`） |
| `--format` | `-f` | 自动 | 格式：`csv` / `json` / `parquet` |
| `--limit` | `-l` | 无 | 最大导出行数 |

S3 凭证从环境变量（`AWS_ACCESS_KEY_ID`、`AWS_SECRET_ACCESS_KEY`）或 `~/.aws/credentials` 读取。

---

### `ch kill` — 终止运行中的查询

```bash
ch kill 3a7f1c2b
ch kill --user analyst
ch kill --user etl_user --yes
```

```
Queries to kill:
┌──────────────────┬──────────┬───────────┬──────────────────────────────────────┐
│ query_id         │ elapsed  │ user      │ query                                │
├──────────────────┼──────────┼───────────┼──────────────────────────────────────┤
│ 3a7f1c2b…        │  38.2 s  │ analyst   │ SELECT uniq(session_id) FROM events… │
└──────────────────┴──────────┴───────────┴──────────────────────────────────────┘
Kill 1 query? [y/N]: y
✓ Killed 3a7f1c2b…
```

---

### `ch top` — 按资源排序的 Top 查询

```bash
ch top
ch top --sort memory
ch top --sort rows --top 10 --interval 5
```

```
 Running: 3   Memory: 234.5 MB   Rows read: 28,103,445

┌──────────────────┬──────────┬───────────┬───────────────┬──────────────────────────────────────┐
│ query_id         │ Elapsed  │ user      │ Memory        │ query                                │
├──────────────────┼──────────┼───────────┼───────────────┼──────────────────────────────────────┤
│ 3a7f1c2b…        │  38.2 s  │ analyst   │    87.5 MB    │ SELECT uniq(session_id) FROM events… │
│ d91e4f07…        │   6.7 s  │ default   │    45.0 MB    │ SELECT count() FROM orders WHERE …   │
└──────────────────┴──────────┴───────────┴───────────────┴──────────────────────────────────────┘
```

| `--sort` 值 | 说明 |
|------------|------|
| `elapsed` | 查询已运行时长（默认） |
| `memory` | 当前内存用量 |
| `rows` | 已读取行数 |
| `cpu` | CPU 时间（微秒） |

按 `Ctrl+C` 退出。

---

## 配置

ClickHawk 通过环境变量或 `.env` 文件进行配置（基于 Pydantic Settings，支持优先级覆盖）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CH_HOST` | `localhost` | ClickHouse 主机地址 |
| `CH_PORT` | `8123` | HTTP 端口 |
| `CH_USER` | `default` | 用户名 |
| `CH_PASSWORD` | `""` | 密码 |
| `CH_DATABASE` | `default` | 默认数据库 |
| `CH_SECURE` | `false` | 是否启用 HTTPS/TLS |

`.env` 文件示例：

```env
CH_HOST=clickhouse.prod.internal
CH_PORT=8123
CH_USER=analyst
CH_PASSWORD=secret
CH_DATABASE=analytics
CH_SECURE=true
```

---

## 测试

**运行单元测试：**

```bash
pytest tests/unit/
```

**运行集成测试（需要运行中的 ClickHouse 实例）：**

```bash
pytest tests/integration/ -m integration
```

**运行所有测试：**

```bash
pytest
```

> 如果 ClickHouse 不可用，集成测试会自动跳过，因此可以在任何环境中安全地运行完整测试套件。

---

## 路线图

| 版本 | 功能 | 状态 |
|------|------|------|
| **v0.1** | `query` / `profile` / `slowlog` / `schema` / `monitor` / `health` | ✅ 已发布 |
| **v0.2** | `ch explain` — 彩色树形 EXPLAIN 输出 | ✅ 已发布 |
| **v0.2** | `ch schema diff` — 跨环境 schema 对比 | ✅ 已发布 |
| **v0.2** | `ch migrate run/status` — 文件驱动的 schema 迁移管理 | ✅ 已发布 |
| **v0.2** | `ch check nulls/cardinality` — 数据质量扫描 | ✅ 已发布 |
| **v0.2** | `ch export` — 导出到 CSV / JSON / Parquet | ✅ 已发布 |
| **v0.3** | `ch kill <query_id>` — 从终端终止运行中的查询 | ✅ 已发布 |
| **v0.3** | `ch export --s3` — 直接上传结果到 S3 | ✅ 已发布 |
| **v0.3** | `ch top` — 按 CPU / 内存 / 行数 / 耗时排序的实时 Top 面板 | ✅ 已发布 |
| **v0.4** | `ch top --filter <user>` — 按用户过滤实时视图 | 规划中 |
| **v0.4** | `ch export --s3` 超大结果集分块 Multipart 上传 | 规划中 |
| **v0.4** | `ch profile --compare` — 两次查询 Profile 对比 | 规划中 |

---

## 文档索引

| 文档 | 说明 |
|------|------|
| [TUTORIAL_CN.md](TUTORIAL_CN.md) | 本地 ClickHouse 安装教程（macOS / Linux / Windows），含完整配置和常见报错解决 |
| [CHANGELOG_CN.md](CHANGELOG_CN.md) | 版本历史和发布说明 |
| [LESSONS_LEARNED_CN.md](LESSONS_LEARNED_CN.md) | 开发过程中踩过的坑，供贡献者参考 |
| [STRUCTURE_CN.md](STRUCTURE_CN.md) | 项目目录结构和模块职责说明 |
| [examples/BASIC_QUERY_CN.md](examples/BASIC_QUERY_CN.md) | `ch query` 使用示例 |
| [examples/PROFILING_CN.md](examples/PROFILING_CN.md) | `ch profile` — 如何读懂指标、诊断慢查询 |
| [examples/MONITORING_CN.md](examples/MONITORING_CN.md) | `ch monitor` + `ch slowlog` — 生产故障排查流程 |
| [examples/SCHEMA_EXPLORATION_CN.md](examples/SCHEMA_EXPLORATION_CN.md) | `ch schema` — 表结构检查和 schema 工作流 |

> 所有文档均有英文和中文两个版本。英文版去掉文件名中的 `_CN` 即可（例如 `TUTORIAL.md`）。

---

## 贡献

欢迎 PR 和 Issue！→ [github.com/handsomevictor/clickhawk](https://github.com/handsomevictor/clickhawk/tree/main)

```bash
# 克隆仓库
git clone https://github.com/handsomevictor/clickhawk.git
cd clickhawk

# 安装开发依赖
pip install -e ".[dev]"

# 运行 linter
ruff check .

# 运行类型检查
mypy clickhawk/

# 运行测试
pytest
```

---

## 许可证

MIT © Victor Li

---

<p align="center">
  如果 ClickHawk 帮你节省了时间，请给个 Star — 这对项目意义重大。
</p>
