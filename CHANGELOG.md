# Changelog

This project follows the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format, and versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

---

## [0.2.0] — 2026-03-17

### Added
- **`ch explain <sql>`** — colorized tree-style EXPLAIN PLAN / PIPELINE / SYNTAX output powered by Rich `Tree`; node types (Filter, Aggregating, ReadFromMergeTree, …) are color-coded for readability
- **`ch schema diff`** — compare a table's schema between two ClickHouse environments; outputs added columns (green), removed columns (red), and type changes (yellow)
- **`ch migrate run`** — apply pending `.sql` migration files from a directory in alphabetical order; tracks applied migrations in a `_clickhawk_migrations` table; supports `--dry-run`
- **`ch migrate status`** — display which migrations are applied, pending, or missing from disk
- **`ch check nulls <table>`** — scan a table (with configurable `--sample` size) and report null percentage per column; highlights columns above 10 % (yellow) and 50 % (red)
- **`ch check cardinality <table>`** — report approximate unique-value count per column with verdict labels (low/medium/high); helps identify candidates for `LowCardinality` or skip indexes
- **`ch export <sql>`** — export query results to CSV, JSON, or Parquet; format auto-detected from the output file extension (`--output out.parquet`); Parquet requires `pip install pyarrow`

### Technical
- New command modules: `explain.py`, `check.py`, `export.py`; `migrate.py` fully rewritten
- `schema.py` extended with `diff` sub-command
- All new commands registered in `main.py`
- Integration test coverage added for all new commands (64 tests total)

### Planned
- `ch kill <query_id>` — terminate a running query from the terminal
- `ch export … --s3` — stream results directly to S3

---

## [0.1.0] — 2026-03-16

### Added
- **`ch health`** — cluster health check displaying version, uptime, database count, and table count
- **`ch query <sql>`** — execute SQL queries with support for `table` (default) / `json` / `csv` output formats and `--limit` row truncation
- **`ch profile <sql>`** — query performance analysis extracting real execution statistics from `system.query_log` (wall time, DB time, rows/bytes read, memory, parts/ranges hit count)
- **`ch slowlog`** — slow query history ranking with customizable `--top`, `--threshold` (milliseconds), and `--hours` parameters
- **`ch schema show <table>`** — display table schema (column name / type / default / comment) with `--database` filter support
- **`ch schema tables`** — list all user tables showing database, engine, disk size, and row count with `--database` filter support
- **`ch monitor`** — real-time live dashboard polling `system.processes`, with color-coded long-running queries (>5s yellow, >30s red) and customizable `--interval` refresh rate
- **`ch migrate run/status`** — placeholder commands, to be fully implemented in v0.2

### Technical Foundation
- CLI framework built on **Typer** with `ch` as the command entry point
- **Rich** for colorized table rendering and Live real-time refresh
- **clickhouse-connect** for ClickHouse connectivity (HTTP protocol)
- **Pydantic Settings v2** for configuration management with `.env` file and environment variable support
- Singleton pattern for the connection client to avoid repeated handshakes
- Python 3.13+ support

---

[Unreleased]: https://github.com/your-username/clickhawk/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-username/clickhawk/releases/tag/v0.1.0
