# ClickHawk

> 中文版文档: [README_CN.md](README_CN.md)

> The command-line Swiss Army knife for ClickHouse data engineers — query, diagnose, monitor, and explore, all in one command.

[![PyPI version](https://badge.fury.io/py/clickhawk.svg)](https://pypi.org/project/clickhawk/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)]()
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

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

```
✓  ClickHouse  24.3.1.1
    Uptime   : 7 days, 3 hours
    Databases: 5
    Tables   : 42
```

**Step 3: Start using**

```bash
ch query "SELECT version()"
ch profile "SELECT uniq(user_id) FROM events WHERE date >= today() - 7"
ch slowlog --top 20
ch monitor
```

---

## Command Reference

### `ch health` — Cluster Health Check

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

### `ch query` — Execute SQL Queries

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
# JSON / CSV output for scripting
ch query "SELECT database, count() FROM system.tables GROUP BY database" --format json

# Limit rows
ch query "SELECT * FROM events" --limit 5
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

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--top` | `-n` | `20` | Number of results to display |
| `--threshold` | `-t` | `1000` | Minimum duration in milliseconds |
| `--hours` | | `24` | Look-back window in hours |

---

### `ch schema show` — Inspect Table Structure

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

### `ch schema tables` — List All Tables

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

### `ch monitor` — Live Query Monitoring

```bash
ch monitor           # default 2s refresh
ch monitor --interval 5
```

```
Running queries  (2026-03-17 09:15:30)
┌──────────────────┬──────────┬───────────┬──────────────────────────────────────┐
│ query_id         │ elapsed  │ user      │ query                                │
├──────────────────┼──────────┼───────────┼──────────────────────────────────────┤
│ 3a7f1c2b…        │  38.2 s  │ analyst   │ SELECT uniq(session_id) FROM events… │  ← red
│ d91e4f07…        │   6.7 s  │ default   │ SELECT count() FROM orders WHERE …   │  ← yellow
└──────────────────┴──────────┴───────────┴──────────────────────────────────────┘
```

Queries running longer than 5 seconds are highlighted in yellow; those running longer than 30 seconds are shown in red. Press `Ctrl+C` to exit.

---

### `ch explain` — Colorized EXPLAIN Tree

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

Renders the EXPLAIN output as a color-coded tree — `ReadFromMergeTree` in cyan, `Filter` in yellow, `Aggregating` in magenta — making query plans readable at a glance.

---

### `ch schema diff` — Compare Schemas Across Environments

```bash
ch schema diff events --host2 staging.internal --database analytics
```

```
Schema diff: demo.events  (prod vs staging)
┌─────────────┬──────────────────────────┬──────────────────────────┐
│ Column      │ prod                     │ staging                  │
├─────────────┼──────────────────────────┼──────────────────────────┤
│ session_id  │ String                   │ —           (removed)    │  ← red
│ v2_flag     │ —           (missing)    │ UInt8                    │  ← green
│ event_type  │ String                   │ LowCardinality(String)   │  ← yellow
└─────────────┴──────────────────────────┴──────────────────────────┘
```

---

### `ch migrate` — Schema Migration Management

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

Applies `.sql` files from a directory in alphabetical order. Tracks applied migrations in a `_clickhawk_migrations` table so runs are idempotent.

---

### `ch check nulls` — Null Percentage per Column

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
│ session_id  │    142,301 │  14.23 % │  ← yellow
│ referrer    │    603,812 │  60.38 % │  ← red
└─────────────┴────────────┴──────────┘
```

---

### `ch check cardinality` — Unique Value Count per Column

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

### `ch export` — Export to CSV / JSON / Parquet / S3

```bash
ch export "SELECT * FROM events WHERE date = today()" --output today.csv
ch export "SELECT * FROM events" --output snapshot.parquet  # requires: pip install pyarrow
ch export events --output events.json --limit 10000

# Upload directly to S3 (requires: pip install boto3)
ch export "SELECT * FROM events" --s3 s3://my-bucket/exports/events.csv
```

```
✓ 12,847,291 rows → today.csv
✓ 12,847,291 rows → s3://my-bucket/exports/events.csv
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | — | Local output file |
| `--s3` | | — | S3 destination URI (`s3://bucket/key`) |
| `--format` | `-f` | auto | Format: `csv` / `json` / `parquet` |
| `--limit` | `-l` | none | Max rows to export |

S3 credentials are read from environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) or `~/.aws/credentials` via boto3.

---

### `ch kill` — Kill Running Queries

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

### `ch top` — Top Queries by Resource Usage

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

| `--sort` value | Description |
|---------------|-------------|
| `elapsed` | Time since query started (default) |
| `memory` | Current memory usage |
| `rows` | Rows read so far |
| `cpu` | CPU time (microseconds) |

Press `Ctrl+C` to exit.

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
| **v0.3** | `ch kill <query_id>` — terminate a running query from the terminal | ✅ Released |
| **v0.3** | `ch export --s3` — upload results directly to S3 | ✅ Released |
| **v0.3** | `ch top` — top queries by CPU / memory / rows / elapsed (live dashboard) | ✅ Released |
| **v0.4** | `ch top --filter <user>` — narrow live view to a specific user | Planned |
| **v0.4** | `ch export --s3` chunked multipart upload for very large result sets | Planned |
| **v0.4** | `ch profile --compare` — diff two query profiles side by side | Planned |

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
