# Changelog

This project follows the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format, and versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Planned
- `ch explain` — colorized tree-style EXPLAIN PLAN output
- `ch schema diff` — compare schema differences between two ClickHouse environments
- `ch migrate run/status` — file-based schema migration management

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
