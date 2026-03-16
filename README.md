# 🦅 ClickHawk

> ClickHouse 数据工程师的命令行瑞士军刀 — 查询、诊断、监控、探索，一个命令搞定。

[![PyPI version](https://badge.fury.io/py/clickhawk.svg)](https://pypi.org/project/clickhawk/)
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

> **没有 ClickHouse？** 查看 [本地安装教程 →](tutorial.md)，包含 macOS / Linux / Windows 完整步骤及常见坑的解决方案。

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

输出示例：
```
✓  ClickHouse  24.3.1.1
    Uptime   : 7 days, 3 hours
    Databases: 5
    Tables   : 42
```

**第三步：开始使用**

```bash
# 执行查询
ch query "SELECT version()"

# 分析慢查询
ch profile "SELECT uniq(user_id) FROM events WHERE date >= today() - 7"

# 查看过去 24h 的慢查询排行
ch slowlog --top 20

# 实时监控当前运行中的查询
ch monitor
```

---

## 命令参考

### `ch health` — 集群健康检查

```bash
ch health
```

检查连接状态，显示版本、uptime、数据库和表的数量。

---

### `ch query` — 执行 SQL 查询

```bash
ch query "SELECT database, count() FROM system.tables GROUP BY database"

# 指定输出格式
ch query "SELECT * FROM my_table" --format json
ch query "SELECT * FROM my_table" --format csv

# 限制返回行数
ch query "SELECT * FROM large_table" --limit 100
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

输出示例：
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
# 查看最近 24h 慢于 1s 的前 20 条查询
ch slowlog

# 自定义参数
ch slowlog --top 50 --threshold 500 --hours 48
```

| 选项 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--top` | `-n` | `20` | 显示条数 |
| `--threshold` | `-t` | `1000` | 最小耗时（毫秒） |
| `--hours` | | `24` | 回溯时间范围（小时） |

---

### `ch schema show` — 查看表结构

```bash
ch schema show my_table

# 指定数据库
ch schema show my_table --database analytics
```

显示列名、类型、默认值和注释。

---

### `ch schema tables` — 列出所有表

```bash
# 列出所有用户表（含大小和行数）
ch schema tables

# 筛选指定数据库
ch schema tables --database analytics
```

---

### `ch monitor` — 实时查询监控

```bash
# 默认每 2s 刷新一次
ch monitor

# 自定义刷新频率
ch monitor --interval 5
```

实时展示 `system.processes` 中的运行查询，超过 5s 显示黄色警告，超过 30s 显示红色告警。按 `Ctrl+C` 退出。

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

## 路线图

| 版本 | 功能 | 状态 |
|------|------|------|
| **v0.1** | `query` / `profile` / `slowlog` / `schema` / `monitor` / `health` | ✅ 已发布 |
| **v0.2** | `ch explain` 彩色树形 EXPLAIN 输出 | 🔜 计划中 |
| **v0.2** | `ch schema diff` 两环境 schema 对比 | 🔜 计划中 |
| **v0.2** | `ch migrate` schema 迁移管理 | 🔜 计划中 |
| **v0.3** | `ch check nulls/cardinality` 数据质量扫描 | 📋 规划中 |
| **v0.3** | `ch export` 导出到 Parquet/CSV/JSON/S3 | 📋 规划中 |

---

## 贡献

欢迎 PR 和 Issue！

```bash
# 克隆仓库
git clone https://github.com/your-username/clickhawk.git
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
  如果 ClickHawk 帮你节省了时间，请给个 ⭐ Star — 这对项目意义重大。
</p>
