# ClickHawk

> 中文版文档: [README_CN.md](README_CN.md)

> The command-line Swiss Army knife for ClickHouse data engineers — query, diagnose, monitor, and explore, all in one command.

[![PyPI version](https://badge.fury.io/py/clickhawk.svg)](https://pypi.org/project/clickhawk/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)]()
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

---

## Why ClickHawk?

The ClickHouse ecosystem has many tools, but none of them address the real pain points data engineers face in daily work:

- Debugging slow queries? You have to hand-write `SELECT * FROM system.query_log WHERE ...` and wade through raw text output.
- Checking currently running queries? You have to log into `clickhouse-client` and run `SELECT * FROM system.processes`.
- Analyzing EXPLAIN output? It's plain-text tree output with no colors or hierarchy — nearly unreadable.
- Inspecting table schemas? You switch to DBeaver/DataGrip, which is slow and heavyweight.
- Comparing schemas across environments? No tool exists; you do it manually.

**ClickHawk unifies these high-frequency operations into a single `ch` command** — one line in the terminal, ready for scripting and pipeline integration.

---

## Comparison with Existing Tools

| Tool | Type | Formatted Output | Performance Analysis | Slow Queries | Live Monitoring | Schema Exploration | Script-Friendly |
|------|------|:---:|:---:|:---:|:---:|:---:|:---:|
| **ClickHawk** | CLI Tool | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `clickhouse-client` | Official CLI | ❌ | ❌ | ❌ | ❌ | Limited | ✅ |
| `clickhouse-connect` | Python SDK | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| DBeaver / DataGrip | GUI | ✅ | Limited | ❌ | ❌ | ✅ | ❌ |
| `infi.clickhouse_orm` | ORM Library | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

**Core advantages:**

- **One command, complete workflow** — from query execution to performance debugging to schema management, with no tool switching required.
- **Native terminal experience** — Rich-powered colored tables and live refresh, a significant step up from the raw text output of `clickhouse-client`.
- **Zero-configuration startup** — a single `.env` file, or set environment variables directly; ready to use after `pip install`.
- **Script-friendly** — supports `--format json/csv` output that can be piped directly.
- **Cross-platform** — pure Python implementation; runs on macOS, Linux, and Windows with no system-level dependencies.
- **Lightweight** — no Java, Electron, or any system dependencies required; just `pip install`.
- **Open source and extensible** — MIT license; contributions of new commands are welcome.

---

## Installation

```bash
pip install clickhawk
```

**Or install from source (development mode):**

```bash
git clone https://github.com/handsomevictor/clickhawk.git
cd clickhawk
pip install -e ".[dev]"
```

**Requirements:** Python 3.13+

> **No ClickHouse?** See the [local installation tutorial](TUTORIAL.md) for complete setup steps on macOS, Linux, and Windows, including solutions to common issues.

---

## Quick Start

**Step 1: Configure the connection**

```bash
cp .env.example .env
# Edit .env and fill in your ClickHouse connection details
```

Or set environment variables directly:

```bash
export CH_HOST=your-clickhouse-host
export CH_USER=default
export CH_PASSWORD=your-password
export CH_DATABASE=default
```

**Step 2: Verify the connection**

```bash
ch health
```

Example output:
```
✓  ClickHouse  24.3.1.1
    Uptime   : 7 days, 3 hours
    Databases: 5
    Tables   : 42
```

**Step 3: Start using**

```bash
# Execute a query
ch query "SELECT version()"

# Profile a query
ch profile "SELECT uniq(user_id) FROM events WHERE date >= today() - 7"

# View the top slow queries from the past 24 hours
ch slowlog --top 20

# Live-monitor currently running queries
ch monitor
```

---

## Command Reference

### `ch health` — Cluster Health Check

```bash
ch health
```

Checks connectivity and displays the ClickHouse version, uptime, and the number of databases and tables.

---

### `ch query` — Execute SQL Queries

```bash
ch query "SELECT database, count() FROM system.tables GROUP BY database"

# Specify output format
ch query "SELECT * FROM my_table" --format json
ch query "SELECT * FROM my_table" --format csv

# Limit the number of rows returned
ch query "SELECT * FROM large_table" --limit 100
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--format` | `-f` | `table` | Output format: `table` / `json` / `csv` |
| `--limit` | `-l` | none | Limit the number of rows returned |

---

### `ch profile` — Query Performance Analysis

```bash
ch profile "SELECT uniq(user_id) FROM events"
```

Example output:
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

Extracts real execution statistics from `system.query_log`, including rows read, bytes read, memory usage, and parts/ranges selected — the core metrics for optimizing ClickHouse queries.

---

### `ch slowlog` — Slow Query History

```bash
# View the top 20 queries slower than 1s in the last 24 hours
ch slowlog

# Customize parameters
ch slowlog --top 50 --threshold 500 --hours 48
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--top` | `-n` | `20` | Number of results to display |
| `--threshold` | `-t` | `1000` | Minimum duration in milliseconds |
| `--hours` | | `24` | Look-back window in hours |

---

### `ch schema show` — Inspect Table Structure

```bash
ch schema show my_table

# Specify a database
ch schema show my_table --database analytics
```

Displays column names, types, default values, and comments.

---

### `ch schema tables` — List All Tables

```bash
# List all user tables with size and row count
ch schema tables

# Filter by database
ch schema tables --database analytics
```

---

### `ch monitor` — Live Query Monitoring

```bash
# Default refresh interval is 2 seconds
ch monitor

# Set a custom refresh interval
ch monitor --interval 5
```

Displays running queries from `system.processes` in real time. Queries running longer than 5 seconds are highlighted in yellow; those running longer than 30 seconds are shown in red. Press `Ctrl+C` to exit.

---

### `ch explain` — Colorized EXPLAIN Tree

```bash
ch explain "SELECT uniq(user_id) FROM events WHERE date >= today() - 7"

# Show pipeline instead of plan
ch explain "SELECT count() FROM events" --kind pipeline

# Show raw syntax
ch explain "select count() from events" --kind syntax
```

Renders the EXPLAIN output as a color-coded tree — `ReadFromMergeTree` in cyan, `Filter` in yellow, `Aggregating` in magenta, and so on — making query plans readable at a glance.

---

### `ch schema diff` — Compare Schemas Across Environments

```bash
ch schema diff events --host2 staging.internal --database analytics
```

Compares a table's column list and types between two ClickHouse hosts. Added columns shown in green, removed in red, type changes in yellow.

---

### `ch migrate` — Schema Migration Management

```bash
# Show migration status
ch migrate status --dir migrations/

# Apply pending migrations (preview first)
ch migrate run --dir migrations/ --dry-run
ch migrate run --dir migrations/
```

Applies `.sql` files from a directory in alphabetical order. Tracks applied migrations in a `_clickhawk_migrations` table so runs are idempotent.

---

### `ch check nulls` — Null Percentage per Column

```bash
ch check nulls events --database analytics

# Sample 500k rows instead of the default 1M
ch check nulls large_table --sample 500000
```

Shows null count and null percentage for every column. Highlights columns above 10 % (yellow) and 50 % (red).

---

### `ch check cardinality` — Unique Value Count per Column

```bash
ch check cardinality events --database analytics
```

Reports approximate cardinality for each column, sorted from highest to lowest. Columns with < 1 % cardinality are flagged as candidates for `LowCardinality`; columns above 95 % are flagged for potential skip indexes.

---

### `ch export` — Export to CSV / JSON / Parquet

```bash
# Auto-detect format from file extension
ch export "SELECT * FROM events WHERE date = today()" --output today.csv
ch export "SELECT * FROM events" --output snapshot.parquet  # requires: pip install pyarrow

# Export a whole table by name (bare name → SELECT *)
ch export events --output events.json --limit 10000
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | required | Output file path |
| `--format` | `-f` | auto | Format: `csv` / `json` / `parquet` |
| `--limit` | `-l` | none | Max rows to export |

---

## Configuration

ClickHawk is configured via environment variables or a `.env` file (backed by Pydantic Settings, with priority-based override support):

| Variable | Default | Description |
|----------|---------|-------------|
| `CH_HOST` | `localhost` | ClickHouse host address |
| `CH_PORT` | `8123` | HTTP port |
| `CH_USER` | `default` | Username |
| `CH_PASSWORD` | `""` | Password |
| `CH_DATABASE` | `default` | Default database |
| `CH_SECURE` | `false` | Enable HTTPS/TLS |

Example `.env` file:

```env
CH_HOST=clickhouse.prod.internal
CH_PORT=8123
CH_USER=analyst
CH_PASSWORD=secret
CH_DATABASE=analytics
CH_SECURE=true
```

---

## Testing

**Run unit tests:**

```bash
pytest tests/unit/
```

**Run integration tests (requires a running ClickHouse instance):**

```bash
pytest tests/integration/ -m integration
```

**Run all tests:**

```bash
pytest
```

> Integration tests automatically skip if ClickHouse is not available, so the full test suite can always be run safely in any environment.

---

## Roadmap

| Version | Feature | Status |
|---------|---------|--------|
| **v0.1** | `query` / `profile` / `slowlog` / `schema` / `monitor` / `health` | ✅ Released |
| **v0.2** | `ch explain` — colorized tree-style EXPLAIN output | ✅ Released |
| **v0.2** | `ch schema diff` — schema comparison across environments | ✅ Released |
| **v0.2** | `ch migrate run/status` — file-based schema migration management | ✅ Released |
| **v0.2** | `ch check nulls/cardinality` — data quality scanning | ✅ Released |
| **v0.2** | `ch export` — export to CSV / JSON / Parquet | ✅ Released |
| **v0.3** | `ch kill <query_id>` — terminate a running query from the terminal | Planned |
| **v0.3** | `ch export --s3` — stream results directly to S3 | Planned |
| **v0.3** | `ch top` — top queries by CPU / memory / rows read (like `htop` for ClickHouse) | Planned |

---

## Documentation

| Document | Description |
|----------|-------------|
| [TUTORIAL.md](TUTORIAL.md) | Local ClickHouse setup guide for macOS / Linux / Windows, including full config and troubleshooting |
| [CHANGELOG.md](CHANGELOG.md) | Version history and release notes |
| [LESSONS_LEARNED.md](LESSONS_LEARNED.md) | Pitfalls encountered during development — useful for contributors |
| [STRUCTURE.md](STRUCTURE.md) | Project layout and module responsibilities |
| [examples/BASIC_QUERY.md](examples/BASIC_QUERY.md) | `ch query` usage examples |
| [examples/PROFILING.md](examples/PROFILING.md) | `ch profile` — how to read metrics and diagnose slow queries |
| [examples/MONITORING.md](examples/MONITORING.md) | `ch monitor` + `ch slowlog` — production incident workflow |
| [examples/SCHEMA_EXPLORATION.md](examples/SCHEMA_EXPLORATION.md) | `ch schema` — table inspection and schema workflows |

> All documents are available in English and Chinese (append `_CN` to the filename for the Chinese version, e.g. `TUTORIAL_CN.md`).

---

## Contributing

PRs and issues are welcome!

```bash
# Clone the repository
git clone https://github.com/your-username/clickhawk.git
cd clickhawk

# Install development dependencies
pip install -e ".[dev]"

# Run the linter
ruff check .

# Run type checks
mypy clickhawk/

# Run tests
pytest
```

---

## License

MIT © Victor Li

---

<p align="center">
  If ClickHawk has saved you time, please give it a Star — it means a lot to the project.
</p>
